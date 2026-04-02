from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
import datetime
import enum

Base = declarative_base()

class JobStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="analyst")

class AOI(Base):
    __tablename__ = "aois"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    geometry = Column(Geometry("POLYGON", srid=4326))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))

class DetectionJob(Base):
    __tablename__ = "detection_jobs"
    id = Column(Integer, primary_key=True, index=True)
    aoi_id = Column(Integer, ForeignKey("aois.id"))
    t1_start = Column(DateTime)
    t1_end = Column(DateTime)
    t2_start = Column(DateTime)
    t2_end = Column(DateTime)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING)
    progress = Column(Integer, default=0)
    result_geojson = Column(Text, nullable=True) # GeoJSON string
    result_tif_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    aoi = relationship("AOI")

class ChangeEvent(Base):
    __tablename__ = "change_events"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("detection_jobs.id"))
    change_type = Column(String) # e.g., Construction, Deforestation
    geometry = Column(Geometry("POLYGON", srid=4326))
    area_m2 = Column(Float)
    confidence = Column(Float)
