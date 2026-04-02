from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from . import models, schemas, tasks
import sqlalchemy
from sqlalchemy.orm import sessionmaker
import os
from typing import List
from fastapi.middleware.cors import CORSMiddleware

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password@localhost:5432/makeit")
engine = sqlalchemy.create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="MakeIt: Satellite Change Detection API")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "MakeIt API is running"}

@app.post("/api/v1/detect", response_model=schemas.JobResponse)
def create_detection_job(request: schemas.JobCreate, db: Session = Depends(get_db)):
    """
    Submit a new change detection job.
    1. Create AOI if needed
    2. Create Detection Job
    3. Push to Celery
    """
    # Create AOI
    # Placeholder: In a real app, we'd check if it exists
    new_aoi = models.AOI(
        name=request.aoi_name,
        geometry=f"SRID=4326;{request.aoi_wkt}", # Simplified WKT
        user_id=1 # Default user
    )
    db.add(new_aoi)
    db.commit()
    db.refresh(new_aoi)
    
    # Create Job
    job = models.DetectionJob(
        aoi_id=new_aoi.id,
        t1_start=request.t1_start,
        t1_end=request.t1_end,
        t2_start=request.t2_start,
        t2_end=request.t2_end,
        status=models.JobStatus.PENDING
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Push to Celery
    tasks.run_change_detection.delay(job.id)
    
    return job

@app.get("/api/v1/jobs/{job_id}", response_model=schemas.JobResponse)
def get_job_status(job_id: int, db: Session = Depends(get_db)):
    job = db.query(models.DetectionJob).filter(models.DetectionJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/api/v1/jobs", response_model=List[schemas.JobResponse])
def list_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.DetectionJob).offset(skip).limit(limit).all()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
