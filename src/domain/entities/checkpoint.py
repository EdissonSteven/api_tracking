from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

@dataclass
class Checkpoint:
    """
    Entidad de dominio que representa un checkpoint de seguimiento.
    
    Esta entidad sigue los principios de DDD, encapsulando la lógica de negocio
    relacionada con los checkpoints y manteniendo la consistencia de datos.
    """
    
    tracking_id: str
    status: str
    location: Optional[str] = None
    description: Optional[str] = None  
    coordinates: Optional[Dict[str, Any]] = None
    meta_data: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    operator: Optional[str] = None
    
    def __post_init__(self):
        """
        Inicializa valores por defecto después de la creación.
        
        Este método garantiza que la entidad siempre tenga valores válidos
        para campos críticos como ID y timestamps.
        """
        current_time = datetime.utcnow()  # Usar UTC para consistencia
        
        # Generar ID si no existe
        if self.id is None:
            self.id = str(uuid.uuid4())
        
        # Asegurar que el ID es siempre string
        if not isinstance(self.id, str):
            self.id = str(self.id)
        
        # Establecer timestamp por defecto
        if self.timestamp is None:
            self.timestamp = current_time
        
        # Establecer created_at por defecto
        if self.created_at is None:
            self.created_at = current_time
        
        # Establecer updated_at por defecto
        if self.updated_at is None:
            self.updated_at = current_time
        
        # Inicializar meta_data como dict vacío si es None
        if self.meta_data is None:
            self.meta_data = {}
        
        # Inicializar coordinates como dict vacío si es None
        if self.coordinates is None:
            self.coordinates = {}
    
    @classmethod
    def create(
        cls,
        tracking_id,  # Acepta tanto string como TrackingId
        status,       # Acepta tanto string como UnitStatus
        timestamp: Optional[datetime] = None,
        location: Optional[str] = None,
        description: Optional[str] = None,
        operator: Optional[str] = None,
        meta_data: Optional[Dict[str, Any]] = None,
        coordinates: Optional[Dict[str, Any]] = None
    ) -> 'Checkpoint':
        """
        Método factory para crear un nuevo checkpoint.
        
        Este método implementa el patrón Factory, permitiendo crear checkpoints
        de forma controlada y garantizando que siempre estén en un estado válido.
        
        Args:
            tracking_id: ID de seguimiento (string o TrackingId)
            status: Estado del checkpoint (string o UnitStatus)
            timestamp: Timestamp del checkpoint
            location: Ubicación del checkpoint
            description: Notas adicionales
            operator: Operador que registra el checkpoint
            meta_data: Metadatos adicionales
            coordinates: Coordenadas GPS
            
        Returns:
            Nueva instancia de Checkpoint
        """
        # Extraer valores de forma segura, manejando tanto value objects como strings
        tracking_id_str = cls._safe_extract_value(tracking_id)
        status_str = cls._safe_extract_value(status)
        
        return cls(
            tracking_id=tracking_id_str,
            status=status_str,
            timestamp=timestamp,
            location=location,
            description=description,
            operator=operator,
            meta_data=meta_data or {},
            coordinates=coordinates or {}
        )
    
    @staticmethod
    def _safe_extract_value(obj):
        """
        Extrae el valor de un objeto de forma segura.
        
        Args:
            obj: Objeto del cual extraer el valor
            
        Returns:
            Valor extraído como string
        """
        if obj is None:
            return None
        
        # Si tiene atributo 'value', es un value object
        if hasattr(obj, 'value'):
            return str(obj.value)
        
        # Si ya es string, devolverlo
        if isinstance(obj, str):
            return obj
        
        # Para otros tipos, convertir a string
        return str(obj)
    
    def update_status(self, new_status: str, description: Optional[str] = None):
        """
        Actualiza el estado del checkpoint.
        
        Args:
            new_status: Nuevo estado
            description: Nuevas notas opcionales
        """
        self.status = self._safe_extract_value(new_status)
        if description is not None:
            self.description = description
        self.updated_at = datetime.utcnow()
    
    def update_location(
        self, 
        location: Optional[str] = None, 
        coordinates: Optional[Dict[str, Any]] = None
    ):
        """
        Actualiza la ubicación del checkpoint.
        
        Args:
            location: Nueva ubicación textual
            coordinates: Nuevas coordenadas GPS
        """
        if location is not None:
            self.location = location
        if coordinates is not None:
            self.coordinates = coordinates
        self.updated_at = datetime.utcnow()
    
    def add_meta_data(self, key: str, value: Any):
        """
        Agrega metadatos al checkpoint.
        
        Args:
            key: Clave del metadato
            value: Valor del metadato
        """
        if self.meta_data is None:
            self.meta_data = {}
        self.meta_data[key] = value
        self.updated_at = datetime.utcnow()
    
    def is_valid(self) -> bool:
        """
        Valida que el checkpoint tenga los datos mínimos requeridos.
        
        Returns:
            True si el checkpoint es válido
        """
        return (
            bool(self.tracking_id) and 
            bool(self.status) and 
            self.timestamp is not None and
            bool(self.id)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la entidad a diccionario.
        
        Returns:
            Diccionario con los datos del checkpoint
        """
        return {
            "id": self.id,
            "tracking_id": self.tracking_id,
            "status": self.status,
            "location": self.location,
            "description": self.description,  
            "coordinates": self.coordinates,
            "meta_data": self.meta_data,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "operator": self.operator
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Checkpoint":
        """
        Crea un checkpoint desde un diccionario.
        
        Args:
            data: Diccionario con los datos
            
        Returns:
            Instancia de Checkpoint
        """
        # Crear una copia para no modificar el original
        checkpoint_data = data.copy()
        
        # Convertir strings de fecha a datetime si es necesario
        for date_field in ["timestamp", "created_at", "updated_at"]:
            if isinstance(checkpoint_data.get(date_field), str):
                try:
                    checkpoint_data[date_field] = datetime.fromisoformat(
                        checkpoint_data[date_field].replace('Z', '+00:00')
                    )
                except (ValueError, AttributeError):
                    checkpoint_data[date_field] = None
        
        # Asegurar que meta_data es un dict
        if checkpoint_data.get('meta_data') is None:
            checkpoint_data['meta_data'] = {}
        
        if checkpoint_data.get('coordinates') is None:
            checkpoint_data['coordinates'] = {}
        
        return cls(**checkpoint_data)
    
    # Propiedades para compatibilidad con código legacy
    @property 
    def id_value(self) -> str:
        """Compatibilidad: retorna el ID como string."""
        return self.id
    
    @property
    def tracking_id_value(self) -> str:
        """Compatibilidad: retorna el tracking_id como string."""
        return self.tracking_id
    
    @property
    def status_value(self) -> str:
        """Compatibilidad: retorna el status como string."""
        return self.status
    
    # Métodos para interoperabilidad con value objects
    def get_tracking_id(self):
        """
        Obtiene el tracking_id, compatible con value objects.
        
        Returns:
            String del tracking ID
        """
        return self.tracking_id
    
    def get_status(self):
        """
        Obtiene el status, compatible con value objects.
        
        Returns:
            String del status
        """
        return self.status
    
    def get_id(self):
        """
        Obtiene el ID, garantizando que es string.
        
        Returns:
            String del ID
        """
        return str(self.id) if self.id else None
    
    def __str__(self) -> str:
        """Representación string del checkpoint."""
        return f"Checkpoint(id={self.id}, tracking_id={self.tracking_id}, status={self.status})"
    
    def __repr__(self) -> str:
        """Representación para debugging."""
        return (f"Checkpoint(id='{self.id}', tracking_id='{self.tracking_id}', "
                f"status='{self.status}', timestamp={self.timestamp})")
    
    def __eq__(self, other) -> bool:
        """Comparación por igualdad basada en ID."""
        if not isinstance(other, Checkpoint):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash basado en ID para uso en sets y dicts."""
        return hash(self.id) if self.id else 0