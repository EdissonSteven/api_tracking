from sqlmodel import Session, select, desc, func
from typing import List, Optional
import logging
from datetime import datetime

from ....domain.entities.unit import Unit
from ....domain.repositories.unit_repository import UnitRepository
from ..models.unit_model import UnitModel
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class UnitRepositoryImpl(UnitRepository):
    """Implementación del repositorio de Unit."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def create(self, unit: Unit) -> UnitModel:
        """Crea una nueva unidad en la base de datos."""
        # acepta tanto Unit domain como UnitModel
        if isinstance(unit, UnitModel):
            db_unit = unit
        else:
            db_unit = UnitModel(**unit.__dict__)
        self._session.add(db_unit)
        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(db_unit)
        return db_unit

    async def get_by_id(self, unit_id: str) -> Optional[UnitModel]:
        q = select(UnitModel).where(UnitModel.id == unit_id)
        result = await self._session.execute(q)
        return result.scalar_one_or_none()
    
    async def get_by_tracking_id(self, tracking_id: str) -> Optional[UnitModel]:
        q = select(UnitModel).where(UnitModel.tracking_id == tracking_id)
        result = await self._session.execute(q)
        return result.scalar_one_or_none()
    
    async def update(self, unit: Unit) -> Optional[UnitModel]:
        """Actualiza todos los campos de la unidad (recibe domain Unit o UnitModel)."""
        tracking_id = getattr(unit, "tracking_id", None)
        if not tracking_id:
            return None
        q = select(UnitModel).where(UnitModel.tracking_id == tracking_id)
        result = await self._session.execute(q)
        db_unit = result.scalar_one_or_none()
        if not db_unit:
            return None
        for k, v in (unit.__dict__.items() if not isinstance(unit, UnitModel) else unit.__dict__.items()):
            if hasattr(db_unit, k) and v is not None:
                setattr(db_unit, k, v)
        db_unit.updated_at = datetime.utcnow()
        self._session.add(db_unit)
        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(db_unit)
        return db_unit
    
    async def delete(self, unit_id: str) -> bool:
        q = select(UnitModel).where(UnitModel.id == unit_id)
        result = await self._session.execute(q)
        db_unit = result.scalar_one_or_none()
        if not db_unit:
            return False
        await self._session.delete(db_unit)
        await self._session.flush()
        await self._session.commit()
        return True
    
    async def get_by_status(
        self, 
        status: str, 
        limit: Optional[int] = None
    ) -> List[UnitModel]:
        q = select(UnitModel).where(UnitModel.status == status).order_by(UnitModel.updated_at.desc())
        if limit:
            q = q.limit(limit)
        result = await self._session.execute(q)
        return result.scalars().all()
    
    async def get_by_origin(self, origin: str) -> List[UnitModel]:
        q = select(UnitModel).where(UnitModel.origin == origin)
        result = await self._session.execute(q)
        return result.scalars().all()
    
    async def get_by_destination(self, destination: str) -> List[UnitModel]:
        q = select(UnitModel).where(UnitModel.destination == destination)
        result = await self._session.execute(q)
        return result.scalars().all()
    
    async def get_all(
        self, 
        limit: Optional[int] = None, 
        offset: Optional[int] = None
    ) -> List[UnitModel]:
        q = select(UnitModel).order_by(UnitModel.created_at.desc())
        if offset:
            q = q.offset(offset)
        if limit:
            q = q.limit(limit)
        result = await self._session.execute(q)
        return result.scalars().all()
    
    async def count_total(self) -> int:
        q = select(func.count()).select_from(UnitModel)
        result = await self._session.execute(q)
        return int(result.scalar_one() or 0)
    
    async def exists(self, unit_id: str) -> bool:
        q = select(UnitModel).where(UnitModel.id == unit_id)
        result = await self._session.execute(q)
        return result.scalar_one_or_none() is not None
    
    async def tracking_id_exists(self, tracking_id: str) -> bool:
        q = select(UnitModel).where(UnitModel.tracking_id == tracking_id)
        result = await self._session.execute(q)
        return result.scalar_one_or_none() is not None

    # Métodos requeridos por la interfaz (nombres abstractos)
    async def save(self, unit: Unit) -> UnitModel:
        """Compatibilidad con interfaz: persiste/actualiza según exista tracking_id."""
        existing = await self.get_by_tracking_id(getattr(unit, "tracking_id", None))
        if existing:
            return await self.update(unit)
        return await self.create(unit)

    async def update_status(self, tracking_id: str, new_status: str) -> Optional[UnitModel]:
        q = select(UnitModel).where(UnitModel.tracking_id == tracking_id)
        result = await self._session.execute(q)
        db_unit = result.scalar_one_or_none()
        if not db_unit:
            return None
        db_unit.status = new_status
        db_unit.updated_at = datetime.utcnow()
        self._session.add(db_unit)
        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(db_unit)
        return db_unit

    async def find_by_tracking_id(self, tracking_id: str) -> Optional[UnitModel]:
        return await self.get_by_tracking_id(tracking_id)

    async def find_by_status(self, status: str, limit: Optional[int] = None) -> List[UnitModel]:
        return await self.get_by_status(status, limit=limit)

    async def exists_by_tracking_id(self, tracking_id: str) -> bool:
        return await self.tracking_id_exists(tracking_id)
    
    def _to_domain_entity(self, db_model: UnitModel) -> Unit:
        """Convierte UnitModel a entidad de dominio si es posible, si no devuelve el model DB."""
        if db_model is None:
            return None
        try:
            return Unit(**db_model.dict())
        except Exception:
            return db_model