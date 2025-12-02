from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

from app.db.base import Base


class Procedure(Base):
    __tablename__ = "procedures"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String(255), unique=True, index=True, nullable=False)
    
    patient_resource_id = Column(String(255), index=True, nullable=True)
    encounter_resource_id = Column(String(255), index=True, nullable=True)
    
    # Procedure details (kept - important for acuity)
    status = Column(String(50), nullable=True)
    code = Column(String(255), nullable=True)  # CPT, SNOMED CT
    display = Column(Text, nullable=True)
    category = Column(String(255), nullable=True)
    
    # Performer (may need anonymization)
    performer_display = Column(String(255), nullable=True)
    
    # Time-shifted
    performed_date = Column(DateTime, nullable=True)
    
    raw_fhir_data = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
