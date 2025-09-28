from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import List, Dict, Any
import uuid
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Generator, AsyncGenerator

# Importaciones de infraestructura
from ....infrastructure.database.connection import get_async_db_session
from ....infrastructure.database.repositories.checkpoint_repository_impl import CheckpointRepositoryImpl
from ....infrastructure.database.repositories.unit_repository_impl import UnitRepositoryImpl
from ....infrastructure.database.repositories.tracking_repository_impl import TrackingRepositoryImpl
from ....infrastructure.security.auth_service import AuthService, JWTManager
from ....infrastructure.security.rate_limiter import RateLimitManager
from ....infrastructure.cache.redis_client import RedisClient

# Importaciones de casos de uso
from ....application.use_cases.create_checkpoint_use_case import CreateCheckpointUseCase
from ....application.use_cases.get_tracking_use_case import GetTrackingUseCase
from ....application.use_cases.list_units_by_status_use_case import ListUnitsByStatusUseCase

# Importaciones de servicios de dominio
from ....domain.services.domain_services import CheckpointValidationService

# Configuración
from ....config.settings import get_settings

# Global instances (en producción, usar un contenedor DI apropiado)
_redis_client = None
_auth_service = None
_rate_limiter = None
security = HTTPBearer()


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency que provee una sesión async de DB para FastAPI.
    
    Esta función sigue el patrón de inyección de dependencias de FastAPI
    y garantiza el manejo correcto de las sesiones de base de datos.
    
    Yields:
        AsyncSession: Sesión de base de datos
    """
    async for session in get_async_db_session():
        yield session


def get_redis_client() -> RedisClient:
    """
    Get Redis client singleton.
    
    Implementa el patrón Singleton para el cliente Redis,
    siguiendo el principio de responsabilidad única.
    
    Returns:
        RedisClient: Cliente de Redis configurado
    """
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = RedisClient(settings.REDIS_URL)
    return _redis_client


def get_auth_service() -> AuthService:
    """
    Get authentication service singleton.
    
    Returns:
        AuthService: Servicio de autenticación configurado
    """
    global _auth_service
    if _auth_service is None:
        settings = get_settings()
        jwt_manager = JWTManager(settings.SECRET_KEY, settings.JWT_ALGORITHM)
        _auth_service = AuthService()
    return _auth_service


def get_rate_limiter() -> RateLimitManager:
    """
    Get rate limiter singleton.
    
    Returns:
        RateLimitManager: Administrador de límites de tasa
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimitManager()
    return _rate_limiter


def get_request_id() -> str:
    """
    Generate unique request ID.
    
    Útil para trazabilidad y logging de solicitudes.
    
    Returns:
        str: ID único de solicitud
    """
    return str(uuid.uuid4())


# Repository Dependencies
def get_checkpoint_repository(
    session: AsyncSession = Depends(get_database_session)
) -> CheckpointRepositoryImpl:
    """
    Get checkpoint repository.
    
    Esta función implementa el patrón de inyección de dependencias,
    siguiendo los principios de Clean Architecture donde las dependencias
    fluyen hacia adentro (hacia el dominio).
    
    Args:
        session: Sesión de base de datos inyectada
        
    Returns:
        CheckpointRepositoryImpl: Implementación del repositorio de checkpoints
    """
    return CheckpointRepositoryImpl(session)


def get_unit_repository(
    session: AsyncSession = Depends(get_database_session)
) -> UnitRepositoryImpl:
    """
    Get unit repository.
    
    Args:
        session: Sesión de base de datos inyectada
        
    Returns:
        UnitRepositoryImpl: Implementación del repositorio de unidades
    """
    return UnitRepositoryImpl(session)


def get_tracking_repository(
    session: AsyncSession = Depends(get_database_session)
) -> TrackingRepositoryImpl:
    """
    Get tracking repository.
    
    Args:
        session: Sesión de base de datos inyectada
        
    Returns:
        TrackingRepositoryImpl: Implementación del repositorio de tracking
    """
    return TrackingRepositoryImpl(session)


# Domain Service Dependencies
def get_checkpoint_validation_service(
    checkpoint_repo: CheckpointRepositoryImpl = Depends(get_checkpoint_repository),
    unit_repo: UnitRepositoryImpl = Depends(get_unit_repository)
) -> CheckpointValidationService:
    """
    Get checkpoint validation service.
    
    Este servicio de dominio encapsula las reglas de negocio para la validación
    de checkpoints, siguiendo el principio de responsabilidad única y
    manteniendo la lógica de dominio separada de la infraestructura.
    
    Args:
        checkpoint_repo: Repositorio de checkpoints inyectado
        unit_repo: Repositorio de unidades inyectado
        
    Returns:
        CheckpointValidationService: Servicio de validación configurado
    """
    return CheckpointValidationService(
        checkpoint_repo=checkpoint_repo,
        unit_repo=unit_repo
    )


# Use Case Dependencies
def get_create_checkpoint_use_case(
    checkpoint_repo: CheckpointRepositoryImpl = Depends(get_checkpoint_repository),
    unit_repo: UnitRepositoryImpl = Depends(get_unit_repository),
    validation_service: CheckpointValidationService = Depends(get_checkpoint_validation_service)
) -> CreateCheckpointUseCase:
    """
    Get create checkpoint use case.
    
    Los casos de uso representan las operaciones de la aplicación y
    coordinan las interacciones entre entidades, servicios de dominio y repositorios.
    
    Args:
        checkpoint_repo: Repositorio de checkpoints
        unit_repo: Repositorio de unidades
        validation_service: Servicio de validación
        
    Returns:
        CreateCheckpointUseCase: Caso de uso para crear checkpoints
    """
    return CreateCheckpointUseCase(
        checkpoint_repo=checkpoint_repo,
        unit_repo=unit_repo,
        validation_service=validation_service
    )


def get_tracking_use_case(
    tracking_repo: TrackingRepositoryImpl = Depends(get_tracking_repository)
) -> GetTrackingUseCase:
    """
    Get tracking use case.
    
    Args:
        tracking_repo: Repositorio de tracking inyectado
        
    Returns:
        GetTrackingUseCase: Caso de uso para obtener información de tracking
    """
    return GetTrackingUseCase(tracking_repo)


def get_list_units_use_case(
    unit_repo: UnitRepositoryImpl = Depends(get_unit_repository)
) -> ListUnitsByStatusUseCase:
    """
    Get list units use case.
    
    Args:
        unit_repo: Repositorio de unidades inyectado
        
    Returns:
        ListUnitsByStatusUseCase: Caso de uso para listar unidades por estado
    """
    return ListUnitsByStatusUseCase(unit_repo)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """
    Dependency para autenticación global.
    
    Extrae y valida el token, retorna datos del usuario o lanza 401.
    """
    user_data = auth_service.get_current_user_from_token(credentials.credentials)
    
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalid or expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user_data

def require_permissions(required_permissions: List[str]):
    """
    Factory que crea un dependency para verificar permisos específicos.
    
    Args:
        required_permissions: Lista de permisos requeridos
        
    Returns:
        Dependency function que valida permisos
    """
    async def permission_dependency(
        current_user: Dict[str, Any] = Depends(get_current_user),
        auth_service: AuthService = Depends(get_auth_service)
    ) -> Dict[str, Any]:
        
        # Verificar cada permiso requerido
        for permission in required_permissions:
            if not auth_service.has_permission(current_user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permission: {permission}"
                )
        
        return current_user
    
    return permission_dependency

def get_correlation_id(request: Request) -> str:
    """
    Obtiene o genera un ID de correlación para la solicitud.
    
    Útil para trazabilidad distribuida y logging.
    
    Args:
        request: Solicitud HTTP de FastAPI
        
    Returns:
        str: ID de correlación
    """
    correlation_id = request.headers.get("X-Correlation-ID")
    if not correlation_id:
        correlation_id = str(uuid.uuid4())
    return correlation_id