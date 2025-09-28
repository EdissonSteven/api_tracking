from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import List
import logging

from ..schemas.tracking_schemas import UnitsListResponse, UnitResponse
from ..schemas.checkpoint_schemas import UnitStatusEnum
from ..schemas.error_schemas import ErrorResponse
from ..dependencies import (
    get_list_units_use_case,
    get_auth_service,
    get_rate_limiter,
    get_request_id
)
from .....application.use_cases.list_units_by_status_use_case import ListUnitsByStatusUseCase
from .....infrastructure.security.auth_service import AuthService
from .....infrastructure.security.rate_limiter import RateLimitManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/shipments", tags=["shipments"])
security = HTTPBearer()

@router.get(
    "",
    response_model=UnitsListResponse,
    responses={
        401: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="List Units by Status",
    description="Retrieve a paginated list of units filtered by status."
)
async def list_units_by_status(
    status: UnitStatusEnum = Query(..., description="Filter by unit status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    request: Request = None,
    list_units_use_case: ListUnitsByStatusUseCase = Depends(get_list_units_use_case),
    auth_service: AuthService = Depends(get_auth_service),
    rate_limiter: RateLimitManager = Depends(get_rate_limiter),
    request_id: str = Depends(get_request_id),
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UnitsListResponse:
    """List units by status with pagination"""
    
    try:
        # Authentication
        token_data = await auth_service.authenticate_token(credentials)
        
        # Check permissions
        if not auth_service.check_permissions(token_data, ["units:read"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Rate limiting
        await rate_limiter.check_rate_limit(
            request, 
            "unit_listing",
            token_data.sub
        )
        
        # Execute use case
        units = await list_units_use_case.execute(status.value, limit, offset)
        
        return UnitsListResponse(
            units=[
                UnitResponse(
                    tracking_id=unit.tracking_id,
                    current_status=UnitStatusEnum(unit.current_status),
                    created_at=unit.created_at,
                    updated_at=unit.updated_at,
                    guide_id=unit.guide_id,
                    weight=unit.weight,
                    dimensions=unit.dimensions,
                    origin=unit.origin,
                    destination=unit.destination
                )
                for unit in units
            ],
            total=len(units),  # In a real implementation, you'd get total count separately
            limit=limit,
            offset=offset
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Validation error in list_units_by_status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in list_units_by_status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )