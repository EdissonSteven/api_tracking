from enum import Enum
from typing import Dict


class CacheKey(Enum):
    """Tipos de claves de caché con sus TTLs"""
    TRACKING = "tracking"
    UNITS_LIST = "units_list"
    CHECKPOINTS = "checkpoints"
    STATISTICS = "statistics"
    DEFAULT = "default"


class CacheConfig:
    """Configuración centralizada de caché"""
    
    # Prefijos de claves por tipo
    KEY_PREFIXES: Dict[CacheKey, str] = {
        CacheKey.TRACKING: "tracking:",
        CacheKey.UNITS_LIST: "units:status:",
        CacheKey.CHECKPOINTS: "checkpoints:",
        CacheKey.STATISTICS: "stats:",
        CacheKey.DEFAULT: "cache:"
    }
    
    @staticmethod
    def get_ttl(cache_type: CacheKey, settings) -> int:
        """Obtener TTL según tipo de caché"""
        ttl_map = {
            CacheKey.TRACKING: settings.CACHE_TTL_TRACKING,
            CacheKey.UNITS_LIST: settings.CACHE_TTL_UNITS_LIST,
            CacheKey.CHECKPOINTS: settings.CACHE_TTL_CHECKPOINTS,
            CacheKey.STATISTICS: settings.CACHE_TTL_STATISTICS,
            CacheKey.DEFAULT: settings.CACHE_TTL_DEFAULT
        }
        return ttl_map.get(cache_type, settings.CACHE_TTL_DEFAULT)
    
    @staticmethod
    def get_key_prefix(cache_type: CacheKey) -> str:
        """Obtener prefijo de clave según tipo"""
        return CacheConfig.KEY_PREFIXES.get(cache_type, "cache:")
    
    @staticmethod
    def build_key(cache_type: CacheKey, *args) -> str:
        """Construir clave de caché completa"""
        prefix = CacheConfig.get_key_prefix(cache_type)
        return prefix + ":".join(str(arg) for arg in args)