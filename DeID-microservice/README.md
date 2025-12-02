# FHIR De-Identification Microservice

This microservice **anonymizes personal and sensitive data** from FHIR (Fast Healthcare Interoperability Resources) before downstream processing for readmission prediction models.

## Purpose

**Role:** De-identify FHIR data from bulk exports to remove PII while preserving clinical features.

- **Technologies:** Python + FastAPI + Faker + PostgreSQL + SQLAlchemy
- **Description:** 
  - Fetches FHIR resources from upstream FHIR Proxy service
  - Removes or replaces direct identifiers (names, addresses, phone, email, IDs) with pseudonyms using Faker
  - Applies consistent date-shifting per patient to maintain temporal relationships
  - Preserves clinical codes (ICD-10, SNOMED CT, LOINC, RxNorm) critical for ML prediction
  - Stores de-identified data in PostgreSQL for downstream analytics

## Critical FHIR Resources Processed

### Must Have (Highest Priority)
- **Patient** - Demographics (anonymized: name, address, phone, email; date-shifted: birthDate)
- **Encounter** - Hospitalization episodes, length of stay (critical for readmission prediction)
- **Condition** - Comorbidities and diagnoses (strongest clinical predictors)
- **Observation** - Vital signs and lab results (hemoglobin, creatinine, glucose, sodium)
- **MedicationRequest** - Discharge medications (polypharmacy indicators)

### Highly Important
- **Procedure** - Surgical procedures and interventions (acuity indicators)
- **DiagnosticReport** - Clinical reports (free text redacted for PII)

## Project Structure

```
deid-microservice
├── app
│   ├── main.py                           # FastAPI app entry point
│   ├── api
│   │   ├── routes.py                     # Legacy example routes
│   │   └── deid_routes.py                # Main de-identification endpoints
│   ├── core
│   │   └── config.py                     # Settings (DATABASE_URL, FHIR_PROXY_BASE_URL)
│   ├── db
│   │   ├── base.py                       # SQLAlchemy Base
│   │   └── session.py                    # DB engine and session management
│   ├── models                            # SQLAlchemy ORM models + Pydantic schemas
│   │   ├── patient.py
│   │   ├── encounter.py
│   │   ├── condition.py
│   │   ├── observation.py
│   │   ├── medication_request.py
│   │   ├── procedure.py
│   │   ├── diagnostic_report.py
│   │   └── schemas.py                    # Pydantic response models
│   └── services
│       ├── deid_service.py               # Faker-based de-identification logic
│       └── fhir_client.py                # HTTP client for FHIR Proxy
├── requirements.txt
└── README.md
```

## Setup Instructions

### Prerequisites
- Python 3.8+
- PostgreSQL database (local or Docker)
- FHIR Proxy service running at `http://localhost:8080` (or configure `FHIR_PROXY_BASE_URL`)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd deid-microservice
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```

3. Activate the virtual environment:
   - Windows (Git Bash / bash.exe):
     ```bash
     source .venv/Scripts/activate
     ```
   - Windows (PowerShell):
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
   - macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```

4. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Database Setup

Set the `DATABASE_URL` and `FHIR_PROXY_BASE_URL` environment variables:

```bash
export DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/deid"
export FHIR_PROXY_BASE_URL="http://localhost:8080"
```

Quick local PostgreSQL with Docker:

```bash
docker run --name deid-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=deid -p 5432:5432 -d postgres:16
```

Tables are created automatically on app startup.

## Usage

### Run the Service

```bash
uvicorn app.main:app --reload
```

Access the service at:
- **API:** `http://127.0.0.1:8000`
- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`

### Key Endpoints

#### 1. Ingest and De-Identify FHIR Data
```bash
POST /deid/ingest?clear_existing={true|false}
```
Fetches all 13 critical FHIR resource types from the proxy, de-identifies PII, and stores in PostgreSQL.

**Parameters:**
- `clear_existing` (optional, default=false): Clear all existing data before ingestion to prevent duplicates/overflow

**Recommended Usage (Clear First):**
```bash
curl -X POST "http://127.0.0.1:8000/deid/ingest?clear_existing=true"
```

**Append Mode (Keep Existing):**
```bash
curl -X POST http://127.0.0.1:8000/deid/ingest
```

**Response:**
```json
{
  "status": "success",
  "message": "FHIR data ingested and de-identified successfully",
  "files_processed": ["Patient", "Encounter", "Condition", "Observation", "MedicationRequest", "Procedure", "DiagnosticReport", "DocumentReference", "AllergyIntolerance", "Immunization", "Practitioner", "PractitionerRole", "Organization"],
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

#### 2. Clear Database
```bash
DELETE /deid/clear-database
```
Removes all de-identified records from the database. Use before re-ingesting to prevent duplicates.

**Example:**
```bash
curl -X DELETE http://127.0.0.1:8000/deid/clear-database
```

**Response:**
```json
{
  "status": "success",
  "message": "Database cleared successfully. 5432 total records deleted.",
  "deleted_counts": {
    "patients": 100,
    "encounters": 450,
    "conditions": 892,
    ...
  }
}
```

#### 3. Retrieve De-Identified Data (13 GET Endpoints)

```bash
# Patient demographics
GET /deid/patients?skip=0&limit=100

# Hospitalizations
GET /deid/encounters?skip=0&limit=100

# Diagnoses
GET /deid/conditions?skip=0&limit=100

# Vitals and labs
GET /deid/observations?skip=0&limit=100

# Medications
GET /deid/medication-requests?skip=0&limit=100

# Procedures
GET /deid/procedures?skip=0&limit=100

# Lab reports
GET /deid/diagnostic-reports?skip=0&limit=100

# Clinical notes
GET /deid/document-references?skip=0&limit=100

# Allergies
GET /deid/allergy-intolerances?skip=0&limit=100

# Vaccinations
GET /deid/immunizations?skip=0&limit=100

# Providers
GET /deid/practitioners?skip=0&limit=100

# Provider roles
GET /deid/practitioner-roles?skip=0&limit=100

# Healthcare facilities
GET /deid/organizations?skip=0&limit=100
```

**Example:**
```bash
curl "http://127.0.0.1:8000/deid/patients?skip=0&limit=10"
```

---

## 🔄 Typical Workflow

1. **Start Service**: `uvicorn app.main:app --reload`
2. **Clear Database** (optional): `curl -X DELETE http://localhost:8000/deid/clear-database`
3. **Ingest FHIR Data**: `curl -X POST "http://localhost:8000/deid/ingest?clear_existing=true"`
4. **Query De-Identified Data**: `curl http://localhost:8000/deid/patients`
5. **Re-ingest** (when new data available): Repeat step 3

---

## De-Identification Strategy

### What Gets Anonymized (PII Removal)
- **Names:** Replaced with Faker-generated names (consistent per original)
- **Addresses:** Replaced with fake addresses
- **Phone/Email:** Replaced with fake contact info
- **Postal Codes:** Fully anonymized or generalized
- **Provider/Location Names:** Replaced with generic names
- **Free Text (Clinical Notes):** Redacted with `[REDACTED]` placeholder

### What Gets Preserved (Clinical Data for ML)
- **Clinical Codes:** ICD-10, SNOMED CT, LOINC, RxNorm codes (not PII)
- **Lab Values:** Numeric measurements (hemoglobin, creatinine, etc.)
- **Vital Signs:** Blood pressure, heart rate, temperature, etc.
- **Medication Names:** Drug codes and dosages
- **Procedure Codes:** CPT codes and procedure types
- **Gender:** Kept as-is (not considered PII for this use case)
- **State/Region:** Kept for geographic analysis

### Date Shifting
- All dates are **consistently shifted** by the same offset per patient
- Maintains temporal relationships (e.g., 30-day readmission window)
- Shift range: ±365 days, deterministic based on patient ID hash

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg2://postgres:postgres@localhost:5432/deid` |
| `FHIR_PROXY_BASE_URL` | Base URL of FHIR Proxy service | `http://localhost:8080` |

Create a `.env` file in the project root:
```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/deid
FHIR_PROXY_BASE_URL=http://localhost:8080
```

## FHIR Proxy Integration

The service expects a FHIR Proxy running at `http://localhost:8080` with these endpoints:

- **GET /bulk/manifest** - Returns list of available NDJSON files:
  ```json
  {
    "files": [
      {"fileName": "Patient.000.ndjson", "url": "/bulk/files/Patient.000.ndjson"},
      {"fileName": "Encounter.000.ndjson", "url": "/bulk/files/Encounter.000.ndjson"},
      ...
    ],
    "exportId": "synthea-export"
  }
  ```

- **GET /bulk/files/{filename}** - Returns NDJSON content (one FHIR resource per line)

## Downstream Usage

After de-identification, the cleaned data can be consumed by:
1. **Feature Engineering Service** - Extract ML features from de-identified clinical data
2. **Prediction Models** - Train/evaluate readmission prediction models
3. **Analytics Dashboards** - Visualize de-identified patient cohorts

Export de-identified data:
```bash
# Query all patients and pipe to downstream service
curl http://127.0.0.1:8000/deid/patients | jq .
```## Architecture

```
┌─────────────────────┐
│   FHIR Proxy        │  (Upstream)
│  localhost:8080     │
│  /bulk/manifest     │
│  /bulk/files/*      │
└──────────┬──────────┘
           │ HTTP
           ▼
┌─────────────────────────────────────┐
│  De-Identification Microservice     │
│  (This Service)                     │
│                                     │
│  • Fetch FHIR Resources (NDJSON)   │
│  • Anonymize PII (Faker)           │
│  • Shift Dates (consistent)        │
│  • Store in PostgreSQL             │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────┐
│   PostgreSQL DB     │
│  De-identified Data │
│  • patients         │
│  • encounters       │
│  • conditions       │
│  • observations     │
│  • medication_req   │
│  • procedures       │
│  • diagnostic_rep   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  Downstream Services                │
│  • Feature Engineering              │
│  • ML Training/Prediction           │
│  • Analytics Dashboards             │
└─────────────────────────────────────┘
```

## Testing

Test the ingestion pipeline:

```bash
# 1. Start PostgreSQL
docker run --name deid-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=deid -p 5432:5432 -d postgres:16

# 2. Ensure FHIR Proxy is running at localhost:8080

# 3. Start this service
uvicorn app.main:app --reload

# 4. Trigger ingestion
curl -X POST http://127.0.0.1:8000/deid/ingest

# 5. Query de-identified patients
curl http://127.0.0.1:8000/deid/patients | jq '.patients[0]'
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

[Specify your license here]