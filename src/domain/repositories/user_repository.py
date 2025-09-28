from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.user import User

class UserRepository(ABC):
    """Interfaz para el repositorio de usuarios."""
    
    @abstractmethod
    async def create(self, user: User) -> User:
        """
        Crea un nuevo usuario.
        
        Args:
            user: Entidad usuario a crear
            
        Returns:
            Usuario creado con ID asignado
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Obtiene un usuario por su ID.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Usuario encontrado o None
        """
        pass
    
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Obtiene un usuario por su username.
        
        Args:
            username: Nombre de usuario
            
        Returns:
            Usuario encontrado o None
        """
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Obtiene un usuario por su email.
        
        Args:
            email: Email del usuario
            
        Returns:
            Usuario encontrado o None
        """
        pass
    
    @abstractmethod
    async def update(self, user: User) -> User:
        """
        Actualiza un usuario existente.
        
        Args:
            user: Entidad usuario actualizada
            
        Returns:
            Usuario actualizado
        """
        pass
    
    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """
        Elimina un usuario por su ID.
        
        Args:
            user_id: ID del usuario a eliminar
            
        Returns:
            True si se eliminó exitosamente
        """
        pass
    
    @abstractmethod
    async def get_active_users(self, limit: Optional[int] = None) -> List[User]:
        """
        Obtiene usuarios activos.
        
        Args:
            limit: Límite opcional de resultados
            
        Returns:
            Lista de usuarios activos
        """
        pass
    
    @abstractmethod
    async def get_by_role(self, role: str) -> List[User]:
        """
        Obtiene usuarios por rol.
        
        Args:
            role: Rol a filtrar
            
        Returns:
            Lista de usuarios con el rol especificado
        """
        pass
    
    @abstractmethod
    async def username_exists(self, username: str) -> bool:
        """
        Verifica si existe un usuario con el username dado.
        
        Args:
            username: Username a verificar
            
        Returns:
            True si existe
        """
        pass
    
    @abstractmethod
    async def email_exists(self, email: str) -> bool:
        """
        Verifica si existe un usuario con el email dado.
        
        Args:
            email: Email a verificar
            
        Returns:
            True si existe
        """
        pass
    
    @abstractmethod
    async def count_total(self) -> int:
        """
        Cuenta el total de usuarios.
        
        Returns:
            Número total de usuarios
        """
        pass
    
    @abstractmethod
    async def get_superusers(self) -> List[User]:
        """
        Obtiene todos los superusuarios.
        
        Returns:
            Lista de superusuarios
        """
        pass
