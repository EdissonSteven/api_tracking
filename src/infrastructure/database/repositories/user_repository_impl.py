from domain.entities.user import User
from sqlmodel import Session, select, desc
from typing import List, Optional
import logging
from datetime import datetime
from ..models.user_model import UserModel

logger = logging.getLogger(__name__)

class UserRepositoryImpl:
    """Implementación del repositorio de User - Versión Síncrona."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_username(self, username: str) -> Optional['User']:
        """
        Obtiene un usuario por su username - SÍNCRONO.
        
        Args:
            username: Nombre de usuario
            
        Returns:
            Usuario encontrado o None
        """
        try:
            statement = select(UserModel).where(UserModel.username == username)
            result = self.session.exec(statement).first()
            
            if result:
                return result
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo usuario por username {username}: {e}")
            raise
    
    def get_by_email(self, email: str) -> Optional['User']:
        """Obtiene usuario por email - SÍNCRONO."""
        try:
            statement = select(UserModel).where(UserModel.email == email)
            result = self.session.exec(statement).first()
            
            if result:
                return result
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo usuario por email {email}: {e}")
            raise
    
    def get_by_id(self, user_id: str) -> Optional['User']:
        """Obtiene usuario por ID - SÍNCRONO."""
        try:
            statement = select(UserModel).where(UserModel.id == user_id)
            result = self.session.exec(statement).first()
            
            if result:
                return result
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo usuario por ID {user_id}: {e}")
            raise
    
    def update(self, user: 'User') -> 'User':
        """Actualiza usuario - SÍNCRONO."""
        try:
            # Encontrar el usuario existente
            statement = select(UserModel).where(UserModel.id == user.id)
            db_user = self.session.exec(statement).first()
            
            if not db_user:
                raise ValueError(f"Usuario con ID {user.id} no encontrado")
            
            # Actualizar campos básicos
            db_user.last_login = datetime.now()
            db_user.updated_at = datetime.now()
            
            self.session.add(db_user)
            self.session.commit()
            self.session.refresh(db_user)
            
            return db_user
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error actualizando usuario {user.id}: {e}")
            raise
    
    def create(self, user: 'User') -> 'User':
        """Crea nuevo usuario - SÍNCRONO."""
        try:
            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)
            return user
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creando usuario: {e}")
            raise