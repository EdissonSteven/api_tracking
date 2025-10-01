"""
Request Validators siguiendo el patrón Chain of Responsibility.

Este módulo implementa validadores extensibles que siguen el principio
Open/Closed: abierto para extensión, cerrado para modificación.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, time
import re
import logging

from ..interfaces.api.v1.schemas.checkpoint_schemas import CreateCheckpointRequest
from ..domain.domain_events import CheckpointValidationFailedEvent, DomainEventDispatcher
from ..domain.domain_exceptions import (
    BusinessHoursViolationError,
    DomainValidationError,
    GeofenceViolationError,
    BusinessRuleViolationError
)
from ..application.result import Result, Success, Failure

logger = logging.getLogger(__name__)


class RequestValidator(ABC):
    """
    Validador base siguiendo el patrón Chain of Responsibility.
    
    Cada validador implementa una regla específica y puede ser compuesto
    con otros validadores siguiendo el principio Open/Closed.
    """
    
    def __init__(self, next_validator: Optional['RequestValidator'] = None):
        self._next_validator = next_validator
    
    def validate(  # ⬅️ SIN async
        self, 
        request: CreateCheckpointRequest, 
        user: Dict[str, Any]
    ) -> Result[bool, DomainValidationError]:
        """
        Valida el request y ejecuta el siguiente validador en la cadena.
        
        Args:
            request: Request a validar
            user: Datos del usuario que hace el request
            
        Returns:
            Result con True si es válido o error si no lo es
        """
        # Ejecutar validación específica
        result = self._execute_validation(request, user)  # ⬅️ SIN await
        
        # Si la validación falla, retornar el error
        if result.is_failure():
            return result
        
        # Si hay siguiente validador, ejecutarlo
        if self._next_validator:
            return self._next_validator.validate(request, user)  # ⬅️ SIN await
        
        # Si no hay más validadores y llegamos aquí, todo es válido
        return Success(True)
    
    @abstractmethod
    def _execute_validation(  # ⬅️ SIN async
        self, 
        request: CreateCheckpointRequest, 
        user: Dict[str, Any]
    ) -> Result[bool, DomainValidationError]:
        """
        Implementa la lógica específica de validación.
        
        Args:
            request: Request a validar
            user: Datos del usuario
            
        Returns:
            Result con True si es válido o error específico
        """
        pass
    
    @abstractmethod
    def get_validator_name(self) -> str:
        """Nombre del validador para logging y debugging."""
        pass


class TrackingIdFormatValidator(RequestValidator):
    """Valida el formato del tracking ID."""
    
    TRACKING_ID_PATTERN = r'^[A-Za-z0-9\-_]{3,50}$'
    
    def _execute_validation(  # ⬅️ SIN async
        self, 
        request: CreateCheckpointRequest, 
        user: Dict[str, Any]
    ) -> Result[bool, DomainValidationError]:
        
        if not request.tracking_id or not request.tracking_id.strip():
            return Failure(DomainValidationError(
                message="El tracking ID es requerido",
                field="tracking_id",
                value=request.tracking_id
            ))
        
        if not re.match(self.TRACKING_ID_PATTERN, request.tracking_id):
            return Failure(DomainValidationError(
                message="El formato del tracking ID es inválido. Debe tener entre 3-50 caracteres alfanuméricos, guiones o guiones bajos",
                field="tracking_id",
                value=request.tracking_id,
                details={"pattern": self.TRACKING_ID_PATTERN}
            ))
        
        logger.debug(f"Validación de formato de tracking ID exitosa: {request.tracking_id}")
        return Success(True)
    
    def get_validator_name(self) -> str:
        return "TrackingIdFormatValidator"


class BusinessHoursValidator(RequestValidator):
    """Valida que la operación se realice dentro del horario comercial."""
    
    def __init__(
        self, 
        start_hour: int = 6,  # 6 AM
        end_hour: int = 22,   # 10 PM
        next_validator: Optional[RequestValidator] = None
    ):
        super().__init__(next_validator)
        self.start_hour = start_hour
        self.end_hour = end_hour
    
    def _execute_validation(  # ⬅️ SIN async
        self, 
        request: CreateCheckpointRequest, 
        user: Dict[str, Any]
    ) -> Result[bool, DomainValidationError]:
        
        current_time = datetime.utcnow().time()
        start_time = time(self.start_hour, 0)
        end_time = time(self.end_hour, 0)
        
        # Verificar si estamos dentro del horario comercial
        if not (start_time <= current_time <= end_time):
            # Excepción para usuarios admin o superuser
            if user.get("is_superuser") or "admin" in user.get("roles", []):
                logger.info(f"Validación de horario comercial omitida para usuario admin: {user.get('username')}")
                return Success(True)
            
            return Failure(BusinessHoursViolationError(
                current_time=current_time.isoformat(),
                business_hours=f"{self.start_hour}:00-{self.end_hour}:00"
            ))
        
        logger.debug(f"Validación de horario comercial exitosa: {current_time}")
        return Success(True)
    
    def get_validator_name(self) -> str:
        return "BusinessHoursValidator"


class GeofenceValidator(RequestValidator):
    """Valida que la ubicación esté dentro de las zonas permitidas."""
    
    def __init__(
        self, 
        allowed_zones: List[Dict[str, Any]] = None,
        next_validator: Optional[RequestValidator] = None
    ):
        super().__init__(next_validator)
        # Zonas permitidas por defecto (ejemplo para Colombia)
        self.allowed_zones = allowed_zones or [
            {
                "name": "Bogotá",
                "bounds": {
                    "north": 4.8356,
                    "south": 4.4699,
                    "east": -74.0154,
                    "west": -74.2478
                }
            },
            {
                "name": "Medellín",
                "bounds": {
                    "north": 6.3659,
                    "south": 6.1701,
                    "east": -75.5042,
                    "west": -75.6764
                }
            }
        ]
    
    def _execute_validation(  # ⬅️ SIN async
        self, 
        request: CreateCheckpointRequest, 
        user: Dict[str, Any]
    ) -> Result[bool, DomainValidationError]:
        
        # Si no hay coordenadas, no validar geofence
        if not hasattr(request, 'coordinates') or not request.coordinates:
            return Success(True)
        
        coordinates = request.coordinates
        if not isinstance(coordinates, dict):
            return Success(True)
        
        lat = coordinates.get('latitude') or coordinates.get('lat')
        lng = coordinates.get('longitude') or coordinates.get('lng')
        
        if not lat or not lng:
            return Success(True)
        
        # Verificar si está dentro de alguna zona permitida
        for zone in self.allowed_zones:
            bounds = zone["bounds"]
            if (bounds["south"] <= lat <= bounds["north"] and 
                bounds["west"] <= lng <= bounds["east"]):
                logger.debug(f"Validación de geofence exitosa: ubicación en {zone['name']}")
                return Success(True)
        
        # Si llegamos aquí, está fuera de todas las zonas permitidas
        return Failure(GeofenceViolationError(
            coordinates={"latitude": lat, "longitude": lng},
            allowed_zones=[zone["name"] for zone in self.allowed_zones]
        ))
    
    def get_validator_name(self) -> str:
        return "GeofenceValidator"


class StatusTransitionValidator(RequestValidator):
    """Valida que la transición de estado sea válida."""
    
    VALID_TRANSITIONS = {
        "created": {"picked_up", "cancelled"},
        "picked_up": {"in_transit", "exception", "returned"},
        "in_transit": {"at_facility", "exception", "returned"},
        "at_facility": {"out_for_delivery", "in_transit", "exception", "returned"},
        "out_for_delivery": {"delivered", "exception", "returned", "at_facility"},
        "delivered": {"returned"},
        "exception": {"in_transit", "at_facility", "out_for_delivery", "returned", "cancelled"},
        "returned": {"delivered", "cancelled", "picked_up"},
        "cancelled": set()
    }
    
    def __init__(
        self, 
        checkpoint_repository=None,
        next_validator: Optional[RequestValidator] = None
    ):
        super().__init__(next_validator)
        self._checkpoint_repo = checkpoint_repository
    
    def _execute_validation(  # ⬅️ SIN async
        self, 
        request: CreateCheckpointRequest, 
        user: Dict[str, Any]
    ) -> Result[bool, DomainValidationError]:
        
        if not self._checkpoint_repo:
            # Si no hay repositorio, asumir válido (para testing)
            return Success(True)
        
        try:
            # Obtener último checkpoint - SIN await
            last_checkpoint = self._checkpoint_repo.get_latest_by_tracking_id(
                request.tracking_id
            )
            
            if not last_checkpoint:
                # Primer checkpoint debe ser "created"
                if request.status.value != "created":
                    return Failure(DomainValidationError(
                        message="El primer checkpoint debe tener estado 'created'",
                        field="status",
                        value=request.status.value,
                        details={"tracking_id": request.tracking_id}
                    ))
                return Success(True)
            
            # Verificar transición válida
            current_status = getattr(last_checkpoint.status, 'value', str(last_checkpoint.status))
            new_status = request.status.value
            
            valid_next_statuses = self.VALID_TRANSITIONS.get(current_status, set())
            
            if new_status not in valid_next_statuses:
                return Failure(BusinessRuleViolationError(
                    message=f"Transición de estado inválida de '{current_status}' a '{new_status}'",
                    rule_name="valid_status_transition",
                    context={
                        "tracking_id": request.tracking_id,
                        "current_status": current_status,
                        "attempted_status": new_status,
                        "valid_next_statuses": list(valid_next_statuses)
                    }
                ))
            
            logger.debug(f"Validación de transición de estado exitosa: {current_status} -> {new_status}")
            return Success(True)
            
        except Exception as e:
            logger.error(f"Error validando transición de estado: {str(e)}")
            # En caso de error, permitir la operación (fail-open)
            return Success(True)
    
    def get_validator_name(self) -> str:
        return "StatusTransitionValidator"


class RoleBasedValidator(RequestValidator):
    """Valida permisos específicos basados en el rol del usuario."""
    
    def __init__(
        self, 
        role_restrictions: Dict[str, List[str]] = None,
        next_validator: Optional[RequestValidator] = None
    ):
        super().__init__(next_validator)
        # Restricciones por rol
        self.role_restrictions = role_restrictions or {
            "viewer": [],  # Solo lectura, no puede crear checkpoints
            "operator": ["created", "picked_up", "in_transit", "delivered"],
            "supervisor": ["created", "picked_up", "in_transit", "delivered", "exception", "returned"],
            "admin": None  # Sin restricciones
        }
    
    def _execute_validation(  # ⬅️ SIN async
        self, 
        request: CreateCheckpointRequest, 
        user: Dict[str, Any]
    ) -> Result[bool, DomainValidationError]:
        
        # Superuser no tiene restricciones
        if user.get("is_superuser"):
            return Success(True)
        
        user_roles = user.get("roles", [])
        if not user_roles:
            return Failure(DomainValidationError(
                message="El usuario no tiene roles asignados",
                details={"user_id": user.get("user_id")}
            ))
        
        # Obtener el rol con más permisos
        allowed_statuses = set()
        for role in user_roles:
            if role in self.role_restrictions:
                role_statuses = self.role_restrictions[role]
                if role_statuses is None:  # Admin role
                    return Success(True)
                allowed_statuses.update(role_statuses)
        
        # Verificar si el status está permitido
        if request.status.value not in allowed_statuses:
            return Failure(DomainValidationError(
                message=f"El rol del usuario no permite crear checkpoints con estado '{request.status.value}'",
                field="status",
                value=request.status.value,
                details={
                    "user_roles": user_roles,
                    "allowed_statuses": list(allowed_statuses)
                }
            ))
        
        logger.debug(f"Validación basada en rol exitosa para usuario {user.get('username')}")
        return Success(True)
    
    def get_validator_name(self) -> str:
        return "RoleBasedValidator"


class ValidatorChainBuilder:
    """Builder para construir cadenas de validadores."""
    
    def __init__(self):
        self._validators = []
    
    def add_validator(self, validator: RequestValidator) -> 'ValidatorChainBuilder':
        """Agregar validador a la cadena."""
        self._validators.append(validator)
        return self
    
    def add_tracking_id_format_validation(self) -> 'ValidatorChainBuilder':
        """Agregar validación de formato de tracking ID."""
        self._validators.append(TrackingIdFormatValidator())
        return self
    
    def add_business_hours_validation(
        self, 
        start_hour: int = 6, 
        end_hour: int = 22
    ) -> 'ValidatorChainBuilder':
        """Agregar validación de horario comercial."""
        self._validators.append(BusinessHoursValidator(start_hour, end_hour))
        return self
    
    def add_geofence_validation(
        self, 
        allowed_zones: List[Dict[str, Any]] = None
    ) -> 'ValidatorChainBuilder':
        """Agregar validación de geofence."""
        self._validators.append(GeofenceValidator(allowed_zones))
        return self
    
    def add_status_transition_validation(
        self, 
        checkpoint_repository=None
    ) -> 'ValidatorChainBuilder':
        """Agregar validación de transición de estado."""
        self._validators.append(StatusTransitionValidator(checkpoint_repository))
        return self
    
    def add_role_based_validation(
        self, 
        role_restrictions: Dict[str, List[str]] = None
    ) -> 'ValidatorChainBuilder':
        """Agregar validación basada en roles."""
        self._validators.append(RoleBasedValidator(role_restrictions))
        return self
    
    def build(self) -> Optional[RequestValidator]:
        """Construir la cadena de validadores."""
        if not self._validators:
            return None
        
        # Conectar validadores en cadena
        for i in range(len(self._validators) - 1):
            self._validators[i]._next_validator = self._validators[i + 1]
        
        return self._validators[0]


class ValidationService:
    """Servicio para ejecutar validaciones con reporte detallado."""
    
    def __init__(
        self, 
        validator_chain: RequestValidator = None,
        event_dispatcher: DomainEventDispatcher = None
    ):
        self._validator_chain = validator_chain
        self._event_dispatcher = event_dispatcher
    
    def validate_request(  # ⬅️ SIN async
        self, 
        request: CreateCheckpointRequest, 
        user: Dict[str, Any]
    ) -> Result[bool, List[DomainValidationError]]:
        """
        Ejecutar todas las validaciones y recopilar errores.
        
        Args:
            request: Request a validar
            user: Datos del usuario
            
        Returns:
            Result con True si es válido o lista de errores
        """
        if not self._validator_chain:
            return Success(True)
        
        start_time = datetime.utcnow()
        
        try:
            result = self._validator_chain.validate(request, user)  # ⬅️ SIN await
            
            validation_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            if result.is_success():
                logger.info(
                    f"Validación exitosa para {request.tracking_id} en {validation_time:.2f}ms"
                )
                return Success(True)
            else:
                error = result.error
                logger.warning(
                    f"Validación fallida para {request.tracking_id}: {error.message}"
                )
                
                # Disparar evento de validación fallida - SIN await
                if self._event_dispatcher:
                    event = CheckpointValidationFailedEvent(
                        tracking_id=request.tracking_id,
                        status=request.status.value,
                        error_reason=error.message,
                        attempted_by=user.get("user_id", "unknown")
                    )
                    self._event_dispatcher.dispatch(event)  # ⬅️ SIN await
                
                return Failure([error])
                
        except Exception as e:
            logger.error(f"Error inesperado durante la validación: {str(e)}")
            return Failure([DomainValidationError(
                message=f"Error del sistema de validación: {str(e)}",
                details={"validation_time_ms": (datetime.utcnow() - start_time).total_seconds() * 1000}
            )])


# Factory para crear configuraciones predeterminadas
def create_default_validator_chain(checkpoint_repository=None) -> RequestValidator:
    """Crear cadena de validadores con configuración predeterminada."""
    return (ValidatorChainBuilder()
            .add_tracking_id_format_validation()
            .add_business_hours_validation(start_hour=6, end_hour=22)
            .add_geofence_validation()
            .add_status_transition_validation(checkpoint_repository)
            .add_role_based_validation()
            .build())


def create_lenient_validator_chain() -> RequestValidator:
    """Crear cadena de validadores más permisiva (para testing)."""
    return (ValidatorChainBuilder()
            .add_tracking_id_format_validation()
            .build())


def create_strict_validator_chain(checkpoint_repository=None) -> RequestValidator:
    """Crear cadena de validadores estricta (para producción)."""
    return (ValidatorChainBuilder()
            .add_tracking_id_format_validation()
            .add_business_hours_validation(start_hour=6, end_hour=20)  # Horario más restrictivo
            .add_geofence_validation()
            .add_status_transition_validation(checkpoint_repository)
            .add_role_based_validation()
            .build())