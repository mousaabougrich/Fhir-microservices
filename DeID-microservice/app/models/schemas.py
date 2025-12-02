from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime

# Unified ORM-friendly BaseModel for Pydantic v1 and v2
try:  # Pydantic v2
    from pydantic import ConfigDict  # type: ignore

    class OrmModel(BaseModel):
        model_config = ConfigDict(from_attributes=True)
except Exception:  # Pydantic v1 fallback
    class OrmModel(BaseModel):
        class Config:
            orm_mode = True


# ========== Item schemas (legacy - can be removed) ==========
class ItemBase(OrmModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: int


class ItemList(OrmModel):
    items: List[Item]


# ========== FHIR Resource schemas (De-identified) ==========
class PatientSchema(OrmModel):
    id: int
    resource_id: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    address_line: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime


class EncounterSchema(OrmModel):
    id: int
    resource_id: str
    patient_resource_id: Optional[str] = None
    status: Optional[str] = None
    class_code: Optional[str] = None
    type_code: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    length_of_stay_days: Optional[float] = None
    location_name: Optional[str] = None
    created_at: datetime


class ConditionSchema(OrmModel):
    id: int
    resource_id: str
    patient_resource_id: Optional[str] = None
    encounter_resource_id: Optional[str] = None
    code: Optional[str] = None
    display: Optional[str] = None
    clinical_status: Optional[str] = None
    verification_status: Optional[str] = None
    category: Optional[str] = None
    onset_date: Optional[datetime] = None
    recorded_date: Optional[datetime] = None
    created_at: datetime


class ObservationSchema(OrmModel):
    id: int
    resource_id: str
    patient_resource_id: Optional[str] = None
    encounter_resource_id: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None
    code: Optional[str] = None
    display: Optional[str] = None
    value_quantity: Optional[float] = None
    value_unit: Optional[str] = None
    value_string: Optional[str] = None
    effective_date: Optional[datetime] = None
    issued_date: Optional[datetime] = None
    created_at: datetime


class MedicationRequestSchema(OrmModel):
    id: int
    resource_id: str
    patient_resource_id: Optional[str] = None
    encounter_resource_id: Optional[str] = None
    status: Optional[str] = None
    intent: Optional[str] = None
    medication_code: Optional[str] = None
    medication_display: Optional[str] = None
    dosage_text: Optional[str] = None
    requester_display: Optional[str] = None
    authored_on: Optional[datetime] = None
    created_at: datetime


class ProcedureSchema(OrmModel):
    id: int
    resource_id: str
    patient_resource_id: Optional[str] = None
    encounter_resource_id: Optional[str] = None
    status: Optional[str] = None
    code: Optional[str] = None
    display: Optional[str] = None
    category: Optional[str] = None
    performer_display: Optional[str] = None
    performed_date: Optional[datetime] = None
    created_at: datetime


class DiagnosticReportSchema(OrmModel):
    id: int
    resource_id: str
    patient_resource_id: Optional[str] = None
    encounter_resource_id: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None
    code: Optional[str] = None
    display: Optional[str] = None
    conclusion: Optional[str] = None
    effective_date: Optional[datetime] = None
    issued_date: Optional[datetime] = None
    created_at: datetime


# ========== List schemas for bulk retrieval ==========
class PatientList(OrmModel):
    patients: List[PatientSchema]


class EncounterList(OrmModel):
    encounters: List[EncounterSchema]


class ConditionList(OrmModel):
    conditions: List[ConditionSchema]


class ObservationList(OrmModel):
    observations: List[ObservationSchema]


class MedicationRequestList(OrmModel):
    medication_requests: List[MedicationRequestSchema]


class ProcedureList(OrmModel):
    procedures: List[ProcedureSchema]


class DiagnosticReportList(OrmModel):
    diagnostic_reports: List[DiagnosticReportSchema]


class DocumentReferenceSchema(OrmModel):
    id: int
    resource_id: str
    patient_resource_id: Optional[str] = None
    encounter_resource_id: Optional[str] = None
    status: Optional[str] = None
    doc_status: Optional[str] = None
    type_code: Optional[str] = None
    type_display: Optional[str] = None
    category_code: Optional[str] = None
    description: Optional[str] = None
    author_display: Optional[str] = None
    custodian_display: Optional[str] = None
    created_date: Optional[datetime] = None
    created_at: datetime


class DocumentReferenceList(OrmModel):
    document_references: List[DocumentReferenceSchema]


class AllergyIntoleranceSchema(OrmModel):
    id: int
    resource_id: str
    patient_resource_id: Optional[str] = None
    encounter_resource_id: Optional[str] = None
    clinical_status: Optional[str] = None
    verification_status: Optional[str] = None
    type: Optional[str] = None
    category: Optional[str] = None
    criticality: Optional[str] = None
    code: Optional[str] = None
    display: Optional[str] = None
    recorder_display: Optional[str] = None
    onset_date: Optional[datetime] = None
    recorded_date: Optional[datetime] = None
    created_at: datetime


class AllergyIntoleranceList(OrmModel):
    allergy_intolerances: List[AllergyIntoleranceSchema]


class ImmunizationSchema(OrmModel):
    id: int
    resource_id: str
    patient_resource_id: Optional[str] = None
    encounter_resource_id: Optional[str] = None
    status: Optional[str] = None
    status_reason_code: Optional[str] = None
    vaccine_code: Optional[str] = None
    vaccine_display: Optional[str] = None
    primary_source: Optional[bool] = None
    performer_display: Optional[str] = None
    location_display: Optional[str] = None
    lot_number: Optional[str] = None
    occurrence_date: Optional[datetime] = None
    recorded_date: Optional[datetime] = None
    created_at: datetime


class ImmunizationList(OrmModel):
    immunizations: List[ImmunizationSchema]


class PractitionerSchema(OrmModel):
    id: int
    resource_id: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    prefix: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    npi: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address_line: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    active: Optional[bool] = None
    created_at: datetime


class PractitionerList(OrmModel):
    practitioners: List[PractitionerSchema]


class PractitionerRoleSchema(OrmModel):
    id: int
    resource_id: str
    practitioner_resource_id: Optional[str] = None
    organization_resource_id: Optional[str] = None
    active: Optional[bool] = None
    role_code: Optional[str] = None
    role_display: Optional[str] = None
    specialty_code: Optional[str] = None
    specialty_display: Optional[str] = None
    location_resource_id: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime


class PractitionerRoleList(OrmModel):
    practitioner_roles: List[PractitionerRoleSchema]


class OrganizationSchema(OrmModel):
    id: int
    resource_id: str
    name: Optional[str] = None
    active: Optional[bool] = None
    type_code: Optional[str] = None
    type_display: Optional[str] = None
    npi: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address_line: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    created_at: datetime


class OrganizationList(OrmModel):
    organizations: List[OrganizationSchema]


# ========== FHIR Proxy API schemas ==========
class FHIRFileInfo(OrmModel):
    fileName: str
    url: str


class FHIRManifest(OrmModel):
    files: List[FHIRFileInfo]
    exportId: str


# ========== Ingestion response ==========
class IngestionResult(OrmModel):
    status: str
    message: str
    files_processed: List[str]
    patients_created: int
    encounters_created: int
    conditions_created: int
    observations_created: int
    medication_requests_created: int
    procedures_created: int
    diagnostic_reports_created: int
    document_references_created: int
    allergy_intolerances_created: int
    immunizations_created: int
    practitioners_created: int
    practitioner_roles_created: int
    organizations_created: int
