import os
from typing import List, Dict, Any, Optional,Union
from enum import Enum
from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic.networks import PostgresDsn
from pydantic import field_validator
from datetime import timedelta


class Environment(str, Enum):
    """Ambientes de ejecución disponibles."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Niveles de logging disponibles."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class RateLimitStrategy(str, Enum):
    """Estrategias de rate limiting."""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"


class ValidationLevel(str, Enum):
    """Niveles de validación."""
    LENIENT = "lenient"      # Validación mínima
    STANDARD = "standard"    # Validación estándar
    STRICT = "strict"        # Validación estricta


class Settings(BaseSettings):
    """
    Configuración principal de la aplicación.
    
    Sigue el patrón de configuración por entorno y feature flags
    para permitir flexibilidad entre development, staging y production.
    """
    
    # ===================
    # Core Application Settings
    # ===================
    APP_NAME: str = Field(default="Tracking API", env="APP_NAME")
    VERSION: str = Field(default="1.0.0", env="VERSION")
    ENVIRONMENT: Environment = Field(default=Environment.DEVELOPMENT, env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # API Configuration
    API_V1_PREFIX: str = Field(default="/api/v1", env="API_V1_PREFIX")
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    
    # ===================
    # Database Configuration
    # ===================
    DATABASE_URL: Optional[PostgresDsn] = Field(default=None, env="DATABASE_URL")
    DATABASE_POOL_SIZE: int = Field(default=10, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    DATABASE_POOL_TIMEOUT: int = Field(default=30, env="DATABASE_POOL_TIMEOUT")
    DATABASE_ECHO: bool = Field(default=False, env="DATABASE_ECHO")
    
    # Database Connection Settings
    DB_CONNECTION_RETRY_ATTEMPTS: int = Field(default=3, env="DB_CONNECTION_RETRY_ATTEMPTS")
    DB_CONNECTION_RETRY_DELAY: float = Field(default=1.0, env="DB_CONNECTION_RETRY_DELAY")
    
    # ===================
    # Redis Configuration
    # ===================
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_ENABLED: bool = Field(default=True, env="REDIS_ENABLED")
    REDIS_ENABLED: bool = True

    # Cache TTL Configuration (en segundos)
    CACHE_TTL_TRACKING: int = 300        # 5 minutos - tracking info
    CACHE_TTL_UNITS_LIST: int = 120      # 2 minutos - listados de units
    CACHE_TTL_CHECKPOINTS: int = 180     # 3 minutos - listados de checkpoints
    CACHE_TTL_STATISTICS: int = 600      # 10 minutos - estadísticas
    CACHE_TTL_DEFAULT: int = 300  
    
    # ===================
    # Security Configuration
    # ===================
    SECRET_KEY: str = Field(default="dev-secret-key-change-in-production", env="SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Password Requirements
    PASSWORD_MIN_LENGTH: int = Field(default=8, env="PASSWORD_MIN_LENGTH")
    PASSWORD_REQUIRE_UPPERCASE: bool = Field(default=True, env="PASSWORD_REQUIRE_UPPERCASE")
    PASSWORD_REQUIRE_NUMBERS: bool = Field(default=True, env="PASSWORD_REQUIRE_NUMBERS")
    PASSWORD_REQUIRE_SPECIAL: bool = Field(default=True, env="PASSWORD_REQUIRE_SPECIAL")
    
    # CORS Settings
    CORS_ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000"], 
        env="CORS_ALLOWED_ORIGINS"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    CORS_ALLOWED_METHODS: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        env="CORS_ALLOWED_METHODS"
    )
    CORS_ALLOWED_HEADERS: List[str] = Field(
        default=["*"],
        env="CORS_ALLOWED_HEADERS"
    )
    
    # ===================
    # Validation Configuration
    # ===================
    VALIDATION_LEVEL: ValidationLevel = Field(
        default=ValidationLevel.STANDARD, 
        env="VALIDATION_LEVEL"
    )
    STRICT_VALIDATION: bool = Field(default=False, env="STRICT_VALIDATION")
    
    # Business Hours Validation
    BUSINESS_HOURS_START: int = Field(default=6, env="BUSINESS_HOURS_START")  # 6 AM
    BUSINESS_HOURS_END: int = Field(default=22, env="BUSINESS_HOURS_END")    # 10 PM
    BUSINESS_HOURS_ENABLED: bool = Field(default=True, env="BUSINESS_HOURS_ENABLED")
    
    # Geofence Validation
    GEOFENCE_VALIDATION_ENABLED: bool = Field(default=True, env="GEOFENCE_VALIDATION_ENABLED")
    ALLOWED_GEOFENCE_ZONES: List[str] = Field(
        default=["Bogotá", "Medellín", "Cali", "Barranquilla"],
        env="ALLOWED_GEOFENCE_ZONES"
    )
    
    # ===================
    # Rate Limiting Configuration
    # ===================
    RATE_LIMITING_ENABLED: bool = Field(default=True, env="RATE_LIMITING_ENABLED")
    RATE_LIMIT_STRATEGY: RateLimitStrategy = Field(
        default=RateLimitStrategy.FIXED_WINDOW,
        env="RATE_LIMIT_STRATEGY"
    )
    
    # Default Rate Limits
    DEFAULT_RATE_LIMIT: int = Field(default=1000, env="DEFAULT_RATE_LIMIT")
    DEFAULT_RATE_LIMIT_WINDOW: int = Field(default=3600, env="DEFAULT_RATE_LIMIT_WINDOW")  # 1 hour
    
    # Endpoint-Specific Rate Limits
    CHECKPOINT_CREATION_RATE_LIMIT: int = Field(default=100, env="CHECKPOINT_CREATION_RATE_LIMIT")
    CHECKPOINT_CREATION_WINDOW: int = Field(default=3600, env="CHECKPOINT_CREATION_WINDOW")
    
    TRACKING_QUERY_RATE_LIMIT: int = Field(default=500, env="TRACKING_QUERY_RATE_LIMIT")
    TRACKING_QUERY_WINDOW: int = Field(default=3600, env="TRACKING_QUERY_WINDOW")
    
    # Rate Limiting Whitelist
    RATE_LIMIT_WHITELIST_IPS: List[str] = Field(
        default=[],
        env="RATE_LIMIT_WHITELIST_IPS"
    )
    
    # ===================
    # Observability Configuration
    # ===================
    
    # Logging
    LOG_LEVEL: LogLevel = Field(default=LogLevel.INFO, env="LOG_LEVEL")
    STRUCTURED_LOGGING: bool = Field(default=True, env="STRUCTURED_LOGGING")
    LOG_TO_FILE: bool = Field(default=False, env="LOG_TO_FILE")
    LOG_FILE_PATH: str = Field(default="logs/tracking.log", env="LOG_FILE_PATH")
    LOG_ROTATION_SIZE: str = Field(default="10 MB", env="LOG_ROTATION_SIZE")
    LOG_RETENTION_DAYS: int = Field(default=30, env="LOG_RETENTION_DAYS")
    
    # Metrics
    METRICS_ENABLED: bool = Field(default=True, env="METRICS_ENABLED")
    METRICS_ENDPOINT: str = Field(default="/metrics", env="METRICS_ENDPOINT")
    METRICS_COLLECTION_INTERVAL: int = Field(default=60, env="METRICS_COLLECTION_INTERVAL")
    
    # Prometheus Integration
    PROMETHEUS_ENABLED: bool = Field(default=False, env="PROMETHEUS_ENABLED")
    PROMETHEUS_HOST: str = Field(default="localhost", env="PROMETHEUS_HOST")
    PROMETHEUS_PORT: int = Field(default=9090, env="PROMETHEUS_PORT")
    
    # Tracing
    TRACING_ENABLED: bool = Field(default=True, env="TRACING_ENABLED")
    TRACING_SAMPLE_RATE: float = Field(default=0.1, env="TRACING_SAMPLE_RATE")  # 10%
    
    # Jaeger Integration
    JAEGER_ENABLED: bool = Field(default=False, env="JAEGER_ENABLED")
    JAEGER_HOST: str = Field(default="localhost", env="JAEGER_HOST")
    JAEGER_PORT: int = Field(default=14268, env="JAEGER_PORT")
    
    # ===================
    # Domain Events Configuration
    # ===================
    DOMAIN_EVENTS_ENABLED: bool = Field(default=True, env="DOMAIN_EVENTS_ENABLED")
    EVENT_STORE_TYPE: str = Field(default="memory", env="EVENT_STORE_TYPE")  # memory, redis, kafka
    
    # Event Processing
    EVENT_PROCESSING_ASYNC: bool = Field(default=True, env="EVENT_PROCESSING_ASYNC")
    EVENT_BATCH_SIZE: int = Field(default=100, env="EVENT_BATCH_SIZE")
    EVENT_PROCESSING_TIMEOUT: int = Field(default=30, env="EVENT_PROCESSING_TIMEOUT")
    
    # Event Retry Configuration
    EVENT_RETRY_ENABLED: bool = Field(default=True, env="EVENT_RETRY_ENABLED")
    EVENT_MAX_RETRIES: int = Field(default=3, env="EVENT_MAX_RETRIES")
    EVENT_RETRY_DELAY: float = Field(default=1.0, env="EVENT_RETRY_DELAY")
    
    # ===================
    # Feature Flags
    # ===================
    
    # Core Features
    FEATURE_CHECKPOINT_CREATION: bool = Field(default=True, env="FEATURE_CHECKPOINT_CREATION")
    FEATURE_CHECKPOINT_UPDATES: bool = Field(default=True, env="FEATURE_CHECKPOINT_UPDATES")
    FEATURE_BULK_OPERATIONS: bool = Field(default=False, env="FEATURE_BULK_OPERATIONS")
    
    # Advanced Features
    FEATURE_REAL_TIME_TRACKING: bool = Field(default=False, env="FEATURE_REAL_TIME_TRACKING")
    FEATURE_ANALYTICS: bool = Field(default=True, env="FEATURE_ANALYTICS")
    FEATURE_REPORTING: bool = Field(default=True, env="FEATURE_REPORTING")
    FEATURE_NOTIFICATIONS: bool = Field(default=False, env="FEATURE_NOTIFICATIONS")
    
    # Experimental Features
    FEATURE_ML_PREDICTIONS: bool = Field(default=False, env="FEATURE_ML_PREDICTIONS")
    FEATURE_BLOCKCHAIN_AUDIT: bool = Field(default=False, env="FEATURE_BLOCKCHAIN_AUDIT")
    
    # ===================
    # Performance Configuration
    # ===================
    
    # Request Processing
    MAX_REQUEST_SIZE: int = Field(default=1048576, env="MAX_REQUEST_SIZE")  # 1MB
    REQUEST_TIMEOUT: int = Field(default=30, env="REQUEST_TIMEOUT")
    
    # Caching
    CACHE_ENABLED: bool = Field(default=True, env="CACHE_ENABLED")
    CACHE_TTL_SECONDS: int = Field(default=300, env="CACHE_TTL_SECONDS")  # 5 minutes
    CACHE_MAX_ENTRIES: int = Field(default=1000, env="CACHE_MAX_ENTRIES")
    
    # Background Tasks
    BACKGROUND_TASKS_ENABLED: bool = Field(default=True, env="BACKGROUND_TASKS_ENABLED")
    MAX_BACKGROUND_TASKS: int = Field(default=100, env="MAX_BACKGROUND_TASKS")
    
    # ===================
    # Monitoring & Health Checks
    # ===================
    HEALTH_CHECK_ENABLED: bool = Field(default=True, env="HEALTH_CHECK_ENABLED")
    HEALTH_CHECK_ENDPOINT: str = Field(default="/health", env="HEALTH_CHECK_ENDPOINT")
    HEALTH_CHECK_TIMEOUT: int = Field(default=10, env="HEALTH_CHECK_TIMEOUT")
    
    # External Service Health Checks
    HEALTH_CHECK_DATABASE: bool = Field(default=True, env="HEALTH_CHECK_DATABASE")
    HEALTH_CHECK_REDIS: bool = Field(default=True, env="HEALTH_CHECK_REDIS")
    HEALTH_CHECK_EXTERNAL_APIS: bool = Field(default=False, env="HEALTH_CHECK_EXTERNAL_APIS")
    
    # ===================
    # Testing Configuration
    # ===================
    TESTING_DATABASE_URL: Optional[str] = Field(default=None, env="TESTING_DATABASE_URL")
    TESTING_REDIS_URL: Optional[str] = Field(default=None, env="TESTING_REDIS_URL")
    TESTING_MODE: bool = Field(default=False, env="TESTING_MODE")
    
    # Test Data
    ENABLE_TEST_DATA: bool = Field(default=False, env="ENABLE_TEST_DATA")
    TEST_DATA_CLEANUP: bool = Field(default=True, env="TEST_DATA_CLEANUP")
    
    # ===================
    # Integration Configuration
    # ===================
    
    # External APIs
    EXTERNAL_API_TIMEOUT: int = Field(default=30, env="EXTERNAL_API_TIMEOUT")
    EXTERNAL_API_RETRIES: int = Field(default=3, env="EXTERNAL_API_RETRIES")
    
    # Webhooks
    WEBHOOKS_ENABLED: bool = Field(default=False, env="WEBHOOKS_ENABLED")
    WEBHOOK_TIMEOUT: int = Field(default=10, env="WEBHOOK_TIMEOUT")
    WEBHOOK_RETRIES: int = Field(default=3, env="WEBHOOK_RETRIES")
    
    # ===================
    # Development Configuration
    # ===================
    ENABLE_SWAGGER: bool = Field(default=True, env="ENABLE_SWAGGER")
    ENABLE_REDOC: bool = Field(default=True, env="ENABLE_REDOC")
    ENABLE_PROFILER: bool = Field(default=False, env="ENABLE_PROFILER")
    
    # Hot Reload
    ENABLE_HOT_RELOAD: bool = Field(default=False, env="ENABLE_HOT_RELOAD")
    HOT_RELOAD_DIRS: List[str] = Field(
        default=["src"],
        env="HOT_RELOAD_DIRS"
    )
    
    # ===================
    # Validators
    # ===================
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v):
        if v is None:
            return v
        if isinstance(v, str) and not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("DATABASE_URL must be a valid PostgreSQL connection string")
        return v
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @field_validator("BUSINESS_HOURS_START", "BUSINESS_HOURS_END")
    @classmethod
    def validate_business_hours(cls, v):
        if not 0 <= v <= 23:
            raise ValueError("Business hours must be between 0 and 23")
        return v
    
    @field_validator("TRACING_SAMPLE_RATE")
    @classmethod
    def validate_sample_rate(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Tracing sample rate must be between 0.0 and 1.0")
        return v
    
    # ===================
    # Computed Properties
    # ===================
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == Environment.DEVELOPMENT
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == Environment.PRODUCTION
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.ENVIRONMENT == Environment.TESTING or self.TESTING_MODE
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL."""
        return str(self.DATABASE_URL).replace("+asyncpg", "")
    
    @property
    def effective_database_url(self) -> str:
        """Get effective database URL (testing override if in test mode)."""
        if self.is_testing and self.TESTING_DATABASE_URL:
            return self.TESTING_DATABASE_URL
        return str(self.DATABASE_URL)
    
    @property
    def effective_redis_url(self) -> str:
        """Get effective Redis URL (testing override if in test mode)."""
        if self.is_testing and self.TESTING_REDIS_URL:
            return self.TESTING_REDIS_URL
        return self.REDIS_URL
    
    # ===================
    # Configuration Methods
    # ===================
    
    def get_validation_config(self) -> Dict[str, Any]:
        """Get validation configuration."""
        return {
            "level": self.VALIDATION_LEVEL,
            "strict": self.STRICT_VALIDATION,
            "business_hours": {
                "enabled": self.BUSINESS_HOURS_ENABLED,
                "start": self.BUSINESS_HOURS_START,
                "end": self.BUSINESS_HOURS_END
            },
            "geofence": {
                "enabled": self.GEOFENCE_VALIDATION_ENABLED,
                "zones": self.ALLOWED_GEOFENCE_ZONES
            }
        }
    
    def get_rate_limit_config(self) -> Dict[str, Any]:
        """Get rate limiting configuration."""
        return {
            "enabled": self.RATE_LIMITING_ENABLED,
            "strategy": self.RATE_LIMIT_STRATEGY,
            "default_limit": self.DEFAULT_RATE_LIMIT,
            "default_window": self.DEFAULT_RATE_LIMIT_WINDOW,
            "whitelist_ips": self.RATE_LIMIT_WHITELIST_IPS,
            "endpoints": {
                "checkpoint_creation": {
                    "limit": self.CHECKPOINT_CREATION_RATE_LIMIT,
                    "window": self.CHECKPOINT_CREATION_WINDOW
                },
                "tracking_query": {
                    "limit": self.TRACKING_QUERY_RATE_LIMIT,
                    "window": self.TRACKING_QUERY_WINDOW
                }
            }
        }
    
    def get_observability_config(self) -> Dict[str, Any]:
        """Get observability configuration."""
        return {
            "logging": {
                "level": self.LOG_LEVEL,
                "structured": self.STRUCTURED_LOGGING,
                "file_enabled": self.LOG_TO_FILE,
                "file_path": self.LOG_FILE_PATH
            },
            "metrics": {
                "enabled": self.METRICS_ENABLED,
                "endpoint": self.METRICS_ENDPOINT,
                "prometheus": self.PROMETHEUS_ENABLED
            },
            "tracing": {
                "enabled": self.TRACING_ENABLED,
                "sample_rate": self.TRACING_SAMPLE_RATE,
                "jaeger": self.JAEGER_ENABLED
            }
        }
    
    def get_feature_flags(self) -> Dict[str, bool]:
        """Get all feature flags."""
        return {
            "checkpoint_creation": self.FEATURE_CHECKPOINT_CREATION,
            "checkpoint_updates": self.FEATURE_CHECKPOINT_UPDATES,
            "bulk_operations": self.FEATURE_BULK_OPERATIONS,
            "real_time_tracking": self.FEATURE_REAL_TIME_TRACKING,
            "analytics": self.FEATURE_ANALYTICS,
            "reporting": self.FEATURE_REPORTING,
            "notifications": self.FEATURE_NOTIFICATIONS,
            "ml_predictions": self.FEATURE_ML_PREDICTIONS,
            "blockchain_audit": self.FEATURE_BLOCKCHAIN_AUDIT
        }
    
    # ===================
    # Environment-Specific Configuration
    # ===================
    
    def configure_for_development(self):
        """Apply development-specific configuration."""
        self.DEBUG = True
        self.LOG_LEVEL = LogLevel.DEBUG
        self.VALIDATION_LEVEL = ValidationLevel.LENIENT
        self.RATE_LIMITING_ENABLED = False
        self.ENABLE_SWAGGER = True
        self.ENABLE_REDOC = True
    
    def configure_for_production(self):
        """Apply production-specific configuration."""
        self.DEBUG = False
        self.LOG_LEVEL = LogLevel.INFO
        self.VALIDATION_LEVEL = ValidationLevel.STRICT
        self.RATE_LIMITING_ENABLED = True
        self.ENABLE_SWAGGER = False
        self.ENABLE_REDOC = False
        self.TRACING_SAMPLE_RATE = 0.01  # 1% in production
    
    def configure_for_testing(self):
        """Apply testing-specific configuration."""
        self.TESTING_MODE = True
        self.DEBUG = True
        self.LOG_LEVEL = LogLevel.WARNING
        self.RATE_LIMITING_ENABLED = False
        self.DOMAIN_EVENTS_ENABLED = False
        self.METRICS_ENABLED = False
        self.TRACING_ENABLED = False
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"
    }


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get settings singleton instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
        
        # Apply environment-specific configuration
        if _settings.ENVIRONMENT == Environment.DEVELOPMENT:
            _settings.configure_for_development()
        elif _settings.ENVIRONMENT == Environment.PRODUCTION:
            _settings.configure_for_production()
        elif _settings.ENVIRONMENT == Environment.TESTING:
            _settings.configure_for_testing()
    
    return _settings


def reload_settings():
    """Reload settings (useful for testing)."""
    global _settings
    _settings = None
    return get_settings()


# Environment-specific factory functions
def create_development_settings() -> Settings:
    """Create development settings."""
    settings = Settings()
    settings.configure_for_development()
    return settings


def create_production_settings() -> Settings:
    """Create production settings."""
    settings = Settings()
    settings.configure_for_production()
    return settings


def create_testing_settings() -> Settings:
    """Create testing settings."""
    settings = Settings()
    settings.configure_for_testing()
    return settings