from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from datetime import datetime

from app.db.base import Base


class PractitionerRole(Base):
    __tablename__ = "practitioner_roles"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String(255), unique=True, index=True, nullable=False)
    
    # References (keep for linking)
    practitioner_resource_id = Column(String(255), index=True, nullable=True)
    organization_resource_id = Column(String(255), index=True, nullable=True)
    
    # Active status
    active = Column(Boolean, nullable=True)
    
    # Role/specialty codes (SNOMED, NUCC - keep)
    role_code = Column(String(255), nullable=True)
    role_display = Column(Text, nullable=True)
    specialty_code = Column(String(255), nullable=True)
    specialty_display = Column(Text, nullable=True)
    
    # Location (facilities - link to organization)
    location_resource_id = Column(String(255), nullable=True)
    
    # Contact (usually organizational - may anonymize)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    
    raw_fhir_data = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
