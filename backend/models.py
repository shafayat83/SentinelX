from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
import datetime
import enum
from sqlalchemy.sql import func

Base = declarative_base()

class JobStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="analyst", nullable=False)
    is_active = Column(Integer, default=1) # 1=active, 0=disabled
    api_key_hash = Column(String(255), nullable=True) # for backend-to-backend calls
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class AOI(Base):
    __tablename__ = "aois"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    geometry = Column(Geometry("POLYGON", srid=4326), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

class DetectionJob(Base):
    __tablename__ = "detection_jobs"
    id = Column(Integer, primary_key=True, index=True)
    aoi_id = Column(Integer, ForeignKey("aois.id", ondelete="CASCADE"), nullable=False)
    t1_start = Column(DateTime(timezone=True), nullable=False)
    t1_end = Column(DateTime(timezone=True), nullable=False)
    t2_start = Column(DateTime(timezone=True), nullable=False)
    t2_end = Column(DateTime(timezone=True), nullable=False)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, index=True)
    progress = Column(Integer, default=0)
    result_geojson = Column(Text, nullable=True) # GeoJSON string
    result_tif_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    aoi = relationship("AOI")

class ChangeEvent(Base):
    __tablename__ = "change_events"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("detection_jobs.id", ondelete="CASCADE"), nullable=False)
    change_type = Column(String(50), nullable=False) # e.g., Construction, Deforestation
    geometry = Column(Geometry("POLYGON", srid=4326), nullable=False)
    area_m2 = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
