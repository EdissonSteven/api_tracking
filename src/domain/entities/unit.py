from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

@dataclass
class Unit:
    """Entidad de dominio que representa una unidad de tracking."""
    
    tracking_id: str
    origin: str
    destination: str
    status: str = "created"
    weight_kg: Optional[float] = None
    dimensions: Optional[Dict[str, Any]] = None
    customer_info: Optional[Dict[str, Any]] = None
    extra_data: Optional[Dict[str, Any]] = None
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Inicializa valores por defecto después de la creación."""
        if self.id is None:
            self.id = str(uuid.uuid4())
        
        current_time = datetime.now()
        
        if self.created_at is None:
            self.created_at = current_time
        
        if self.updated_at is None:
            self.updated_at = current_time
    
    def update_status(self, new_status: str):
        """
        Actualiza el estado de la unidad.
        
        Args:
            new_status: Nuevo estado
        """
        self.status = new_status
        self.updated_at = datetime.now()
    
    def update_location(self, new_origin: Optional[str] = None, new_destination: Optional[str] = None):
        """
        Actualiza origen o destino de la unidad.
        
        Args:
            new_origin: Nuevo origen
            new_destination: Nuevo destino
        """
        if new_origin is not None:
            self.origin = new_origin
        if new_destination is not None:
            self.destination = new_destination
        self.updated_at = datetime.now()
    
    def add_customer_info(self, key: str, value: Any):
        """
        Agrega información del cliente.
        
        Args:
            key: Clave del dato
            value: Valor del dato
        """
        if self.customer_info is None:
            self.customer_info = {}
        self.customer_info[key] = value
        self.updated_at = datetime.now()
    
    def add_meta_data(self, key: str, value: Any):
        """
        Agrega metadatos a la unidad.
        
        Args:
            key: Clave del metadato
            value: Valor del metadato
        """
        if self.extra_data is None:
            self.extra_data = {}
        self.extra_data[key] = value
        self.updated_at = datetime.now()
    
    def set_dimensions(self, length: float, width: float, height: float, unit: str = "cm"):
        """
        Establece las dimensiones del paquete.
        
        Args:
            length: Largo
            width: Ancho  
            height: Alto
            unit: Unidad de medida
        """
        self.dimensions = {
            "length": length,
            "width": width,
            "height": height,
            "unit": unit
        }
        self.updated_at = datetime.now()
    
    def is_valid(self) -> bool:
        """
        Valida que la unidad tenga los datos mínimos requeridos.
        
        Returns:
            True si la unidad es válida
        """
        return (
            bool(self.tracking_id) and 
            bool(self.origin) and 
            bool(self.destination) and
            bool(self.status)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la entidad a diccionario.
        
        Returns:
            Diccionario con los datos de la unidad
        """
        return {
            "id": self.id,
            "tracking_id": self.tracking_id,
            "origin": self.origin,
            "destination": self.destination,
            "status": self.status,
            "weight_kg": self.weight_kg,
            "dimensions": self.dimensions,
            "customer_info": self.customer_info,
            "meta_data": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Unit":
        """
        Crea una unidad desde un diccionario.
        
        Args:
            data: Diccionario con los datos
            
        Returns:
            Instancia de Unit
        """
        # Convertir strings de fecha a datetime si es necesario
        for date_field in ["created_at", "updated_at"]:
            if isinstance(data.get(date_field), str):
                data[date_field] = datetime.fromisoformat(data[date_field])
        
        # Mapear meta_data a extra_data
        if "meta_data" in data:
            data["extra_data"] = data.pop("meta_data")
        
        return cls(**data)
    
    def __str__(self) -> str:
        """Representación string de la unidad."""
        return f"Unit(id={self.id}, tracking_id={self.tracking_id}, status={self.status})"
    
    def __repr__(self) -> str:
        """Representación para debugging."""
        return self.__str__()