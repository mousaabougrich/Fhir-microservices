from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

from app.db.base import Base


class MedicationRequest(Base):
    __tablename__ = "medication_requests"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String(255), unique=True, index=True, nullable=False)
    
    patient_resource_id = Column(String(255), index=True, nullable=True)
    encounter_resource_id = Column(String(255), index=True, nullable=True)
    
    # Medication info (kept - critical for polypharmacy analysis)
    status = Column(String(50), nullable=True)
    intent = Column(String(50), nullable=True)
    medication_code = Column(String(255), nullable=True)  # RxNorm code
    medication_display = Column(Text, nullable=True)
    
    # Dosage (important for treatment complexity)
    dosage_text = Column(Text, nullable=True)
    
    # Requester (may need anonymization)
    requester_display = Column(String(255), nullable=True)
    
    # Time-shifted
    authored_on = Column(DateTime, nullable=True)
    
    raw_fhir_data = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
