-- Manual SQL migration for patient_features table
-- Run this against your featDB database

CREATE TABLE IF NOT EXISTS patient_features (
    id SERIAL PRIMARY KEY,
    patient_resource_id VARCHAR(255) UNIQUE NOT NULL,
    gender VARCHAR(50),
    birth_date VARCHAR(50),
    state VARCHAR(100),
    num_encounters INTEGER DEFAULT 0,
    avg_los FLOAT DEFAULT 0.0,
    num_conditions INTEGER DEFAULT 0,
    num_med_requests INTEGER DEFAULT 0,
    obs_abnormal_count INTEGER DEFAULT 0,
    ner_entities JSONB,
    embedding_mean JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS ix_patient_features_patient_resource_id 
ON patient_features(patient_resource_id);

CREATE INDEX IF NOT EXISTS ix_patient_features_id 
ON patient_features(id);