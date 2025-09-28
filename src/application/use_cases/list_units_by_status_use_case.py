import logging
from typing import List

from ..dtos.tracking_dto import UnitResponse
from ...domain.entities.unit import Unit
from ...domain.value_objects.unit_status import UnitStatus
from ...domain.repositories.unit_repository import UnitRepository


logger = logging.getLogger(__name__)


class ListUnitsByStatusUseCase:
    """Use case for listing units by status"""
    
    def __init__(self, unit_repo: UnitRepository):
        self._unit_repo = unit_repo
    
    async def execute(
        self, 
        status_str: str, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[UnitResponse]:
        """Execute list units by status use case"""
        
        try:
            status = UnitStatus(status_str)
            
            units = await self._unit_repo.find_by_status(status, limit, offset)
            
            return [self._map_to_response(unit) for unit in units]
            
        except ValueError as e:
            logger.error(f"Validation error listing units: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error listing units: {str(e)}")
            raise Exception("Internal error listing units")
    
    def _map_to_response(self, unit: Unit) -> UnitResponse:
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