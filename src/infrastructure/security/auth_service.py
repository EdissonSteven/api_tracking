from http.client import HTTPException
from fastapi import HTTPException, status
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from passlib.hash import bcrypt
import logging
from pydantic import BaseModel

from ...config.settings import get_settings
from ...domain.entities.user import User

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """Servicio para manejo de autenticación y JWT."""
    
    def __init__(self):
        self.settings = get_settings()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = self.settings.SECRET_KEY
        self.algorithm = getattr(self.settings, 'JWT_ALGORITHM', 'HS256')
        self.access_token_expire_minutes = getattr(
            self.settings, 'ACCESS_TOKEN_EXPIRE_MINUTES', 30
        )
    
    def hash_password(self, password: str) -> str:
        """
        Genera hash de una contraseña.
        
        Args:
            password: Contraseña en texto plano
            
        Returns:
            Hash de la contraseña
        """
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verifica una contraseña contra su hash.
        
        Args:
            plain_password: Contraseña en texto plano
            hashed_password: Hash almacenado
            
        Returns:
            True si la contraseña es correcta
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(
        self, 
        user: User, 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Crea un token JWT de acceso.
        
        Args:
            user: Usuario para el token
            expires_delta: Tiempo de expiración personalizado
            
        Returns:
            Token JWT
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.access_token_expire_minutes
            )
        
        to_encode = {
            "sub": user.username,
            "user_id": str(user.id),
            "email": user.email,
            "roles": user.roles or [],
            "permissions": user.permissions or [],
            "is_superuser": user.is_superuser,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        try:
            encoded_jwt = jwt.encode(
                to_encode, 
                self.secret_key, 
                algorithm=self.algorithm
            )
            logger.info(f"Token creado para usuario: {user.username}")
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creando token: {e}")
            raise
    
    def create_refresh_token(self, user: User) -> str:
        """
        Crea un token de refresh.
        
        Args:
            user: Usuario para el token
            
        Returns:
            Token de refresh
        """
        expire = datetime.utcnow() + timedelta(days=7)  # 7 días para refresh
        
        to_encode = {
            "sub": user.username,
            "user_id": str(user.id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        try:
            encoded_jwt = jwt.encode(
                to_encode, 
                self.secret_key, 
                algorithm=self.algorithm
            )
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creando refresh token: {e}")
            raise
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decodifica y valida un token JWT.
        
        Args:
            token: Token JWT a decodificar
            
        Returns:
            Payload del token o None si es inválido
        """
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            
            # Verificar que no esté expirado
            exp = payload.get("exp")
            if exp and datetime.utcnow() > datetime.fromtimestamp(exp):
                logger.warning("Token expirado")
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expirado")
            return None
        except jwt.JWTError as e:
            logger.warning(f"Token inválido: {e}")
            return None
        except Exception as e:
            logger.error(f"Error decodificando token: {e}")
            return None
    
    def get_current_user_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Extrae información del usuario actual desde un token.
        
        Args:
            token: Token JWT
            
        Returns:
            Datos del usuario o None si el token es inválido
        """
        payload = self.decode_token(token)
        if not payload:
            return None
        
        # Verificar que sea un token de acceso
        if payload.get("type") != "access":
            logger.warning("Token no es de tipo access")
            return None
        
        return {
            "username": payload.get("sub"),
            "user_id": payload.get("user_id"),
            "email": payload.get("email"),
            "roles": payload.get("roles", []),
            "permissions": payload.get("permissions", []),
            "is_superuser": payload.get("is_superuser", False)
        }
    
    def authenticate_user(
        
        self, 
        username: str, 
        password: str, 
        user_repository
    ) -> Optional[User]:
        """
        Autentica un usuario con username/email y contraseña.
        
        Args:
            username: Nombre de usuario o email
            password: Contraseña en texto plano
            user_repository: Repositorio de usuarios
            
        Returns:
            Usuario autenticado o None si las credenciales son incorrectas
            
        Raises:
            Exception: Propaga errores técnicos (BD, etc.) para manejo en el controlador
        """
        # Buscar usuario por username o email - errores técnicos se propagan
        user = None
        if "@" in username:
            # Es un email
            user = user_repository.get_by_email(username)
        else:
            # Es un username
            user = user_repository.get_by_username(username)
        
        if not user:
            logger.warning(f"Usuario no encontrado: {username}")
            return None
        
        if not user.is_active:
            logger.warning(f"Usuario inactivo: {username}")
            return None
        
        if not self.verify_password(password, user.hashed_password):
            logger.warning(f"Contraseña incorrecta para: {username}")
            return None
        
        # Actualizar último login en el registro DB (compatibilidad con UserModel)
        try:
            if hasattr(user, "last_login"):
                user.last_login = datetime.utcnow()
            if hasattr(user, "updated_at"):
                user.updated_at = datetime.utcnow()
            # Persistir cambios; repository debe encargarse del commit/refresh
            user_repository.update(user)
        except Exception as e:
            logger.error(f"Error actualizando last_login para {username}: {e}")
            raise
        
        logger.info(f"Usuario autenticado exitosamente: {username}")
        return user
    
    def has_permission(self, user_data: Dict[str, Any], required_permission: str) -> bool:
        """
        Verifica si un usuario tiene un permiso específico.
        
        Args:
            user_data: Datos del usuario desde el token
            required_permission: Permiso requerido
            
        Returns:
            True si el usuario tiene el permiso
        """
        # Superusuarios tienen todos los permisos
        if user_data.get("is_superuser"):
            return True
        
        # Verificar permisos específicos
        permissions = user_data.get("permissions", [])
        if required_permission in permissions:
            return True
        
        # Verificar permisos por rol
        roles = user_data.get("roles", [])
        role_permissions = {
            "admin": ["read", "write", "delete", "admin"],
            "operator": ["read", "write"],
            "viewer": ["read"]
        }
        
        for role in roles:
            if role in role_permissions:
                if required_permission in role_permissions[role]:
                    return True
        
        return False
    
    def has_role(self, user_data: Dict[str, Any], required_role: str) -> bool:
        """
        Verifica si un usuario tiene un rol específico.
        
        Args:
            user_data: Datos del usuario desde el token
            required_role: Rol requerido
            
        Returns:
            True si el usuario tiene el rol
        """
        if user_data.get("is_superuser"):
            return True
        
        roles = user_data.get("roles", [])
        return required_role in roles

# Instancia global del servicio de autenticación
auth_service = AuthService()

def get_auth_service() -> AuthService:
    """Obtiene la instancia del servicio de autenticación."""
    return auth_service

class TokenData(BaseModel):
    sub: Optional[str] = None
    scopes: list[str] = []
    exp: Optional[datetime] = None

class JWTManager:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def create_access_token(
        self, 
        data: dict, 
        expires_delta: Optional[timedelta] = None,
        scopes: Optional[list[str]] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({
            "exp": expire,
            "scopes": scopes or []
        })
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating JWT token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create access token"
            )
    
    def verify_token(self, token: str) -> TokenData:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            sub: str = payload.get("sub")
            if sub is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            scopes = payload.get("scopes", [])
            exp = payload.get("exp")
            
            return TokenData(
                sub=sub, 
                scopes=scopes,
                exp=datetime.fromtimestamp(exp) if exp else None
            )
            
        except JWTError as e:
            logger.warning(f"JWT verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash password"""
        return pwd_context.hash(password)
    