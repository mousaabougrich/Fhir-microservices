from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from datetime import datetime

from app.db.base import Base


class Observation(Base):
    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String(255), unique=True, index=True, nullable=False)
    
    patient_resource_id = Column(String(255), index=True, nullable=True)
    encounter_resource_id = Column(String(255), index=True, nullable=True)
    
    # Clinical measurements (kept - vital for prediction)
    status = Column(String(50), nullable=True)
    category = Column(String(255), nullable=True)  # vital-signs, laboratory, etc.
    code = Column(String(255), nullable=True)  # LOINC code
    display = Column(Text, nullable=True)  # Observation name
    
    # Value (numeric or text)
    value_quantity = Column(Float, nullable=True)
    value_unit = Column(String(50), nullable=True)
    value_string = Column(Text, nullable=True)
    
    # Time-shifted
    effective_date = Column(DateTime, nullable=True)
    issued_date = Column(DateTime, nullable=True)
    
    raw_fhir_data = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
