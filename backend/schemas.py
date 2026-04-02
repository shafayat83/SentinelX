from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobCreate(BaseModel):
    aoi_name: str
    aoi_wkt: str # WKT representation of the polygon
    t1_start: datetime
    t1_end: datetime
    t2_start: datetime
    t2_end: datetime

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
