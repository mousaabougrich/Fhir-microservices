from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON
from sqlalchemy.sql import func
from featurizer.database import Base


class PatientFeatures(Base):
    __tablename__ = "patient_features"

    id = Column(Integer, primary_key=True, index=True)
    patient_resource_id = Column(String(255), unique=True, index=True, nullable=False)
    
    # Demographics
    gender = Column(String(50), nullable=True)
    birth_date = Column(String(50), nullable=True)  # Keep as string from DeID
    state = Column(String(100), nullable=True)
    
    # Structured features
    num_encounters = Column(Integer, default=0)
    avg_los = Column(Float, default=0.0)
    num_conditions = Column(Integer, default=0)
    num_med_requests = Column(Integer, default=0)
    obs_abnormal_count = Column(Integer, default=0)
    
    # NLP features (stored as JSON)
    ner_entities = Column(JSON, nullable=True)
    embedding_mean = Column(JSON, nullable=True)  # Store as array
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "patient_resource_id": self.patient_resource_id,
            "gender": self.gender,
            "birth_date": self.birth_date,
            "state": self.state,
            "num_encounters": self.num_encounters,
            "avg_los": self.avg_los,
            "num_conditions": self.num_conditions,
            "num_med_requests": self.num_med_requests,
            "obs_abnormal_count": self.obs_abnormal_count,
            "ner_entities": self.ner_entities,
            "embedding_mean": self.embedding_mean,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }