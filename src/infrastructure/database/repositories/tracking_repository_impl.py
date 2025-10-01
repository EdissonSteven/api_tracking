from sqlmodel import Session, select, desc
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from ....domain.entities.unit import Unit
from ....domain.entities.checkpoint import Checkpoint
from ....infrastructure.database.models.unit_model import UnitModel
from ....infrastructure.database.models.checkpoint_model import CheckpointModel
from ...cache.redis_client import get_redis_client
from ...cache.cache_config import CacheKey

logger = logging.getLogger(__name__)

class TrackingRepositoryImpl:
    """Implementación del repositorio de Tracking que combina Units y Checkpoints."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_tracking_info(self, tracking_id: str) -> Dict[str, Any]:
        try:
            unit_statement = select(UnitModel).where(UnitModel.tracking_id == tracking_id)
            unit_result = self.session.exec(unit_statement).first()
            
            if not unit_result:
                return {"error": "Tracking ID no encontrado", "tracking_id": tracking_id}
            
            # Obtener checkpoints
            checkpoint_statement = select(CheckpointModel).where(
                CheckpointModel.tracking_id == tracking_id
            ).order_by(desc(CheckpointModel.timestamp))
            
            checkpoint_results = self.session.exec(checkpoint_statement).all()
            
            # Convertir a diccionario
            tracking_info = {
                "tracking_id": tracking_id,
                "unit_info": {
                    "id": unit_result.id,
                    "origin": getattr(unit_result, 'origin', None),
                    "destination": getattr(unit_result, 'destination', None),
                    "status": unit_result.status,
                    "weight_kg": getattr(unit_result, 'weight_kg', None),
                    "dimensions": getattr(unit_result, 'dimensions', None),
                    "customer_info": getattr(unit_result, 'customer_info', None),
                    "meta_data": getattr(unit_result, 'extra_data', None),
                    "created_at": unit_result.created_at,
                    "updated_at": unit_result.updated_at
                },
                "checkpoints": [
                    {
                        "id": cp.id,
                        "status": cp.status,
                        "location": cp.location,
                        "description": cp.description,
                        "coordinates": getattr(cp, 'coordinates', None),
                        "meta_data": getattr(cp, 'meta_data', None),
                        "timestamp": cp.timestamp,
                        "created_at": cp.created_at,
                        "updated_at": getattr(cp, 'updated_at', None)
                    }
                    for cp in checkpoint_results
                ],
                "total_checkpoints": len(checkpoint_results),
                "last_update": checkpoint_results[0].timestamp if checkpoint_results else unit_result.updated_at
            }
            return tracking_info
            
        except Exception as e:
            logger.error(f"Error obteniendo información de tracking {tracking_id}: {e}")
            raise
    
    def get_tracking_status(self, tracking_id: str) -> Optional[str]:
        """
        Obtiene el estado actual de un tracking.
        
        Args:
            tracking_id: ID de seguimiento
            
        Returns:
            Estado actual o None si no existe
        """
        print(f"🎯 get_tracking_status: {tracking_id}")
        try:
            # Buscar el checkpoint más reciente
            checkpoint_statement = select(CheckpointModel).where(
                CheckpointModel.tracking_id == tracking_id
            ).order_by(desc(CheckpointModel.timestamp)).limit(1)
            
            checkpoint_result = self.session.exec(checkpoint_statement).first()
            
            if checkpoint_result:
                return checkpoint_result.status
            
            # Si no hay checkpoints, obtener estado de la unidad
            unit_statement = select(UnitModel).where(UnitModel.tracking_id == tracking_id)
            unit_result = self.session.exec(unit_statement).first()
            
            if unit_result:
                return unit_result.status
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de tracking {tracking_id}: {e}")
            raise
    
    def get_tracking_timeline(self, tracking_id: str) -> List[Dict[str, Any]]:
        print(f"🎯 get_tracking_timeline: {tracking_id}")
        """
        Obtiene la línea de tiempo completa de un tracking.
        
        Args:
            tracking_id: ID de seguimiento
            
        Returns:
            Lista ordenada de eventos del tracking
        """
        try:
            # Obtener todos los checkpoints
            checkpoint_statement = select(CheckpointModel).where(
                CheckpointModel.tracking_id == tracking_id
            ).order_by(CheckpointModel.timestamp)
            
            checkpoint_results = self.session.exec(checkpoint_statement).all()
            
            timeline = []
            
            for cp in checkpoint_results:
                timeline.append({
                    "type": "checkpoint",
                    "id": cp.id,
                    "status": cp.status,
                    "location": cp.location,
                    "description": cp.description,
                    "coordinates": cp.coordinates,
                    "timestamp": cp.timestamp,
                    "meta_data": cp.meta_data,
                })
            
            return timeline
            
        except Exception as e:
            logger.error(f"Error obteniendo timeline de tracking {tracking_id}: {e}")
            raise
    
    def search_trackings(
        self, 
        status: Optional[str] = None,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca trackings con filtros opcionales.
        
        Args:
            status: Filtrar por estado
            origin: Filtrar por origen
            destination: Filtrar por destino
            limit: Límite de resultados
            
        Returns:
            Lista de información de trackings
        """
        try:
            statement = select(UnitModel)
            
            # Aplicar filtros
            if status:
                statement = statement.where(UnitModel.status == status)
            if origin:
                statement = statement.where(UnitModel.origin.ilike(f"%{origin}%"))
            if destination:
                statement = statement.where(UnitModel.destination.ilike(f"%{destination}%"))
            
            statement = statement.order_by(desc(UnitModel.created_at))
            
            if limit:
                statement = statement.limit(limit)
            
            results = self.session.exec(statement).all()
            
            tracking_list = []
            for unit in results:
                # Obtener último checkpoint para cada unidad
                last_checkpoint_statement = select(CheckpointModel).where(
                    CheckpointModel.tracking_id == unit.tracking_id
                ).order_by(desc(CheckpointModel.timestamp)).limit(1)
                
                last_checkpoint = self.session.exec(last_checkpoint_statement).first()
                
                tracking_list.append({
                    "tracking_id": unit.tracking_id,
                    "origin": unit.origin,
                    "destination": unit.destination,
                    "current_status": last_checkpoint.status if last_checkpoint else unit.status,
                    "last_location": last_checkpoint.location if last_checkpoint else None,
                    "last_update": last_checkpoint.timestamp if last_checkpoint else unit.updated_at,
                    "created_at": unit.created_at
                })
            
            return tracking_list
            
        except Exception as e:
            logger.error(f"Error buscando trackings: {e}")
            raise

    def get_by_tracking_id(self, tracking_id: str) -> List[Checkpoint]:
        redis = get_redis_client()
        cache_key = f"tracking_by_id:{tracking_id}"
        if redis.is_available:
            cached = redis.get(cache_key)
            if cached:
                print(f"🎯 Cache HIT: {tracking_id}")
                # Reconstruir objetos Checkpoint con from_dict
                checkpoints = [Checkpoint.from_dict(item) for item in cached]
                return checkpoints

        try:
            print(f"🎯 get_by_tracking_id: {tracking_id}")
            tracking_id_str = getattr(tracking_id, 'value', str(tracking_id))
            
            logger.debug(f"Buscando checkpoints para tracking_id: {tracking_id_str}")
            
            statement = select(CheckpointModel).where(
                CheckpointModel.tracking_id == tracking_id_str
            ).order_by(desc(CheckpointModel.timestamp))
            
            results = self.session.exec(statement).all()
            
            checkpoints = [self._model_to_entity(result) for result in results]
            
            logger.debug(f"Encontrados {len(checkpoints)} checkpoints para {tracking_id_str}")
            # Guardar lista de dicts en cache
            redis.set_with_type(CacheKey.TRACKING, cache_key, [c.to_dict() for c  in checkpoints])
            print(f"💾 Cache MISS: {tracking_id} - guardado en caché")
            return checkpoints
            
        except Exception as e:
            logger.error(f"Error obteniendo checkpoints para tracking {tracking_id}: {str(e)}")
            raise

    
    def tracking_exists(self, tracking_id: str) -> bool:
        """
        Verifica si existe un tracking.
        
        Args:
            tracking_id: ID de seguimiento
            
        Returns:
            True si existe
        """
        try:
            statement = select(UnitModel).where(UnitModel.tracking_id == tracking_id)
            result = self.session.exec(statement).first()
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Error verificando existencia de tracking {tracking_id}: {e}")
            raise
    
    def get_tracking_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas generales de tracking.
        
        Returns:
            Diccionario con estadísticas
        """
        try:
            # Contar unidades por estado
            unit_statement = select(UnitModel)
            all_units = self.session.exec(unit_statement).all()
            
            status_counts = {}
            for unit in all_units:
                status_counts[unit.status] = status_counts.get(unit.status, 0) + 1
            
            # Contar checkpoints totales
            checkpoint_statement = select(CheckpointModel)
            all_checkpoints = self.session.exec(checkpoint_statement).all()
            
            return {
                "total_trackings": len(all_units),
                "total_checkpoints": len(all_checkpoints),
                "status_distribution": status_counts,
                "generated_at": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            raise
    
    def _model_to_entity(self, model: CheckpointModel) -> Checkpoint:
        """
        Convierte un modelo de base de datos a entidad de dominio.
        
        Args:
            model: Modelo de base de datos (CheckpointModel)
            
        Returns:
            Entidad de dominio Checkpoint
        """
        return Checkpoint(
            id=model.id,
            tracking_id=model.tracking_id,
            status=model.status,
            location=model.location,
            description=model.description,
            coordinates=getattr(model, 'coordinates', None),
            meta_data=getattr(model, 'meta_data', {}),
            timestamp=model.timestamp,
            created_at=model.created_at,
            updated_at=getattr(model, 'updated_at', None),
            operator=getattr(model, 'operator', None)
        )