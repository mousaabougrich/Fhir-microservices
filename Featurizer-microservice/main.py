from fastapi import FastAPI, HTTPException, Depends
from typing import List
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Load environment variables from .env file
load_dotenv()

from featurizer.services.featurizer_service import FeaturizerService
from featurizer.database import get_db, engine
from featurizer.models import PatientFeatures

app = FastAPI(title="Featurizer Service")

# Create database tables
PatientFeatures.metadata.create_all(bind=engine)

BASE = os.getenv("DEID_BASE_URL", "http://deid:8000")


@app.get("/featurize/patient/{patient_id}")
def featurize_patient(patient_id: str, force_refresh: bool = False, db: Session = Depends(get_db)):
    try:
        service = FeaturizerService(base_url=BASE, db_session=db)
        return service.featurize_patient_with_db(patient_id, force_refresh)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/featurize/bulk")
def featurize_bulk(patient_ids: List[str], db: Session = Depends(get_db)):
    try:
        service = FeaturizerService(base_url=BASE, db_session=db)
        results = []
        for pid in patient_ids:
            try:
                features = service.featurize_patient_with_db(pid)
                results.append(features)
            except Exception as e:
                results.append({"patient_resource_id": pid, "error": str(e)})
        return {"rows": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/features/patient/{patient_id}")
def get_cached_features(patient_id: str, db: Session = Depends(get_db)):
    """Get cached features from database only"""
    try:
        service = FeaturizerService(base_url=BASE, db_session=db)
        cached = service.get_features_from_db(patient_id)
        if not cached:
            raise HTTPException(status_code=404, detail="Features not found in cache")
        return cached.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/features/all")
def get_all_cached_features(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all cached features with pagination"""
    try:
        features = db.query(PatientFeatures).offset(skip).limit(limit).all()
        return {"rows": [f.to_dict() for f in features]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok", "deid_base_url": BASE}
