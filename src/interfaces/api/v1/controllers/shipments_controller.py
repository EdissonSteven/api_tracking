from fastapi import APIRouter, Depends, HTTPException, status as http_status, Query
from typing import List
import logging

from ..schemas.tracking_schemas import UnitsListResponse, UnitResponse
from ..schemas.checkpoint_schemas import UnitStatusEnum
from ..schemas.error_schemas import ErrorResponse
from ..dependencies import (
    get_list_units_use_case,
    require_permissions
)
from .....application.use_cases.list_units_by_status_use_case import ListUnitsByStatusUseCase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/shipments", tags=["shipments"])

@router.get(
    "",
    response_model=UnitsListResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid status"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    summary="List Units by Status",
    description="Retrieve a paginated list of units filtered by status with authentication and authorization.",
    operation_id="list_units_by_status"
)
async def list_units_by_status(
    status: UnitStatusEnum = Query(..., description="Filter by unit status", alias="status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    list_units_use_case: ListUnitsByStatusUseCase = Depends(get_list_units_use_case),
    current_user: dict = Depends(require_permissions(["units:read"]))
) -> UnitsListResponse:
    """
    List units by status with pagination.
    
    Requires authentication and 'units:read' permission.
    """
    
    try:
        logger.info(
            f"Listing units - status={status.value}, limit={limit}, "
            f"offset={offset}, user={current_user.get('user_id')}"
        )
        
        # Ejecuta use case
        unit_dtos, total_count = list_units_use_case.execute(status.value, limit, offset)
        
        # Mapear DTOs → Schemas API
        unit_responses = []
        for dto in unit_dtos:
            unit_responses.append(UnitResponse(
                tracking_id=dto.tracking_id,
                current_status=UnitStatusEnum(dto.status),
                created_at=dto.created_at,
                updated_at=dto.updated_at,
                guide_id=dto.guide_id,
                weight_kg=dto.weight_kg,
                dimensions=dto.dimensions,
                origin=dto.origin,
                destination=dto.destination
            ))
        
        logger.info(f"Found {len(unit_responses)} units for status {status.value}")
        
        return UnitsListResponse(
            units=unit_responses,
            total=total_count,
            limit=limit,
            offset=offset
        )
        
    except ValueError as e:
        logger.warning(f"Validation error listing units: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error listing units: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error listing units"
        )