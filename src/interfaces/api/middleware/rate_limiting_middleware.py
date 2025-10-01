import time
import hashlib
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..infrastructure.observability.observability import MetricsService, StructuredLogger


class RateLimitStrategy(Enum):
    """Estrategias de rate limiting disponibles."""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"  
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"


@dataclass
class RateLimitConfig:
    """Configuración para rate limiting."""
    limit: int = 100  # Número de requests permitidos
    window_seconds: int = 3600  # Ventana de tiempo en segundos
    strategy: RateLimitStrategy = RateLimitStrategy.FIXED_WINDOW
    burst_limit: Optional[int] = None  # Para token bucket
    leak_rate: Optional[float] = None  # Para leaky bucket
    key_function: Optional[Callable[[Request], str]] = None
    excluded_paths: list = field(default_factory=list)
    whitelist_ips: list = field(default_factory=list)
    headers_enabled: bool = True


@dataclass
class RateLimitResult:
    """Resultado de verificación de rate limit."""
    allowed: bool
    remaining: int
    reset_time: int
    retry_after: Optional[int] = None
    limit: int = 0
    used: int = 0


class RateLimitStore(ABC):
    """Interfaz para almacenamiento de datos de rate limiting."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Obtener datos de rate limiting para una clave."""
        pass
    
    @abstractmethod
    async def set(
        self, 
        key: str, 
        value: Dict[str, Any], 
        ttl: Optional[int] = None
    ):
        """Establecer datos de rate limiting para una clave."""
        pass
    
    @abstractmethod
    async def increment(self, key: str, window_seconds: int) -> int:
        """Incrementar contador para una clave."""
        pass
    
    @abstractmethod
    async def delete(self, key: str):
        """Eliminar datos para una clave."""
        pass


class MemoryRateLimitStore(RateLimitStore):
    """Implementación en memoria para rate limiting (desarrollo/testing)."""
    
    def __init__(self):
        self._data: Dict[str, Dict[str, Any]] = {}
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        current_time = time.time()
        
        if key in self._data:
            data = self._data[key]
            # Check if data has expired
            if data.get("expires_at", 0) > current_time:
                return data
            else:
                # Clean up expired data
                del self._data[key]
        
        return None
    
    async def set(
        self, 
        key: str, 
        value: Dict[str, Any], 
        ttl: Optional[int] = None
    ):
        current_time = time.time()
        
        if ttl:
            value["expires_at"] = current_time + ttl
        
        self._data[key] = value
    
    async def increment(self, key: str, window_seconds: int) -> int:
        current_time = time.time()
        window_start = int(current_time // window_seconds) * window_seconds
        
        data = await self.get(key)
        
        if not data or data.get("window_start") != window_start:
            # New window
            data = {
                "count": 1,
                "window_start": window_start,
                "first_request": current_time
            }
        else:
            # Same window
            data["count"] += 1
        
        await self.set(key, data, window_seconds)
        return data["count"]
    
    async def delete(self, key: str):
        if key in self._data:
            del self._data[key]


class RateLimiter(ABC):
    """Interfaz base para implementaciones de rate limiting."""
    
    @abstractmethod
    async def is_allowed(
        self, 
        key: str, 
        config: RateLimitConfig
    ) -> RateLimitResult:
        """Verificar si un request está permitido."""
        pass


class FixedWindowRateLimiter(RateLimiter):
    """Rate limiter con ventana fija."""
    
    def __init__(self, store: RateLimitStore):
        self.store = store
    
    async def is_allowed(
        self, 
        key: str, 
        config: RateLimitConfig
    ) -> RateLimitResult:
        current_time = time.time()
        window_start = int(current_time // config.window_seconds) * config.window_seconds
        window_key = f"{key}:{window_start}"
        
        # Get current count
        data = await self.store.get(window_key)
        current_count = data.get("count", 0) if data else 0
        
        if current_count >= config.limit:
            # Rate limit exceeded
            reset_time = int(window_start + config.window_seconds)
            retry_after = reset_time - int(current_time)
            
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=reset_time,
                retry_after=retry_after,
                limit=config.limit,
                used=current_count
            )
        
        # Increment counter
        new_count = await self.store.increment(window_key, config.window_seconds)
        
        reset_time = int(window_start + config.window_seconds)
        remaining = max(0, config.limit - new_count)
        
        return RateLimitResult(
            allowed=True,
            remaining=remaining,
            reset_time=reset_time,
            limit=config.limit,
            used=new_count
        )


class SlidingWindowRateLimiter(RateLimiter):
    """Rate limiter con ventana deslizante."""
    
    def __init__(self, store: RateLimitStore):
        self.store = store
    
    async def is_allowed(
        self, 
        key: str, 
        config: RateLimitConfig
    ) -> RateLimitResult:
        current_time = time.time()
        window_start = current_time - config.window_seconds
        
        # Get request timestamps
        data = await self.store.get(key)
        timestamps = data.get("timestamps", []) if data else []
        
        # Filter timestamps within window
        valid_timestamps = [
            ts for ts in timestamps 
            if ts > window_start
        ]
        
        if len(valid_timestamps) >= config.limit:
            # Rate limit exceeded
            oldest_timestamp = min(valid_timestamps)
            reset_time = int(oldest_timestamp + config.window_seconds)
            retry_after = max(0, reset_time - int(current_time))
            
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=reset_time,
                retry_after=retry_after,
                limit=config.limit,
                used=len(valid_timestamps)
            )
        
        # Add current timestamp
        valid_timestamps.append(current_time)
        
        # Store updated timestamps
        await self.store.set(
            key, 
            {"timestamps": valid_timestamps},
            config.window_seconds
        )
        
        remaining = config.limit - len(valid_timestamps)
        reset_time = int(valid_timestamps[0] + config.window_seconds)
        
        return RateLimitResult(
            allowed=True,
            remaining=remaining,
            reset_time=reset_time,
            limit=config.limit,
            used=len(valid_timestamps)
        )


class TokenBucketRateLimiter(RateLimiter):
    """Rate limiter tipo token bucket."""
    
    def __init__(self, store: RateLimitStore):
        self.store = store
    
    async def is_allowed(
        self, 
        key: str, 
        config: RateLimitConfig
    ) -> RateLimitResult:
        current_time = time.time()
        
        # Get bucket state
        data = await self.store.get(key)
        
        if not data:
            # Initialize bucket
            tokens = config.limit
            last_refill = current_time
        else:
            tokens = data.get("tokens", 0)
            last_refill = data.get("last_refill", current_time)
        
        # Calculate tokens to add based on time elapsed
        elapsed = current_time - last_refill
        refill_rate = config.limit / config.window_seconds  # tokens per second
        tokens_to_add = elapsed * refill_rate
        
        # Update tokens (capped at limit)
        tokens = min(config.limit, tokens + tokens_to_add)
        
        if tokens < 1:
            # No tokens available
            retry_after = int((1 - tokens) / refill_rate)
            
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=int(current_time + retry_after),
                retry_after=retry_after,
                limit=config.limit,
                used=config.limit
            )
        
        # Consume one token
        tokens -= 1
        
        # Save bucket state
        await self.store.set(key, {
            "tokens": tokens,
            "last_refill": current_time
        }, config.window_seconds * 2)  # TTL longer than window
        
        return RateLimitResult(
            allowed=True,
            remaining=int(tokens),
            reset_time=int(current_time + config.window_seconds),
            limit=config.limit,
            used=config.limit - int(tokens)
        )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware de rate limiting para FastAPI.
    
    Implementa rate limiting global con configuración flexible
    y soporte para múltiples estrategias.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        default_config: RateLimitConfig = None,
        store: RateLimitStore = None,
        metrics_service: MetricsService = None,
        logger: StructuredLogger = None
    ):
        super().__init__(app)
        
        self.default_config = default_config or RateLimitConfig()
        self.store = store or MemoryRateLimitStore()
        self.metrics_service = metrics_service
        self.logger = logger
        
        # Rate limiter implementations
        self.limiters = {
            RateLimitStrategy.FIXED_WINDOW: FixedWindowRateLimiter(self.store),
            RateLimitStrategy.SLIDING_WINDOW: SlidingWindowRateLimiter(self.store),
            RateLimitStrategy.TOKEN_BUCKET: TokenBucketRateLimiter(self.store),
        }
        
        # Per-endpoint configurations
        self.endpoint_configs: Dict[str, RateLimitConfig] = {}
    
    def configure_endpoint(self, path: str, config: RateLimitConfig):
        """Configurar rate limiting para un endpoint específico."""
        self.endpoint_configs[path] = config
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Procesar request con rate limiting."""
        
        # Check if path should be excluded
        if self._is_excluded_path(request.url.path):
            return await call_next(request)
        
        # Get configuration for this endpoint
        config = self._get_endpoint_config(request.url.path)
        
        # Check if IP is whitelisted
        if self._is_whitelisted_ip(request):
            return await call_next(request)
        
        try:
            # Generate rate limit key
            limit_key = self._generate_key(request, config)
            
            # Get appropriate rate limiter
            limiter = self.limiters.get(
                config.strategy, 
                self.limiters[RateLimitStrategy.FIXED_WINDOW]
            )
            
            # Check rate limit
            result = await limiter.is_allowed(limit_key, config)
            
            if not result.allowed:
                # Rate limit exceeded
                await self._handle_rate_limit_exceeded(request, result, config)
                return self._create_rate_limit_response(result)
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            if config.headers_enabled:
                self._add_rate_limit_headers(response, result)
            
            # Record metrics
            await self._record_metrics(request, result, "allowed")
            
            return response
            
        except Exception as e:
            if self.logger:
                self.logger.error(
                    "Error in rate limiting middleware",
                    error=e,
                    path=request.url.path,
                    method=request.method
                )
            
            # On error, allow the request (fail-open)
            return await call_next(request)
    
    def _is_excluded_path(self, path: str) -> bool:
        """Verificar si el path está excluido del rate limiting."""
        excluded = ["/health", "/metrics", "/docs", "/openapi.json"]
        excluded.extend(self.default_config.excluded_paths)
        
        return any(path.startswith(excluded_path) for excluded_path in excluded)
    
    def _is_whitelisted_ip(self, request: Request) -> bool:
        """Verificar si la IP está en whitelist."""
        if not self.default_config.whitelist_ips:
            return False
        
        client_ip = self._get_client_ip(request)
        return client_ip in self.default_config.whitelist_ips
    
    def _get_client_ip(self, request: Request) -> str:
        """Obtener IP del cliente."""
        # Check forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to client IP
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _get_endpoint_config(self, path: str) -> RateLimitConfig:
        """Obtener configuración para un endpoint específico."""
        # Try exact match first
        if path in self.endpoint_configs:
            return self.endpoint_configs[path]
        
        # Try pattern matching
        for pattern, config in self.endpoint_configs.items():
            if path.startswith(pattern):
                return config
        
        return self.default_config
    
    def _generate_key(self, request: Request, config: RateLimitConfig) -> str:
        """Generar clave para rate limiting."""
        if config.key_function:
            return config.key_function(request)
        
        # Default key: IP + endpoint
        client_ip = self._get_client_ip(request)
        endpoint = f"{request.method}:{request.url.path}"
        
        # Create hash to avoid very long keys
        key_data = f"{client_ip}:{endpoint}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        
        return f"rate_limit:{key_hash}"
    
    async def _handle_rate_limit_exceeded(
        self, 
        request: Request, 
        result: RateLimitResult,
        config: RateLimitConfig
    ):
        """Manejar cuando se excede el rate limit."""
        if self.logger:
            self.logger.warning(
                "Rate limit exceeded",
                path=request.url.path,
                method=request.method,
                client_ip=self._get_client_ip(request),
                limit=result.limit,
                used=result.used,
                retry_after=result.retry_after
            )
        
        await self._record_metrics(request, result, "exceeded")
    
    def _create_rate_limit_response(self, result: RateLimitResult) -> JSONResponse:
        """Crear respuesta para rate limit excedido."""
        content = {
            "error": True,
            "error_code": "RATE_LIMIT_EXCEEDED",
            "message": "Rate limit exceeded",
            "details": {
                "limit": result.limit,
                "used": result.used,
                "retry_after": result.retry_after,
                "reset_time": result.reset_time
            }
        }
        
        headers = {}
        if result.retry_after:
            headers["Retry-After"] = str(result.retry_after)
        
        self._add_rate_limit_headers_to_dict(headers, result)
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=content,
            headers=headers
        )
    
    def _add_rate_limit_headers(self, response: Response, result: RateLimitResult):
        """Agregar headers de rate limiting a la respuesta."""
        response.headers["X-RateLimit-Limit"] = str(result.limit)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        response.headers["X-RateLimit-Reset"] = str(result.reset_time)
        response.headers["X-RateLimit-Used"] = str(result.used)
    
    def _add_rate_limit_headers_to_dict(
        self, 
        headers: Dict[str, str], 
        result: RateLimitResult
    ):
        """Agregar headers de rate limiting a un diccionario."""
        headers.update({
            "X-RateLimit-Limit": str(result.limit),
            "X-RateLimit-Remaining": str(result.remaining),
            "X-RateLimit-Reset": str(result.reset_time),
            "X-RateLimit-Used": str(result.used)
        })
    
    async def _record_metrics(
        self, 
        request: Request, 
        result: RateLimitResult,
        outcome: str
    ):
        """Registrar métricas de rate limiting."""
        if not self.metrics_service:
            return
        
        tags = {
            "method": request.method,
            "endpoint": request.url.path,
            "outcome": outcome,
            "strategy": self.default_config.strategy.value
        }
        
        self.metrics_service.increment("rate_limit.requests", tags=tags)
        
        if outcome == "exceeded":
            self.metrics_service.increment("rate_limit.exceeded", tags=tags)
        
        # Record current usage
        if result.limit > 0:
            usage_percent = (result.used / result.limit) * 100
            self.metrics_service.gauge("rate_limit.usage_percent", usage_percent, tags=tags)


# Factory functions for common configurations
def create_default_rate_limit_middleware(
    app: ASGIApp,
    metrics_service: MetricsService = None,
    logger: StructuredLogger = None
) -> RateLimitMiddleware:
    """Crear middleware con configuración predeterminada."""
    config = RateLimitConfig(
        limit=1000,  # 1000 requests per hour
        window_seconds=3600,
        strategy=RateLimitStrategy.FIXED_WINDOW
    )
    
    return RateLimitMiddleware(
        app=app,
        default_config=config,
        metrics_service=metrics_service,
        logger=logger
    )


def create_strict_rate_limit_middleware(
    app: ASGIApp,
    metrics_service: MetricsService = None,
    logger: StructuredLogger = None
) -> RateLimitMiddleware:
    """Crear middleware con configuración estricta."""
    config = RateLimitConfig(
        limit=100,  # 100 requests per hour
        window_seconds=3600,
        strategy=RateLimitStrategy.SLIDING_WINDOW
    )
    
    middleware = RateLimitMiddleware(
        app=app,
        default_config=config,
        metrics_service=metrics_service,
        logger=logger
    )
    
    # Configure stricter limits for specific endpoints
    middleware.configure_endpoint("/api/v1/checkpoints", RateLimitConfig(
        limit=50,
        window_seconds=3600,
        strategy=RateLimitStrategy.TOKEN_BUCKET
    ))
    
    return middleware


def create_development_rate_limit_middleware(
    app: ASGIApp,
    metrics_service: MetricsService = None,
    logger: StructuredLogger = None
) -> RateLimitMiddleware:
    """Crear middleware para desarrollo (muy permisivo)."""
    config = RateLimitConfig(
        limit=10000,  # Very high limit for development
        window_seconds=3600,
        strategy=RateLimitStrategy.FIXED_WINDOW,
        excluded_paths=["/api/v1/health", "/docs", "/redoc"]
    )
    
    return RateLimitMiddleware(
        app=app,
        default_config=config,
        metrics_service=metrics_service,
        logger=logger
    )