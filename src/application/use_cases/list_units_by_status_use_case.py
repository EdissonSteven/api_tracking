from typing import List, Tuple
import logging

from ..dtos.tracking_dto import UnitResponse
from ...domain.entities.unit import Unit
from ...domain.value_objects.unit_status import UnitStatus
from ...domain.repositories.unit_repository import UnitRepository

logger = logging.getLogger(__name__)


class ListUnitsByStatusUseCase:
    """Use case for listing units by status"""
    
    def __init__(self, unit_repo: UnitRepository):
        self._unit_repo = unit_repo
    
    def execute(
        self, 
        status_str: str, 
        limit: int = 100, 
        offset: int = 0
    ) -> Tuple[List[UnitResponse], int]:
        """Execute list units by status use case"""
        
        try:
            status = UnitStatus(status_str)
            
            # Get units and total count
            units = self._unit_repo.find_by_status(status, limit, offset)
            total_count = self._unit_repo.count_by_status(status)
            
            # Map to DTO
            unit_responses = [self._map_to_response(unit) for unit in units]
            
            return unit_responses, total_count
            
        except ValueError as e:
            logger.error(f"Validation error listing units: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error listing units: {str(e)}", exc_info=True)
            raise Exception(f"Internal error listing units: {str(e)}")
    
    def _map_to_response(self, unit: Unit) -> UnitResponse:
        """Map unit entity to DTO"""
        
        def safe_value(obj):
            return obj.value if hasattr(obj, 'value') else str(obj)
        
        return UnitResponse(
            id=getattr(unit, 'id', None),
            tracking_id=safe_value(unit.tracking_id),
            origin=getattr(unit, 'origin', None),
            destination=getattr(unit, 'destination', None),
            status=safe_value(unit.current_status),
            created_at=unit.created_at,
            updated_at=unit.updated_at,
            guide_id=str(unit.guide_id) if unit.guide_id else None,
            weight_kg=getattr(unit, 'weight_kg', None),
            dimensions=getattr(unit, 'dimensions', None),
            customer_info=getattr(unit, 'customer_info', None),
            meta_data=getattr(unit, 'meta_data', None)
        )