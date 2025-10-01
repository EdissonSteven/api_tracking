from abc import ABC, abstractmethod
from typing import List, Optional

from ..value_objects.tracking_id import TrackingId
from ..value_objects.unit_status import UnitStatus
from ..entities.checkpoint import Checkpoint

class CheckpointRepository(ABC):
    """Interfaz para el repositorio de checkpoints."""
    
    @abstractmethod
    async def create(self, checkpoint: Checkpoint) -> Checkpoint:
        """
        Crea un nuevo checkpoint.
        
        Args:
            checkpoint: Entidad checkpoint a crear
            
        Returns:
            Checkpoint creado con ID asignado
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """
        Obtiene un checkpoint por su ID.
        
        Args:
            checkpoint_id: ID del checkpoint
            
        Returns:
            Checkpoint encontrado o None
        """
        pass
    
    @abstractmethod
    async def get_by_tracking_id(self, tracking_id: str) -> List[Checkpoint]:
        """
        Obtiene todos los checkpoints de un tracking ID.
        
        Args:
            tracking_id: ID de seguimiento
            
        Returns:
            Lista de checkpoints ordenados por timestamp
        """
        pass
    
    @abstractmethod
    async def get_latest_by_tracking_id(self, tracking_id: str) -> Optional[Checkpoint]:
        """
        Obtiene el checkpoint más reciente de un tracking ID.
        
        Args:
            tracking_id: ID de seguimiento
            
        Returns:
            Checkpoint más reciente o None
        """
        pass
    
    @abstractmethod
    async def update(self, checkpoint: Checkpoint) -> Checkpoint:
        """
        Actualiza un checkpoint existente.
        
        Args:
            checkpoint: Entidad checkpoint actualizada
            
        Returns:
            Checkpoint actualizado
        """
        pass
    
    @abstractmethod
    async def delete(self, checkpoint_id: str) -> bool:
        """
        Elimina un checkpoint por su ID.
        
        Args:
            checkpoint_id: ID del checkpoint a eliminar
            
        Returns:
            True si se eliminó exitosamente
        """
        pass
    
    @abstractmethod
    async def get_by_status(
        self, 
        status: str, 
        limit: Optional[int] = None
    ) -> List[Checkpoint]:
        """
        Obtiene checkpoints por estado.
        
        Args:
            status: Estado a filtrar
            limit: Límite opcional de resultados
            
        Returns:
            Lista de checkpoints con el estado especificado
        """
        pass
    
    @abstractmethod
    async def count_by_tracking_id(self, tracking_id: str) -> int:
        """
        Cuenta los checkpoints de un tracking ID.
        
        Args:
            tracking_id: ID de seguimiento
            
        Returns:
            Número de checkpoints
        """
        pass
    
    @abstractmethod
    async def exists(self, checkpoint_id: str) -> bool:
        """
        Verifica si existe un checkpoint con el ID dado.
        
        Args:
            checkpoint_id: ID del checkpoint
            
        Returns:
            True si existe
        """
        pass

    @abstractmethod
    async def exists_by_tracking_id_and_status(
        self, 
        tracking_id: TrackingId, 
        status: UnitStatus
    ) -> bool:
        """Check if a checkpoint already exists with specific tracking_id and status"""
        pass