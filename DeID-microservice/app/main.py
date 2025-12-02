from fastapi import FastAPI
from app.api.routes import router as api_router
from app.api.deid_routes import router as deid_router
from app.db.session import engine
from app.db.base import Base

# Import models to register them with SQLAlchemy metadata
import app.models.item  # noqa: F401
import app.models.patient  # noqa: F401
import app.models.encounter  # noqa: F401
import app.models.condition  # noqa: F401
import app.models.observation  # noqa: F401
import app.models.medication_request  # noqa: F401
import app.models.procedure  # noqa: F401
import app.models.diagnostic_report  # noqa: F401
import app.models.document_reference  # noqa: F401
import app.models.allergy_intolerance  # noqa: F401
import app.models.immunization  # noqa: F401
import app.models.practitioner  # noqa: F401
import app.models.practitioner_role  # noqa: F401
import app.models.organization  # noqa: F401

app = FastAPI(
    title="FHIR De-Identification Service",
    description="Anonymizes personal and sensitive data from FHIR resources before downstream processing",
    version="1.0.0"
)

app.include_router(api_router)
app.include_router(deid_router)

@app.get("/")
def read_root():
    return {
        "message": "FHIR De-Identification Microservice",
        "description": "Anonymizes PII from FHIR data using Faker and PostgreSQL",
        "critical_resources": [
            "Patient", "Encounter", "Condition", "Observation", 
            "MedicationRequest", "Procedure", "DiagnosticReport",
            "DocumentReference", "AllergyIntolerance", "Immunization",
            "Practitioner", "PractitionerRole", "Organization"
        ],
        "endpoints": {
            "ingest": "POST /deid/ingest - Fetch, de-identify, and store all critical FHIR resources",
            "patients": "GET /deid/patients",
            "encounters": "GET /deid/encounters",
            "conditions": "GET /deid/conditions",
            "observations": "GET /deid/observations",
            "medications": "GET /deid/medication-requests",
            "procedures": "GET /deid/procedures",
            "reports": "GET /deid/diagnostic-reports",
            "documents": "GET /deid/document-references",
            "allergies": "GET /deid/allergy-intolerances",
            "immunizations": "GET /deid/immunizations",
            "practitioners": "GET /deid/practitioners",
            "roles": "GET /deid/practitioner-roles",
            "organizations": "GET /deid/organizations",
        }
    }


@app.on_event("startup")
def on_startup():
    # Create database tables if they don't exist
    Base.metadata.create_all(bind=engine)