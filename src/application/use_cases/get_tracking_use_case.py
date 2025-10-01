import logging
from typing import Optional
from datetime import datetime

from ...application.dtos.tracking_dto import TrackingResponse, UnitResponse
from ...application.dtos.checkpoint_dto import CheckpointResponse
from ...domain.entities.checkpoint import Checkpoint
from ...domain.value_objects.tracking_id import TrackingId
from ...domain.repositories.tracking_repository import TrackingRepository
from ...domain.repositories.unit_repository import UnitRepository


logger = logging.getLogger(__name__)


class GetTrackingUseCase:
    """Use case for getting tracking information"""
    
    def __init__(self, tracking_repo: TrackingRepository, unit_repo: UnitRepository = None):
        self._tracking_repo = tracking_repo
        self._unit_repo = unit_repo
    
    def execute(self, tracking_id_str: str) -> Optional[TrackingResponse]:
        """Execute get tracking use case"""
        
        try:
            # Validar y crear value object
            tracking_id = TrackingId(tracking_id_str) if not isinstance(tracking_id_str, TrackingId) else tracking_id_str
            
            logger.info(f"Getting tracking for {tracking_id_str}")
            
            # Obtener checkpoints del repositorio
            checkpoints = self._tracking_repo.get_by_tracking_id(tracking_id)
            
            if not checkpoints:
                logger.warning(f"No checkpoints found for {tracking_id_str}")
                return None
            
            # Obtener unidad si hay repositorio de unidades
            unit = None
            if self._unit_repo:
                try:
                    unit = self._unit_repo.get_by_tracking_id(tracking_id)
                except Exception as e:
                    logger.warning(f"Could not get unit info: {str(e)}")
            
            # Determinar estado actual (del checkpoint más reciente)
            current_status = checkpoints[0].status if checkpoints else 'unknown'
            
            return self._map_to_response(tracking_id_str, current_status, checkpoints, unit)
            
        except ValueError as e:
            logger.error(f"Validation error getting tracking: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error getting tracking: {str(e)}", exc_info=True)
            raise Exception("Internal error getting tracking")
    
    def _map_to_response(
        self, 
        tracking_id_str: str, 
        current_status: str,
        checkpoints: list,
        unit
    ) -> TrackingResponse:
        """Map domain data to response DTO"""
        
        # Mapear checkpoints
        checkpoint_responses = [self._map_checkpoint_to_response(cp) for cp in checkpoints]
        
        # Determinar última actualización
        last_update = checkpoints[0].timestamp if checkpoints else datetime.utcnow()
        
        return TrackingResponse(
            tracking_id=tracking_id_str,
            unit=self._map_unit_to_response(unit) if unit else self._create_minimal_unit_response(tracking_id_str, current_status),
            checkpoints=checkpoint_responses,
            total_checkpoints=len(checkpoint_responses),
            last_update=last_update,
            estimated_delivery=None,
            is_delayed=False
        )
    
    def _map_checkpoint_to_response(self, checkpoint: Checkpoint) -> CheckpointResponse:
        """Map checkpoint entity to response DTO"""
        
        # Helper para extraer valores
        def get_value(obj, default=None):
            return getattr(obj, 'value', obj) if obj is not None else default
        
        return CheckpointResponse(
            id=get_value(checkpoint.id, checkpoint.id),
            tracking_id=get_value(checkpoint.tracking_id, checkpoint.tracking_id),
            status=get_value(checkpoint.status, checkpoint.status),
            timestamp=checkpoint.timestamp,
            location=checkpoint.location,
            coordinates=getattr(checkpoint, 'coordinates', {}),
            description=checkpoint.description,
            operator=getattr(checkpoint, 'operator', None),
            meta_data=getattr(checkpoint, 'meta_data', {}),
            created_at=checkpoint.created_at,
            updated_at=checkpoint.updated_at
        )
    
    def _map_unit_to_response(self, unit) -> UnitResponse:
        """Map unit entity to response DTO"""
        
        if not unit:
            return None
        
        # Helper para extraer valores
        def get_value(obj, default=None):
            return getattr(obj, 'value', obj) if obj is not None else default
        
        return UnitResponse(
            id=get_value(getattr(unit, 'id', 'unknown')),
            tracking_id=get_value(getattr(unit, 'tracking_id', None), 'unknown'),
            origin=unit.origin if unit.origin else 'unknown',
            destination=unit.destination if unit.destination else 'unknown',
            status=get_value(getattr(unit, 'current_status', None), getattr(unit, 'status', 'unknown')),
            created_at=getattr(unit, 'created_at', datetime.utcnow()),
            updated_at=getattr(unit, 'updated_at', datetime.utcnow()),
            guide_id=str(unit.guide_id) if unit.guide_id else None,
            weight_kg=getattr(unit, 'weight_kg', None),
            dimensions=getattr(unit, 'dimensions', None),
            customer_info=getattr(unit, 'customer_info', None),
            meta_data=getattr(unit, 'meta_data', None)
        )
    
    def _create_minimal_unit_response(self, tracking_id: str, status: str) -> UnitResponse:
        """Crear respuesta mínima de unidad cuando no hay datos de unidad"""
        
        # Extraer valor si es value object
        status_str = getattr(status, 'value', str(status))
        
        return UnitResponse(
            id="unknown",
            tracking_id=tracking_id,
            origin="unknown",
            destination="unknown",
            status=status_str,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )