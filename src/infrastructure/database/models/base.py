from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class BaseTable(SQLModel):
    """Base model con campos comunes"""
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow, index=True)