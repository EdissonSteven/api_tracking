
import uuid
from fastapi import Depends, Request, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session
from typing import Generator, AsyncGenerator, Dict, Any, List

# Core Infrastructure
from ....infrastructure.database.connection import get_async_db_session
from ....infrastructure.database.repositories.checkpoint_repository_impl import CheckpointRepositoryImpl
from ....infrastructure.database.repositories.unit_repository_impl import UnitRepositoryImpl
from ....infrastructure.database.repositories.tracking_repository_impl import TrackingRepositoryImpl
from ....infrastructure.security.auth_service import AuthService, JWTManager
from ....infrastructure.security.rate_limiter import RateLimitManager
from ....infrastructure.cache.redis_client import RedisClient

# Use Cases
from ....application.use_cases.create_checkpoint_use_case import CreateCheckpointUseCase
from ....application.use_cases.get_tracking_use_case import GetTrackingUseCase
from ....application.use_cases.list_units_by_status_use_case import ListUnitsByStatusUseCase

# Domain Services
from ....domain.services.domain_services import CheckpointValidationService

# New Architecture Components
from ....domain.domain_events import (
    DomainEventDispatcher, 
    create_event_dispatcher
)
from ....application.validators import (
    ValidationService,
    ValidatorChainBuilder,
    create_default_validator_chain,
    create_strict_validator_chain
)

from ....application.mappers import (
    CheckpointRequestMapper,
    CheckpointResponseMapper,
    BatchCheckpointMapper,
    ErrorResponseMapper,
    MapperFactory
)

# Configuration
from ....config.settings import get_settings

# Security
security = HTTPBearer()

# Global singletons (in production, use proper DI container)
_redis_client = None
_auth_service = None
_rate_limiter = None
_event_dispatcher = None
_validation_service = None
_metrics_service = None
_tracing_service = None
_performance_monitor = None
_structured_logger = None


# =====================
# Core Infrastructure Dependencies
# =====================

async def get_database_session() -> AsyncGenerator[Session, None]:
    """Database session dependency."""
    async for session in get_async_db_session():
        yield session


def get_redis_client() -> RedisClient:
    """Redis client singleton."""
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = RedisClient(settings.REDIS_URL)
    return _redis_client


def get_auth_service() -> AuthService:
    """Authentication service singleton."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


def get_rate_limiter() -> RateLimitManager:
    """Rate limiter singleton."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimitManager()
    return _rate_limiter


def get_request_id() -> str:
    """Generate unique request ID."""
    return str(uuid.uuid4())


# =====================
# Repository Dependencies
# =====================

def get_checkpoint_repository(
    session: Session = Depends(get_database_session)
) -> CheckpointRepositoryImpl:
    """Checkpoint repository dependency."""
    return CheckpointRepositoryImpl(session)


def get_unit_repository(
    session: Session = Depends(get_database_session)
) -> UnitRepositoryImpl:
    """Unit repository dependency."""
    return UnitRepositoryImpl(session)


def get_tracking_repository(
    session: Session = Depends(get_database_session)
) -> TrackingRepositoryImpl:
    """Tracking repository dependency."""
    return TrackingRepositoryImpl(session)


# =====================
# Domain Service Dependencies
# =====================

def get_checkpoint_validation_service(
    checkpoint_repo: CheckpointRepositoryImpl = Depends(get_checkpoint_repository),
    unit_repo: UnitRepositoryImpl = Depends(get_unit_repository)
) -> CheckpointValidationService:
    """Checkpoint validation service dependency."""
    return CheckpointValidationService(
        checkpoint_repo=checkpoint_repo,
        unit_repo=unit_repo
    )


# =====================
# Event System Dependencies
# =====================

def get_event_dispatcher() -> DomainEventDispatcher:
    """Event dispatcher singleton."""
    global _event_dispatcher
    if _event_dispatcher is None:
        _event_dispatcher = create_event_dispatcher()
    return _event_dispatcher


# =====================
# Validation Dependencies
# =====================

def get_validator_chain(
    checkpoint_repo: CheckpointRepositoryImpl = Depends(get_checkpoint_repository)
):
    """Validator chain dependency."""
    settings = get_settings()
    
    # Choose validation level based on environment
    if getattr(settings, 'ENVIRONMENT', 'development') == 'production':
        return create_strict_validator_chain(checkpoint_repo)
    else:
        return create_default_validator_chain(checkpoint_repo)


def get_validator_service(
    validator_chain=Depends(get_validator_chain),
    event_dispatcher: DomainEventDispatcher = Depends(get_event_dispatcher)
) -> ValidationService:
    """Validation service dependency."""
    global _validation_service
    if _validation_service is None:
        _validation_service = ValidationService(
            validator_chain=validator_chain,
            event_dispatcher=event_dispatcher
        )
    return _validation_service


# =====================
# Observability Dependencies
# =====================

#def get_metrics_service_dependency() -> MetricsService:
    """Metrics service dependency."""
    return get_metrics_service()


#def get_tracing_service_dependency() -> TracingService:
    """Tracing service dependency."""
    return get_tracing_service()


#def get_performance_monitor_dependency(
#    metrics: MetricsService = Depends(get_metrics_service_dependency),
#    tracing: TracingService = Depends(get_tracing_service_dependency)
#) -> PerformanceMonitor:
#    """Performance monitor dependency."""
#    global _performance_monitor
#    if _performance_monitor is None:
#        _performance_monitor = PerformanceMonitor(metrics, tracing)
#    return _performance_monitor


#def get_structured_logger(
#    metrics: MetricsService = Depends(get_metrics_service_dependency)
#) -> StructuredLogger:
#    """Structured logger dependency."""
#    global _structured_logger
#    if _structured_logger is None:
#        _structured_logger = StructuredLogger("tracking.api", metrics)
#    return _structured_logger


# =====================
# Mapper Dependencies
# =====================

def get_request_mapper() -> CheckpointRequestMapper:
    """Request mapper dependency."""
    return MapperFactory.create_request_mapper()


def get_response_mapper() -> CheckpointResponseMapper:
    """Response mapper dependency."""
    return MapperFactory.create_response_mapper()


def get_batch_mapper() -> BatchCheckpointMapper:
    """Batch mapper dependency."""
    return MapperFactory.create_batch_mapper()


def get_error_mapper() -> ErrorResponseMapper:
    """Error mapper dependency."""
    return MapperFactory.create_error_mapper()


# =====================
# Use Case Dependencies
# =====================

def get_create_checkpoint_use_case(
    checkpoint_repo: CheckpointRepositoryImpl = Depends(get_checkpoint_repository),
    unit_repo: UnitRepositoryImpl = Depends(get_unit_repository),
    validation_service: CheckpointValidationService = Depends(get_checkpoint_validation_service),
    event_dispatcher: DomainEventDispatcher = Depends(get_event_dispatcher)
) -> CreateCheckpointUseCase:
    """Create checkpoint use case dependency."""
    return CreateCheckpointUseCase(
        checkpoint_repo=checkpoint_repo,
        unit_repo=unit_repo,
        validation_service=validation_service,
        event_dispatcher=event_dispatcher
    )


def get_tracking_use_case(
    tracking_repo: TrackingRepositoryImpl = Depends(get_tracking_repository),
    unit_repo: UnitRepositoryImpl = Depends(get_unit_repository)
) -> GetTrackingUseCase:
    """Tracking use case dependency."""
    return GetTrackingUseCase(tracking_repo, unit_repo)


def get_list_units_use_case(
    unit_repo: UnitRepositoryImpl = Depends(get_unit_repository)
) -> ListUnitsByStatusUseCase:
    """List units use case dependency."""
    return ListUnitsByStatusUseCase(unit_repo)


# =====================
# Authentication & Authorization Dependencies
# =====================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """
    Authentication dependency.
    
    Validates token and returns user data or raises 401.
    """
    user_data = auth_service.get_current_user_from_token(credentials.credentials)
    
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o expirado",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user_data


def require_permissions(required_permissions: List[str]):
    """
    Authorization dependency factory.
    
    Creates a dependency that validates user has required permissions.
    """
    async def permission_dependency(
        current_user: Dict[str, Any] = Depends(get_current_user),
        auth_service: AuthService = Depends(get_auth_service)
    ) -> Dict[str, Any]:
        
        for permission in required_permissions:
            if not auth_service.has_permission(current_user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permission: {permission}"
                )
        
        return current_user
    
    return permission_dependency


def require_roles(required_roles: List[str]):
    """
    Role-based authorization dependency factory.
    
    Creates a dependency that validates user has required roles.
    """
    async def role_dependency(
        current_user: Dict[str, Any] = Depends(get_current_user),
        auth_service: AuthService = Depends(get_auth_service)
    ) -> Dict[str, Any]:
        
        user_roles = current_user.get("roles", [])
        has_required_role = any(role in user_roles for role in required_roles)
        
        if not has_required_role and not current_user.get("is_superuser"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required role. Required: {required_roles}, User has: {user_roles}"
            )
        
        return current_user
    
    return role_dependency


# =====================
# Rate Limiting Dependencies
# =====================

def rate_limit(operation: str, limit: int = 100, window: int = 3600):
    """
    Rate limiting dependency factory.
    
    Creates a dependency that enforces rate limits for specific operations.
    """
    async def rate_limit_dependency(
        request: Request,
        current_user: Dict[str, Any] = Depends(get_current_user),
        rate_limiter: RateLimitManager = Depends(get_rate_limiter)
    ):
        try:
            await rate_limiter.check_rate_limit(
                request, 
                operation,
                user_id=current_user.get("user_id"),
                limit=limit,
                window=window
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for {operation}",
                headers={"Retry-After": str(window)}
            )
    
    return rate_limit_dependency


# =====================
# Utility Dependencies
# =====================

def get_correlation_id(request: Request) -> str:
    """
    Correlation ID dependency for distributed tracing.
    """
    correlation_id = request.headers.get("X-Correlation-ID")
    if not correlation_id:
        correlation_id = str(uuid.uuid4())
    return correlation_id


def get_user_context(
    current_user: Dict[str, Any] = Depends(get_current_user),
    request: Request = None,
    correlation_id: str = Depends(get_correlation_id)
) -> Dict[str, Any]:
    """
    Complete user context dependency.
    """
    context = {
        "user_id": current_user.get("user_id"),
        "username": current_user.get("username"),
        "roles": current_user.get("roles", []),
        "permissions": current_user.get("permissions", []),
        "is_superuser": current_user.get("is_superuser", False),
        "correlation_id": correlation_id
    }
    
    if request:
        context.update({
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "request_method": request.method,
            "request_path": str(request.url.path)
        })
    
    return context


# =====================
# Environment-Specific Dependencies
# =====================

def get_environment_config() -> Dict[str, Any]:
    """Environment-specific configuration."""
    settings = get_settings()
    
    return {
        "environment": getattr(settings, 'ENVIRONMENT', 'development'),
        "debug": getattr(settings, 'DEBUG', False),
        "version": getattr(settings, 'VERSION', '1.0.0'),
        "features": {
            "strict_validation": getattr(settings, 'STRICT_VALIDATION', False),
            "detailed_logging": getattr(settings, 'DETAILED_LOGGING', True),
            "metrics_enabled": getattr(settings, 'METRICS_ENABLED', True),
            "tracing_enabled": getattr(settings, 'TRACING_ENABLED', True)
        }
    }


# =====================
# Health Check Dependencies
# =====================

async def get_health_status(
    redis_client: RedisClient = Depends(get_redis_client),
    db_session: Session = Depends(get_database_session)
) -> Dict[str, Any]:
    """
    Health status dependency for health check endpoints.
    """
    health_status = {
        "status": "healthy",
        "timestamp": uuid.uuid4().hex,
        "dependencies": {}
    }
    
    # Check database
    try:
        await db_session.execute("SELECT 1")
        health_status["dependencies"]["database"] = "healthy"
    except Exception as e:
        health_status["dependencies"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        # Assuming Redis client has a health check method
        if hasattr(redis_client, 'ping'):
            await redis_client.ping()
        health_status["dependencies"]["redis"] = "healthy"
    except Exception as e:
        health_status["dependencies"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status


# =====================
# Testing Dependencies
# =====================

def get_test_dependencies():
    """
    Dependencies specifically for testing environments.
    """
    from unittest.mock import Mock
    
    return {
        "mock_metrics": Mock(spec=MetricsService),
        "mock_tracing": Mock(spec=TracingService),
        "mock_event_dispatcher": Mock(spec=DomainEventDispatcher)
    }


# =====================
# Cleanup Functions
# =====================

def reset_global_dependencies():
    """Reset all global dependencies (useful for testing)."""
    global _redis_client, _auth_service, _rate_limiter, _event_dispatcher
    global _validation_service, _metrics_service, _tracing_service
    global _performance_monitor, _structured_logger
    
    _redis_client = None
    _auth_service = None
    _rate_limiter = None
    _event_dispatcher = None
    _validation_service = None
    _metrics_service = None
    _tracing_service = None
    _performance_monitor = None
    _structured_logger = None


def configure_production_dependencies():
    """Configure dependencies for production environment."""
    # This would typically configure real services like:
    # - Prometheus metrics
    # - Jaeger tracing
    # - Production event dispatchers
    # - etc.
    pass


def configure_development_dependencies():
    """Configure dependencies for development environment."""
    # Use in-memory implementations for development
    pass