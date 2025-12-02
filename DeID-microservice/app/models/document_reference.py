from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

from app.db.base import Base


class DocumentReference(Base):
    __tablename__ = "document_references"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String(255), unique=True, index=True, nullable=False)
    
    patient_resource_id = Column(String(255), index=True, nullable=True)
    encounter_resource_id = Column(String(255), index=True, nullable=True)
    
    # Document metadata
    status = Column(String(50), nullable=True)
    doc_status = Column(String(50), nullable=True)  # document status
    type_code = Column(String(255), nullable=True)  # LOINC code
    type_display = Column(Text, nullable=True)
    category_code = Column(String(255), nullable=True)
    
    # Content description (may contain PII - redact)
    description = Column(Text, nullable=True)
    
    # Author (provider - anonymize)
    author_display = Column(String(255), nullable=True)
    
    # Custodian (organization - anonymize)
    custodian_display = Column(String(255), nullable=True)
    
    # Time-shifted
    created_date = Column(DateTime, nullable=True)
    
    raw_fhir_data = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
