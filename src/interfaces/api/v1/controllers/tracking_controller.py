import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Path

from ..schemas.tracking_schemas import TrackingResponse, UnitResponse
from ..schemas.checkpoint_schemas import CheckpointResponse, UnitStatusEnum
from ..schemas.error_schemas import ErrorResponse, NotFoundErrorResponse
from ..dependencies import (
    get_tracking_use_case,
    require_permissions
)
# Use Cases
from .....application.use_cases.get_tracking_use_case import GetTrackingUseCase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tracking", tags=["tracking"])


@router.get(
    "/{tracking_id}",
    response_model=TrackingResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Authentication Error"},
        404: {"model": NotFoundErrorResponse, "description": "Tracking Not Found"},
        429: {"model": ErrorResponse, "description": "Rate Limit Exceeded"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    summary="Get Tracking Information",
    description="Retrieve complete tracking history for a unit by tracking ID.",
    operation_id="get_tracking"
)
async def get_tracking(
    tracking_id: str = Path(..., description="Unit tracking identifier"),
    use_case: GetTrackingUseCase = Depends(get_tracking_use_case),
    current_user: Dict[str, Any] = Depends(require_permissions(["tracking:read"]))
) -> TrackingResponse:
    """
    Get complete tracking information by tracking ID.
    
    Returns tracking history with all checkpoints and unit information.
    """
    
    try:
        logger.info(
            f"Getting tracking information - "
            f"tracking_id={tracking_id}, "
            f"user_id={current_user.get('user_id')}"
        )
        
        # Ejecuta use case
        result = use_case.execute(tracking_id)
        
        if not result:
            logger.warning(f"Tracking not found - tracking_id={tracking_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tracking information not found for ID: {tracking_id}"
            )
        
        # Transform response
        response = TrackingResponse(
            tracking_id=result.tracking_id,
            current_status=UnitStatusEnum(result.unit.status),
            checkpoints=[
                CheckpointResponse(
                    id=cp.id,
                    tracking_id=cp.tracking_id,
                    status=UnitStatusEnum(cp.status),
                    timestamp=cp.timestamp,
                    location=cp.location,
                    description=cp.description,
                    operator=cp.operator,
                    meta_data=cp.meta_data or {},
                    coordinates=cp.coordinates or {},
                    created_at=cp.created_at,
                    updated_at=cp.updated_at
                )
                for cp in result.checkpoints
            ],
            unit_info=UnitResponse(
                tracking_id=result.unit.tracking_id,
                current_status=UnitStatusEnum(result.unit.status),
                created_at=result.unit.created_at,
                updated_at=result.unit.updated_at,
                guide_id=getattr(result.unit, 'guide_id', None),
                weight_kg=getattr(result.unit, 'weight_kg', None),
                dimensions=getattr(result.unit, 'dimensions', None),
                origin=result.unit.origin if result.unit.origin else "unknown",
                destination=result.unit.destination if result.unit.destination else "unknown"
            )
        )
        
        logger.info(
            f"Tracking retrieved successfully - "
            f"tracking_id={tracking_id}, "
            f"checkpoints_count={len(result.checkpoints)}"
        )
        
        return response
        
    except HTTPException:
        raise
        
    except ValueError as e:
        logger.warning(f"Validation error in get_tracking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except Exception as e:
        logger.error(
            f"Unexpected error in get_tracking - "
            f"tracking_id={tracking_id}, "
            f"error={str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/health",
    response_model=Dict[str, Any],
    summary="Tracking Service Health Check",
    operation_id="tracking_health_check"
)
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for the tracking service."""
    
    return {
        "status": "healthy",
        "service": "tracking-service",
        "version": "1.0.0"
    }