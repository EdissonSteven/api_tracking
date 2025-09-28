from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.unit import Unit
from ..value_objects.tracking_id import TrackingId
from ..value_objects.unit_status import UnitStatus


class UnitRepository(ABC):
    """Repository interface for unit persistence"""
    
    @abstractmethod
    async def save(self, unit: Unit) -> Unit:
        """Save a unit"""
        pass
    
    @abstractmethod
    async def find_by_tracking_id(self, tracking_id: TrackingId) -> Optional[Unit]:
        """Find unit by tracking ID"""
        pass
    
    @abstractmethod
    async def exists_by_tracking_id(self, tracking_id: TrackingId) -> bool:
        """Check if unit exists by tracking ID"""
        pass
    
    @abstractmethod
    async def find_by_status(self, status: UnitStatus, limit: int = 100, offset: int = 0) -> List[Unit]:
        """Find units by status with pagination"""
        pass
    
    @abstractmethod
    async def update_status(self, tracking_id: TrackingId, status: UnitStatus) -> None:
        """Update unit status"""
        pass