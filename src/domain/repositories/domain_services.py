from typing import Optional
from datetime import datetime

from ..entities.checkpoint import Checkpoint
from ..entities.tracking import Tracking
from ..value_objects.tracking_id import TrackingId
from ..value_objects.unit_status import UnitStatus
from ..repositories.checkpoint_repository import CheckpointRepository
from ..repositories.unit_repository import UnitRepository


class CheckpointValidationService:
    """Domain service for checkpoint validation"""
    
    def __init__(
        self,
        checkpoint_repo: CheckpointRepository,
        unit_repo: UnitRepository
    ):
        self._checkpoint_repo = checkpoint_repo
        self._unit_repo = unit_repo
    
    async def validate_checkpoint_creation(
        self,
        tracking_id: TrackingId,
        new_status: UnitStatus,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Validate if a checkpoint can be created"""
        
        # Check if unit exists
        unit_exists = await self._unit_repo.exists_by_tracking_id(tracking_id)
        if not unit_exists:
            raise ValueError(f"Unit with tracking_id {tracking_id.value} does not exist")
        
        # Get current status
        latest_checkpoint = await self._checkpoint_repo.find_latest_by_tracking_id(tracking_id)
        
        if latest_checkpoint:
            # Validate status transition
            if not latest_checkpoint.status.can_transition_to(new_status):
                raise ValueError(
                    f"Invalid status transition from {latest_checkpoint.status.value} to {new_status.value}"
                )
            
            # Validate timestamp is not in the past
            if timestamp and timestamp < latest_checkpoint.timestamp:
                raise ValueError("Checkpoint timestamp cannot be in the past")
        
        return True
    
    async def ensure_idempotency(
        self,
        tracking_id: TrackingId,
        status: UnitStatus
    ) -> bool:
        """Check if checkpoint already exists (for idempotency)"""
        return await self._checkpoint_repo.exists_by_tracking_id_and_status(
            tracking_id, status
        )