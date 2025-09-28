from sqlmodel import Session, select, desc
from typing import List, Optional
import logging
from datetime import datetime

from domain.entities.checkpoint import Checkpoint
from domain.repositories.checkpoint_repository import CheckpointRepository
from ...database.models.checkpoint_model import CheckpointModel

logger = logging.getLogger(__name__)

class CheckpointRepositoryImpl(CheckpointRepository):
    """
    Implementación del repositorio de Checkpoint siguiendo principios de Clean Architecture.
    
    Esta clase es parte de la capa de infraestructura y implementa la interfaz
    definida en la capa de dominio (Dependency Inversion Principle).
    """
    
    def __init__(self, session: Session):
        """
        Constructor que recibe la sesión de base de datos.
        
        Args:
            session: Sesión de SQLModel/SQLAlchemy
        """
        self.session = session
        logger.debug("CheckpointRepositoryImpl inicializado")
    
    async def create(self, checkpoint: Checkpoint) -> Checkpoint:
        """
        Crea un nuevo checkpoint en la base de datos.
        
        Args:
            checkpoint: Entidad checkpoint a crear
            
        Returns:
            Checkpoint creado con ID asignado
            
        Raises:
            Exception: Si hay error en la creación
        """
        try:
            logger.debug(f"Creando checkpoint: {checkpoint.id}")
            
            # Convertir entidad de dominio a modelo de base de datos
            db_checkpoint = self._entity_to_model(checkpoint)
            
            self.session.add(db_checkpoint)
            self.session.commit()
            self.session.refresh(db_checkpoint)
            
            logger.debug(f"Checkpoint creado exitosamente: {db_checkpoint.id}")
            
            # Convertir modelo de DB de vuelta a entidad de dominio
            return self._model_to_entity(db_checkpoint)
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creando checkpoint: {str(e)}")
            raise
    
    async def save(self, checkpoint: Checkpoint) -> Checkpoint:
        """
        Guarda un checkpoint en la base de datos.
        Este método funciona tanto para crear como para actualizar.
        
        Args:
            checkpoint: Checkpoint a guardar
            
        Returns:
            Checkpoint guardado
            
        Raises:
            Exception: Si hay error al guardar
        """
        try:
            logger.debug(f"Guardando checkpoint: {checkpoint.id}")
            
            # Verificar si el checkpoint ya existe
            existing = await self.get_by_id(checkpoint.id)
            
            if existing:
                # Actualizar checkpoint existente
                return await self.update(checkpoint)
            else:
                # Crear nuevo checkpoint
                return await self.create(checkpoint)
                
        except Exception as e:
            logger.error(f"Error guardando checkpoint: {str(e)}")
            raise
    
    async def get_by_id(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """
        Obtiene un checkpoint por su ID.
        
        Args:
            checkpoint_id: ID del checkpoint
            
        Returns:
            Checkpoint encontrado o None
        """
        try:
            logger.debug(f"Buscando checkpoint por ID: {checkpoint_id}")
            
            statement = select(CheckpointModel).where(
                CheckpointModel.id == checkpoint_id
            )
            result = self.session.exec(statement).first()
            
            if result:
                logger.debug(f"Checkpoint encontrado: {checkpoint_id}")
                return self._model_to_entity(result)
                
            logger.debug(f"Checkpoint no encontrado: {checkpoint_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo checkpoint por ID {checkpoint_id}: {str(e)}")
            raise
    
    async def get_by_tracking_id(self, tracking_id: str) -> List[Checkpoint]:
        """
        Obtiene todos los checkpoints de un tracking ID.
        
        Args:
            tracking_id: ID de seguimiento
            
        Returns:
            Lista de checkpoints ordenados por timestamp DESC
        """
        try:
            # Extraer valor si es value object
            tracking_id_str = getattr(tracking_id, 'value', str(tracking_id))
            
            logger.debug(f"Buscando checkpoints para tracking_id: {tracking_id_str}")
            
            statement = select(CheckpointModel).where(
                CheckpointModel.tracking_id == tracking_id_str
            ).order_by(desc(CheckpointModel.timestamp))
            
            results = self.session.exec(statement).all()
            
            checkpoints = [self._model_to_entity(result) for result in results]
            
            logger.debug(f"Encontrados {len(checkpoints)} checkpoints para {tracking_id_str}")
            return checkpoints
            
        except Exception as e:
            logger.error(f"Error obteniendo checkpoints para tracking {tracking_id}: {str(e)}")
            raise
    
    async def get_latest_by_tracking_id(self, tracking_id: str) -> Optional[Checkpoint]:
        """
        Obtiene el checkpoint más reciente de un tracking ID.
        
        Args:
            tracking_id: ID de seguimiento
            
        Returns:
            Checkpoint más reciente o None
        """
        try:
            # Extraer valor si es value object
            tracking_id_str = getattr(tracking_id, 'value', str(tracking_id))
            
            logger.debug(f"Buscando último checkpoint para: {tracking_id_str}")
            
            statement = select(CheckpointModel).where(
                CheckpointModel.tracking_id == tracking_id_str
            ).order_by(desc(CheckpointModel.timestamp)).limit(1)
            
            result = self.session.exec(statement).first()
            
            if result:
                logger.debug(f"Último checkpoint encontrado para {tracking_id_str}")
                return self._model_to_entity(result)
                
            logger.debug(f"No hay checkpoints para {tracking_id_str}")
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo último checkpoint para tracking {tracking_id}: {str(e)}")
            raise
    
    async def find_latest_by_tracking_id(self, tracking_id) -> Optional[Checkpoint]:
        """
        Alias para get_latest_by_tracking_id para compatibilidad.
        """
        return await self.get_latest_by_tracking_id(tracking_id)
    
    async def update(self, checkpoint: Checkpoint) -> Checkpoint:
        """
        Actualiza un checkpoint existente.
        
        Args:
            checkpoint: Entidad checkpoint actualizada
            
        Returns:
            Checkpoint actualizado
        """
        try:
            logger.debug(f"Actualizando checkpoint: {checkpoint.id}")
            
            statement = select(CheckpointModel).where(
                CheckpointModel.id == checkpoint.id
            )
            db_checkpoint = self.session.exec(statement).first()
            
            if not db_checkpoint:
                raise ValueError(f"Checkpoint con ID {checkpoint.id} no encontrado")
            
            # Actualizar campos
            self._update_model_from_entity(db_checkpoint, checkpoint)
            
            self.session.commit()
            self.session.refresh(db_checkpoint)
            
            logger.debug(f"Checkpoint actualizado exitosamente: {checkpoint.id}")
            
            return self._model_to_entity(db_checkpoint)
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error actualizando checkpoint {checkpoint.id}: {str(e)}")
            raise
    
    async def delete(self, checkpoint_id: str) -> bool:
        """
        Elimina un checkpoint por su ID.
        
        Args:
            checkpoint_id: ID del checkpoint a eliminar
            
        Returns:
            True si se eliminó exitosamente
        """
        try:
            logger.debug(f"Eliminando checkpoint: {checkpoint_id}")
            
            statement = select(CheckpointModel).where(
                CheckpointModel.id == checkpoint_id
            )
            db_checkpoint = self.session.exec(statement).first()
            
            if not db_checkpoint:
                logger.warning(f"Checkpoint {checkpoint_id} no encontrado para eliminar")
                return False
            
            self.session.delete(db_checkpoint)
            self.session.commit()
            
            logger.debug(f"Checkpoint eliminado exitosamente: {checkpoint_id}")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error eliminando checkpoint {checkpoint_id}: {str(e)}")
            raise
    
    async def get_by_status(
        self, 
        status: str, 
        limit: Optional[int] = None
    ) -> List[Checkpoint]:
        """
        Obtiene checkpoints por estado.
        
        Args:
            status: Estado a filtrar
            limit: Límite opcional de resultados
            
        Returns:
            Lista de checkpoints con el estado especificado
        """
        try:
            logger.debug(f"Buscando checkpoints por status: {status}")
            
            statement = select(CheckpointModel).where(
                CheckpointModel.status == status
            ).order_by(desc(CheckpointModel.timestamp))
            
            if limit:
                statement = statement.limit(limit)
            
            results = self.session.exec(statement).all()
            
            checkpoints = [self._model_to_entity(result) for result in results]
            
            logger.debug(f"Encontrados {len(checkpoints)} checkpoints con status {status}")
            return checkpoints
            
        except Exception as e:
            logger.error(f"Error obteniendo checkpoints por estado {status}: {str(e)}")
            raise
    
    async def count_by_tracking_id(self, tracking_id: str) -> int:
        """
        Cuenta los checkpoints de un tracking ID.
        
        Args:
            tracking_id: ID de seguimiento
            
        Returns:
            Número de checkpoints
        """
        try:
            # Extraer valor si es value object
            tracking_id_str = getattr(tracking_id, 'value', str(tracking_id))
            
            logger.debug(f"Contando checkpoints para: {tracking_id_str}")
            
            statement = select(CheckpointModel).where(
                CheckpointModel.tracking_id == tracking_id_str
            )
            results = self.session.exec(statement).all()
            
            count = len(results)
            logger.debug(f"Encontrados {count} checkpoints para {tracking_id_str}")
            
            return count
            
        except Exception as e:
            logger.error(f"Error contando checkpoints para tracking {tracking_id}: {str(e)}")
            raise
    
    async def exists(self, checkpoint_id: str) -> bool:
        """
        Verifica si existe un checkpoint con el ID dado.
        
        Args:
            checkpoint_id: ID del checkpoint
            
        Returns:
            True si existe
        """
        try:
            logger.debug(f"Verificando existencia de checkpoint: {checkpoint_id}")
            
            statement = select(CheckpointModel).where(
                CheckpointModel.id == checkpoint_id
            )
            result = self.session.exec(statement).first()
            
            exists = result is not None
            logger.debug(f"Checkpoint {checkpoint_id} existe: {exists}")
            
            return exists
            
        except Exception as e:
            logger.error(f"Error verificando existencia de checkpoint {checkpoint_id}: {str(e)}")
            raise
    
    def _entity_to_model(self, checkpoint: Checkpoint) -> CheckpointModel:
        """
        Convierte una entidad de dominio a modelo de base de datos.
        
        Args:
            checkpoint: Entidad de dominio
            
        Returns:
            Modelo de base de datos
        """
        return CheckpointModel(
            id=checkpoint.id,
            tracking_id=checkpoint.tracking_id,
            status=checkpoint.status,
            location=checkpoint.location,
            description=checkpoint.description,
            coordinates=checkpoint.coordinates,
            timestamp=checkpoint.timestamp or datetime.utcnow(),
            created_at=checkpoint.created_at or datetime.utcnow(),
            updated_at=checkpoint.updated_at or datetime.utcnow()
        )
    
    def _model_to_entity(self, db_model: CheckpointModel) -> Checkpoint:
        """
        Convierte un modelo de base de datos a entidad de dominio.
        
        Args:
            db_model: Modelo de base de datos
            
        Returns:
            Entidad de dominio
        """
        return Checkpoint(
            id=db_model.id,
            tracking_id=db_model.tracking_id,
            status=db_model.status,
            location=db_model.location,
            description=db_model.description,
            coordinates=db_model.coordinates,
            meta_data=getattr(db_model, 'meta_data', None) or {},
            timestamp=db_model.timestamp,
            created_at=db_model.created_at,
            updated_at=db_model.updated_at,
            operator=getattr(db_model, 'operator', None)
        )
    
    def _update_model_from_entity(self, db_model: CheckpointModel, checkpoint: Checkpoint):
        """
        Actualiza un modelo de base de datos con datos de una entidad.
        
        Args:
            db_model: Modelo de base de datos a actualizar
            checkpoint: Entidad con los nuevos datos
        """
        db_model.tracking_id = checkpoint.tracking_id
        db_model.status = checkpoint.status
        db_model.location = checkpoint.location
        db_model.description = checkpoint.description
        db_model.coordinates = checkpoint.coordinates
        db_model.timestamp = checkpoint.timestamp
        db_model.updated_at = datetime.utcnow()
        
        # Actualizar campos adicionales si existen
        if hasattr(db_model, 'meta_data') and hasattr(checkpoint, 'meta_data'):
            db_model.meta_data = checkpoint.meta_data
            
        if hasattr(db_model, 'operator') and hasattr(checkpoint, 'operator'):
            db_model.operator = checkpoint.operator