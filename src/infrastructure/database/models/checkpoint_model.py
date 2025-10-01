from sqlmodel import SQLModel, Field, Column, JSON
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

class CheckpointModel(SQLModel, table=True):
    """
    Modelo de base de datos para checkpoints.
    
    Este modelo sigue el patrón de Clean Architecture donde los modelos
    de persistencia están separados de las entidades de dominio.
    """
    
    __tablename__ = "checkpoints"
    
    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        description="ID único del checkpoint"
    )
    
    tracking_id: str = Field(
        index=True,
        max_length=50,
        description="ID de seguimiento de la unidad"
    )
    
    status: str = Field(
        index=True,
        max_length=20,
        description="Estado del checkpoint"
    )
    
    location: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Ubicación textual del checkpoint"
    )
    
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Descripción del checkpoint"
    )
    
    operator: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Operador que registró el checkpoint"
    )
    
    coordinates: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column("coordinates",JSON),
        description="Coordenadas GPS del checkpoint"
    )
    
    meta_data: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column("meta_data",JSON),
        description="Metadatos adicionales del checkpoint"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        index=True,
        description="Timestamp del evento del checkpoint"
    )
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Fecha de creación del registro"
    )
    
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Fecha de última actualización"
    )
    
    class Config:
        """Configuración del modelo."""
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "tracking_id": "TRK001",
                "status": "in_transit",
                "location": "Centro de Distribución Bogotá",
                "description": "Paquete en tránsito hacia destino",
                "operator": "Juan Pérez",
                "coordinates": {
                    "latitude": 4.7110,
                    "longitude": -74.0721
                },
                "meta_data": {
                    "driver": "Carlos Rodríguez",
                    "vehicle": "ABC123",
                    "temperature": "22°C"
                },
                "timestamp": "2025-09-28T12:30:00Z",
                "created_at": "2025-09-28T12:30:00Z",
                "updated_at": "2025-09-28T12:30:00Z"
            }
        }