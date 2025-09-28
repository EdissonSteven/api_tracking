from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime

class LoginRequest(BaseModel):
    """Schema para solicitud de login."""
    
    username: str = Field(
        ...,
        description="Nombre de usuario o email",
        min_length=3,
        max_length=255,
        example="admin"
    )
    
    password: str = Field(
        ...,
        description="Contraseña del usuario",
        min_length=6,
        max_length=100,
        example="admin123"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "admin",
                "password": "admin123"
            }
        }
    )

class RegisterRequest(BaseModel):
    """Schema para solicitud de registro."""
    
    username: str = Field(
        ...,
        description="Nombre de usuario único",
        min_length=3,
        max_length=50,
        example="nuevo_usuario"
    )
    
    email: EmailStr = Field(
        ...,
        description="Email único del usuario",
        example="usuario@empresa.com"
    )
    
    password: str = Field(
        ...,
        description="Contraseña del usuario",
        min_length=6,
        max_length=100,
        example="contraseña123"
    )
    
    full_name: Optional[str] = Field(
        None,
        description="Nombre completo del usuario",
        max_length=100,
        example="Juan Pérez"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "nuevo_usuario",
                "email": "usuario@empresa.com",
                "password": "contraseña123",
                "full_name": "Juan Pérez"
            }
        }
    )

class TokenResponse(BaseModel):
    """Schema para respuesta de token."""
    
    access_token: str = Field(
        ...,
        description="Token JWT de acceso"
    )
    
    refresh_token: str = Field(
        ...,
        description="Token de refresh"
    )
    
    token_type: str = Field(
        default="bearer",
        description="Tipo de token"
    )
    
    expires_in: int = Field(
        ...,
        description="Tiempo de expiración en segundos"
    )
    
    user: "UserResponse" = Field(
        ...,
        description="Información del usuario autenticado"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
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
    )

class UserResponse(BaseModel):
    """Schema para respuesta de usuario."""
    
    id: UUID = Field(
        ...,
        description="ID único del usuario"
    )
    
    username: str = Field(
        ...,
        description="Nombre de usuario"
    )
    
    email: str = Field(
        ...,
        description="Email del usuario"
    )
    
    full_name: Optional[str] = Field(
        None,
        description="Nombre completo del usuario"
    )
    
    is_active: bool = Field(
        ...,
        description="Si el usuario está activo"
    )
    
    is_superuser: bool = Field(
        default=False,
        description="Si el usuario es superusuario"
    )
    
    roles: Optional[List[str]] = Field(
        None,
        description="Roles del usuario"
    )
    
    permissions: Optional[List[str]] = Field(
        None,
        description="Permisos específicos del usuario"
    )
    
    last_login: Optional[datetime] = Field(
        None,
        description="Último login del usuario"
    )
    
    created_at: datetime = Field(
        ...,
        description="Fecha de creación"
    )
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "admin",
                "email": "admin@empresa.com",
                "full_name": "Administrador",
                "is_active": True,
                "is_superuser": False,
                "roles": ["admin"],
                "permissions": ["read", "write", "admin"],
                "last_login": "2025-09-27T15:30:00Z",
                "created_at": "2025-09-27T10:00:00Z"
            }
        }
    )

class RefreshTokenRequest(BaseModel):
    """Schema para solicitud de refresh de token."""
    
    refresh_token: str = Field(
        ...,
        description="Token de refresh"
    )

class ChangePasswordRequest(BaseModel):
    """Schema para cambio de contraseña."""
    
    current_password: str = Field(
        ...,
        description="Contraseña actual",
        min_length=6,
        max_length=100
    )
    
    new_password: str = Field(
        ...,
        description="Nueva contraseña",
        min_length=6,
        max_length=100
    )
    
    confirm_password: str = Field(
        ...,
        description="Confirmación de la nueva contraseña",
        min_length=6,
        max_length=100
    )

class UpdateProfileRequest(BaseModel):
    """Schema para actualización de perfil."""
    
    full_name: Optional[str] = Field(
        None,
        description="Nuevo nombre completo",
        max_length=100
    )
    
    email: Optional[EmailStr] = Field(
        None,
        description="Nuevo email"
    )

class AuthStatusResponse(BaseModel):
    """Schema para respuesta de estado de autenticación."""
    
    authenticated: bool = Field(
        ...,
        description="Si el usuario está autenticado"
    )
    
    user: Optional[UserResponse] = Field(
        None,
        description="Información del usuario si está autenticado"
    )
    
    permissions: List[str] = Field(
        default=[],
        description="Permisos del usuario actual"
    )
    
    expires_at: Optional[datetime] = Field(
        None,
        description="Cuándo expira el token actual"
    )

class LoginResponse(BaseModel):
    """Schema para respuesta exitosa de login."""
    
    message: str = Field(
        default="Login exitoso",
        description="Mensaje de éxito"
    )
    
    token: TokenResponse = Field(
        ...,
        description="Información del token"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Login exitoso",
                "token": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
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
    )

class RegisterResponse(BaseModel):
    """Schema para respuesta exitosa de registro."""
    
    message: str = Field(
        default="Usuario registrado exitosamente",
        description="Mensaje de éxito"
    )
    
    user: UserResponse = Field(
        ...,
        description="Usuario creado"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Usuario registrado exitosamente",
                "user": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "username": "nuevo_usuario",
                    "email": "usuario@empresa.com",
                    "full_name": "Juan Pérez",
                    "is_active": True,
                    "roles": ["user"]
                }
            }
        }
    )