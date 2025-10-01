"""
Test Helpers y Factories para tests unitarios.

Factories para crear objetos de prueba sin dependencias de infraestructura.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4

from src.application.dtos.checkpoint_dto import CheckpointResponse as CheckpointDTO


class DTOFactory:
    """Factory para crear DTOs de aplicación en tests."""
    
    @staticmethod
    def create_checkpoint_dto(
        checkpoint_id: Optional[str] = None,
        tracking_id: str = "TRK001",
        status: str = "CREATED",
        location: str = "Test Location",
        operator: str = "Test Operator",
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ) -> CheckpointDTO:
        """Crea un CheckpointDTO para tests."""
        now = datetime.now()
        
        return CheckpointDTO(
            id=checkpoint_id or str(uuid4()),
            tracking_id=tracking_id,
            status=status,
            location=location,
            operator=operator,
            description=description,
            metadata=metadata or {},
            timestamp=timestamp or now,
            created_at=created_at or now,
            updated_at=updated_at or now
        )


class UserFactory:
    """Factory para crear usuarios de prueba."""
    
    @staticmethod
    def create_user_data(
        user_id: Optional[str] = None,
        username: str = "test_user",
        email: str = "test@example.com",
        roles: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None,
        is_superuser: bool = False
    ) -> Dict[str, Any]:
        """Crea datos de usuario para tests."""
        return {
            "user_id": user_id or str(uuid4()),
            "username": username,
            "email": email,
            "roles": roles or ["viewer"],
            "permissions": permissions or ["tracking:read"],
            "is_superuser": is_superuser,
            "is_active": True
        }
    
    @staticmethod
    def create_admin_user() -> Dict[str, Any]:
        """Crea un usuario administrador."""
        return UserFactory.create_user_data(
            username="admin",
            roles=["admin"],
            permissions=["checkpoint:create", "checkpoint:read", "tracking:read", "units:read"],
            is_superuser=True
        )
    
    @staticmethod
    def create_operator_user() -> Dict[str, Any]:
        """Crea un usuario operador con permisos de escritura."""
        return UserFactory.create_user_data(
            username="operator",
            roles=["operator"],
            permissions=["checkpoint:create", "checkpoint:read", "tracking:read", "units:read"],
            is_superuser=False
        )
    
    @staticmethod
    def create_viewer_user() -> Dict[str, Any]:
        """Crea un usuario visualizador (solo lectura, SIN checkpoint:create)."""
        return UserFactory.create_user_data(
            username="viewer",
            roles=["viewer"],
            permissions=["tracking:read", "units:read"],  # NO tiene checkpoint:create
            is_superuser=False
        )