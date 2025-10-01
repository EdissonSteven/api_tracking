import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Importaciones de configuración
from .config.settings import get_settings

# Importaciones de infraestructura
from .infrastructure.database.connection import db_manager
from .infrastructure.cache.redis_client import get_redis_client


# Importaciones de controladores
from .interfaces.api.v1.controllers import (
    checkpoint_controller, 
    tracking_controller, 
    shipments_controller
)
from .interfaces.api.v1.controllers.auth_controller import router as auth_router

# Importaciones de middleware
from .interfaces.api.middleware.error_handler import setup_error_handlers

logger = logging.getLogger(__name__)
redis_client = get_redis_client()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestor de ciclo de vida de la aplicación."""
    
    # Startup
    logger.info("Iniciando aplicación Tracking API...")
    
    try:
        # Inicializar base de datos
        db_manager.create_tables()
        logger.info("Base de datos inicializada")
        
        # Verificar conexión Redis
        if redis_client.is_available:
            logger.info("Redis conectado")
        else:
            logger.warning("Redis no disponible - funcionando sin cache")
        
        logger.info("Aplicación iniciada exitosamente")
        
    except Exception as e:
        logger.error(f"Error iniciando aplicación: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Cerrando aplicación...")
    
    try:
        # Cerrar conexiones
        db_manager.close()
        redis_client.close()
        logger.info("Aplicación cerrada correctamente")
        
    except Exception as e:
        logger.error(f"Error cerrando aplicación: {e}")

# Crear aplicación FastAPI
def create_app() -> FastAPI:
    """Factory para crear la aplicación FastAPI."""
    
    settings = get_settings()
    
    app = FastAPI(
        title="Tracking API",
        description="""
        **API de Seguimiento de Paquetes** 
        
        Sistema completo de tracking con autenticación JWT, siguiendo principios de Clean Architecture y DDD.
        
        ## Autenticación
        
        La API utiliza autenticación JWT Bearer Token. Para acceder a los endpoints protegidos:
        
        1. **Obtener token**: POST `/api/v1/auth/login`
        2. **Usar token**: Incluir en header `Authorization: Bearer <token>`
        
        ### Usuarios de prueba:
        - **admin** / admin123 (Administrador - todos los permisos)
        - **operator** / operator123 (Operador - lectura y escritura)  
        - **viewer** / viewer123 (Visualizador - solo lectura)
        
        ## Funcionalidades
        
        - ✅ **Gestión de checkpoints** con validación de estados
        - ✅ **Tracking completo** con información detallada  
        - ✅ **Búsqueda avanzada** con filtros múltiples
        - ✅ **Autenticación JWT** con roles y permisos
        - ✅ **Rate limiting** y middleware de seguridad
        - ✅ **Documentación interactiva** en español
        
        ## Arquitectura
        
        - **Clean Architecture** con separación clara de capas
        - **Domain Driven Design (DDD)** con entidades y servicios de dominio
        - **Principios SOLID** en toda la implementación
        - **PostgreSQL** para persistencia con SQLModel
        - **Redis** para cache y rate limiting
        """,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Configurar manejadores de error
    setup_error_handlers(app)
    
    # Registrar routers
    
    # Router de autenticación (sin prefijo adicional ya que tiene su propio prefijo)
    app.include_router(auth_router, prefix="/api/v1")
    
    # Routers principales de la API
    app.include_router(checkpoint_controller.router, prefix="/api/v1")
    app.include_router(tracking_controller.router, prefix="/api/v1")
    app.include_router(shipments_controller.router, prefix="/api/v1")
    
    # Eliminar llamada sin await que se ejecuta en import-time, por ejemplo:
    # db_manager.create_tables()

    # Añadir gestión correcta en startup
    async def _on_startup() -> None:
        # await creación de tablas/migrations
        try:
            await db_manager.create_tables()
        except Exception as e:
            # loguear pero seguir arrancando si quieres tolerancia
            import logging
            logging.getLogger("src.main").warning(f"Error creando tablas en startup: {e}")

    app.add_event_handler("startup", _on_startup)
    
    return app

# Crear la aplicación
app = create_app()

# Health check endpoint
@app.get("/health", tags=["Sistema"])
async def health_check():
    """
    Endpoint de verificación de salud del sistema.
    
    Verifica el estado de:
    - API (siempre responde si está funcionando)
    - Base de datos PostgreSQL
    - Cache Redis
    """
    try:
        # Verificar base de datos
        db_status = "connected"
        try:
            # Simple query para verificar DB
            with db_manager.get_session() as session:
                session.exec("SELECT 1").first()
        except Exception:
            db_status = "disconnected"
        
        # Verificar Redis
        redis_status = "connected" if redis_client.is_available else "disconnected"
        
        return {
            "status": "healthy",
            "service": "Tracking API",
            "version": "1.0.0",
            "timestamp": "2025-09-28T04:33:13.642411Z",
            "database": db_status,
            "cache": redis_status,
            "authentication": "enabled"
        }
        
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy", 
                "error": str(e),
                "service": "Tracking API"
            }
        )

# Información de la API
@app.get("/api/v1/info", tags=["Sistema"])
async def api_info():
    """
    Información general de la API.
    
    Endpoint público que proporciona información básica sobre la API,
    incluyendo versión, funcionalidades y enlaces útiles.
    """
    settings = get_settings()
    
    return {
        "name": "Tracking API",
        "version": "1.0.0",
        "description": "API de seguimiento de paquetes con autenticación JWT",
        "features": [
            "Autenticación JWT con roles y permisos",
            "Gestión completa de checkpoints",
            "Tracking en tiempo real",
            "Búsqueda avanzada con filtros",
            "Rate limiting y seguridad",
            "Documentación interactiva en español"
        ],
        "authentication": {
            "type": "JWT Bearer Token",
            "login_endpoint": "/api/v1/auth/login",
            "test_users": {
                "admin": "admin123 (Administrador)",
                "operator": "operator123 (Operador)", 
                "viewer": "viewer123 (Visualizador)"
            }
        },
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json"
        },
        "environment": settings.environment,
        "architecture": {
            "pattern": "Clean Architecture + DDD",
            "principles": ["SOLID", "Domain Driven Design"],
            "database": "PostgreSQL",
            "cache": "Redis"
        }
    }

# Endpoint raíz
@app.get("/", tags=["Sistema"])
async def root():
    """
    Endpoint raíz de la API.
    
    Redirige a la documentación y proporciona enlaces rápidos.
    """
    return {
        "message": "Tracking API - Sistema de seguimiento de paquetes",
        "version": "1.0.0",
        "status": "running",
        "authentication_required": True,
        "documentation": "/docs",
        "health_check": "/health",
        "api_info": "/api/v1/info",
        "login": "/api/v1/auth/login"
    }