from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List
import uuid


class DomainEvent(ABC):
    """Base class para eventos de dominio."""
    
    def __init__(self):
        self.event_id = str(uuid.uuid4())
        self.occurred_at = datetime.utcnow()
        self.event_version = "1.0"
    
    @abstractmethod
    def event_name(self) -> str:
        """Nombre único del evento."""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializar evento a diccionario."""
        return {
            "event_id": self.event_id,
            "event_name": self.event_name(),
            "occurred_at": self.occurred_at.isoformat(),
            "event_version": self.event_version,
            "payload": self._get_payload()
        }
    
    @abstractmethod
    def _get_payload(self) -> Dict[str, Any]:
        """Obtener payload específico del evento."""
        pass


@dataclass
class CheckpointCreatedEvent(DomainEvent):
    """Evento disparado cuando se crea un checkpoint."""
    
    def __init__(
        self,
        checkpoint_id: str,
        tracking_id: str,
        status: str,
        created_by: str,
        location: str = None,
        operator: str = None
    ):
        super().__init__()
        self.checkpoint_id = checkpoint_id
        self.tracking_id = tracking_id
        self.status = status
        self.created_by = created_by
        self.location = location
        self.operator = operator
    
    def event_name(self) -> str:
        return "checkpoint.created"
    
    def _get_payload(self) -> Dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "tracking_id": self.tracking_id,
            "status": self.status,
            "created_by": self.created_by,
            "location": self.location,
            "operator": self.operator
        }


@dataclass
class CheckpointValidationFailedEvent(DomainEvent):
    """Evento disparado cuando falla la validación de un checkpoint."""
    
    def __init__(
        self,
        tracking_id: str,
        status: str,
        error_reason: str,
        attempted_by: str
    ):
        super().__init__()
        self.tracking_id = tracking_id
        self.status = status
        self.error_reason = error_reason
        self.attempted_by = attempted_by
    
    def event_name(self) -> str:
        return "checkpoint.validation_failed"
    
    def _get_payload(self) -> Dict[str, Any]:
        return {
            "tracking_id": self.tracking_id,
            "status": self.status,
            "error_reason": self.error_reason,
            "attempted_by": self.attempted_by
        }


class DomainEventHandler(ABC):
    """Handler base para eventos de dominio."""
    
    @abstractmethod
    def handle(self, event: DomainEvent) -> None:
        """Manejar evento de dominio."""
        pass


class DomainEventDispatcher:
    """Dispatcher para eventos de dominio."""
    
    def __init__(self):
        self._handlers: Dict[str, List[DomainEventHandler]] = {}
    
    def register(self, event_name: str, handler: DomainEventHandler):
        """Registrar handler para un evento."""
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)
    
    def dispatch(self, event: DomainEvent):
        """Disparar evento a todos los handlers registrados."""
        event_name = event.event_name()
        
        if event_name in self._handlers:
            for handler in self._handlers[event_name]:
                try:
                    handler.handle(event)  # ⬅️ SIN await
                except Exception as e:
                    # Log error pero no fallar el proceso principal
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error handling event {event_name}: {str(e)}")


# Event Handlers específicos
class CheckpointCreatedEventHandler(DomainEventHandler):
    """Handler para eventos de checkpoint creado."""
    
    def handle(self, event: DomainEvent) -> None:
        if isinstance(event, CheckpointCreatedEvent):
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Checkpoint created: {event.checkpoint_id} for tracking {event.tracking_id}")


class MetricsEventHandler(DomainEventHandler):
    """Handler para actualizar métricas basado en eventos."""
    
    def handle(self, event: DomainEvent) -> None:
        # Actualizar métricas según el tipo de evento
        if isinstance(event, CheckpointCreatedEvent):
            # Incrementar contador de checkpoints creados
            # metrics.increment("checkpoints.created", tags={"status": event.status})
            pass


# Factory para crear dispatcher configurado
def create_event_dispatcher() -> DomainEventDispatcher:
    """Crear dispatcher con handlers predeterminados."""
    dispatcher = DomainEventDispatcher()
    
    # Registrar handlers
    dispatcher.register("checkpoint.created", CheckpointCreatedEventHandler())
    dispatcher.register("checkpoint.created", MetricsEventHandler())
    dispatcher.register("checkpoint.validation_failed", MetricsEventHandler())
    
    return dispatcher