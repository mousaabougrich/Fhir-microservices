from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

from app.db.base import Base


class DiagnosticReport(Base):
    __tablename__ = "diagnostic_reports"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String(255), unique=True, index=True, nullable=False)
    
    patient_resource_id = Column(String(255), index=True, nullable=True)
    encounter_resource_id = Column(String(255), index=True, nullable=True)
    
    # Report details (clinical data kept)
    status = Column(String(50), nullable=True)
    category = Column(String(255), nullable=True)
    code = Column(String(255), nullable=True)  # LOINC code
    display = Column(Text, nullable=True)
    
    # Results summary (may contain sensitive info - needs review)
    conclusion = Column(Text, nullable=True)
    
    # Time-shifted
    effective_date = Column(DateTime, nullable=True)
    issued_date = Column(DateTime, nullable=True)
    
    raw_fhir_data = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
