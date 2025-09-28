from application.dtos.checkpoint_dto import CheckpointResponse
from application.dtos.tracking_dto import UnitResponse
from fastapi import APIRouter, Depends, HTTPException, status, Request, Path
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Dict, Any
import logging

from interfaces.api.v1.schemas.checkpoint_schemas import UnitStatusEnum

from ..schemas.tracking_schemas import TrackingResponse
from ..schemas.error_schemas import ErrorResponse, NotFoundErrorResponse
from ..dependencies import (
    get_tracking_use_case,
    get_auth_service,
    get_rate_limiter,
    get_request_id,
    require_permissions
)
from .....application.use_cases.get_tracking_use_case import GetTrackingUseCase
from .....infrastructure.security.auth_service import AuthService
from .....infrastructure.security.rate_limiter import RateLimitManager
security = HTTPBearer()

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tracking", tags=["tracking"])


@router.get(
    "/{tracking_id}",
    response_model=TrackingResponse,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": NotFoundErrorResponse},
        429: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Get Tracking Information",
    description="Retrieve complete tracking history for a unit by tracking ID."
)
async def get_tracking(
    tracking_id: str = Path(..., description="Unit tracking identifier"),
    get_tracking_use_case: GetTrackingUseCase = Depends(get_tracking_use_case),
    rate_limiter: RateLimitManager = Depends(get_rate_limiter),
    current_user: Dict[str, Any] = Depends(require_permissions(["checkpoint:create"]))
) -> TrackingResponse:
    """Get tracking information by tracking ID"""
    
    try:
        
        # Rate limiting
        #await rate_limiter.check_rate_limit(
        #    http_request, 
        #    "checkpoint_creation"
        #)
        
        # Execute use case
        result = await get_tracking_use_case.execute(tracking_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tracking information not found for ID: {tracking_id}"
            )
        
        return TrackingResponse(
            tracking_id=result.tracking_id,
            current_status=UnitStatusEnum(result.current_status),
            checkpoints=[
                CheckpointResponse(
                    id=cp.id,
                    tracking_id=cp.tracking_id,
                    status=UnitStatusEnum(cp.status),
                    timestamp=cp.timestamp,
                    location=cp.location,
                    description=cp.description,
                    operator=cp.operator,
                    meta_data=cp.meta_data,
                    created_at=cp.created_at
                )
                for cp in result.checkpoints
            ],
            unit_info=UnitResponse(
                tracking_id=result.unit_info.tracking_id,
                current_status=UnitStatusEnum(result.unit_info.current_status),
                created_at=result.unit_info.created_at,
                updated_at=result.unit_info.updated_at,
                guide_id=result.unit_info.guide_id,
                weight=result.unit_info.weight,
                dimensions=result.unit_info.dimensions,
                origin=result.unit_info.origin,
                destination=result.unit_info.destination
            ) if result.unit_info else None
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Validation error in get_tracking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_tracking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )