from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from datetime import datetime

from app.db.base import Base


class Encounter(Base):
    __tablename__ = "encounters"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String(255), unique=True, index=True, nullable=False)
    
    patient_resource_id = Column(String(255), index=True, nullable=True)  # Link to patient
    
    # Clinical data (kept for prediction)
    status = Column(String(50), nullable=True)
    class_code = Column(String(100), nullable=True)  # inpatient, outpatient, emergency
    type_code = Column(String(255), nullable=True)
    
    # Time-shifted dates for privacy
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    
    # Length of stay (derived, important for readmission)
    length_of_stay_days = Column(Float, nullable=True)
    
    # Location info (may need de-identification)
    location_name = Column(String(255), nullable=True)
    
    raw_fhir_data = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
