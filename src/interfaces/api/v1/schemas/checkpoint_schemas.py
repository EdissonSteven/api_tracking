from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class CheckpointStatus(str, Enum):
    """Estados posibles de un checkpoint."""
    CREATED = "created"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    EXCEPTION = "exception"
    RETURNED = "returned"
    CANCELLED = "cancelled"
    AT_FACILITY = "at_facility"

class UnitStatusEnum(str, Enum):
    CREATED = "created"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    EXCEPTION = "exception"
    RETURNED = "returned"
    CANCELLED = "cancelled"
    AT_FACILITY = "at_facility"
    

class CoordinatesSchema(BaseModel):
    """Schema para coordenadas geográficas."""
    latitude: float = Field(..., description="Latitud", ge=-90, le=90)
    longitude: float = Field(..., description="Longitud", ge=-180, le=180)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "latitude": 4.7110,
                "longitude": -74.0721
            }
        }
    )

class CreateCheckpointRequest(BaseModel):
    """Request para crear un nuevo checkpoint."""
    
    tracking_id: str = Field(
        ..., 
        description="ID de seguimiento de la unidad",
        min_length=1,
        max_length=50,
        example="TRK001"
    )
    
    status: CheckpointStatus = Field(
        ..., 
        description="Estado del checkpoint",
        example=CheckpointStatus.IN_TRANSIT
    )
    
    location: Optional[str] = Field(
        None,
        description="Ubicación textual del checkpoint",
        max_length=255,
        example="Centro de Distribución Bogotá"
    )
    
    description: Optional[str] = Field(
        None,
        description="Descripción detallada del checkpoint",
        max_length=500,
        example="Paquete recogido y procesado correctamente"
    )

    operator: Optional[str] = Field(
        None,
        description="Quien Manipuló el paquete",
        max_length=100,
        example="Juan Pérez"
    )
    
    coordinates: Optional[CoordinatesSchema] = Field(
        None,
        description="Coordenadas GPS del checkpoint"
    )
    
    meta_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadatos adicionales del checkpoint",
        example={
            "driver": "Juan Pérez",
            "vehicle": "ABC123",
            "temperature": "22°C"
        }
    )
    
    timestamp: Optional[datetime] = Field(
        None,
        description="Timestamp del checkpoint (opcional, se usa datetime.now() si no se especifica)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tracking_id": "TRK001",
                "status": "in_transit",
                "location": "Terminal de Transporte",
                "description": "En ruta hacia destino",
                "operator": "Juan Pérez",
                "coordinates": {
                    "latitude": 4.7110,
                    "longitude": -74.0721
                },
                "meta_data": {
                    "driver": "Carlos Rodríguez",
                    "vehicle": "ABC123"
                }
            }
        }
    )

class UpdateCheckpointRequest(BaseModel):
    """Request para actualizar un checkpoint existente."""
    
    status: Optional[CheckpointStatus] = Field(
        None,
        description="Nuevo estado del checkpoint"
    )
    
    location: Optional[str] = Field(
        None,
        description="Nueva ubicación del checkpoint",
        max_length=255
    )
    
    description: Optional[str] = Field(
        None,
        description="Nueva descripción del checkpoint",
        max_length=500
    )

    operator: Optional[str] = Field(
        None,
        description="Nuevo operador que manipuló el paquete",
        max_length=100
    )   
    
    coordinates: Optional[CoordinatesSchema] = Field(
        None,
        description="Nuevas coordenadas GPS del checkpoint"
    )
    
    meta_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Nuevos metadatos del checkpoint"
    )

class CheckpointResponse(BaseModel):
    """Response de un checkpoint."""
    
    id: str = Field(
        ..., 
        description="ID único del checkpoint",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    
    tracking_id: str = Field(
        ..., 
        description="ID de seguimiento de la unidad",
        example="TRK001"
    )
    
    status: CheckpointStatus = Field(
        ..., 
        description="Estado del checkpoint",
        example=CheckpointStatus.IN_TRANSIT
    )
    
    location: Optional[str] = Field(
        None,
        description="Ubicación del checkpoint",
        example="Centro de Distribución Bogotá"
    )
    
    description: Optional[str] = Field(
        None,
        description="Descripción del checkpoint",
        example="Paquete recogido y procesado"
    )

    operator: Optional[str] = Field(
        None,
        description="Quien Manipuló el paquete",
        example="Juan Pérez"
    )       
    
    coordinates: Optional[CoordinatesSchema] = Field(
        None,
        description="Coordenadas GPS del checkpoint"
    )
    
    meta_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadatos del checkpoint"
    )
    
    timestamp: datetime = Field(
        ..., 
        description="Timestamp del checkpoint",
        example="2025-09-27T12:30:00Z"
    )
    
    created_at: datetime = Field(
        ..., 
        description="Fecha de creación del checkpoint",
        example="2025-09-27T12:30:00Z"
    )
    
    updated_at: datetime = Field(
        None, 
        description="Fecha de última actualización",
        example="2025-09-27T12:30:00Z"
    )
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "tracking_id": "TRK001",
                "status": "in_transit",
                "location": "Terminal de Transporte",
                "description": "En ruta hacia destino",
                "operator": "Juan Pérez",
                "coordinates": {
                    "latitude": 4.7110,
                    "longitude": -74.0721
                },
                "meta_data": {
                    "driver": "Carlos Rodríguez",
                    "vehicle": "ABC123"
                },
                "timestamp": "2025-09-27T12:30:00Z",
                "created_at": "2025-09-27T12:30:00Z",
                "updated_at": "2025-09-27T12:30:00Z"
            }
        }
    )

class CheckpointListResponse(BaseModel):
    """Response para lista de checkpoints."""
    
    tracking_id: str = Field(
        ..., 
        description="ID de seguimiento",
        example="TRK001"
    )
    
    checkpoints: List[CheckpointResponse] = Field(
        ..., 
        description="Lista de checkpoints ordenados por timestamp"
    )
    
    total_count: int = Field(
        ..., 
        description="Número total de checkpoints",
        example=5
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tracking_id": "TRK001",
                "total_count": 2,
                "checkpoints": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "tracking_id": "TRK001",
                        "status": "picked_up",
                        "location": "Centro de Distribución",
                        "description": "Paquete recogido",
                        "operator": "Juan Pérez",
                        "timestamp": "2025-09-27T10:00:00Z",
                        "created_at": "2025-09-27T10:00:00Z",
                        "updated_at": "2025-09-27T10:00:00Z"
                    },
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440001",
                        "tracking_id": "TRK001", 
                        "status": "in_transit",
                        "location": "Terminal de Transporte",
                        "description": "En ruta",
                        "operator": "Juan Pérez",
                        "timestamp": "2025-09-27T12:30:00Z",
                        "created_at": "2025-09-27T12:30:00Z",
                        "updated_at": "2025-09-27T12:30:00Z"
                    }
                ]
            }
        }
    )

class ErrorResponse(BaseModel):
    """Schema para respuestas de error."""
    
    error: bool = Field(True, description="Indica que es un error")
    message: str = Field(..., description="Mensaje de error")
    details: Optional[Dict[str, Any]] = Field(
        None, 
        description="Detalles adicionales del error"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": True,
                "message": "Tracking ID no encontrado",
                "details": {
                    "tracking_id": "TRK999",
                    "timestamp": "2025-09-27T12:30:00Z"
                }
            }
        }
    )