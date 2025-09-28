from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class ErrorDetail(BaseModel):
    """Detalle específico de un error."""
    
    field: Optional[str] = Field(
        None, 
        description="Campo que causó el error"
    )
    
    message: str = Field(
        ..., 
        description="Mensaje específico del error"
    )
    
    code: Optional[str] = Field(
        None, 
        description="Código de error específico"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "field": "tracking_id",
                "message": "El tracking ID debe tener entre 1 y 50 caracteres",
                "code": "INVALID_LENGTH"
            }
        }
    )

class ErrorResponse(BaseModel):
    """Schema base para respuestas de error."""
    
    error: bool = Field(
        True, 
        description="Indica que es una respuesta de error"
    )
    
    message: str = Field(
        ..., 
        description="Mensaje principal del error"
    )
    
    details: Optional[List[ErrorDetail]] = Field(
        None, 
        description="Detalles específicos del error"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp del error"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": True,
                "message": "Error de validación en los datos enviados",
                "details": [
                    {
                        "field": "tracking_id",
                        "message": "El tracking ID es requerido",
                        "code": "REQUIRED_FIELD"
                    }
                ],
                "timestamp": "2025-09-27T12:30:00Z"
            }
        }
    )

class ValidationErrorResponse(BaseModel):
    """Schema específico para errores de validación."""
    
    error: bool = Field(True, description="Indica que es un error")
    
    message: str = Field(
        default="Error de validación", 
        description="Mensaje del error de validación"
    )
    
    validation_errors: List[ErrorDetail] = Field(
        ..., 
        description="Lista de errores de validación específicos"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp del error"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": True,
                "message": "Error de validación",
                "validation_errors": [
                    {
                        "field": "status",
                        "message": "El estado debe ser uno de: created, picked_up, in_transit, delivered",
                        "code": "INVALID_CHOICE"
                    },
                    {
                        "field": "tracking_id", 
                        "message": "El tracking ID no puede estar vacío",
                        "code": "REQUIRED_FIELD"
                    }
                ],
                "timestamp": "2025-09-27T12:30:00Z"
            }
        }
    )

class BusinessErrorResponse(BaseModel):
    """Schema para errores de lógica de negocio."""
    
    error: bool = Field(True, description="Indica que es un error")
    
    error_code: str = Field(
        ..., 
        description="Código específico del error de negocio"
    )
    
    message: str = Field(
        ..., 
        description="Mensaje descriptivo del error"
    )
    
    context: Optional[Dict[str, Any]] = Field(
        None, 
        description="Contexto adicional del error"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp del error"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": True,
                "error_code": "TRACKING_NOT_FOUND",
                "message": "No se encontró información para el tracking ID especificado",
                "context": {
                    "tracking_id": "TRK999",
                    "searched_at": "2025-09-27T12:30:00Z"
                },
                "timestamp": "2025-09-27T12:30:00Z"
            }
        }
    )

class NotFoundErrorResponse(BaseModel):
    """Schema específico para errores 404."""
    
    error: bool = Field(True, description="Indica que es un error")
    
    message: str = Field(
        ..., 
        description="Mensaje del error 404"
    )
    
    resource: str = Field(
        ..., 
        description="Recurso que no fue encontrado"
    )
    
    resource_id: Optional[str] = Field(
        None, 
        description="ID del recurso que no fue encontrado"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp del error"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": True,
                "message": "Tracking no encontrado",
                "resource": "tracking",
                "resource_id": "TRK999",
                "timestamp": "2025-09-27T12:30:00Z"
            }
        }
    )

class ConflictErrorResponse(BaseModel):
    """Schema específico para errores 409 (conflictos)."""
    
    error: bool = Field(True, description="Indica que es un error")
    
    message: str = Field(
        ..., 
        description="Mensaje del error de conflicto"
    )
    
    conflict_type: str = Field(
        ..., 
        description="Tipo de conflicto"
    )
    
    existing_resource: Optional[Dict[str, Any]] = Field(
        None, 
        description="Información del recurso existente que causa el conflicto"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp del error"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": True,
                "message": "Ya existe un tracking con este ID",
                "conflict_type": "DUPLICATE_TRACKING_ID",
                "existing_resource": {
                    "tracking_id": "TRK001",
                    "created_at": "2025-09-27T10:00:00Z"
                },
                "timestamp": "2025-09-27T12:30:00Z"
            }
        }
    )

class RateLimitErrorResponse(BaseModel):
    """Schema específico para errores de rate limiting."""
    
    error: bool = Field(True, description="Indica que es un error")
    
    message: str = Field(
        default="Demasiadas solicitudes", 
        description="Mensaje del error de rate limit"
    )
    
    retry_after: int = Field(
        ..., 
        description="Segundos que debe esperar antes de reintentar"
    )
    
    limit: int = Field(
        ..., 
        description="Límite de solicitudes permitidas"
    )
    
    window: int = Field(
        ..., 
        description="Ventana de tiempo en segundos"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp del error"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": True,
                "message": "Demasiadas solicitudes. Intente de nuevo más tarde",
                "retry_after": 60,
                "limit": 100,
                "window": 3600,
                "timestamp": "2025-09-27T12:30:00Z"
            }
        }
    )

class InternalServerErrorResponse(BaseModel):
    """Schema para errores internos del servidor."""
    
    error: bool = Field(True, description="Indica que es un error")
    
    message: str = Field(
        default="Error interno del servidor", 
        description="Mensaje del error interno"
    )
    
    error_id: Optional[str] = Field(
        None, 
        description="ID único del error para tracking interno"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp del error"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": True,
                "message": "Error interno del servidor. Por favor contacte al administrador",
                "error_id": "ERR-550e8400-e29b-41d4",
                "timestamp": "2025-09-27T12:30:00Z"
            }
        }
    )