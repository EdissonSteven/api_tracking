import redis
import json
import logging
from typing import Optional, Any
from .cache_config import CacheKey, CacheConfig

logger = logging.getLogger(__name__)


class RedisClient:
    """Cliente Redis síncrono con configuración centralizada"""
    
    def __init__(self, redis_url: str, settings):
        self.redis_url = redis_url
        self.settings = settings
        self._client = None
        self._available = False
        
        if settings.REDIS_ENABLED:
            self._connect()
    
    def _connect(self):
        """Conectar a Redis de forma segura"""
        try:
            self._client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            self._client.ping()
            self._available = True
            logger.info("Redis conectado exitosamente")
        except Exception as e:
            self._available = False
            logger.warning(f"Redis no disponible: {str(e)}")
    
    @property
    def is_available(self) -> bool:
        """Verifica si Redis está disponible"""
        return self._available and self._client is not None
    
    def get(self, key: str) -> Optional[Any]:
        """Obtener valor de caché"""
        if not self.is_available:
            return None
        
        try:
            value = self._client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Redis GET error: {str(e)}")
            return None
    
    def set_with_type(
        self, 
        cache_type: CacheKey,
        key: str, 
        value: Any
    ) -> bool:
        """Guardar valor con TTL según tipo de caché"""
        if not self.is_available:
            return False
        
        try:
            ttl = CacheConfig.get_ttl(cache_type, self.settings)
            serialized = json.dumps(value, default=str)
            self._client.setex(key, ttl, serialized)
            logger.debug(f"Cache guardado: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.warning(f"Redis SET error: {str(e)}")
            return False
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Guardar valor con TTL personalizado o default"""
        if not self.is_available:
            return False
        
        try:
            if ttl is None:
                ttl = self.settings.CACHE_TTL_DEFAULT
            
            serialized = json.dumps(value, default=str)
            self._client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.warning(f"Redis SET error: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Eliminar clave de caché"""
        if not self.is_available:
            return False
        
        try:
            self._client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis DELETE error: {str(e)}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Eliminar claves que coincidan con patrón"""
        if not self.is_available:
            return 0
        
        try:
            keys = self._client.keys(pattern)
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Redis DELETE_PATTERN error: {str(e)}")
            return 0
    
    def invalidate_tracking(self, tracking_id: str):
        """Invalidar caché de un tracking específico"""
        self.delete(f"tracking:{tracking_id}")
        self.delete(f"checkpoints:{tracking_id}")
    
    def invalidate_units_cache(self):
        """Invalidar caché de listados de unidades"""
        self.delete_pattern("units:status:*")


# Singleton global
_redis_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """Obtener instancia singleton de Redis"""
    global _redis_client
    if _redis_client is None:
        from ...config.settings import get_settings
        settings = get_settings()
        _redis_client = RedisClient(settings.REDIS_URL, settings)
    return _redis_client