from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

from ..value_objects.tracking_id import TrackingId
from ..value_objects.unit_status import UnitStatus
from ..domain_exceptions import BusinessRuleViolationError


@dataclass
class Unit:
    """
    Entidad de dominio que representa una unidad de tracking.
    
    Esta es la entidad central del agregado de tracking.
    """
    
    # Identificadores
    tracking_id: TrackingId
    guide_id: Optional[str] = None
    
    # Estado
    current_status: UnitStatus = field(default=UnitStatus.CREATED)
    
    # Información del paquete
    weight_kg: Optional[float] = None  # kg
    dimensions: Optional[str] = None  # Formato: "LxWxH"
    
    # Ubicaciones
    origin: Optional[str] = None
    destination: Optional[str] = None
    
    # Metadata
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Inicializa valores por defecto después de la creación."""
        if self.id is None:
            self.id = str(uuid.uuid4())
        
        current_time = datetime.utcnow()
        
        if self.created_at is None:
            self.created_at = current_time
        
        if self.updated_at is None:
            self.updated_at = current_time
    
    @classmethod
    def create(
        cls,
        tracking_id: TrackingId,
        guide_id: Optional[str] = None,
        weight_kg: Optional[float] = None,
        dimensions: Optional[str] = None,
        origin: Optional[str] = None,
        destination: Optional[str] = None
    ) -> "Unit":
        """
        Factory method para crear una nueva unidad.
        
        Args:
            tracking_id: ID de seguimiento único
            guide_id: ID de la guía asociada
            weight_kg: Peso en kilogramos
            dimensions: Dimensiones del paquete
            origin: Origen
            destination: Destino
            
        Returns:
            Nueva instancia de Unit
        """
        unit = cls(
            tracking_id=tracking_id,
            guide_id=guide_id,
            current_status=UnitStatus.CREATED,
            weight_kg=weight_kg,
            dimensions=dimensions,
            origin=origin,
            destination=destination
        )
        
        if not unit.is_valid():
            raise BusinessRuleViolationError("Invalid unit data")
        
        return unit
    
    def update_status(self, new_status: UnitStatus) -> None:
        """
        Actualiza el estado de la unidad con validación de transiciones.
        
        Args:
            new_status: Nuevo estado
            
        Raises:
            BusinessRuleViolationError: Si la transición no es válida
        """
        # Validar transición de estado
        if not self.current_status.can_transition_to(new_status):
            raise BusinessRuleViolationError(
                message=f"Invalid status transition from {self.current_status.value} to {new_status.value}",
                rule_name="status_transition",
                context={
                    "current_status": self.current_status.value,
                    "new_status": new_status.value,
                    "tracking_id": self.tracking_id.value
                }
            )
        
        self.current_status = new_status
        self.updated_at = datetime.utcnow()
    
    def update_weight(self, weight_kg: float) -> None:
        """
        Actualiza el peso de la unidad.
        
        Args:
            weight_kg: Peso en kilogramos
        """
        if weight_kg <= 0:
            raise BusinessRuleViolationError("weight_kg must be positive")
        
        if weight_kg > 100:  # Límite de negocio
            raise BusinessRuleViolationError("weight_kg exceeds maximum limit of 100kg")
        
        self.weight_kg = weight_kg
        self.updated_at = datetime.utcnow()
    
    def is_valid(self) -> bool:
        """
        Valida que la unidad tenga los datos mínimos requeridos.
        
        Returns:
            True si la unidad es válida
        """
        return (
            self.tracking_id is not None and
            self.current_status is not None
        )
    
    def is_in_transit(self) -> bool:
        """Check if unit is currently in transit"""
        return self.current_status in [
            UnitStatus.PICKED_UP,
            UnitStatus.IN_TRANSIT,
            UnitStatus.OUT_FOR_DELIVERY
        ]
    
    def is_delivered(self) -> bool:
        """Check if unit has been delivered"""
        return self.current_status == UnitStatus.DELIVERED
    
    def can_be_modified(self) -> bool:
        """Check if unit can still be modified"""
        return self.current_status in [UnitStatus.CREATED, UnitStatus.PICKED_UP]
    
    def __str__(self) -> str:
        """Representación string de la unidad."""
        return f"Unit(tracking_id={self.tracking_id.value}, status={self.current_status.value})"
    
    def __repr__(self) -> str:
        """Representación para debugging."""
        return self.__str__()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tracking_id": self.tracking_id.value if self.tracking_id else None,
            "guide_id": self.guide_id,
            "current_status": self.current_status.value if self.current_status else None,
            "weight_kg": self.weight_kg,
            "dimensions": self.dimensions,
            "origin": self.origin,
            "destination": self.destination,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Unit":
        from ..value_objects.tracking_id import TrackingId
        from ..value_objects.unit_status import UnitStatus
        
        return cls(
            id=data.get("id"),
            tracking_id=TrackingId(data["tracking_id"]) if data.get("tracking_id") else None,
            guide_id=data.get("guide_id"),
            current_status=UnitStatus(data["current_status"]) if data.get("current_status") else UnitStatus.CREATED,
            weight_kg=data.get("weight_kg"),
            dimensions=data.get("dimensions"),
            origin=data.get("origin"),
            destination=data.get("destination"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )