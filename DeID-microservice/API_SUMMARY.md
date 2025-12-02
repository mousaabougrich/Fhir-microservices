# API Endpoints Summary

## 📋 Complete Endpoint List

### 🔄 Data Ingestion (Write Operations)

| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| POST | `/deid/ingest` | Fetch from FHIR Proxy → De-identify → Store in PostgreSQL | `clear_existing` (bool, optional) |
| DELETE | `/deid/clear-database` | Remove all records from database | None |

---

### 📊 Data Retrieval (Read Operations - All 13 Resources)

| Method | Endpoint | Description | Pagination |
|--------|----------|-------------|------------|
| GET | `/deid/patients` | Patient demographics (anonymized) | `skip`, `limit` |
| GET | `/deid/encounters` | Hospitalization episodes | `skip`, `limit` |
| GET | `/deid/conditions` | Diagnoses and comorbidities | `skip`, `limit` |
| GET | `/deid/observations` | Vitals and lab results | `skip`, `limit` |
| GET | `/deid/medication-requests` | Discharge medications | `skip`, `limit` |
| GET | `/deid/procedures` | Surgical procedures | `skip`, `limit` |
| GET | `/deid/diagnostic-reports` | Clinical reports | `skip`, `limit` |
| GET | `/deid/document-references` | Clinical notes | `skip`, `limit` |
| GET | `/deid/allergy-intolerances` | Medication allergies | `skip`, `limit` |
| GET | `/deid/immunizations` | Vaccination history | `skip`, `limit` |
| GET | `/deid/practitioners` | Provider demographics | `skip`, `limit` |
| GET | `/deid/practitioner-roles` | Provider roles/specialties | `skip`, `limit` |
| GET | `/deid/organizations` | Healthcare facilities | `skip`, `limit` |

---

## 🎯 Usage Examples

### 1. Initial Setup (First Time)
```bash
# Start the service
uvicorn app.main:app --reload

# Ingest FHIR data with automatic cleanup
curl -X POST "http://localhost:8000/deid/ingest?clear_existing=true"
```

**Response:**
```json
{
  "status": "success",
  "message": "FHIR data ingested and de-identified successfully",
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

### 2. Re-Ingesting Data (Prevent Duplicates)

**Option A: Clear During Ingestion**
```bash
curl -X POST "http://localhost:8000/deid/ingest?clear_existing=true"
```

**Option B: Manual Clear Then Ingest**
```bash
# Step 1: Clear database
curl -X DELETE http://localhost:8000/deid/clear-database

# Step 2: Ingest fresh data
curl -X POST http://localhost:8000/deid/ingest
```

---

### 3. Querying De-Identified Data

**Get First 10 Patients:**
```bash
curl "http://localhost:8000/deid/patients?skip=0&limit=10"
```

**Get Encounters for Analysis:**
```bash
curl "http://localhost:8000/deid/encounters?skip=0&limit=100"
```

**Get High-Risk Conditions:**
```bash
curl http://localhost:8000/deid/conditions
```

**Get Lab Results:**
```bash
curl http://localhost:8000/deid/observations
```

---

## 🔒 What Gets De-Identified?

### ❌ Removed/Anonymized (PII)
- **Names**: Patient, practitioner → Faker-generated
- **Addresses**: Street, city → Faker-generated
- **Contact**: Phone, email → Faker-generated
- **Identifiers**: SSN, Driver's License, Passport → Removed
- **Dates**: All dates → Shifted ±365 days (per patient)
- **Free Text**: Clinical notes, conclusions → "[PII REDACTED]"

### ✅ Preserved (Clinical Value)
- **Medical Codes**: ICD-10, SNOMED, LOINC, RxNorm, CVX, CPT, NUCC
- **Measurements**: BP, HR, lab values, vitals
- **Professional IDs**: NPI (practitioner/organization linking)
- **Geographic**: State level (not city/address)
- **Temporal Relationships**: Date intervals maintained

---

## 📈 Data Flow Architecture

```
┌─────────────────┐
│  FHIR Proxy     │  http://localhost:8080/bulk/manifest
│  (Synthea Data) │
└────────┬────────┘
         │
         │ POST /deid/ingest
         ▼
┌─────────────────┐
│   FastAPI       │  1. Fetch NDJSON files
│   Microservice  │  2. Parse FHIR resources
│                 │  3. De-identify PII (Faker)
│                 │  4. Date-shift (±365 days)
│                 │  5. Store in PostgreSQL
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   PostgreSQL    │  13 tables with de-identified data
│   Database      │  - patients
│   (deid)        │  - encounters
│                 │  - conditions
│                 │  - observations
│                 │  - medication_requests
│                 │  - procedures
│                 │  - diagnostic_reports
│                 │  - document_references
│                 │  - allergy_intolerances
│                 │  - immunizations
│                 │  - practitioners
│                 │  - practitioner_roles
│                 │  - organizations
└────────┬────────┘
         │
         │ GET /deid/{resource-type}
         ▼
┌─────────────────┐
│  ML Pipeline    │  Readmission prediction model
│  (Downstream)   │  - Feature engineering
│                 │  - Model training
│                 │  - Risk scoring
└─────────────────┘
```

---

## 🚦 Endpoint Decision Tree

### When to use `POST /deid/ingest?clear_existing=true`
✅ First time ingestion  
✅ New FHIR data source  
✅ Database is full/overflowing  
✅ Testing/development cycles  
✅ Weekly/monthly data refresh  

### When to use `POST /deid/ingest` (no clear)
⚠️ Incremental updates (rare)  
⚠️ Multiple FHIR sources (advanced)  
❌ **NOT recommended**: May create duplicates  

### When to use `DELETE /deid/clear-database`
✅ Manual cleanup before re-ingestion  
✅ Reset for testing  
✅ Emergency database overflow  
✅ Switching FHIR Proxy sources  

### When to use GET endpoints
✅ Query de-identified data for ML  
✅ Exploratory data analysis  
✅ Export to CSV/JSON for downstream  
✅ API integration with analytics tools  

---

## ⚡ Performance Tips

### Pagination Best Practices
```bash
# Small batches for quick preview
curl "http://localhost:8000/deid/patients?skip=0&limit=10"

# Larger batches for bulk export
curl "http://localhost:8000/deid/observations?skip=0&limit=1000"

# Iterate through all records
for i in {0..10000..1000}; do
  curl "http://localhost:8000/deid/patients?skip=$i&limit=1000" >> patients.json
done
```

### Ingestion Performance
- **Small Dataset** (100 patients): ~10-30 seconds
- **Medium Dataset** (1000 patients): ~2-5 minutes
- **Large Dataset** (10000 patients): ~20-30 minutes

### Database Cleanup
- **DELETE /deid/clear-database**: Instant (< 1 second for 10K records)
- Foreign key constraints respected automatically

---

## 🔧 Swagger UI

Access interactive API documentation:
```
http://localhost:8000/docs
```

**Features:**
- Test all endpoints in browser
- Auto-generated request/response schemas
- Parameter validation
- Try it out with real data

---

## 📌 Quick Reference

| Task | Command |
|------|---------|
| Start service | `uvicorn app.main:app --reload` |
| Ingest (safe) | `curl -X POST "http://localhost:8000/deid/ingest?clear_existing=true"` |
| Clear DB | `curl -X DELETE http://localhost:8000/deid/clear-database` |
| Get patients | `curl http://localhost:8000/deid/patients` |
| Swagger UI | `http://localhost:8000/docs` |

---

## ✅ Your Service Architecture

**You are correct!** The service:

1. ✅ **Reads** data from FHIR Proxy (`http://localhost:8080`)
2. ✅ **De-identifies** PII using Faker + date-shifting
3. ✅ **Saves** to PostgreSQL database
4. ✅ **One endpoint** triggers the procedure (`POST /deid/ingest`)
5. ✅ **Database cleared** before ingestion to avoid overflow (`clear_existing=true`)
6. ✅ **GET endpoints** for all 13 resource types

**Perfect design for hospital readmission ML pipeline!** 🎉
