import logging
from typing import Optional

from application.dtos.tracking_dto import TrackingResponse, UnitResponse
from application.dtos.checkpoint_dto import CheckpointResponse
from domain.entities.checkpoint import Checkpoint
from domain.entities.unit import Unit
from domain.value_objects.tracking_id import TrackingId
from domain.repositories.tracking_repository import TrackingRepository


logger = logging.getLogger(__name__)


class GetTrackingUseCase:
    """Use case for getting tracking information"""
    
    def __init__(self, tracking_repo: TrackingRepository):
        self._tracking_repo = tracking_repo
    
    async def execute(self, tracking_id_str: str) -> Optional[TrackingResponse]:
        """Execute get tracking use case"""
        
        try:
            tracking_id = TrackingId(tracking_id_str)
            
            tracking = await self._tracking_repo.get_by_tracking_id(tracking_id)
            
            if not tracking:
                return None
            
            return self._map_to_response(tracking)
            
        except ValueError as e:
            logger.error(f"Validation error getting tracking: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error getting tracking: {str(e)}")
            raise Exception("Internal error getting tracking")
    
    def _map_to_response(self, tracking) -> TrackingResponse:
        """Map domain aggregate to response DTO"""
        return TrackingResponse(
            tracking_id=tracking.unit.tracking_id.value,
            current_status=tracking.unit.current_status.value,
            checkpoints=[self._map_checkpoint_to_response(cp) for cp in tracking.get_history()],
            unit_info=self._map_unit_to_response(tracking.unit)
        )
    
    def _map_checkpoint_to_response(self, checkpoint: Checkpoint) -> CheckpointResponse:
        """Map checkpoint entity to response DTO"""
        return CheckpointResponse(
            id=checkpoint.id.value,
            tracking_id=checkpoint.tracking_id.value,
            status=checkpoint.status.value,
            timestamp=checkpoint.timestamp,
            location=checkpoint.location,
            description=checkpoint.description,
            operator=checkpoint.operator,
            meta_data=checkpoint.meta_data,
            created_at=checkpoint.created_at
        )
    
    def _map_unit_to_response(self, unit: Unit) -> UnitResponse:
        """Map unit entity to response DTO"""
        return UnitResponse(
            tracking_id=unit.tracking_id.value,
            current_status=unit.current_status.value,
            created_at=unit.created_at,
            updated_at=unit.updated_at,
            guide_id=unit.guide_id,
            weight=unit.weight,
            dimensions=unit.dimensions,
            origin=unit.origin,
            destination=unit.destination
        )