import re
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ..entities.checkpoint import Checkpoint
from ..entities.unit import Unit

logger = logging.getLogger(__name__)


class CheckpointValidationService:
    """Servicio de validación para checkpoints."""
    
    # Estados válidos para checkpoints
    VALID_STATUSES = {
        "created", "picked_up", "in_transit", "at_facility", "out_for_delivery",
        "delivered", "exception", "returned", "cancelled"
    }
    
    # Transiciones válidas entre estados
    VALID_TRANSITIONS = {
        "created": {"picked_up", "cancelled"},
        "picked_up": {"in_transit", "exception", "returned"},
        "in_transit": {"at_facility", "exception", "returned"},
        "at_facility": {"out_for_delivery", "in_transit", "exception", "returned"},
        "out_for_delivery": {"delivered", "exception", "returned", "at_facility"},
        "delivered": {"returned"},  # Solo devoluciones desde entregado
        "exception": {"in_transit", "at_facility", "out_for_delivery", "returned", "cancelled"},
        "returned": {"delivered", "cancelled", "picked_up"},  # Reintento
        "cancelled": set()  # Estado final
    }
    
    def __init__(self, checkpoint_repo=None, unit_repo=None):
        """
        Constructor simplificado siguiendo principios SOLID.
        
        Args:
            checkpoint_repo: Repositorio de checkpoints (inyección de dependencia)
            unit_repo: Repositorio de unidades (inyección de dependencia)
        """
        self._checkpoint_repo = checkpoint_repo
        self._unit_repo = unit_repo
        
        logger.debug(f"CheckpointValidationService inicializado")
    
    async def ensure_idempotency(self, tracking_id, status) -> bool:
        """
        Verifica si ya existe un checkpoint con el mismo tracking_id y status.
        
        Args:
            tracking_id: ID de seguimiento (puede ser objeto TrackingId o string)
            status: Estado del checkpoint (puede ser objeto UnitStatus o string)
            
        Returns:
            True si el checkpoint ya existe (idempotente), False si es nuevo
        """
        try:
            # Convertir a strings si son objetos
            tracking_id_str = getattr(tracking_id, 'value', str(tracking_id))
            status_str = getattr(status, 'value', str(status))
            
            logger.debug(f"Verificando idempotencia para {tracking_id_str} con status {status_str}")
            
            # Si no tenemos repositorio, asumir que no existe (para testing)
            if not self._checkpoint_repo:
                logger.warning("No hay repositorio de checkpoints, asumiendo no idempotente")
                return False
            
            # Buscar checkpoint existente - CORREGIDO: solo pasar tracking_id
            try:
                checkpoints = await self._checkpoint_repo.get_by_tracking_id(tracking_id_str)
                
                # Filtrar por status manualmente
                existing_checkpoint = None
                for cp in checkpoints:
                    cp_status = getattr(cp.status, 'value', str(cp.status))
                    if cp_status == status_str:
                        existing_checkpoint = cp
                        break
                
                if existing_checkpoint:
                    logger.info(f"Checkpoint idempotente encontrado para {tracking_id_str}")
                    return True
                
                logger.debug(f"Checkpoint nuevo para {tracking_id_str} con status {status_str}")
                return False
                
            except Exception as repo_error:
                logger.warning(f"Error en repositorio durante idempotencia: {str(repo_error)}")
                return False
            
        except Exception as e:
            logger.error(f"Error verificando idempotencia: {str(e)}")
            return False
    
    async def validate_checkpoint_creation(self, tracking_id, status, timestamp=None):
        """
        Valida que un checkpoint puede ser creado según las reglas de negocio.
        
        Args:
            tracking_id: ID de seguimiento
            status: Estado del checkpoint
            timestamp: Timestamp del checkpoint (opcional)
            
        Raises:
            ValueError: Si la validación falla, con todos los errores acumulados
        """
        try:
            # Convertir a strings si son objetos
            tracking_id_str = getattr(tracking_id, 'value', str(tracking_id))
            status_str = getattr(status, 'value', str(status))
            
            logger.debug(f"Validando creación de checkpoint para {tracking_id_str}")
            
            # Lista para acumular errores
            validation_errors = []
            
            # 1. Verificar que la unidad existe
            unit_errors = await self._validate_unit_exists(tracking_id_str)
            validation_errors.extend(unit_errors)
            
            # 2. Validar transición de estado
            transition_errors = await self._validate_status_transition(tracking_id_str, status_str)
            validation_errors.extend(transition_errors)
            
            # 3. Validar timestamp
            timestamp_errors = self._validate_timestamp(timestamp)
            validation_errors.extend(timestamp_errors)
            
            # 4. Validar que no hay estados finales siendo modificados
            final_status_errors = await self._validate_not_final_status(tracking_id_str, status_str)
            validation_errors.extend(final_status_errors)
            
            # 5. Si hay errores, lanzar excepción con todos los errores
            if validation_errors:
                error_message = "; ".join(validation_errors)
                logger.warning(f"Errores de validación: {error_message}")
                raise ValueError(error_message)
            
            logger.debug(f"Validación exitosa para {tracking_id_str}")
            
        except ValueError:
            # Re-lanzar errores de validación que ya tienen el formato correcto
            raise
        except Exception as e:
            logger.error(f"Error inesperado en validación: {str(e)}")
            raise ValueError(f"Error validando checkpoint: {str(e)}")
    
    async def _validate_unit_exists(self, tracking_id_str: str) -> List[str]:
        """
        Valida que la unidad existe.
        """
        errors = []
        
        try:
            if not self._unit_repo:
                logger.warning("No hay repositorio de unidades, asumiendo que existe")
                return errors
            
            try:
                if hasattr(self._unit_repo, 'exists_by_tracking_id'):
                    unit_exists = await self._unit_repo.exists_by_tracking_id(tracking_id_str)
                else:
                    # Fallback: intentar buscar la unidad
                    unit = await self._unit_repo.get_by_tracking_id(tracking_id_str)
                    unit_exists = unit is not None
                
                if not unit_exists:
                    errors.append(f"La unidad con ID {tracking_id_str} no existe")
                    logger.warning(f"Unidad no encontrada: {tracking_id_str}")
                else:
                    logger.debug(f"Unidad {tracking_id_str} existe")
                
            except Exception as repo_error:
                logger.warning(f"No se pudo verificar existencia de unidad: {str(repo_error)}")
                # En desarrollo, no agregar error; en producción podrías querer agregarlo
                
        except Exception as e:
            logger.error(f"Error verificando existencia de unidad: {str(e)}")
            errors.append(f"Error verificando existencia de unidad: {str(e)}")
        
        return errors
    
    async def _validate_status_transition(self, tracking_id_str: str, new_status: str) -> List[str]:
        """
        Valida que la transición de estado es permitida.
        """
        errors = []
        
        try:
            if not self._checkpoint_repo:
                logger.warning("No hay repositorio de checkpoints, asumiendo transición válida")
                return errors
            
            # Obtener el último checkpoint - CORREGIDO: usar método existente
            try:
                if hasattr(self._checkpoint_repo, 'get_latest_by_tracking_id'):
                    last_checkpoint = await self._checkpoint_repo.get_latest_by_tracking_id(tracking_id_str)
                else:
                    # Fallback: buscar todos y obtener el último
                    checkpoints = await self._checkpoint_repo.get_by_tracking_id(tracking_id_str)
                    last_checkpoint = max(checkpoints, key=lambda cp: cp.timestamp) if checkpoints else None
                    
            except Exception as e:
                logger.warning(f"No se pudo obtener último checkpoint: {str(e)}")
                last_checkpoint = None
            
            if not last_checkpoint:
                # Si no hay checkpoints previos, solo permitir CREATED
                if new_status != "created":
                    errors.append(f"El primer checkpoint debe ser 'created', recibido: {new_status}")
                    logger.warning(f"Primera transición debe ser 'created', recibido: {new_status}")
                else:
                    logger.debug(f"Primera transición válida: {new_status}")
                return errors
            
            # Obtener el estado actual
            current_status = getattr(last_checkpoint.status, 'value', str(last_checkpoint.status))
            
            # Verificar si la transición es permitida
            if not self.validate_status_transition(current_status, new_status):
                errors.append(f"Transición de estado inválida: de '{current_status}' a '{new_status}'")
                logger.warning(f"Transición inválida: {current_status} -> {new_status}")
            else:
                logger.debug(f"Transición válida: {current_status} -> {new_status}")
            
        except Exception as e:
            logger.error(f"Error validando transición: {str(e)}")
            errors.append(f"Error validando transición: {str(e)}")
        
        return errors
    
    def _validate_timestamp(self, timestamp: Optional[datetime]) -> List[str]:
        """
        Valida que el timestamp es válido.
        """
        errors = []
        
        try:
            if timestamp is None:
                return errors  # Timestamp es opcional
            
            now = datetime.utcnow()
            
            # No permitir timestamps muy antiguos (más de 7 días)
            if timestamp < now - timedelta(days=7):
                errors.append("El timestamp no puede ser mayor a 7 días en el pasado")
                logger.warning(f"Timestamp muy antiguo: {timestamp}")
            
            # No permitir timestamps muy futuros (más de 1 hora)
            if timestamp > now + timedelta(hours=1):
                errors.append("El timestamp no puede ser mayor a 1 hora en el futuro")
                logger.warning(f"Timestamp muy futuro: {timestamp}")
            
            if not errors:
                logger.debug(f"Timestamp válido: {timestamp}")
            
        except Exception as e:
            logger.error(f"Error validando timestamp: {str(e)}")
            errors.append(f"Error validando timestamp: {str(e)}")
        
        return errors
    
    async def _validate_not_final_status(self, tracking_id_str: str, new_status: str) -> List[str]:
        """
        Valida que no se esté modificando un estado final.
        """
        errors = []
        
        try:
            if not self._checkpoint_repo:
                logger.warning("No hay repositorio de checkpoints, asumiendo estado no final")
                return errors
            
            # Obtener el último checkpoint
            try:
                if hasattr(self._checkpoint_repo, 'get_latest_by_tracking_id'):
                    last_checkpoint = await self._checkpoint_repo.get_latest_by_tracking_id(tracking_id_str)
                else:
                    checkpoints = await self._checkpoint_repo.get_by_tracking_id(tracking_id_str)
                    last_checkpoint = max(checkpoints, key=lambda cp: cp.timestamp) if checkpoints else None
                    
            except Exception as e:
                logger.warning(f"No se pudo verificar estado final: {str(e)}")
                return errors
            
            if not last_checkpoint:
                return errors  # No hay checkpoint previo
            
            current_status = getattr(last_checkpoint.status, 'value', str(last_checkpoint.status))
            
            # Estados finales que no pueden ser modificados (excepto devoluciones)
            final_statuses = ["delivered", "cancelled"]
            
            if current_status in final_statuses and new_status != current_status:
                # Permitir devoluciones desde delivered
                if current_status == "delivered" and new_status == "returned":
                    logger.debug(f"Devolución permitida: {current_status} -> {new_status}")
                    return errors
                
                errors.append(f"No se puede cambiar el estado de una unidad '{current_status}'")
                logger.warning(f"Intento de modificar estado final: {current_status} -> {new_status}")
            else:
                logger.debug(f"Estado no final, transición permitida")
            
        except Exception as e:
            logger.error(f"Error validando estado final: {str(e)}")
            errors.append(f"Error validando estado final: {str(e)}")
        
        return errors

    # Métodos estáticos para validación de objetos (mantener compatibilidad)
    @classmethod
    def validate_checkpoint(cls, checkpoint: Checkpoint) -> List[str]:
        """
        Valida un checkpoint y retorna lista de errores.
        """
        errors = []
        
        # Validar tracking_id
        if not checkpoint.tracking_id:
            errors.append("El tracking_id es requerido")
        elif not cls._is_valid_tracking_id(str(checkpoint.tracking_id)):
            errors.append("El tracking_id tiene un formato inválido")
        
        # Validar status
        checkpoint_status = getattr(checkpoint.status, 'value', str(checkpoint.status))
        if not checkpoint_status:
            errors.append("El status es requerido")
        elif checkpoint_status not in cls.VALID_STATUSES:
            errors.append(f"Status inválido. Debe ser uno de: {', '.join(cls.VALID_STATUSES)}")
        
        # Validar timestamp
        if checkpoint.timestamp and checkpoint.timestamp > datetime.utcnow():
            errors.append("El timestamp no puede ser futuro")
        
        # Validar coordenadas si están presentes
        if hasattr(checkpoint, 'coordinates') and checkpoint.coordinates:
            coord_errors = cls._validate_coordinates(checkpoint.coordinates)
            errors.extend(coord_errors)
        
        # Validar longitud de campos
        if checkpoint.location and len(checkpoint.location) > 255:
            errors.append("La ubicación no puede exceder 255 caracteres")
        
        if hasattr(checkpoint, 'description') and checkpoint.description and len(checkpoint.description) > 500:
            errors.append("La descripción no puede exceder 500 caracteres")
        
        return errors
    
    @classmethod
    def validate_status_transition(cls, from_status: str, to_status: str) -> bool:
        """
        Valida si una transición de estado es válida.
        """
        if from_status not in cls.VALID_TRANSITIONS:
            return False
        
        return to_status in cls.VALID_TRANSITIONS[from_status]
    
    @classmethod
    def get_valid_next_statuses(cls, current_status: str) -> List[str]:
        """
        Obtiene los estados válidos siguientes para un estado actual.
        """
        return list(cls.VALID_TRANSITIONS.get(current_status, set()))
    
    @classmethod
    def _is_valid_tracking_id(cls, tracking_id: str) -> bool:
        """Valida el formato del tracking ID."""
        pattern = r'^[A-Za-z0-9\-_]{3,50}$'
        return bool(re.match(pattern, tracking_id))
    
    @classmethod
    def _validate_coordinates(cls, coordinates: Dict[str, Any]) -> List[str]:
        """Valida coordenadas GPS."""
        errors = []
        
        if not isinstance(coordinates, dict):
            errors.append("Las coordenadas deben ser un objeto")
            return errors
        
        # Validar latitud
        latitude = coordinates.get("latitude") or coordinates.get("lat")
        if latitude is None:
            errors.append("La latitud es requerida en las coordenadas")
        elif not isinstance(latitude, (int, float)):
            errors.append("La latitud debe ser un número")
        elif not (-90 <= latitude <= 90):
            errors.append("La latitud debe estar entre -90 y 90")
        
        # Validar longitud
        longitude = coordinates.get("longitude") or coordinates.get("lng")
        if longitude is None:
            errors.append("La longitud es requerida en las coordenadas")
        elif not isinstance(longitude, (int, float)):
            errors.append("La longitud debe ser un número")
        elif not (-180 <= longitude <= 180):
            errors.append("La longitud debe estar entre -180 y 180")
        
        return errors

class UnitValidationService:
    """Servicio de validación para unidades."""
    
    # Estados válidos para unidades
    VALID_STATUSES = {
        "created", "processing", "in_transit", "delivered", "cancelled", "exception"
    }
    
    @classmethod
    def validate_unit(cls, unit: Unit) -> List[str]:
        """
        Valida una unidad y retorna lista de errores.
        MÉTODO ESTÁTICO - retorna lista de errores, no lanza excepciones.
        """
        errors = []
        
        # Validar tracking_id
        unit_tracking_id = getattr(unit.tracking_id, 'value', str(unit.tracking_id))
        if not unit_tracking_id:
            errors.append("El tracking_id es requerido")
        elif not cls._is_valid_tracking_id(unit_tracking_id):
            errors.append("El tracking_id tiene un formato inválido")
        
        # Validar origen
        if not unit.origin:
            errors.append("El origen es requerido")
        elif len(unit.origin) > 100:
            errors.append("El origen no puede exceder 100 caracteres")
        
        # Validar destino
        if not unit.destination:
            errors.append("El destino es requerido")
        elif len(unit.destination) > 100:
            errors.append("El destino no puede exceder 100 caracteres")
        
        # Validar que origen y destino sean diferentes
        if unit.origin and unit.destination and unit.origin.lower() == unit.destination.lower():
            errors.append("El origen y destino no pueden ser iguales")
        
        # Validar status
        unit_status = getattr(unit.status, 'value', str(unit.status))
        if unit_status and unit_status not in cls.VALID_STATUSES:
            errors.append(f"Status inválido. Debe ser uno de: {', '.join(cls.VALID_STATUSES)}")
        
        # Validar peso
        if hasattr(unit, 'weight_kg') and unit.weight_kg is not None:
            if unit.weight_kg < 0:
                errors.append("El peso no puede ser negativo")
            elif unit.weight_kg > 1000:  # Límite de 1000kg
                errors.append("El peso no puede exceder 1000 kg")
        
        # Validar dimensiones
        if hasattr(unit, 'dimensions') and unit.dimensions:
            dim_errors = cls._validate_dimensions(unit.dimensions)
            errors.extend(dim_errors)
        
        # Validar información del cliente
        if hasattr(unit, 'customer_info') and unit.customer_info:
            customer_errors = cls._validate_customer_info(unit.customer_info)
            errors.extend(customer_errors)
        
        return errors
    
    @classmethod
    def _is_valid_tracking_id(cls, tracking_id: str) -> bool:
        """Valida el formato del tracking ID."""
        pattern = r'^[A-Za-z0-9\-_]{3,50}$'
        return bool(re.match(pattern, tracking_id))
    
    @classmethod
    def _validate_dimensions(cls, dimensions: Dict[str, Any]) -> List[str]:
        """Valida las dimensiones del paquete."""
        errors = []
        
        if not isinstance(dimensions, dict):
            errors.append("Las dimensiones deben ser un objeto")
            return errors
        
        required_fields = ["length", "width", "height"]
        for field in required_fields:
            value = dimensions.get(field)
            if value is None:
                errors.append(f"El campo {field} es requerido en las dimensiones")
            elif not isinstance(value, (int, float)):
                errors.append(f"El campo {field} debe ser un número")
            elif value <= 0:
                errors.append(f"El campo {field} debe ser mayor a 0")
            elif value > 500:  # Límite de 500cm
                errors.append(f"El campo {field} no puede exceder 500 cm")
        
        return errors
    
    @classmethod
    def _validate_customer_info(cls, customer_info: Dict[str, Any]) -> List[str]:
        """Valida la información del cliente."""
        errors = []
        
        if not isinstance(customer_info, dict):
            errors.append("La información del cliente debe ser un objeto")
            return errors
        
        # Validar nombre si está presente
        name = customer_info.get("name")
        if name and (not isinstance(name, str) or len(name.strip()) < 2):
            errors.append("El nombre del cliente debe tener al menos 2 caracteres")
        
        # Validar teléfono si está presente
        phone = customer_info.get("phone")
        if phone and not cls._is_valid_phone(phone):
            errors.append("El teléfono del cliente tiene un formato inválido")
        
        # Validar email si está presente
        email = customer_info.get("email")
        if email and not cls._is_valid_email(email):
            errors.append("El email del cliente tiene un formato inválido")
        
        return errors
    
    @classmethod
    def _is_valid_phone(cls, phone: str) -> bool:
        """Valida formato de teléfono."""
        pattern = r'^\+?[\d\s\-\(\)]{7,15}$'
        return bool(re.match(pattern, phone))
    
    @classmethod
    def _is_valid_email(cls, email: str) -> bool:
        """Valida formato de email."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))


class TrackingBusinessRules:
    """Reglas de negocio para el tracking."""
    
    @classmethod
    def can_add_checkpoint(cls, unit: Unit, new_checkpoint: Checkpoint) -> tuple[bool, str]:
        """
        Verifica si se puede agregar un checkpoint a una unidad.
        
        Args:
            unit: Unidad existente
            new_checkpoint: Nuevo checkpoint a agregar
            
        Returns:
            Tupla con (permitido, razón)
        """
        # Verificar que el tracking_id coincida
        unit_tracking_id = getattr(unit.tracking_id, 'value', str(unit.tracking_id))
        checkpoint_tracking_id = getattr(new_checkpoint.tracking_id, 'value', str(new_checkpoint.tracking_id))
        
        if unit_tracking_id != checkpoint_tracking_id:
            return False, "El tracking_id no coincide con la unidad"
        
        # No permitir checkpoints en unidades canceladas o entregadas
        unit_status = getattr(unit.status, 'value', str(unit.status))
        if unit_status in ["cancelled", "delivered"]:
            return False, f"No se pueden agregar checkpoints a unidades con estado '{unit_status}'"
        
        # No permitir checkpoints muy antiguos (más de 30 días)
        if new_checkpoint.timestamp:
            days_old = (datetime.utcnow() - new_checkpoint.timestamp).days
            if days_old > 30:
                return False, "No se pueden agregar checkpoints con más de 30 días de antigüedad"
        
        return True, "Checkpoint permitido"
    
    @classmethod
    def calculate_estimated_delivery(cls, unit: Unit, checkpoints: List[Checkpoint]) -> Optional[datetime]:
        """Calcula la fecha estimada de entrega basada en el historial."""
        if not checkpoints:
            # Sin historial, estimar basado en origen/destino
            return datetime.utcnow() + timedelta(days=3)  # Default 3 días
        
        # Obtener último checkpoint
        latest_checkpoint = max(checkpoints, key=lambda cp: cp.timestamp)
        
        # Estimar basado en el estado actual
        status_to_days = {
            "created": 3,
            "picked_up": 2,
            "in_transit": 1,
            "at_facility": 1,
            "out_for_delivery": 0.5,
            "delivered": 0
        }
        
        latest_status = getattr(latest_checkpoint.status, 'value', str(latest_checkpoint.status))
        days_remaining = status_to_days.get(latest_status, 2)
        return latest_checkpoint.timestamp + timedelta(days=days_remaining)
    
    @classmethod
    def is_delivery_delayed(cls, unit: Unit, checkpoints: List[Checkpoint]) -> bool:
        """Determina si una entrega está retrasada."""
        estimated_delivery = cls.calculate_estimated_delivery(unit, checkpoints)
        if not estimated_delivery:
            return False
        
        unit_status = getattr(unit.status, 'value', str(unit.status))
        return datetime.utcnow() > estimated_delivery and unit_status != "delivered"