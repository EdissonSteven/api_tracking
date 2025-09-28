from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from .checkpoint import Checkpoint
from .unit import Unit
from ..value_objects.tracking_id import TrackingId
from ..value_objects.unit_status import UnitStatus


@dataclass
class Tracking:
    """Aggregate root for tracking information"""
    
    unit: Unit
    checkpoints: List[Checkpoint] = field(default_factory=list)
    
    def add_checkpoint(self, checkpoint: Checkpoint) -> None:
        """Add a new checkpoint with business validation"""
        
        # Validate checkpoint belongs to this unit
        if checkpoint.tracking_id != self.unit.tracking_id:
            raise ValueError("Checkpoint tracking_id doesn't match unit tracking_id")
        
        # Validate business rules for status transition
        if self.checkpoints and self.get_current_status():
            current_status = self.get_current_status()
            if not current_status.can_transition_to(checkpoint.status):
                raise ValueError(
                    f"Invalid status transition from {current_status.value} to {checkpoint.status.value}"
                )
        
        # Validate checkpoint is not in the past relative to last checkpoint
        if self.checkpoints:
            last_checkpoint = max(self.checkpoints, key=lambda cp: cp.timestamp)
            if checkpoint.timestamp < last_checkpoint.timestamp:
                raise ValueError("Checkpoint timestamp cannot be in the past relative to last checkpoint")
        
        # Add checkpoint and update unit status
        self.checkpoints.append(checkpoint)
        self.checkpoints.sort(key=lambda cp: cp.timestamp)
        self.unit.update_status(checkpoint.status)
    
    def get_current_status(self) -> Optional[UnitStatus]:
        """Get current status from latest checkpoint"""
        if not self.checkpoints:
            return None
        
        latest_checkpoint = max(self.checkpoints, key=lambda cp: cp.timestamp)
        return latest_checkpoint.status
    
    def get_history(self) -> List[Checkpoint]:
        """Get ordered checkpoint history"""
        return sorted(self.checkpoints, key=lambda cp: cp.timestamp)
    
    def get_last_checkpoint(self) -> Optional[Checkpoint]:
        """Get the most recent checkpoint"""
        if not self.checkpoints:
            return None
        return max(self.checkpoints, key=lambda cp: cp.timestamp)
    
    def is_complete(self) -> bool:
        """Check if tracking is complete (delivered or exception)"""
        current_status = self.get_current_status()
        return current_status in [UnitStatus.DELIVERED, UnitStatus.EXCEPTION]