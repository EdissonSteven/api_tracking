"""
Mappers para transformación entre DTOs y entidades de dominio.

Este módulo separa las responsabilidades de transformación de datos,
siguiendo el principio de Single Responsibility y facilitando el mantenimiento.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from ...interfaces.api.v1.schemas.checkpoint_schemas import (
    CreateCheckpointRequest, 
    CheckpointResponse, 
    UnitStatusEnum
)
from ...application.dtos.checkpoint_dto import (
    CreateCheckpointRequest as UseCaseRequest,
    CheckpointResponse as UseCaseResponse
)
from ...domain.entities.checkpoint import Checkpoint
from ...domain.domain_exceptions import DomainValidationError

logger = logging.getLogger(__name__)


class Mapper(ABC):
    """Mapper base para transformaciones entre tipos."""
    
    @abstractmethod
    def map(self, source: Any) -> Any:
        """Mapear desde tipo origen a tipo destino."""
        pass


class CheckpointRequestMapper:
    """Mapper para transformar requests de API a DTOs de use case."""
    
    @staticmethod
    def to_use_case_request(api_request: CreateCheckpointRequest) -> UseCaseRequest:
        """
        Transformar request de API a DTO de use case.
        
        Args:
            api_request: Request desde la API
            
        Returns:
            DTO para el use case
            
        Raises:
            DomainValidationError: Si hay errores en la transformación
        """
        try:
            return UseCaseRequest(
                tracking_id=api_request.tracking_id.strip() if api_request.tracking_id else None,
                status=api_request.status.value if api_request.status else None,
                timestamp=api_request.timestamp,
                location=api_request.location.strip() if api_request.location else None,
                description=api_request.description.strip() if api_request.description else None,
                operator=api_request.operator.strip() if api_request.operator else None,
                meta_data=api_request.meta_data or {}
            )
        except Exception as e:
            logger.error(f"Error mapping API request to use case request: {str(e)}")
            raise DomainValidationError(
                message=f"Invalid request data: {str(e)}",
                details={"original_error": str(e)}
            )
    
    @staticmethod
    def to_domain_entity(api_request: CreateCheckpointRequest) -> Checkpoint:
        """
        Transformar request de API directamente a entidad de dominio.
        
        Args:
            api_request: Request desde la API
            
        Returns:
            Entidad de dominio Checkpoint
        """
        try:
            return Checkpoint.create(
                tracking_id=api_request.tracking_id,
                status=api_request.status.value,
                timestamp=api_request.timestamp,
                location=api_request.location,
                description=api_request.description,
                operator=api_request.operator,
                meta_data=api_request.meta_data or {}
            )
        except Exception as e:
            logger.error(f"Error mapping API request to domain entity: {str(e)}")
            raise DomainValidationError(
                message=f"Cannot create checkpoint entity: {str(e)}",
                details={"original_error": str(e)}
            )

class MetricsService:
    def __init__(self): pass

class TracingService:
    def __init__(self): pass
    
class StructuredLogger:
    def __init__(self, name, metrics=None): 
        self.logger = logging.getLogger(name)
    def info(self, msg, **kwargs): self.logger.info(msg)
    def warning(self, msg, **kwargs): self.logger.warning(msg)
    def error(self, msg, **kwargs): self.logger.error(msg)
    def debug(self, msg, **kwargs): self.logger.debug(msg)

class PerformanceMonitor:
    def __init__(self, metrics=None, tracing=None): pass
    
class CheckpointResponseMapper:
    """Mapper para transformar entidades/DTOs a responses de API."""
    
    @staticmethod
    def from_domain_entity(checkpoint: Checkpoint) -> CheckpointResponse:
        """
        Transformar entidad de dominio a response de API.
        
        Args:
            checkpoint: Entidad de dominio
            
        Returns:
            Response para la API
        """
        try:
            return CheckpointResponse(
                id=CheckpointResponseMapper._safe_extract_value(checkpoint.id),
                tracking_id=CheckpointResponseMapper._safe_extract_value(checkpoint.tracking_id),
                status=UnitStatusEnum(CheckpointResponseMapper._safe_extract_value(checkpoint.status)),
                timestamp=checkpoint.timestamp or datetime.utcnow(),
                location=checkpoint.location,
                description=checkpoint.description,
                operator=getattr(checkpoint, 'operator', None),
                meta_data=getattr(checkpoint, 'meta_data', None) or {},
                created_at=checkpoint.created_at or datetime.utcnow(),
                updated_at=checkpoint.updated_at or datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Error mapping domain entity to API response: {str(e)}")
            raise DomainValidationError(
                message=f"Cannot create API response: {str(e)}",
                details={
                    "checkpoint_id": getattr(checkpoint, 'id', 'unknown'),
                    "original_error": str(e)
                }
            )
    
    @staticmethod
    def from_use_case_response(use_case_response: UseCaseResponse) -> CheckpointResponse:
        """
        Transformar response de use case a response de API.
        
        Args:
            use_case_response: Response del use case
            
        Returns:
            Response para la API
        """
        try:
            return CheckpointResponse(
                id=use_case_response.id,
                tracking_id=use_case_response.tracking_id,
                status=UnitStatusEnum(use_case_response.status),
                timestamp=use_case_response.timestamp,
                location=use_case_response.location,
                description=use_case_response.description,
                operator=use_case_response.operator,
                meta_data=use_case_response.meta_data or {},
                created_at=use_case_response.created_at,
                updated_at=getattr(use_case_response, 'updated_at', None) or datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Error mapping use case response to API response: {str(e)}")
            raise DomainValidationError(
                message=f"Cannot create API response from use case: {str(e)}",
                details={"original_error": str(e)}
            )
    
    @staticmethod
    def _safe_extract_value(obj, default=None):
        """
        Extraer valor de forma segura de objetos que pueden ser value objects o primitivos.
        
        Args:
            obj: Objeto del cual extraer valor
            default: Valor por defecto si obj es None
            
        Returns:
            Valor extraído
        """
        if obj is None:
            return default
        
        # Si tiene atributo 'value', es un value object
        if hasattr(obj, 'value'):
            return obj.value
        
        # Si es un tipo primitivo, retornarlo tal como está
        if isinstance(obj, (str, int, float, bool)):
            return obj
        
        # Para otros tipos (como UUID), convertir a string
        return str(obj)


class BatchCheckpointMapper:
    """Mapper para operaciones en lote de checkpoints."""
    
    @staticmethod
    def map_list_to_responses(checkpoints: List[Checkpoint]) -> List[CheckpointResponse]:
        """
        Mapear lista de entidades a lista de responses.
        
        Args:
            checkpoints: Lista de entidades de dominio
            
        Returns:
            Lista de responses de API
        """
        responses = []
        errors = []
        
        for checkpoint in checkpoints:
            try:
                response = CheckpointResponseMapper.from_domain_entity(checkpoint)
                responses.append(response)
            except Exception as e:
                logger.error(f"Error mapping checkpoint {getattr(checkpoint, 'id', 'unknown')}: {str(e)}")
                errors.append({
                    "checkpoint_id": getattr(checkpoint, 'id', 'unknown'),
                    "error": str(e)
                })
        
        if errors:
            logger.warning(f"Failed to map {len(errors)} checkpoints out of {len(checkpoints)}")
        
        return responses
    
    @staticmethod
    def create_summary_response(
        checkpoints: List[Checkpoint],
        total_count: int = None
    ) -> Dict[str, Any]:
        """
        Crear response de resumen para múltiples checkpoints.
        
        Args:
            checkpoints: Lista de checkpoints
            total_count: Total de checkpoints (si es diferente de len(checkpoints))
            
        Returns:
            Diccionario con resumen y lista de checkpoints
        """
        responses = BatchCheckpointMapper.map_list_to_responses(checkpoints)
        
        # Estadísticas
        status_counts = {}
        for checkpoint in checkpoints:
            status = CheckpointResponseMapper._safe_extract_value(checkpoint.status)
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "checkpoints": responses,
            "total_count": total_count or len(checkpoints),
            "returned_count": len(responses),
            "statistics": {
                "status_distribution": status_counts,
                "unique_tracking_ids": len(set(
                    CheckpointResponseMapper._safe_extract_value(cp.tracking_id) 
                    for cp in checkpoints
                ))
            }
        }


class ErrorResponseMapper:
    """Mapper para transformar errores de dominio a responses de API."""
    
    @staticmethod
    def from_domain_exception(exception: Exception) -> Dict[str, Any]:
        """
        Mapear excepción de dominio a response de error.
        
        Args:
            exception: Excepción a mapear
            
        Returns:
            Diccionario con información del error
        """
        if hasattr(exception, 'to_dict'):
            return exception.to_dict()
        
        return {
            "error_code": "UNKNOWN_ERROR",
            "message": str(exception),
            "exception_type": exception.__class__.__name__,
            "details": {}
        }
    
    @staticmethod
    def from_validation_errors(validation_errors: List[Any]) -> Dict[str, Any]:
        """
        Mapear errores de validación de Pydantic a response de error.
        
        Args:
            validation_errors: Lista de errores de Pydantic
            
        Returns:
            Diccionario con información consolidada de errores
        """
        formatted_errors = []
        
        for error in validation_errors:
            formatted_error = {
                "field": ".".join(str(loc) for loc in error.get('loc', [])),
                "message": error.get('msg', 'Validation error'),
                "type": error.get('type', 'validation_error'),
                "input": str(error.get('input', '')) if error.get('input') is not None else None
            }
            formatted_errors.append(formatted_error)
        
        return {
            "error_code": "VALIDATION_ERROR",
            "message": f"Validation failed for {len(formatted_errors)} field(s)",
            "validation_errors": formatted_errors,
            "details": {
                "error_count": len(formatted_errors),
                "failed_fields": [error["field"] for error in formatted_errors]
            }
        }


class MetadataMapper:
    """Mapper para transformar metadatos entre diferentes representaciones."""
    
    @staticmethod
    def normalize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalizar metadatos para consistencia.
        
        Args:
            metadata: Metadatos originales
            
        Returns:
            Metadatos normalizados
        """
        if not metadata:
            return {}
        
        normalized = {}
        
        for key, value in metadata.items():
            # Normalizar keys a snake_case
            normalized_key = MetadataMapper._to_snake_case(key)
            
            # Normalizar values
            if isinstance(value, str):
                normalized[normalized_key] = value.strip()
            elif isinstance(value, (int, float, bool)):
                normalized[normalized_key] = value
            elif isinstance(value, dict):
                normalized[normalized_key] = MetadataMapper.normalize_metadata(value)
            elif isinstance(value, list):
                normalized[normalized_key] = [
                    MetadataMapper.normalize_metadata(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                normalized[normalized_key] = str(value)
        
        return normalized
    
    @staticmethod
    def _to_snake_case(camel_str: str) -> str:
        """Convertir camelCase a snake_case."""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    @staticmethod
    def add_system_metadata(metadata: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agregar metadatos del sistema.
        
        Args:
            metadata: Metadatos originales
            user: Información del usuario
            
        Returns:
            Metadatos con información del sistema agregada
        """
        system_metadata = {
            "created_by_user": user.get("user_id"),
            "created_by_username": user.get("username"),
            "created_at_timestamp": datetime.utcnow().isoformat(),
            "user_agent": None,  # Se puede obtener del request
            "ip_address": None,  # Se puede obtener del request
            "system_version": "1.0"
        }
        
        # Combinar metadatos originales con metadatos del sistema
        combined = MetadataMapper.normalize_metadata(metadata or {})
        combined["_system"] = system_metadata
        
        return combined


class MapperFactory:
    """Factory para crear mappers configurados."""
    
    @staticmethod
    def create_request_mapper() -> CheckpointRequestMapper:
        """Crear mapper de requests."""
        return CheckpointRequestMapper()
    
    @staticmethod
    def create_response_mapper() -> CheckpointResponseMapper:
        """Crear mapper de responses."""
        return CheckpointResponseMapper()
    
    @staticmethod
    def create_batch_mapper() -> BatchCheckpointMapper:
        """Crear mapper para operaciones en lote."""
        return BatchCheckpointMapper()
    
    @staticmethod
    def create_error_mapper() -> ErrorResponseMapper:
        """Crear mapper de errores."""
        return ErrorResponseMapper()


# Funciones de conveniencia para uso directo
def map_request_to_use_case(api_request: CreateCheckpointRequest) -> UseCaseRequest:
    """Función de conveniencia para mapear request de API a use case."""
    return CheckpointRequestMapper.to_use_case_request(api_request)


def map_entity_to_response(checkpoint: Checkpoint) -> CheckpointResponse:
    """Función de conveniencia para mapear entidad a response de API."""
    return CheckpointResponseMapper.from_domain_entity(checkpoint)


def map_use_case_to_response(use_case_response: UseCaseResponse) -> CheckpointResponse:
    """Función de conveniencia para mapear response de use case a API."""
    return CheckpointResponseMapper.from_use_case_response(use_case_response)


def enrich_metadata_with_user_info(
    metadata: Dict[str, Any], 
    user: Dict[str, Any]
) -> Dict[str, Any]:
    """Función de conveniencia para enriquecer metadatos con información del usuario."""
    return MetadataMapper.add_system_metadata(metadata, user)