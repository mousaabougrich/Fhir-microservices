from sqlalchemy import Column, DateTime, Integer, String, Text, Date, Boolean
from datetime import datetime

from app.db.base import Base


class Practitioner(Base):
    __tablename__ = "practitioners"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String(255), unique=True, index=True, nullable=False)
    
    # De-identified fields
    given_name = Column(String(255), nullable=True)  # Anonymized
    family_name = Column(String(255), nullable=True)  # Anonymized
    prefix = Column(String(50), nullable=True)  # Dr., Mrs., etc. - can keep
    
    # Gender (not PII for provider context)
    gender = Column(String(50), nullable=True)
    
    # Birth date (anonymize by date shifting)
    birth_date = Column(Date, nullable=True)
    
    # Identifiers - NPI is not PII but unique identifier
    # We'll keep NPI for linking but note it's a professional ID, not personal PII
    npi = Column(String(50), nullable=True, index=True)
    
    # Contact (anonymize)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    
    # Address (anonymize)
    address_line = Column(Text, nullable=True)
    city = Column(String(255), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    
    # Active status
    active = Column(Boolean, nullable=True)
    
    raw_fhir_data = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
