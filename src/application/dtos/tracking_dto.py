from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class UnitResponse:
    """DTO para respuesta de unidad."""
    
    id: str
    tracking_id: str
    origin: str
    destination: str
    status: str
    created_at: datetime
    updated_at: datetime
    guide_id: Optional[str] = None
    weight_kg: Optional[float] = None
    dimensions: Optional[Dict[str, Any]] = None
    customer_info: Optional[Dict[str, Any]] = None
    meta_data: Optional[Dict[str, Any]] = None


@dataclass
class TrackingResponse:
    """DTO para respuesta completa de tracking."""
    
    tracking_id: str
    unit: UnitResponse
    checkpoints: List[Any]
    total_checkpoints: int
    last_update: datetime
    estimated_delivery: Optional[datetime] = None
    is_delayed: bool = False


@dataclass
class TrackingStatusResponse:
    """DTO para respuesta de estado de tracking."""
    
    tracking_id: str
    current_status: str
    last_update: datetime
    last_location: Optional[str] = None


@dataclass
class TrackingTimelineEvent:
    """DTO para evento en la línea de tiempo de tracking."""
    
    type: str
    timestamp: datetime
    status: str
    location: Optional[str] = None
    description: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None


@dataclass
class TrackingTimelineResponse:
    """DTO para respuesta de línea de tiempo de tracking."""
    
    tracking_id: str
    events: List[TrackingTimelineEvent]
    total_events: int


@dataclass
class TrackingSearchResult:
    """DTO para resultado de búsqueda de tracking."""
    
    tracking_id: str
    origin: str
    destination: str
    current_status: str
    last_update: datetime
    created_at: datetime
    last_location: Optional[str] = None


@dataclass
class TrackingSearchResponse:
    """DTO para respuesta de búsqueda de trackings."""
    
    results: List[TrackingSearchResult]
    total_count: int
    page: int
    page_size: int


@dataclass
class TrackingStatistics:
    """DTO para estadísticas de tracking."""
    
    total_trackings: int
    total_checkpoints: int
    status_distribution: Dict[str, int]
    generated_at: datetime


@dataclass
class CreateTrackingRequest:
    """DTO para solicitud de creación de tracking."""
    
    tracking_id: str
    origin: str
    destination: str
    weight_kg: Optional[float] = None
    dimensions: Optional[Dict[str, Any]] = None
    customer_info: Optional[Dict[str, Any]] = None
    meta_data: Optional[Dict[str, Any]] = None


@dataclass
class UpdateTrackingRequest:
    """DTO para solicitud de actualización de tracking."""
    
    origin: Optional[str] = None
    destination: Optional[str] = None
    status: Optional[str] = None
    weight_kg: Optional[float] = None
    dimensions: Optional[Dict[str, Any]] = None
    customer_info: Optional[Dict[str, Any]] = None
    meta_data: Optional[Dict[str, Any]] = None

@dataclass
class CheckpointValidationResult:
    """DTO para resultado de validación de checkpoint."""
    
    is_valid: bool
    errors: List[str]
    warnings: List[str] = None


@dataclass
class UnitValidationResult:
    """DTO para resultado de validación de unidad."""
    
    is_valid: bool
    errors: List[str]
    warnings: List[str] = None


@dataclass
class BusinessRuleResult:
    """DTO para resultado de reglas de negocio."""
    
    allowed: bool
    reason: str
    additional_info: Optional[Dict[str, Any]] = None