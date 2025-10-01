from typing import Optional
from datetime import datetime

from ..domain_exceptions import BusinessRuleViolationError
from ..value_objects.tracking_id import TrackingId
from ..value_objects.unit_status import UnitStatus
from ..repositories.checkpoint_repository import CheckpointRepository
from ..repositories.unit_repository import UnitRepository


class CheckpointValidationService:
    """Domain service for checkpoint validation"""
    
    def __init__(self, checkpoint_repo: CheckpointRepository, unit_repo: UnitRepository):
        self._checkpoint_repo = checkpoint_repo
        self._unit_repo = unit_repo
    
    def validate_checkpoint_creation(
        self,
        tracking_id: TrackingId,
        new_status: UnitStatus,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Validate if a checkpoint can be created"""
        
        # Check if unit exists
        unit_exists = self._unit_repo.exists_by_tracking_id(tracking_id)
        if not unit_exists:
            raise BusinessRuleViolationError(
                    message=f"La unidad con tracking_id {tracking_id.value} no existe",
                rule_name="unit_existence",
                context={"tracking_id": tracking_id.value}
            )
        
        # Get current status
        latest_checkpoint = self._checkpoint_repo.find_latest_by_tracking_id(tracking_id)
        
        if latest_checkpoint:
            # Convertir status string a UnitStatus para validación
            current_status = UnitStatus(latest_checkpoint.status) if isinstance(latest_checkpoint.status, str) else latest_checkpoint.status
            allowed_transitions = current_status.get_allowed_transitions()
            # Validate status transition
            if not current_status.can_transition_to(new_status):
                raise BusinessRuleViolationError(
                    message=f"Invalid status transition from {current_status.value} to {new_status.value}",
                    rule_name="status_transition",
                    context={
                        "from_status": current_status.value,
                        "to_status": new_status.value,
                        "allowed_transitions": allowed_transitions
                    }
                )
            
            # Validate timestamp
            if timestamp and timestamp < latest_checkpoint.timestamp:
                raise BusinessRuleViolationError(
                    message="La fecha del checkpoint no puede ser anterior al checkpoint previo",
                    rule_name="timestamp_order"
                )
        
        return True
    
    def ensure_idempotency(
        self,
        tracking_id: TrackingId,
        status: UnitStatus
    ) -> bool:
        """Check if checkpoint already exists (for idempotency)"""
        # SIN await
        return self._checkpoint_repo.exists_by_tracking_id_and_status(tracking_id, status)