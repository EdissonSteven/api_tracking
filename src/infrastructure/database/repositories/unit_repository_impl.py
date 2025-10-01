from ....domain.value_objects.tracking_id import TrackingId
from sqlmodel import Session, select, desc, func  # Session síncrona
from typing import List, Optional
import logging
from datetime import datetime

from ....domain.value_objects.unit_status import UnitStatus
from ....domain.entities.unit import Unit
from ....domain.repositories.unit_repository import UnitRepository
from ..models.unit_model import UnitModel
from ...cache.redis_client import get_redis_client
from ...cache.cache_config import CacheKey

logger = logging.getLogger(__name__)

class UnitRepositoryImpl(UnitRepository):
    """Implementación del repositorio de Unit - SÍNCRONO."""
    
    def __init__(self, session: Session):  # ⬅️ Session, no AsyncSession
        self._session = session
    
    def create(self, unit: Unit) -> UnitModel:  
        """Crea una nueva unidad en la base de datos."""
        if isinstance(unit, UnitModel):
            db_unit = unit
        else:
            db_unit = UnitModel(**unit.__dict__)
        self._session.add(db_unit)
        self._session.flush()  
        self._session.commit()  
        self._session.refresh(db_unit)  
        return db_unit

    def get_by_id(self, unit_id: str) -> Optional[UnitModel]:  
        q = select(UnitModel).where(UnitModel.id == unit_id)
        result = self._session.execute(q)  
        return result.scalar_one_or_none()
    
    def get_by_tracking_id(self, tracking_id: str) -> Optional[UnitModel]:  
        tracking_id_str = tracking_id.value if hasattr(tracking_id, 'value') else str(tracking_id)
        
        q = select(UnitModel).where(UnitModel.tracking_id == tracking_id_str)
        result = self._session.execute(q)
        return result.scalar_one_or_none()
    
    def update(self, unit: Unit) -> Optional[UnitModel]:  
        """Actualiza todos los campos de la unidad."""
        tracking_id = getattr(unit, "tracking_id", None)
        if not tracking_id:
            return None
        q = select(UnitModel).where(UnitModel.tracking_id == tracking_id)
        result = self._session.execute(q)  
        db_unit = result.scalar_one_or_none()
        if not db_unit:
            return None
        for k, v in unit.__dict__.items():
            if hasattr(db_unit, k) and v is not None:
                setattr(db_unit, k, v)
        db_unit.updated_at = datetime.utcnow()
        self._session.add(db_unit)
        self._session.flush()  
        self._session.commit()  
        self._session.refresh(db_unit)  
        return db_unit
    
    def delete(self, unit_id: str) -> bool:  
        q = select(UnitModel).where(UnitModel.id == unit_id)
        result = self._session.execute(q)  
        db_unit = result.scalar_one_or_none()
        if not db_unit:
            return False
        self._session.delete(db_unit)  
        self._session.flush()  
        self._session.commit()  
        return True
    
    def find_by_status(self, status: UnitStatus, limit: int = 100, offset: int = 0) -> List[Unit]:  
        redis = get_redis_client()
        cache_key = f"units:status:{status.value}:limit:{limit}:offset:{offset}"
        
        # Leer desde cache
        if redis.is_available:
            cached = redis.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT: units by status {status.value}")
                return [Unit.from_dict(item) for item in cached]

        # Consultar desde base de datos
        status_str = status.value if hasattr(status, 'value') else str(status)
        
        q = select(UnitModel).where(
            UnitModel.status == status_str
        ).order_by(UnitModel.updated_at.desc()).offset(offset).limit(limit)
        
        result = self._session.execute(q)  
        db_models = result.scalars().all()

        # Convertir a entidades de dominio
        units = [self._to_domain_entity(model) for model in db_models]

        # Guardar en cache
        if redis.is_available and units:
            cacheable = [unit.to_dict() for unit in units]
            redis.set_with_type(CacheKey.UNITS_LIST, cache_key, cacheable)

        return units

    def count_by_status(self, status: UnitStatus) -> int:  
        """Count total units with specific status"""
        try:
            status_str = status.value if hasattr(status, 'value') else str(status)
            
            statement = select(func.count(UnitModel.id)).where(
                UnitModel.status == status_str
            )
            
            result = self._session.execute(statement)  
            count = result.scalar_one_or_none()
            return int(count) if count else 0
            
        except Exception as e:
            logger.error(f"Error counting units by status: {str(e)}")
            return 0
    
    def save(self, unit: Unit) -> UnitModel:  
        """Compatibilidad con interfaz."""
        existing = self.get_by_tracking_id(getattr(unit, "tracking_id", None))  
        if existing:
            return self.update(unit)  
        return self.create(unit)  

    def update_status(self, tracking_id, new_status: str) -> Optional[UnitModel]:
        tracking_id_str = tracking_id.value if hasattr(tracking_id, 'value') else str(tracking_id)
        status_str = new_status.value if hasattr(new_status, 'value') else str(new_status)
        
        q = select(UnitModel).where(UnitModel.tracking_id == tracking_id_str)
        result = self._session.execute(q)
        db_unit = result.scalar_one_or_none()
        if not db_unit:
            return None
        db_unit.status = status_str
        db_unit.updated_at = datetime.utcnow()
        self._session.add(db_unit)
        self._session.flush()
        self._session.commit()
        self._session.refresh(db_unit)
        return db_unit

    def find_by_tracking_id(self, tracking_id: str) -> Optional[UnitModel]:  
        tracking_id_str = tracking_id.value if hasattr(tracking_id, 'value') else str(tracking_id)
    
        q = select(UnitModel).where(UnitModel.tracking_id == tracking_id_str)
        result = self._session.execute(q)
        return result.scalar_one_or_none()

    def exists_by_tracking_id(self, tracking_id: str) -> bool:  
        tracking_id_str = tracking_id.value if hasattr(tracking_id, 'value') else str(tracking_id)
        
        q = select(UnitModel).where(UnitModel.tracking_id == tracking_id_str)
        result = self._session.execute(q)
        return result.scalar_one_or_none() is not None
    
    def _to_domain_entity(self, model: UnitModel) -> Unit:
        return Unit(
            id=model.id,
            tracking_id=TrackingId(model.tracking_id),
            guide_id=model.guide_id,
            current_status=UnitStatus(model.status),
            weight_kg=model.weight_kg,
            dimensions=model.dimensions,
            origin=model.origin,
            destination=model.destination,
            created_at=model.created_at,
            updated_at=model.updated_at
        )