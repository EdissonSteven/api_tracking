from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Dict, Any
import logging

from ..schemas.checkpoint_schemas import CreateCheckpointRequest, CheckpointResponse, UnitStatusEnum
from ..schemas.error_schemas import ErrorResponse, ValidationErrorResponse, BusinessErrorResponse
from ..dependencies import (
    get_create_checkpoint_use_case,
    require_permissions,
    get_rate_limiter,
    get_request_id
)
from .....application.use_cases.create_checkpoint_use_case import CreateCheckpointUseCase
from .....application.dtos.checkpoint_dto import CreateCheckpointRequest as UseCaseRequest
from .....infrastructure.security.auth_service import AuthService
from .....infrastructure.security.rate_limiter import RateLimitManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/checkpoints", tags=["checkpoints"])
security = HTTPBearer()

@router.post(
    "",
    response_model=CheckpointResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ValidationErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        409: {"model": BusinessErrorResponse},
        429: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Create Checkpoint",
    description="Register a new checkpoint for a unit. Implements idempotency based on tracking_id + status."
)
async def create_checkpoint(
    request: CreateCheckpointRequest,
    http_request: Request,
    background_tasks: BackgroundTasks,
    create_checkpoint_use_case: CreateCheckpointUseCase = Depends(get_create_checkpoint_use_case),
    rate_limiter: RateLimitManager = Depends(get_rate_limiter),
    request_id: str = Depends(get_request_id),
    current_user: Dict[str, Any] = Depends(require_permissions(["checkpoint:create"]))
) -> CheckpointResponse:
    """Create a new checkpoint"""
    
    try:
        # Rate limiting
        await rate_limiter.check_rate_limit(
            http_request, 
            "checkpoint_creation"
        )
        
        # Execute use case
        use_case_request = UseCaseRequest(
            tracking_id=request.tracking_id,
            status=request.status.value,
            timestamp=request.timestamp,
            location=request.location,
            description=request.description,
            operator=request.operator,
            meta_data=request.meta_data
        )
        
        result = await create_checkpoint_use_case.execute(use_case_request)
        
        # Log success (background task)
        background_tasks.add_task(
            log_checkpoint_creation,
            request_id,
            request.tracking_id,
            request.status.value
        )
        
        return CheckpointResponse(
            id=result.id,
            tracking_id=result.tracking_id,
            status=UnitStatusEnum(result.status),
            timestamp=result.timestamp,
            location=result.location,
            description=result.description,
            operator=result.operator,
            meta_data=result.meta_data,
            created_at=result.created_at
        )
        
    except ValueError as e:
        logger.warning(f"Validation error in create_checkpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in create_checkpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


async def log_checkpoint_creation(
    request_id: str,
    tracking_id: str,
    status: str,
    user_id: str
):
    """Background task to log checkpoint creation"""
    logger.info(
        "Checkpoint created",
        extra={
            "request_id": request_id,
            "tracking_id": tracking_id,
            "status": status,
            "user_id": user_id,
            "event": "checkpoint_created"
        }
    )
