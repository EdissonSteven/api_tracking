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
        """
        Add a new checkpoint (assumes validations were done by domain service).
        
        This method only performs structural validation, NOT business rules.
        Business rules (status transitions, timestamps) are validated by 
        CheckpointValidationService before calling this method.
        """
        
        # Solo validación estructural
        checkpoint_tracking_id = self._extract_value(checkpoint.tracking_id)
        unit_tracking_id = self._extract_value(self.unit.tracking_id)
        
        if checkpoint_tracking_id != unit_tracking_id:
            raise ValueError(
                f"Checkpoint tracking_id ({checkpoint_tracking_id}) "
                f"doesn't match unit tracking_id ({unit_tracking_id})"
            )
        
        # Add and sort
        self.checkpoints.append(checkpoint)
        self.checkpoints.sort(key=lambda cp: cp.timestamp)
        
        # Update unit status
        self.unit.update_status(checkpoint.status)
    
    def get_current_status(self) -> Optional[UnitStatus]:
        """Get current status from latest checkpoint"""
        if not self.checkpoints:
            return None
        
        # Los checkpoints están ordenados, tomar el último
        return self.checkpoints[-1].status
    
    def get_history(self) -> List[Checkpoint]:
        """Get ordered checkpoint history (oldest to newest)"""
        return list(self.checkpoints)  # Ya están ordenados
    
    def get_last_checkpoint(self) -> Optional[Checkpoint]:
        """Get the most recent checkpoint"""
        if not self.checkpoints:
            return None
        
        # Los checkpoints están ordenados, tomar el último
        return self.checkpoints[-1]
    
    def is_complete(self) -> bool:
        """Check if tracking is complete (delivered or exception)"""
        current_status = self.get_current_status()
        if not current_status:
            return False
        
        return current_status in [UnitStatus.DELIVERED, UnitStatus.EXCEPTION]
    
    @staticmethod
    def _extract_value(obj):
        """Extract value from value object or return as-is"""
        if hasattr(obj, 'value'):
            return obj.value
        return obj