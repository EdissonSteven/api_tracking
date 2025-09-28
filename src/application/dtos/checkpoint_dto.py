from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class CreateCheckpointRequest:
    """
    DTO para solicitud de creación de checkpoint.
    
    Este DTO representa los datos de entrada para crear un checkpoint,
    siguiendo el patrón de separación entre la capa de aplicación y las interfaces.
    """
    tracking_id: str
    status: str
    timestamp: Optional[datetime] = None
    location: Optional[str] = None
    description: Optional[str] = None
    operator: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validaciones básicas después de la inicialización."""
        if not self.tracking_id or not self.tracking_id.strip():
            raise ValueError("tracking_id es requerido")
        
        if not self.status or not self.status.strip():
            raise ValueError("status es requerido")
        
        # Limpiar strings
        self.tracking_id = self.tracking_id.strip()
        self.status = self.status.strip()
        
        # Inicializar meta_data si es None
        if self.meta_data is None:
            self.meta_data = {}


@dataclass
class CheckpointResponse:
    """
    DTO para respuesta de checkpoint.
    
    Este DTO representa la respuesta que se envía al cliente,
    con todos los campos necesarios para mostrar la información del checkpoint.
    """
    id: str
    tracking_id: str
    status: str
    timestamp: datetime
    location: Optional[str] = None
    description: Optional[str] = None
    operator: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validaciones y normalizaciones después de la inicialización."""
        # Asegurar que ID es string
        if self.id is not None:
            self.id = str(self.id)
        
        # Asegurar que tracking_id es string
        if self.tracking_id is not None:
            self.tracking_id = str(self.tracking_id)
        
        # Asegurar que status es string
        if self.status is not None:
            self.status = str(self.status)
        
        # Asegurar que meta_data es un dict
        if self.meta_data is None:
            self.meta_data = {}
        
        # Validar campos requeridos
        if not self.id:
            raise ValueError("ID es requerido en la respuesta")
        
        if not self.tracking_id:
            raise ValueError("tracking_id es requerido en la respuesta")
        
        if not self.status:
            raise ValueError("status es requerido en la respuesta")
        
        if self.timestamp is None:
            raise ValueError("timestamp es requerido en la respuesta")
    
    @classmethod
    def from_checkpoint(cls, checkpoint, created_at: Optional[datetime] = None):
        """
        Crear CheckpointResponse desde una entidad Checkpoint.
        
        Args:
            checkpoint: Entidad de dominio Checkpoint
            created_at: Fecha de creación opcional
            
        Returns:
            CheckpointResponse: DTO de respuesta
        """
        # Función helper para extraer valores de forma segura
        def safe_extract(obj, default=None):
            if obj is None:
                return default
            if hasattr(obj, 'value'):
                return obj.value
            return str(obj) if obj is not None else default
        
        return cls(
            id=safe_extract(checkpoint.id),
            tracking_id=safe_extract(checkpoint.tracking_id),
            status=safe_extract(checkpoint.status),
            timestamp=checkpoint.timestamp or datetime.utcnow(),
            location=checkpoint.location,
            description=checkpoint.description,
            operator=getattr(checkpoint, 'operator', None),
            meta_data=getattr(checkpoint, 'meta_data', None) or {},
            created_at=created_at or getattr(checkpoint, 'created_at', None) or datetime.utcnow(),
            updated_at=created_at or getattr(checkpoint, 'created_at', None) or datetime.utcnow()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el DTO a diccionario para serialización.
        
        Returns:
            Dict con los datos del checkpoint
        """
        return {
            "id": self.id,
            "tracking_id": self.tracking_id,
            "status": self.status,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "location": self.location,
            "description": self.description,
            "operator": self.operator,
            "meta_data": self.meta_data,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }