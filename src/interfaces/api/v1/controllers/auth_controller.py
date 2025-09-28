from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session
from typing import Dict, Any
import logging

from ..schemas.auth_schemas import LoginRequest, TokenResponse, UserResponse
from ..schemas.error_schemas import ErrorResponse, BusinessErrorResponse
from src.infrastructure.database.connection import get_db_session
from src.infrastructure.database.repositories.user_repository_impl import UserRepositoryImpl
from src.infrastructure.security.auth_service import get_auth_service
from src.config.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Autenticación"])
security = HTTPBearer()

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión",
    description="Autentica un usuario y retorna un token JWT para acceso a la API",
    responses={
        200: {
            "description": "Login exitoso",
            "model": TokenResponse,
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "expires_in": 1800,
                        "user": {
                            "id": "550e8400-e29b-41d4-a716-446655440000",
                            "username": "admin",
                            "email": "admin@empresa.com",
                            "full_name": "Administrador",
                            "is_active": True,
                            "roles": ["admin"]
                        }
                    }
                }
            }
        },
        401: {
            "description": "Credenciales inválidas",
            "model": ErrorResponse
        },
        422: {
            "description": "Error de validación",
            "model": ErrorResponse
        },
        500: {
            "description": "Error del servidor",
            "model": ErrorResponse
        }
    }
)
async def login(
    login_data: LoginRequest,
    session: Session = Depends(get_db_session)
):
    """
    Endpoint de login para obtener token JWT.
    
    **Usuarios de prueba:**
    - Username: `admin`, Password: `admin123` (Administrador - todos los permisos)
    - Username: `operator`, Password: `operator123` (Operador - lectura y escritura)
    - Username: `viewer`, Password: `viewer123` (Visualizador - solo lectura)
    
    **El token retornado debe incluirse en el header de las siguientes requests:**
    ```
    Authorization: Bearer <access_token>
    ```
    """
    try:
        # Obtener servicios
        auth_service = get_auth_service()
        user_repository = UserRepositoryImpl(session)
        settings = get_settings()
        
        # Autenticar usuario
        user = auth_service.authenticate_user(
            username=login_data.username,
            password=login_data.password,
            user_repository=user_repository
        )
        
        if not user:
            logger.warning(f"Intento de login fallido para: {login_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if not user.is_active:
            logger.warning(f"Intento de login con usuario inactivo: {login_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario inactivo",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Crear tokens
        access_token = auth_service.create_access_token(user)

        # Crear refresh token si el servicio lo soporta, si no usar fallback
        try:
            if hasattr(auth_service, "create_refresh_token"):
                refresh_token = auth_service.create_refresh_token(user)
            else:
                refresh_token = access_token
        except Exception:
            # no queremos que la creación del refresh token rompa el login,
            # devolver al menos el access token como fallback
            refresh_token = access_token
            
        # Preparar respuesta de usuario
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            roles=user.roles,
            permissions=user.permissions,
            last_login=user.last_login,
            created_at=user.created_at
        )
        
        # Respuesta exitosa
        logger.info(f"Login exitoso para usuario: {user.username}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,  # Convertir a segundos
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Información del usuario actual",
    description="Obtiene la información del usuario autenticado basado en el token JWT",
    responses={
        200: {
            "description": "Información del usuario actual",
            "model": UserResponse
        },
        401: {
            "description": "Token inválido o expirado",
            "model": ErrorResponse
        }
    }
)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_db_session)
):
    """
    Obtiene la información del usuario actual basado en el token JWT.
    
    **Requiere autenticación:**
    ```
    Authorization: Bearer <access_token>
    ```
    """
    try:
        # Verificar token
        auth_service = get_auth_service()
        user_data = auth_service.get_current_user_from_token(credentials.credentials)
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Obtener usuario completo de la base de datos
        user_repository = UserRepositoryImpl(session)
        user = user_repository.get_by_username(user_data["username"])
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado o inactivo",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            roles=user.roles,
            permissions=user.permissions,
            last_login=user.last_login,
            created_at=user.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo usuario actual: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@router.post(
    "/validate",
    response_model=Dict[str, Any],
    summary="Validar token",
    description="Valida un token JWT y retorna información sobre su validez",
    responses={
        200: {
            "description": "Token válido",
            "content": {
                "application/json": {
                    "example": {
                        "valid": True,
                        "username": "admin",
                        "roles": ["admin"],
                        "permissions": ["read", "write", "delete", "admin"],
                        "expires_at": "2025-09-28T05:30:00Z"
                    }
                }
            }
        },
        401: {
            "description": "Token inválido",
            "model": ErrorResponse
        }
    }
)
async def validate_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Valida un token JWT sin necesidad de acceso a base de datos.
    
    **Útil para verificar si un token es válido antes de hacer otras requests.**
    """
    try:
        auth_service = get_auth_service()
        payload = auth_service.decode_token(credentials.credentials)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return {
            "valid": True,
            "username": payload.get("sub"),
            "user_id": payload.get("user_id"),
            "roles": payload.get("roles", []),
            "permissions": payload.get("permissions", []),
            "is_superuser": payload.get("is_superuser", False),
            "expires_at": payload.get("exp"),
            "token_type": payload.get("type")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validando token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )