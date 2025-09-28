from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
from typing import Optional, List
import json

class Settings(BaseSettings):
    """Configuración completa de la aplicación Tracking API."""
    DATABASE_URL: str
    DB_ECHO: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str
    APP_NAME: str = "Tracking API"
    APP_VERSION: str = "1.0.0"
    JWT_ALGORITHM: str = "HS256"
    ALLOWED_ORIGINS: List[str] = ["*"]
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # ...existing code...

    # Añadir configuración de logging por defecto
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DEBUG: bool = True

    class Config:
        env_file = ".env"
    
    # === CONFIGURACIÓN BÁSICA DE LA APLICACIÓN ===
    app_name: str = Field(default="Tracking API", description="Nombre de la aplicación")
    app_version: str = Field(default="1.0.0", description="Versión de la aplicación")
    debug: bool = Field(default=False, description="Modo debug")
    environment: str = Field(default="development", description="Entorno de ejecución")
    reload: bool = Field(default=False, description="Auto-reload de la aplicación")
    
    # === CONFIGURACIÓN DE BASE DE DATOS ===
    database_url: str = Field(
        default="postgresql://postgres:postgres@postgres:5432/tracking_db",
        description="URL de conexión a la base de datos"
    )
    db_echo: bool = Field(default=False, description="Log de consultas SQL")
    db_pool_size: int = Field(default=10, description="Tamaño del pool de conexiones")
    db_max_overflow: int = Field(default=20, description="Máximo overflow del pool")
    
    # === CONFIGURACIÓN DE REDIS/CACHE ===
    redis_url: str = Field(
        default="redis://redis:6379/0",
        description="URL de conexión a Redis"
    )
    cache_ttl: int = Field(default=300, description="TTL del cache en segundos")
    
    # === CONFIGURACIÓN DEL SERVIDOR ===
    host: str = Field(default="0.0.0.0", description="Host del servidor")
    port: int = Field(default=8000, description="Puerto del servidor")
    
    # === CONFIGURACIÓN DE SEGURIDAD/JWT ===
    secret_key: str = Field(
        default="your-secret-key-here-change-in-production",
        description="Clave secreta para JWT"
    )
    jwt_algorithm: str = Field(default="HS256", description="Algoritmo JWT")
    access_token_expire_minutes: int = Field(
        default=30, 
        description="Minutos de expiración del token"
    )
    
    # === CONFIGURACIÓN DE CORS ===
    allowed_origins: List[str] = Field(
        default=["*"],
        description="Orígenes permitidos para CORS"
    )
    
    # === CONFIGURACIÓN DE RATE LIMITING ===
    rate_limit_enabled: bool = Field(
        default=True, 
        description="Habilitar rate limiting"
    )
    
    # === CONFIGURACIÓN DE LOGGING ===
    log_level: str = Field(default="INFO", description="Nivel de logging")
    log_format: str = Field(default="json", description="Formato de logs")
    
    # === CONFIGURACIÓN DE MÉTRICAS Y MONITORING ===
    metrics_enabled: bool = Field(
        default=True, 
        description="Habilitar métricas"
    )
    health_check_interval: int = Field(
        default=30, 
        description="Intervalo de health check en segundos"
    )
    
    # === CONFIGURACIÓN ESPECÍFICA DEL TRACKING ===
    max_checkpoints_per_unit: int = Field(
        default=50, 
        description="Máximo de checkpoints por unidad"
    )
    tracking_ttl_days: int = Field(
        default=90, 
        description="TTL de tracking en días"
    )
    
    # === CONFIGURACIÓN DEL MODELO ===
    #model_config = ConfigDict(
    #    env_file=".env",
    ##    env_file_encoding="utf-8",
    #    case_sensitive=False,
    #    extra="ignore"  # Ignora campos extra en lugar de fallar
    #)
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convierte allowed_origins a lista si viene como string."""
        if isinstance(self.allowed_origins, str):
            try:
                return json.loads(self.allowed_origins)
            except json.JSONDecodeError:
                return self.allowed_origins.split(",")
        return self.allowed_origins

# Instancia global de configuración
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """
    Obtiene la instancia de configuración (patrón singleton).
    
    Returns:
        Settings: Instancia de configuración
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

# Para facilitar el acceso
settings = get_settings()