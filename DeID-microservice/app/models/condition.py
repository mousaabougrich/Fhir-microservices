from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

from app.db.base import Base


class Condition(Base):
    __tablename__ = "conditions"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String(255), unique=True, index=True, nullable=False)
    
    patient_resource_id = Column(String(255), index=True, nullable=True)
    encounter_resource_id = Column(String(255), index=True, nullable=True)
    
    # Clinical codes (kept - critical for prediction)
    code = Column(String(255), nullable=True)  # ICD-10, SNOMED CT
    display = Column(Text, nullable=True)  # Condition name
    clinical_status = Column(String(50), nullable=True)  # active, resolved, etc.
    verification_status = Column(String(50), nullable=True)
    category = Column(String(255), nullable=True)  # problem-list-item, encounter-diagnosis
    
    # Time-shifted
    onset_date = Column(DateTime, nullable=True)
    recorded_date = Column(DateTime, nullable=True)
    
    raw_fhir_data = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
