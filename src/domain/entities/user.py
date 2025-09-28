from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

@dataclass
class User:
    """Entidad de dominio que representa un usuario del sistema."""
    
    username: str
    email: str
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    roles: Optional[List[str]] = None
    permissions: Optional[List[str]] = None
    extra_data: Optional[Dict[str, Any]] = None
    last_login: Optional[datetime] = None
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Inicializa valores por defecto después de la creación."""
        if self.id is None:
            self.id = str(uuid.uuid4())
        
        current_time = datetime.now()
        
        if self.created_at is None:
            self.created_at = current_time
        
        if self.updated_at is None:
            self.updated_at = current_time
        
        if self.roles is None:
            self.roles = ["user"]  # Rol por defecto
    
    def add_role(self, role: str):
        """
        Agrega un rol al usuario.
        
        Args:
            role: Nuevo rol a agregar
        """
        if self.roles is None:
            self.roles = []
        
        if role not in self.roles:
            self.roles.append(role)
            self.updated_at = datetime.now()
    
    def remove_role(self, role: str):
        """
        Remueve un rol del usuario.
        
        Args:
            role: Rol a remover
        """
        if self.roles and role in self.roles:
            self.roles.remove(role)
            self.updated_at = datetime.now()
    
    def has_role(self, role: str) -> bool:
        """
        Verifica si el usuario tiene un rol específico.
        
        Args:
            role: Rol a verificar
            
        Returns:
            True si el usuario tiene el rol
        """
        return self.roles is not None and role in self.roles
    
    def add_permission(self, permission: str):
        """
        Agrega un permiso al usuario.
        
        Args:
            permission: Nuevo permiso a agregar
        """
        if self.permissions is None:
            self.permissions = []
        
        if permission not in self.permissions:
            self.permissions.append(permission)
            self.updated_at = datetime.now()
    
    def has_permission(self, permission: str) -> bool:
        """
        Verifica si el usuario tiene un permiso específico.
        
        Args:
            permission: Permiso a verificar
            
        Returns:
            True si el usuario tiene el permiso
        """
        return self.permissions is not None and permission in self.permissions
    
    def activate(self):
        """Activa el usuario."""
        self.is_active = True
        self.updated_at = datetime.now()
    
    def deactivate(self):
        """Desactiva el usuario."""
        self.is_active = False
        self.updated_at = datetime.now()
    
    def update_last_login(self):
        """Actualiza la fecha del último login."""
        self.last_login = datetime.now()
        self.updated_at = datetime.now()
    
    def update_profile(self, full_name: Optional[str] = None, email: Optional[str] = None):
        """
        Actualiza el perfil del usuario.
        
        Args:
            full_name: Nuevo nombre completo
            email: Nuevo email
        """
        if full_name is not None:
            self.full_name = full_name
        
        if email is not None:
            self.email = email
        
        self.updated_at = datetime.now()
    
    def is_valid(self) -> bool:
        """
        Valida que el usuario tenga los datos mínimos requeridos.
        
        Returns:
            True si el usuario es válido
        """
        return (
            bool(self.username) and 
            bool(self.email) and 
            bool(self.hashed_password) and
            self.is_active is not None
        )
    
    def to_dict(self, include_password: bool = False) -> Dict[str, Any]:
        """
        Convierte la entidad a diccionario.
        
        Args:
            include_password: Si incluir la contraseña hasheada
            
        Returns:
            Diccionario con los datos del usuario
        """
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "roles": self.roles,
            "permissions": self.permissions,
            "extra_data": self.extra_data,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_password:
            data["hashed_password"] = self.hashed_password
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """
        Crea un usuario desde un diccionario.
        
        Args:
            data: Diccionario con los datos
            
        Returns:
            Instancia de User
        """
        # Convertir strings de fecha a datetime si es necesario
        for date_field in ["last_login", "created_at", "updated_at"]:
            if isinstance(data.get(date_field), str):
                data[date_field] = datetime.fromisoformat(data[date_field])
        
        return cls(**data)
    
    def __str__(self) -> str:
        """Representación string del usuario."""
        return f"User(id={self.id}, username={self.username}, email={self.email})"
    
    def __repr__(self) -> str:
        """Representación para debugging."""
        return self.__str__()