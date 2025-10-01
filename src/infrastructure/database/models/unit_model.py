from sqlmodel import SQLModel, Field, Column, JSON
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

class UnitModel(SQLModel, table=True):
    """Modelo de base de datos para unidades de tracking."""
    
    __tablename__ = "units"
    
    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        description="ID único de la unidad"
    )
    
    tracking_id: str = Field(
        unique=True,
        index=True,
        max_length=50,
        description="ID de seguimiento único de la unidad"
    )
    
    origin: str = Field(
        max_length=100,
        description="Origen del envío"
    )
    
    destination: str = Field(
        max_length=100,
        description="Destino del envío"
    )

    guide_id: Optional[str] = Field(
         default_factory=lambda: str(uuid.uuid4()),
        max_length=50,
        description="ID de la guía asociada",
    )
    
    status: str = Field(
        default="created",
        index=True,
        max_length=20,
        description="Estado actual de la unidad"
    )
    
    weight_kg: Optional[float] = Field(
        default=None,
        description="Peso en kilogramos"
    )
    
    dimensions: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Dimensiones del paquete"
    )
    
    customer_info: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Información del cliente"
    )
    
    extra_data: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Datos adicionales de la unidad",
        alias="meta_data"
    )
    
    created_at: datetime = Field(
        default_factory=datetime.now,
        index=True,
        description="Fecha de creación del registro"
    )
    
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Fecha de última actualización"
    )