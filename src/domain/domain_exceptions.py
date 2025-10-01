"""
Excepciones personalizadas para el dominio de tracking.

Estas excepciones siguen los principios de Clean Architecture,
separando errores de dominio de errores técnicos de infraestructura.
"""

from typing import Optional, Dict, Any


class TrackingDomainException(Exception):
    """Excepción base para errores de dominio en tracking."""
    
    def __init__(
        self, 
        message: str, 
        error_code: str = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "DOMAIN_ERROR"
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir excepción a diccionario para serialización."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "exception_type": self.__class__.__name__
        }


class DomainValidationError(TrackingDomainException):
    """Error de validación de reglas de dominio."""
    
    def __init__(
        self, 
        message: str, 
        field: str = None,
        value: Any = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details or {}
        )
        self.field = field
        self.value = value
        
        if field:
            self.details["field"] = field
        if value is not None:
            self.details["invalid_value"] = str(value)


class BusinessRuleViolationError(TrackingDomainException):
    """Error por violación de reglas de negocio."""
    
    def __init__(
        self, 
        message: str, 
        rule_name: str = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="BUSINESS_RULE_VIOLATION",
            details=context or {}
        )
        self.rule_name = rule_name
        
        if rule_name:
            self.details["violated_rule"] = rule_name


class CheckpointValidationError(DomainValidationError):
    """Error específico de validación de checkpoints."""
    
    def __init__(
        self, 
        message: str, 
        tracking_id: str = None,
        status: str = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.error_code = "CHECKPOINT_VALIDATION_ERROR"
        
        if tracking_id:
            self.details["tracking_id"] = tracking_id
        if status:
            self.details["status"] = status


class InvalidStateTransitionError(BusinessRuleViolationError):
    """Error por transición de estado inválida."""
    
    def __init__(
        self, 
        current_status: str, 
        target_status: str,
        tracking_id: str = None
    ):
        message = f"Invalid transition from '{current_status}' to '{target_status}'"
        super().__init__(
            message=message,
            rule_name="valid_status_transition"
        )
        self.error_code = "INVALID_STATE_TRANSITION"
        self.current_status = current_status
        self.target_status = target_status
        
        self.details.update({
            "current_status": current_status,
            "target_status": target_status
        })
        
        if tracking_id:
            self.details["tracking_id"] = tracking_id


class UnitNotFoundError(TrackingDomainException):
    """Error cuando no se encuentra una unidad."""
    
    def __init__(self, tracking_id: str):
        super().__init__(
            message=f"Unit with tracking ID '{tracking_id}' not found",
            error_code="UNIT_NOT_FOUND"
        )
        self.tracking_id = tracking_id
        self.details["tracking_id"] = tracking_id


class IdempotencyViolationError(BusinessRuleViolationError):
    """Error por violación de idempotencia."""
    
    def __init__(
        self, 
        tracking_id: str, 
        status: str,
        existing_checkpoint_id: str = None
    ):
        message = f"Checkpoint for tracking '{tracking_id}' with status '{status}' already exists"
        super().__init__(
            message=message,
            rule_name="checkpoint_idempotency"
        )
        self.error_code = "IDEMPOTENCY_VIOLATION"
        
        self.details.update({
            "tracking_id": tracking_id,
            "status": status
        })
        
        if existing_checkpoint_id:
            self.details["existing_checkpoint_id"] = existing_checkpoint_id


class GeofenceViolationError(BusinessRuleViolationError):
    """Error por violación de geofence."""
    
    def __init__(
        self, 
        location: str = None,
        coordinates: Dict[str, float] = None,
        allowed_zones: list = None
    ):
        message = "Location is outside allowed operational zones"
        super().__init__(
            message=message,
            rule_name="geofence_validation"
        )
        self.error_code = "GEOFENCE_VIOLATION"
        
        if location:
            self.details["location"] = location
        if coordinates:
            self.details["coordinates"] = coordinates
        if allowed_zones:
            self.details["allowed_zones"] = allowed_zones


class BusinessHoursViolationError(BusinessRuleViolationError):
    """Error por operación fuera de horario comercial."""
    
    def __init__(self, current_time: str = None, business_hours: str = None):
        message = "Operation not allowed outside business hours"
        super().__init__(
            message=message,
            rule_name="business_hours_validation"
        )
        self.error_code = "BUSINESS_HOURS_VIOLATION"
        
        if current_time:
            self.details["current_time"] = current_time
        if business_hours:
            self.details["business_hours"] = business_hours


class AuthenticationError(TrackingDomainException):
    """Error de autenticación."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR"
        )


class AuthorizationError(TrackingDomainException):
    """Error de autorización."""
    
    def __init__(
        self, 
        message: str = "Access denied", 
        required_permission: str = None,
        user_permissions: list = None
    ):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR"
        )
        
        if required_permission:
            self.details["required_permission"] = required_permission
        if user_permissions:
            self.details["user_permissions"] = user_permissions


class ConcurrencyError(TrackingDomainException):
    """Error de concurrencia/conflicto de versiones."""
    
    def __init__(
        self, 
        resource_id: str,
        expected_version: str = None,
        actual_version: str = None
    ):
        message = f"Concurrency conflict for resource '{resource_id}'"
        super().__init__(
            message=message,
            error_code="CONCURRENCY_ERROR"
        )
        
        self.details.update({
            "resource_id": resource_id
        })
        
        if expected_version:
            self.details["expected_version"] = expected_version
        if actual_version:
            self.details["actual_version"] = actual_version


class RateLimitExceededError(TrackingDomainException):
    """Error por exceder límites de tasa."""
    
    def __init__(
        self, 
        limit: int,
        window: str,
        retry_after: int = None
    ):
        message = f"Rate limit exceeded: {limit} requests per {window}"
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED"
        )
        
        self.details.update({
            "limit": limit,
            "window": window
        })
        
        if retry_after:
            self.details["retry_after_seconds"] = retry_after


# Mapeo de excepciones a códigos HTTP
EXCEPTION_TO_HTTP_STATUS = {
    DomainValidationError: 400,
    CheckpointValidationError: 400,
    BusinessRuleViolationError: 409,
    InvalidStateTransitionError: 409,
    IdempotencyViolationError: 409,
    GeofenceViolationError: 422,
    BusinessHoursViolationError: 422,
    UnitNotFoundError: 404,
    AuthenticationError: 401,
    AuthorizationError: 403,
    ConcurrencyError: 409,
    RateLimitExceededError: 429,
    TrackingDomainException: 500  # Fallback genérico
}


def get_http_status_for_exception(exception: Exception) -> int:
    """
    Obtener código HTTP apropiado para una excepción.
    
    Args:
        exception: Excepción a mapear
        
    Returns:
        Código de estado HTTP apropiado
    """
    for exception_type, status_code in EXCEPTION_TO_HTTP_STATUS.items():
        if isinstance(exception, exception_type):
            return status_code
    
    # Fallback para excepciones no manejadas
    return 500


def create_domain_exception_from_validation_errors(
    validation_errors: list,
    context: str = "Request validation"
) -> DomainValidationError:
    """
    Crear excepción de dominio desde errores de validación de Pydantic.
    
    Args:
        validation_errors: Lista de errores de Pydantic
        context: Contexto donde ocurrió la validación
        
    Returns:
        DomainValidationError con detalles consolidados
    """
    if len(validation_errors) == 1:
        error = validation_errors[0]
        return DomainValidationError(
            message=f"{context}: {error['msg']}",
            field=".".join(str(loc) for loc in error['loc']),
            value=error.get('input'),
            details={"validation_errors": validation_errors}
        )
    
    # Múltiples errores
    fields = [".".join(str(loc) for loc in error['loc']) for error in validation_errors]
    return DomainValidationError(
        message=f"{context}: Multiple validation errors in fields: {', '.join(fields)}",
        details={
            "validation_errors": validation_errors,
            "failed_fields": fields
        }
    )