from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from .checkpoint_schemas import CheckpointResponse, UnitStatusEnum


class UnitResponse(BaseModel):
    tracking_id: str = Field(..., description="Unit tracking identifier")
    current_status: UnitStatusEnum = Field(..., description="Current unit status")
    created_at: datetime = Field(..., description="Unit creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    guide_id: Optional[str] = Field(None, description="Guide identifier")
    weight_kg: Optional[float] = Field(None, description="Package weight")
    dimensions: Optional[str] = Field(None, description="Package dimensions")
    origin: Optional[str] = Field(None, description="Origin location")
    destination: Optional[str] = Field(None, description="Destination location")


class TrackingResponse(BaseModel):
    tracking_id: str = Field(..., description="Tracking identifier")
    current_status: UnitStatusEnum = Field(..., description="Current status")
    checkpoints: List[CheckpointResponse] = Field(..., description="Checkpoint history")
    unit_info: Optional[UnitResponse] = Field(None, description="Unit information")


class UnitsListResponse(BaseModel):
    units: List[UnitResponse] = Field(..., description="List of units")
    total: int = Field(..., description="Total number of units")
    limit: int = Field(..., description="Limit used for pagination")
    offset: int = Field(..., description="Offset used for pagination")