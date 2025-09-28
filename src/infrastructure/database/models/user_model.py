from sqlmodel import SQLModel, Field, Column, JSON
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

class UserModel(SQLModel, table=True):
    """Modelo de base de datos para usuarios."""
    
    __tablename__ = "users"
    
    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        description="ID único del usuario"
    )
    
    username: str = Field(
        unique=True,
        index=True,
        max_length=50,
        description="Nombre de usuario único"
    )
    
    email: str = Field(
        unique=True,
        index=True,
        max_length=255,
        description="Email único del usuario"
    )
    
    hashed_password: str = Field(
        max_length=255,
        description="Contraseña hasheada"
    )
    
    full_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Nombre completo del usuario"
    )
    
    is_active: bool = Field(
        default=True,
        index=True,
        description="Si el usuario está activo"
    )
    
    is_superuser: bool = Field(
        default=False,
        description="Si el usuario es superusuario"
    )
    
    roles: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Roles del usuario"
    )
    
    permissions: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Permisos específicos del usuario"
    )
    
    extra_data: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Datos adicionales del usuario"
    )
    
    last_login: Optional[datetime] = Field(
        default=None,
        description="Último login del usuario"
    )
    
    created_at: datetime = Field(
        default_factory=datetime.now,
        index=True,
        description="Fecha de creación"
    )
    
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Fecha de última actualización"
    )