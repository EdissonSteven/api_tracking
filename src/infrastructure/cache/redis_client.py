# ...existing code...
import redis.asyncio as redis
import json
import logging
from typing import Optional, Any, Union
from ...config.settings import get_settings

logger = logging.getLogger(__name__)

class RedisClient:
    """Cliente Redis para operaciones de cache (async)."""
    
    def __init__(self, redis_url: Optional[str] = None):
        settings = get_settings()
        self.redis_url = (
            redis_url
            or getattr(settings, "REDIS_URL", None)
            or getattr(settings, "redis_url", "redis://localhost:6379/0")
        )
        # único atributo consistente
        self._redis_client: Optional[redis.Redis] = None

    async def connect(self) -> redis.Redis:
        """Inicializa conexión async con Redis (llamar en lifespan/startup)."""
        if self._redis_client is None:
            self._redis_client = redis.from_url(self.redis_url, decode_responses=True)
            try:
                await self._redis_client.ping()
                logger.info("Conectado a Redis")
            except Exception as e:
                logger.warning(f"No se pudo hacer ping a Redis: {e}")
        return self._redis_client

    def client(self) -> redis.Redis:
        """Devuelve el cliente si ya está inicializado (sync getter)."""
        if self._redis_client is None:
            raise RuntimeError("Redis no inicializado. Llama a await connect() en startup.")
        return self._redis_client

    async def close(self) -> None:
        """Cierra la conexión a Redis (llamar en shutdown)."""
        if self._redis_client:
            try:
                await self._redis_client.close()
                logger.info("Conexión Redis cerrada")
            except Exception as e:
                logger.warning(f"Error cerrando Redis: {e}")
            finally:
                self._redis_client = None
    
    @property
    def is_connected(self) -> bool:
        """Verifica si Redis está conectado (non-blocking)."""
        return self._redis_client is not None
    
    # Métodos de cache asíncronos (usar await en callers)
    async def get(self, key: str) -> Optional[Any]:
        if not self.is_connected:
            return None
        try:
            value = await self._redis_client.get(key)
            if value is None:
                return None
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.warning(f"Error obteniendo clave '{key}' de Redis: {e}")
            return None

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        if not self.is_connected:
            return False
        try:
            if not isinstance(value, str):
                value = json.dumps(value, default=str)
            if expire is None:
                expire = getattr(get_settings(), 'cache_ttl', 300)
            result = await self._redis_client.setex(key, expire, value)
            return bool(result)
        except Exception as e:
            logger.warning(f"Error guardando clave '{key}' en Redis: {e}")
            return False

    async def delete(self, key: str) -> bool:
        if not self.is_connected:
            return False
        try:
            result = await self._redis_client.delete(key)
            return bool(result)
        except Exception as e:
            logger.warning(f"Error eliminando clave '{key}' de Redis: {e}")
            return False

    async def exists(self, key: str) -> bool:
        if not self.is_connected:
            return False
        try:
            return bool(await self._redis_client.exists(key))
        except Exception as e:
            logger.warning(f"Error verificando clave '{key}' en Redis: {e}")
            return False

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        if not self.is_connected:
            return None
        try:
            return await self._redis_client.incrby(key, amount)
        except Exception as e:
            logger.warning(f"Error incrementando clave '{key}' en Redis: {e}")
            return None

    def get_tracking_cache_key(self, tracking_id: str) -> str:
        return f"tracking:{tracking_id}"
    
    def get_checkpoints_cache_key(self, tracking_id: str) -> str:
        return f"checkpoints:{tracking_id}"
# ...existing code...
redis_client = RedisClient()
def get_redis_client() -> RedisClient:
    return redis_client