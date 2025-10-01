"""
Controlador de Checkpoints siguiendo Clean Architecture, DDD y SOLID.

Este controlador implementa:
- Single Responsibility Principle: Solo orquesta, no contiene lógica de negocio
- Open/Closed Principle: Extensible vía validators y mappers
- Dependency Inversion: Todas las dependencias inyectadas
- Clean Architecture: Separación clara de capas
- Domain-Driven Design: Eventos de dominio y excepciones específicas
"""

import time
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.responses import JSONResponse

from ..schemas.checkpoint_schemas import CreateCheckpointRequest, CheckpointResponse
from ..schemas.error_schemas import ErrorResponse, ValidationErrorResponse, BusinessErrorResponse
from ..dependencies import (
    get_create_checkpoint_use_case,
    require_permissions,
    get_request_id,
    get_validator_service,
    get_event_dispatcher,
    get_request_mapper,
    get_response_mapper
)

# Use Cases
from .....application.use_cases.create_checkpoint_use_case import CreateCheckpointUseCase

# Domain Components
from .....domain.domain_events import (
    CheckpointCreatedEvent, 
    DomainEventDispatcher
)
from .....domain.domain_exceptions import (
    DomainValidationError,
    BusinessRuleViolationError,
    AuthenticationError,
    AuthorizationError,
    get_http_status_for_exception
)

# Application Components
from .....application.validators import ValidationService
from .....application.mappers import (
    CheckpointRequestMapper,
    CheckpointResponseMapper,
    ErrorResponseMapper
)

router = APIRouter(prefix="/checkpoints", tags=["checkpoints"])
logger = logging.getLogger(__name__)


@router.post(
    "",
    response_model=CheckpointResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Validation Error"},
        401: {"model": ErrorResponse, "description": "Authentication Error"},
        403: {"model": ErrorResponse, "description": "Authorization Error"},
        409: {"model": BusinessErrorResponse, "description": "Business Rule Violation"},
        422: {"model": ErrorResponse, "description": "Business Logic Error"},
        429: {"model": ErrorResponse, "description": "Rate Limit Exceeded"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    summary="Create Checkpoint",
    description="""
    Create a new checkpoint for a tracking unit.
    
    This endpoint implements:
    - Comprehensive validation chain
    - Idempotency based on tracking_id + status
    - Domain events for observability
    - Structured error handling
    """,
    operation_id="create_checkpoint"
)
async def create_checkpoint(
    request: CreateCheckpointRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
    current_user: Dict[str, Any] = Depends(require_permissions(["checkpoint:create"])),
    use_case: CreateCheckpointUseCase = Depends(get_create_checkpoint_use_case),
    validator_service: ValidationService = Depends(get_validator_service),
    event_dispatcher: DomainEventDispatcher = Depends(get_event_dispatcher),
    request_mapper: CheckpointRequestMapper = Depends(get_request_mapper),
    response_mapper: CheckpointResponseMapper = Depends(get_response_mapper),
    request_id: str = Depends(get_request_id)
) -> CheckpointResponse:
    """
    Create a new checkpoint with comprehensive validation and monitoring.
    
    This method follows Clean Architecture principles:
    1. Input validation and transformation
    2. Business logic execution via use case
    3. Output transformation
    4. Cross-cutting concerns (logging, events)
    """
    
    try:
        # Log request initiation
        logger.info(
            f"Checkpoint creation initiated - "
            f"request_id={request_id}, "
            f"tracking_id={request.tracking_id}, "
            f"status={request.status.value}, "
            f"user_id={current_user.get('user_id')}"
        )
        
        # Step 1: Request Validation (Chain of Responsibility)
        validation_start = time.time()
        validation_result = validator_service.validate_request(request, current_user)  # ⬅️ SIN await
        validation_duration = (time.time() - validation_start) * 1000
        
        if validation_result.is_failure():
            validation_errors = validation_result.error
            logger.warning(
                f"Checkpoint validation failed - "
                f"request_id={request_id}, "
                f"tracking_id={request.tracking_id}, "
                f"errors={len(validation_errors)}"
            )
            
            return _handle_validation_error(
                validation_errors, request_id, background_tasks
            )
        
        logger.debug(
            f"Checkpoint validation passed - "
            f"request_id={request_id}, "
            f"duration={validation_duration:.2f}ms"
        )
        
        # Step 2: Transform Request (Single Responsibility)
        transform_start = time.time()
        use_case_request = request_mapper.to_use_case_request(request)
        transform_duration = (time.time() - transform_start) * 1000
        
        # Step 3: Execute Business Logic (Dependency Inversion)
        business_logic_start = time.time()
        use_case_result = use_case.execute(use_case_request)  # ⬅️ SIN await
        business_logic_duration = (time.time() - business_logic_start) * 1000
        
        # Step 4: Transform Response (Single Responsibility)
        response_start = time.time()
        api_response = response_mapper.from_use_case_response(use_case_result)
        response_duration = (time.time() - response_start) * 1000
        
        # Step 5: Domain Events (Domain-Driven Design)
        _dispatch_success_events(
            api_response,
            current_user,
            event_dispatcher,
            background_tasks
        )
        
        # Step 6: Success Logging
        total_duration = (
            validation_duration + 
            transform_duration + 
            business_logic_duration + 
            response_duration
        )
        
        logger.info(
            f"Checkpoint created successfully - "
            f"request_id={request_id}, "
            f"checkpoint_id={api_response.id}, "
            f"tracking_id={api_response.tracking_id}, "
            f"total_duration={total_duration:.2f}ms"
        )
        
        # Background task for analytics
        background_tasks.add_task(
            _log_checkpoint_analytics,
            request_id=request_id,
            checkpoint_data=api_response.dict(),
            user_data=current_user,
            performance_metrics={
                "total_duration_ms": total_duration,
                "validation_duration_ms": validation_duration,
                "business_logic_duration_ms": business_logic_duration
            }
        )
        
        return api_response
        
    except DomainValidationError as e:
        return _handle_domain_validation_error(e, request_id)
        
    except BusinessRuleViolationError as e:
        return _handle_business_rule_error(e, request_id)
        
    except (AuthenticationError, AuthorizationError) as e:
        return _handle_auth_error(e, request_id)
        
    except Exception as e:
        return _handle_unexpected_error(e, request_id)


def _handle_validation_error(  # ⬅️ SIN async
    validation_errors: List[DomainValidationError],
    request_id: str,
    background_tasks: BackgroundTasks
) -> JSONResponse:
    """Handle validation errors with appropriate HTTP status."""
    
    # Convert domain validation errors to API response format
    formatted_errors = []
    for error in validation_errors:
        formatted_errors.append(error.to_dict())
    
    response_data = {
        "error": True,
        "message": f"Validation failed: {len(validation_errors)} error(s)",
        "validation_errors": formatted_errors,
        "request_id": request_id,
        "timestamp": time.time()
    }
    
    # Background task to track validation failures
    background_tasks.add_task(
        _track_validation_failure,
        validation_errors=formatted_errors,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=response_data
    )


def _handle_domain_validation_error(  # ⬅️ SIN async
    error: DomainValidationError,
    request_id: str
) -> JSONResponse:
    """Handle domain validation errors."""
    
    logger.warning(
        f"Domain validation error - "
        f"request_id={request_id}, "
        f"error_code={error.error_code}, "
        f"message={error.message}"
    )
    
    return JSONResponse(
        status_code=get_http_status_for_exception(error),
        content={
            "error": True,
            "error_code": error.error_code,
            "message": error.message,
            "details": error.details,
            "request_id": request_id
        }
    )


def _handle_business_rule_error(  # ⬅️ SIN async
    error: BusinessRuleViolationError,
    request_id: str
) -> JSONResponse:
    """Handle business rule violations."""
    
    logger.warning(
        f"Business rule violation - "
        f"request_id={request_id}, "
        f"error_code={error.error_code}, "
        f"rule={getattr(error, 'rule_name', 'unknown')}"
    )
    
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": True,
            "error_code": error.error_code,
            "message": error.message,
            "rule_violation": getattr(error, 'rule_name', 'unknown'),
            "details": error.details,
            "request_id": request_id
        }
    )


def _handle_auth_error(  # ⬅️ SIN async
    error: Exception,
    request_id: str
) -> JSONResponse:
    """Handle authentication/authorization errors."""
    
    logger.warning(
        f"Authentication/Authorization error - "
        f"request_id={request_id}, "
        f"error_type={error.__class__.__name__}"
    )
    
    http_status = get_http_status_for_exception(error)
    
    return JSONResponse(
        status_code=http_status,
        content={
            "error": True,
            "error_code": getattr(error, 'error_code', 'AUTH_ERROR'),
            "message": str(error),
            "request_id": request_id
        }
    )


def _handle_unexpected_error(  # ⬅️ SIN async
    error: Exception,
    request_id: str
) -> JSONResponse:
    """Handle unexpected errors with proper logging."""
    
    logger.error(
        f"Unexpected error in checkpoint creation - "
        f"request_id={request_id}, "
        f"error_type={error.__class__.__name__}, "
        f"error={str(error)}",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "error_code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "request_id": request_id
        }
    )


def _dispatch_success_events(  # ⬅️ SIN async
    response: CheckpointResponse,
    user: Dict[str, Any],
    event_dispatcher: DomainEventDispatcher,
    background_tasks: BackgroundTasks
):
    """Dispatch domain events for successful checkpoint creation."""
    
    # Create domain event
    event = CheckpointCreatedEvent(
        checkpoint_id=response.id,
        tracking_id=response.tracking_id,
        status=response.status.value,
        created_by=user.get("user_id", "unknown"),
        location=response.location,
        operator=response.operator
    )
    
    # Dispatch event in background to not block response
    background_tasks.add_task(
        _dispatch_event_async,
        event_dispatcher=event_dispatcher,
        event=event
    )


def _dispatch_event_async(  # ⬅️ SIN async
    event_dispatcher: DomainEventDispatcher, 
    event
):
    """Event dispatch for background tasks."""
    try:
        event_dispatcher.dispatch(event)
    except Exception as e:
        logger.error(f"Error dispatching event {event.event_name()}: {str(e)}")


def _log_checkpoint_analytics(  # ⬅️ SIN async
    request_id: str,
    checkpoint_data: Dict[str, Any],
    user_data: Dict[str, Any],
    performance_metrics: Dict[str, float]
):
    """Background task for detailed analytics logging."""
    
    analytics_data = {
        "event_type": "checkpoint_created",
        "request_id": request_id,
        "checkpoint": {
            "id": checkpoint_data.get("id"),
            "tracking_id": checkpoint_data.get("tracking_id"),
            "status": checkpoint_data.get("status"),
            "location": checkpoint_data.get("location"),
            "has_metadata": bool(checkpoint_data.get("metadata"))
        },
        "user": {
            "user_id": user_data.get("user_id"),
            "roles": user_data.get("roles", []),
            "is_superuser": user_data.get("is_superuser", False)
        },
        "performance": performance_metrics,
        "timestamp": time.time()
    }
    
    analytics_logger = logging.getLogger("analytics")
    analytics_logger.info(f"Checkpoint analytics: {analytics_data}")


def _track_validation_failure(  # ⬅️ SIN async
    validation_errors: List[Dict[str, Any]],
    request_id: str
):
    """Background task to track validation failures for improvement."""
    
    failure_data = {
        "event_type": "validation_failure",
        "request_id": request_id,
        "error_count": len(validation_errors),
        "error_types": [error.get("error_code") for error in validation_errors],
        "failed_fields": [error.get("field") for error in validation_errors if error.get("field")],
        "timestamp": time.time()
    }
    
    monitoring_logger = logging.getLogger("monitoring")
    monitoring_logger.warning(f"Validation failure tracked: {failure_data}")


@router.get(
    "/health",
    response_model=Dict[str, Any],
    summary="Health Check",
    description="Check the health status of the checkpoint service",
    operation_id="checkpoint_health_check"
)
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for the checkpoint service."""
    
    return {
        "status": "healthy",
        "service": "checkpoint-service",
        "version": "1.0.0",
        "timestamp": time.time()
    }