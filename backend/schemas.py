from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
from typing import Optional, List
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobCreate(BaseModel):
    aoi_name: str = Field(..., min_length=3, max_length=100, description="Name for the AOI")
    aoi_wkt: str = Field(..., min_length=10, max_length=100000, description="WKT string of the AOI polygon")
    t1_start: datetime
    t1_end: datetime
    t2_start: datetime
    t2_end: datetime

    @field_validator('aoi_wkt')
    def validate_wkt(cls, v):
        from .security import sanitize_wkt
        return sanitize_wkt(v)

    @field_validator('t1_end')
    def validate_t1_range(cls, v, info):
        if 't1_start' in info.data and v <= info.data['t1_start']:
            raise ValueError('t1_end must be after t1_start')
        return v

    @field_validator('t2_end')
    def validate_t2_range(cls, v, info):
        if 't2_start' in info.data and v <= info.data['t2_start']:
            raise ValueError('t2_end must be after t2_start')
        if 't1_end' in info.data and v <= info.data['t1_end']:
            raise ValueError('t2 range must be after t1 range')
        if v > datetime.now(timezone.utc):
            raise ValueError('t2_end cannot be in the future')
        return v

# -- Auth Schemas

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=8)

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True

class JobResponse(BaseModel):
    id: int
    aoi_id: int
    t1_start: datetime
    t1_end: datetime
    t2_start: datetime
    t2_end: datetime
    status: str
    progress: int
    result_geojson: Optional[str] = None
    result_tif_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AOISchema(BaseModel):
    id: int
    name: str
    geometry: str
    created_at: datetime

    class Config:
        from_attributes = True
