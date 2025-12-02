from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

from app.db.base import Base


class AllergyIntolerance(Base):
    __tablename__ = "allergy_intolerances"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String(255), unique=True, index=True, nullable=False)
    
    patient_resource_id = Column(String(255), index=True, nullable=True)
    encounter_resource_id = Column(String(255), index=True, nullable=True)
    
    # Clinical data (kept for prediction)
    clinical_status = Column(String(50), nullable=True)
    verification_status = Column(String(50), nullable=True)
    type = Column(String(50), nullable=True)  # allergy, intolerance
    category = Column(String(50), nullable=True)  # food, medication, environment
    criticality = Column(String(50), nullable=True)  # low, high, unable-to-assess
    
    # Allergen code (SNOMED, RxNorm - keep)
    code = Column(String(255), nullable=True)
    display = Column(Text, nullable=True)
    
    # Recorder/asserter (provider - anonymize)
    recorder_display = Column(String(255), nullable=True)
    
    # Time-shifted
    onset_date = Column(DateTime, nullable=True)
    recorded_date = Column(DateTime, nullable=True)
    
    raw_fhir_data = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
