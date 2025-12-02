from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from datetime import datetime

from app.db.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String(255), unique=True, index=True, nullable=False)
    
    # Organization info (anonymize name)
    name = Column(Text, nullable=True)  # Anonymized facility name
    active = Column(Boolean, nullable=True)
    
    # Type/category (keep - not PII)
    type_code = Column(String(255), nullable=True)
    type_display = Column(Text, nullable=True)
    
    # Identifiers - NPI for organizations (keep for linking)
    npi = Column(String(50), nullable=True, index=True)
    
    # Contact (anonymize)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    
    # Address (anonymize)
    address_line = Column(Text, nullable=True)
    city = Column(String(255), nullable=True)
    state = Column(String(100), nullable=True)  # Can keep state
    postal_code = Column(String(20), nullable=True)
    
    raw_fhir_data = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
