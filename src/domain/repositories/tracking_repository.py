from abc import ABC, abstractmethod
from typing import Optional

from ..entities.tracking import Tracking
from ..value_objects.tracking_id import TrackingId


class TrackingRepository(ABC):
    """Repository interface for tracking aggregate"""
    
    @abstractmethod
    async def find_by_tracking_id(self, tracking_id: TrackingId) -> Optional[Tracking]:
        """Find complete tracking information by tracking ID"""
        pass
    
    @abstractmethod
    async def save(self, tracking: Tracking) -> Tracking:
        """Save tracking aggregate"""
        pass