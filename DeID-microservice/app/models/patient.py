from sqlalchemy import Column, Integer, String, Text, Date, DateTime
from datetime import datetime

from app.db.base import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String(255), unique=True, index=True, nullable=False)  # Original FHIR resource ID
    
    # De-identified fields (replaced with Faker)
    given_name = Column(String(255), nullable=True)  # First name (anonymized)
    family_name = Column(String(255), nullable=True)  # Last name (anonymized)
    birth_date = Column(Date, nullable=True)  # Date shifted for privacy
    gender = Column(String(50), nullable=True)  # Kept as is (not PII)
    address_line = Column(Text, nullable=True)  # Anonymized address
    city = Column(String(255), nullable=True)  # Anonymized city
    state = Column(String(100), nullable=True)  # Can be kept or generalized
    postal_code = Column(String(20), nullable=True)  # Anonymized or generalized
    phone = Column(String(50), nullable=True)  # Anonymized phone
    email = Column(String(255), nullable=True)  # Anonymized email
    
    # Original raw FHIR JSON (optional, for audit)
    raw_fhir_data = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
