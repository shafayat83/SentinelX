import os
from celery import Celery
from .models import DetectionJob, JobStatus, ChangeEvent, Base
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from processing.sentinel_loader import SentinelLoader
from processing.preprocessing import Preprocessor
from processing.postprocessing import Postprocessor
from model.inference import InferenceEngine
import datetime

# Celery Configuration
CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("tasks", broker=CELERY_BROKER_URL)

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password@localhost:5432/makeit")
engine = sqlalchemy.create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@celery_app.task(bind=True)
def run_change_detection(self, job_id: int):
    """
    Async task for change detection.
    1. Fetch Job from DB
    2. Download T1, T2 Imagery
    3. Run Inference
    4. Post-process & Save results
    """
    db = SessionLocal()
    job = db.query(DetectionJob).filter(DetectionJob.id == job_id).first()
    if not job:
        return "Job not found"
    
    try:
        job.status = JobStatus.PROCESSING
        job.progress = 10
        db.commit()
        
        # 1. Initialize Loader & Fetch Data
        loader = SentinelLoader()
        aoi_geojson = job.aoi.geometry # simplified access for demo
        
        t1_ds = loader.fetch_aoi(aoi_geojson, job.t1_start, job.t1_end)
        job.progress = 30
        db.commit()
        
        t2_ds = loader.fetch_aoi(aoi_geojson, job.t2_start, job.t2_end)
        job.progress = 50
        db.commit()
        
        if not t1_ds or not t2_ds:
            raise ValueError("No imagery found for one of the time periods.")
        
        # 2. Preprocessing
        preprocessor = Preprocessor()
        t1_data = preprocessor.process(t1_ds)
        t2_data = preprocessor.process(t2_ds)
        job.progress = 60
        db.commit()
        
        # 3. Inference
        inference_engine = InferenceEngine(model_path="weights.pth")
        change_mask = inference_engine.predict_from_arrays(t1_data, t2_data)
        job.progress = 80
        db.commit()
        
        # 4. Post-processing
        postprocessor = Postprocessor()
        results_gdf = postprocessor.vectorize(change_mask, t1_ds.rio.transform())
        job.result_geojson = postprocessor.to_geojson(results_gdf)
        
        # 5. Finalize
        job.status = JobStatus.COMPLETED
        job.progress = 100
        db.commit()
        
    except Exception as e:
        job.status = JobStatus.FAILED
        db.commit()
        print(f"Job {job_id} failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Base.metadata.create_all(bind=engine)
    pass
