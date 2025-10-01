import logging
from typing import Optional
from datetime import datetime

from ...application.mappers import CheckpointResponseMapper
from ...application.dtos.checkpoint_dto import CreateCheckpointRequest, CheckpointResponse
from ...domain.entities.checkpoint import Checkpoint
from ...domain.value_objects.tracking_id import TrackingId
from ...domain.value_objects.unit_status import UnitStatus
from ...domain.repositories.checkpoint_repository import CheckpointRepository
from ...domain.repositories.unit_repository import UnitRepository
from ...domain.services.domain_services import CheckpointValidationService
from ...domain.domain_events import (
    DomainEventDispatcher,
    CheckpointCreatedEvent,
    CheckpointValidationFailedEvent
)
from ...domain.domain_exceptions import (
    DomainValidationError,
    BusinessRuleViolationError,
    UnitNotFoundError
)
from ..result import (
    Result,
    Success,
    Failure
)

logger = logging.getLogger(__name__)


class CreateCheckpointUseCase:
    """Use case para crear checkpoints siguiendo Clean Architecture y DDD."""
    
    def __init__(
        self,
        checkpoint_repo: CheckpointRepository,
        unit_repo: UnitRepository,
        validation_service: CheckpointValidationService,
        event_dispatcher: DomainEventDispatcher = None,
        response_mapper: CheckpointResponseMapper = None
    ):
        self._checkpoint_repo = checkpoint_repo
        self._unit_repo = unit_repo
        self._validation_service = validation_service
        self._event_dispatcher = event_dispatcher
        self._response_mapper = response_mapper or CheckpointResponseMapper()
        
        logger.debug("CreateCheckpointUseCase initialized")
    
    def execute(self, request: CreateCheckpointRequest) -> CheckpointResponse:  
        """Ejecutar el caso de uso de creación de checkpoint."""
        
        operation_start = datetime.utcnow()
        
        try:
            logger.info(f"Starting checkpoint creation for {request.tracking_id}")
            
            # Step 1: Input Validation and Transformation
            validation_result = self._validate_and_transform_input(request)  
            if validation_result.is_failure():
                error = validation_result.error
                self._dispatch_validation_failed_event(request, str(error))  
                raise error
            
            tracking_id, status = validation_result.unwrap()
            
            # Step 2: Business Rules Validation
            business_rules_result = self._validate_business_rules(  
                tracking_id, status, request.timestamp
            )
            if business_rules_result.is_failure():
                error = business_rules_result.error
                self._dispatch_validation_failed_event(request, str(error))  
                raise error
            
            # Step 3: Idempotency Check
            idempotency_result = self._check_idempotency(tracking_id, status)  
            if idempotency_result.is_success():
                existing_checkpoint = idempotency_result.unwrap()
                if existing_checkpoint:
                    logger.info(f"Returning existing checkpoint (idempotent): {existing_checkpoint.id}")
                    return CheckpointResponseMapper.from_domain_entity(existing_checkpoint)
            
            # Step 4: Create Domain Entity
            entity_creation_result = self._create_checkpoint_entity(  
                tracking_id, status, request
            )
            if entity_creation_result.is_failure():
                raise entity_creation_result.error
            
            checkpoint = entity_creation_result.unwrap()
            
            # Step 5: Persist Checkpoint
            persistence_result = self._persist_checkpoint(checkpoint)  
            if persistence_result.is_failure():
                raise persistence_result.error
            
            saved_checkpoint = persistence_result.unwrap()
            
            # Step 6: Update Unit Status (if needed)
            unit_update_result = self._update_unit_status(tracking_id, status)  
            if unit_update_result.is_failure():
                logger.warning(f"Failed to update unit status: {unit_update_result.error}")
            
            # Step 7: Dispatch Success Events
            self._dispatch_success_events(saved_checkpoint, request)  
            
            # Step 8: Build Response
            response = CheckpointResponseMapper.from_domain_entity(saved_checkpoint)
            
            operation_duration = (datetime.utcnow() - operation_start).total_seconds() * 1000
            logger.info(
                f"Checkpoint created successfully: {saved_checkpoint.id} "
                f"for {request.tracking_id} in {operation_duration:.2f}ms"
            )
            
            return response
            
        except (DomainValidationError, BusinessRuleViolationError, UnitNotFoundError) as e:
            logger.warning(f"Domain error creating checkpoint: {str(e)}")
            raise e
            
        except Exception as e:
            operation_duration = (datetime.utcnow() - operation_start).total_seconds() * 1000
            logger.error(
                f"Unexpected error creating checkpoint for {request.tracking_id} "
                f"after {operation_duration:.2f}ms: {str(e)}",
                exc_info=True
            )
            raise Exception(f"Internal error creating checkpoint: {str(e)}")
    
    def _validate_and_transform_input(  
        self, 
        request: CreateCheckpointRequest
    ) -> Result[tuple[TrackingId, UnitStatus], DomainValidationError]:
        """Validar y transformar entrada a value objects de dominio."""
        try:
            tracking_id = TrackingId(request.tracking_id)
            status = UnitStatus(request.status)
            
            logger.debug(f"Input validation successful for {request.tracking_id}")
            return Success((tracking_id, status))
            
        except Exception as e:
            error = DomainValidationError(
                message=f"Invalid input data: {str(e)}",
                details={
                    "tracking_id": request.tracking_id,
                    "status": request.status,
                    "original_error": str(e)
                }
            )
            return Failure(error)
    
    def _validate_business_rules(  
        self, 
        tracking_id: TrackingId, 
        status: UnitStatus, 
        timestamp: Optional[datetime]
    ) -> Result[bool, BusinessRuleViolationError]:
        """Validar reglas de negocio usando el servicio de dominio."""
        try:
            self._validation_service.validate_checkpoint_creation(  
                tracking_id, status, timestamp
            )
            
            logger.debug(f"Business rules validation successful for {tracking_id.value}")
            return Success(True)
            
        except Exception as e:
            if isinstance(e, (DomainValidationError, BusinessRuleViolationError)):
                return Failure(e)
            
            error = BusinessRuleViolationError(
                message=f"Business rule validation failed: {str(e)}",
                rule_name="general_validation",
                context={
                    "tracking_id": str(tracking_id.value),
                    "status": str(status.value),
                    "original_error": str(e)
                }
            )
            return Failure(error)
    
    def _check_idempotency(  
        self, 
        tracking_id: TrackingId, 
        status: UnitStatus
    ) -> Result[Optional[Checkpoint], Exception]:
        """Verificar idempotencia y retornar checkpoint existente si aplica."""
        try:
            is_idempotent = self._validation_service.ensure_idempotency(  
                tracking_id, status
            )
            
            if is_idempotent:
                existing_checkpoint = self._checkpoint_repo.get_latest_by_tracking_id(  
                    tracking_id
                )
                logger.info(f"Idempotent checkpoint found for {tracking_id.value}")
                return Success(existing_checkpoint)
            
            return Success(None)
            
        except Exception as e:
            logger.warning(f"Error checking idempotency: {str(e)}")
            return Success(None)
    
    def _create_checkpoint_entity(  
        self, 
        tracking_id: TrackingId, 
        status: UnitStatus, 
        request: CreateCheckpointRequest
    ) -> Result[Checkpoint, DomainValidationError]:
        """Crear entidad de dominio Checkpoint."""
        try:
            checkpoint = Checkpoint.create(
                tracking_id=tracking_id,
                status=status,
                timestamp=request.timestamp,
                location=request.location,
                description=request.description,
                operator=request.operator,
                meta_data=request.meta_data,
                coordinates=request.coordinates
            )
            
            if not checkpoint.is_valid():
                raise DomainValidationError(
                    message="Created checkpoint entity is invalid",
                    details={"checkpoint_id": checkpoint.id}
                )
            
            logger.debug(f"Checkpoint entity created: {checkpoint.id}")
            return Success(checkpoint)
            
        except Exception as e:
            error = DomainValidationError(
                message=f"Failed to create checkpoint entity: {str(e)}",
                details={"original_error": str(e)}
            )
            return Failure(error)
    
    def _persist_checkpoint(  
        self, 
        checkpoint: Checkpoint
    ) -> Result[Checkpoint, Exception]:
        """Persistir checkpoint en el repositorio."""
        try:
            saved_checkpoint = self._checkpoint_repo.save(checkpoint)  
            
            logger.debug(f"Checkpoint persisted: {saved_checkpoint.id}")
            return Success(saved_checkpoint)
            
        except Exception as e:
            logger.error(f"Error persisting checkpoint: {str(e)}")
            return Failure(e)
    
    def _update_unit_status(  
        self, 
        tracking_id: TrackingId, 
        status: UnitStatus
    ) -> Result[bool, Exception]:
        """Actualizar estado de la unidad."""
        try:
            self._unit_repo.update_status(tracking_id, status)  
            logger.debug(f"Unit status updated for {tracking_id.value}")
            return Success(True)
            
        except Exception as e:
            logger.warning(f"Failed to update unit status: {str(e)}")
            return Failure(e)
    
    def _dispatch_success_events(  
        self, 
        checkpoint: Checkpoint, 
        request: CreateCheckpointRequest
    ):
        """Disparar eventos de dominio para checkpoint creado exitosamente."""
        if not self._event_dispatcher:
            return
        
        try:
            event = CheckpointCreatedEvent(
                checkpoint_id=checkpoint.id,
                tracking_id=checkpoint.tracking_id,
                status=checkpoint.status,
                created_by=request.operator or "system",
                location=checkpoint.location,
                operator=checkpoint.operator
            )
            
            self._event_dispatcher.dispatch(event)
            logger.debug(f"Success events dispatched for checkpoint {checkpoint.id}")
            
        except Exception as e:
            logger.error(f"Error dispatching success events: {str(e)}")
    
    def _dispatch_validation_failed_event(  
        self, 
        request: CreateCheckpointRequest, 
        error_reason: str
    ):
        """Disparar evento de validación fallida."""
        if not self._event_dispatcher:
            return
        
        try:
            event = CheckpointValidationFailedEvent(
                tracking_id=request.tracking_id,
                status=request.status,
                error_reason=error_reason,
                attempted_by=request.operator or "unknown"
            )
            
            self._event_dispatcher.dispatch(event)
            
        except Exception as e:
            logger.error(f"Error dispatching validation failed event: {str(e)}")