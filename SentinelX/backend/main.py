from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
from typing import List
from fastapi.security import OAuth2PasswordRequestForm

from . import models, schemas, tasks, auth
from .database import engine, get_db, Base
from .security import SecurityHeadersMiddleware, AuditLoggerMiddleware, logger
from .rate_limiter import setup_rate_limiting, limiterGLOBAL_LIMIT = os.getenv("RATE_LIMIT_GLOBAL", "60/minute")
DETECT_LIMIT = os.getenv("RATE_LIMIT_DETECT", "5/minute")
AUTH_LIMIT = os.getenv("RATE_LIMIT_AUTH", "10/minute")

# Create tables (In production, use Alembic migrations instead)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SentinelX: High-Security Satellite API")

# ── Security Middlewares & Rate Limiting ────────────────────────────────────
setup_rate_limiting(app)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(AuditLoggerMiddleware)

# CORS Configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/")
@app.state.limiter.limit(GLOBAL_LIMIT)
def read_root(request: Request):
    return {"message": "SentinelX API is running securely."}


# ── Auth Endpoints ───────────────────────────────────────────────────────────
@app.post("/api/v1/auth/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
@app.state.limiter.limit(AUTH_LIMIT)
def register_user(request: Request, user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(
        (models.User.email == user.email) | (models.User.username == user.username)
    ).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info("user_registered", user_id=new_user.id, username=new_user.username)
    return new_user


@app.post("/api/v1/auth/login", response_model=schemas.TokenResponse)
@app.state.limiter.limit(AUTH_LIMIT)
def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        logger.warning("failed_login_attempt", username=form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    access_token = auth.create_access_token(user.id, user.role)
    logger.info("user_logged_in", user_id=user.id)
    return {"access_token": access_token, "token_type": "bearer"}


# ── Job Endpoints ────────────────────────────────────────────────────────────
@app.post("/api/v1/detect", response_model=schemas.JobResponse, status_code=status.HTTP_201_CREATED)
@app.state.limiter.limit(DETECT_LIMIT)
def create_detection_job(
    request: Request,
    job_req: schemas.JobCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Submit a securely authenticated change detection job."""
    try:
        # Create AOI securely
        new_aoi = models.AOI(
            name=job_req.aoi_name,
            geometry=f"SRID=4326;{job_req.aoi_wkt}",
            user_id=current_user.id
        )
        db.add(new_aoi)
        db.commit()
        db.refresh(new_aoi)
        
        # Create Job
        job = models.DetectionJob(
            aoi_id=new_aoi.id,
            t1_start=job_req.t1_start,
            t1_end=job_req.t1_end,
            t2_start=job_req.t2_start,
            t2_end=job_req.t2_end,
            status=models.JobStatus.PENDING
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Push to Celery
        tasks.run_change_detection.delay(job.id)
        
        logger.info("job_created", job_id=job.id, user_id=current_user.id)
        return job
    except Exception as e:
        logger.error("job_creation_failed", error=str(e), user_id=current_user.id)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create detection job")


@app.get("/api/v1/jobs/{job_id}", response_model=schemas.JobResponse)
@app.state.limiter.limit(GLOBAL_LIMIT)
def get_job_status(
    request: Request,
    job_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    # Ensure user only sees their own jobs (join AOI to verify ownership)
    job = db.query(models.DetectionJob).join(models.AOI).filter(
        models.DetectionJob.id == job_id,
        models.AOI.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/api/v1/jobs", response_model=List[schemas.JobResponse])
@app.state.limiter.limit(GLOBAL_LIMIT)
def list_jobs(
    request: Request,
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    # Hard cap on pagination
    actual_limit = min(limit, 200)
    
    jobs = db.query(models.DetectionJob).join(models.AOI).filter(
        models.AOI.user_id == current_user.id
    ).order_by(models.DetectionJob.created_at.desc()).offset(skip).limit(actual_limit).all()
    
    return jobs
