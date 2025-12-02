from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from datetime import datetime

from app.db.base import Base


class Immunization(Base):
    __tablename__ = "immunizations"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String(255), unique=True, index=True, nullable=False)
    
    patient_resource_id = Column(String(255), index=True, nullable=True)
    encounter_resource_id = Column(String(255), index=True, nullable=True)
    
    # Vaccination data
    status = Column(String(50), nullable=True)
    status_reason_code = Column(String(255), nullable=True)
    
    # Vaccine code (CVX code - keep)
    vaccine_code = Column(String(255), nullable=True)
    vaccine_display = Column(Text, nullable=True)
    
    # Primary source (true if directly observed)
    primary_source = Column(Boolean, nullable=True)
    
    # Performer (provider - anonymize)
    performer_display = Column(String(255), nullable=True)
    
    # Location (facility - anonymize)
    location_display = Column(String(255), nullable=True)
    
    # Lot number (could be PII context - optional redact)
    lot_number = Column(String(255), nullable=True)
    
    # Time-shifted
    occurrence_date = Column(DateTime, nullable=True)
    recorded_date = Column(DateTime, nullable=True)
    
    raw_fhir_data = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
