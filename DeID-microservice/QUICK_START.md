# Quick Start Guide - FHIR De-Identification Microservice

## Prerequisites
- Python 3.13.5
- PostgreSQL installed and running
- FHIR Proxy at `http://localhost:8080`

---

## 1️⃣ Activate Virtual Environment

### Windows
```bash
venv\Scripts\activate.bat
```

### Mac/Linux
```bash
source venv/bin/activate
```

---

## 2️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 3️⃣ Configure Environment
Create `.env` file in project root:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/deid
FHIR_PROXY_BASE_URL=http://localhost:8080
```

---

## 4️⃣ Create Database
```bash
# PostgreSQL command
createdb deid

# Or using psql
psql -U postgres -c "CREATE DATABASE deid;"
```

---

## 5️⃣ Start the Service
```bash
uvicorn app.main:app --reload
```

The service will:
- Create all 13 database tables automatically on startup
- Listen on `http://localhost:8000`
- Serve Swagger UI at `http://localhost:8000/docs`

---

## 6️⃣ Ingest FHIR Data

### Option 1: Clear Database First (Recommended)
Prevents duplicates and database overflow by clearing existing data before ingestion.

```bash
# Using curl
curl -X POST "http://localhost:8000/deid/ingest?clear_existing=true"

# Using Swagger UI
# Go to http://localhost:8000/docs
# Expand POST /deid/ingest
# Click "Try it out"
# Set clear_existing = true
# Click "Execute"
```

### Option 2: Append to Existing Data
Only adds new records (may create duplicates if same data exists).

```bash
curl -X POST http://localhost:8000/deid/ingest
```

### Option 3: Manual Database Cleanup
Clear the database separately before ingestion.

```bash
# Clear all data first
curl -X DELETE http://localhost:8000/deid/clear-database

# Then ingest
curl -X POST http://localhost:8000/deid/ingest
```

### Expected Response
```json
{
  "status": "success",
  "message": "FHIR data ingested and de-identified successfully",
  "files_processed": ["Patient", "Encounter", "Condition", ...],
  "patients_created": 100,
  "encounters_created": 450,
  "conditions_created": 892,
  "observations_created": 3540,
  "medication_requests_created": 678,
  "procedures_created": 234,
  "diagnostic_reports_created": 156,
  "document_references_created": 89,
  "allergy_intolerances_created": 45,
  "immunizations_created": 120,
  "practitioners_created": 67,
  "practitioner_roles_created": 67,
  "organizations_created": 12
}
```

---

## 7️⃣ Query De-Identified Data

### Get All Patients
```bash
curl http://localhost:8000/deid/patients
```

### Get All Encounters
```bash
curl http://localhost:8000/deid/encounters
```

### Get Conditions (with pagination)
```bash
curl "http://localhost:8000/deid/conditions?skip=0&limit=50"
```

### All Available Endpoints
- `/deid/patients`
- `/deid/encounters`
- `/deid/conditions`
- `/deid/observations`
- `/deid/medication-requests`
- `/deid/procedures`
- `/deid/diagnostic-reports`
- `/deid/document-references`
- `/deid/allergy-intolerances`
- `/deid/immunizations`
- `/deid/practitioners`
- `/deid/practitioner-roles`
- `/deid/organizations`

---

## 8️⃣ Test Integration (Optional)
```bash
python test_complete_integration.py
```

This validates all 13 resource types are processing correctly.

---

## 🗑️ Database Management

### Clear All Data
```bash
curl -X DELETE http://localhost:8000/deid/clear-database
```

**Response:**
```json
{
  "status": "success",
  "message": "Database cleared successfully. 5432 total records deleted.",
  "deleted_counts": {
    "document_references": 89,
    "allergy_intolerances": 45,
    "immunizations": 120,
    "diagnostic_reports": 156,
    "procedures": 234,
    "medication_requests": 678,
    "observations": 3540,
    "conditions": 892,
    "practitioner_roles": 67,
    "practitioners": 67,
    "organizations": 12,
    "encounters": 450,
    "patients": 100
  }
}
```

**When to use:**
- Before re-ingesting data to prevent duplicates
- When database is full/overflowing
- When switching to a new FHIR data source
- For testing/development cycles

---

## 🔍 Troubleshooting

### Error: "Can't connect to PostgreSQL"
- Check PostgreSQL is running: `pg_isready`
- Verify DATABASE_URL in `.env`
- Test connection: `psql -U username -d deid`

### Error: "FHIR Proxy not reachable"
- Verify FHIR Proxy is running at `http://localhost:8080`
- Test: `curl http://localhost:8080/bulk/manifest`
- Check FHIR_PROXY_BASE_URL in `.env`

### Error: "ModuleNotFoundError"
- Ensure venv is activated (prompt should show `(venv)`)
- Reinstall: `pip install -r requirements.txt`

### Error: "Table already exists"
- Tables are created automatically on first run
- To reset: `DROP DATABASE deid; CREATE DATABASE deid;`

---

## 📊 Sample Query Results

### Patient (De-Identified)
```json
{
  "id": 1,
  "resource_id": "abc123",
  "given_name": "John",        // ← Anonymized with Faker
  "family_name": "Smith",      // ← Anonymized with Faker
  "gender": "male",
  "birth_date": "1985-03-15",  // ← Date-shifted ±365 days
  "city": "Springfield",       // ← Anonymized with Faker
  "state": "MA",               // ← Preserved
  "phone": "555-0123",         // ← Anonymized with Faker
  "email": "john@example.com"  // ← Anonymized with Faker
}
```

### Condition (Clinical Codes Preserved)
```json
{
  "id": 1,
  "resource_id": "cond456",
  "patient_resource_id": "abc123",
  "code": "44054006",          // ← SNOMED code PRESERVED
  "display": "Type 2 diabetes", // ← PRESERVED
  "onset_date": "2020-06-15",  // ← Date-shifted (same offset as patient)
  "clinical_status": "active"
}
```

---

## 🎯 Key Features

### ✓ Anonymization
- Names, addresses, phone, email → Faker (deterministic)
- SSN, Driver's License, Passport → Removed
- Free text (notes, conclusions) → "[PII REDACTED]"

### ✓ Clinical Preservation
- All medical codes (ICD-10, SNOMED, LOINC, RxNorm, CVX, CPT, NUCC)
- All measurements (vitals, lab values)
- Professional identifiers (NPI for linking)

### ✓ Temporal Relationships
- Each patient gets unique date offset (±365 days)
- All dates shifted by same offset per patient
- Preserves intervals (length of stay, time between visits)

---

## 🚀 Production Deployment

### Environment Variables
```env
DATABASE_URL=postgresql://prod_user:secure_pass@db-host:5432/deid_prod
FHIR_PROXY_BASE_URL=https://fhir-proxy.hospital.org
```

### Run with Gunicorn (Production Server)
```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

### Docker Deployment (Optional)
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 📈 Monitoring

### Health Check
```bash
curl http://localhost:8000/
```

### Database Record Counts
```sql
SELECT 
  'patients' as table_name, COUNT(*) FROM patients
UNION ALL
SELECT 'encounters', COUNT(*) FROM encounters
UNION ALL
SELECT 'conditions', COUNT(*) FROM conditions;
```

---

## 🎉 You're All Set!

Your FHIR de-identification microservice is now running with:
- ✅ 13 critical FHIR resource types
- ✅ Deterministic PII anonymization
- ✅ Clinical code preservation
- ✅ REST API with Swagger UI
- ✅ PostgreSQL persistence

Ready for hospital readmission prediction ML pipeline! 🏥📊🤖
