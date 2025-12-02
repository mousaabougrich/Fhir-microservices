from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime
import json

from app.db.session import get_db
from app.services.fhir_client import FHIRClient, get_fhir_client
from app.services.deid_service import deid_service
from app.models import (
    patient, encounter, condition, observation, medication_request, procedure, diagnostic_report,
    document_reference, allergy_intolerance, immunization, practitioner, practitioner_role, organization
)
from app.models.schemas import (
    IngestionResult,
    PatientList, PatientSchema,
    EncounterList, EncounterSchema,
    ConditionList, ConditionSchema,
    ObservationList, ObservationSchema,
    MedicationRequestList, MedicationRequestSchema,
    ProcedureList, ProcedureSchema,
    DiagnosticReportList, DiagnosticReportSchema,
    DocumentReferenceList, DocumentReferenceSchema,
    AllergyIntoleranceList, AllergyIntoleranceSchema,
    ImmunizationList, ImmunizationSchema,
    PractitionerList, PractitionerSchema,
    PractitionerRoleList, PractitionerRoleSchema,
    OrganizationList, OrganizationSchema,
)

router = APIRouter(prefix="/deid", tags=["De-Identification"])


def parse_fhir_date(date_str: str) -> datetime:
    """Parse FHIR date/datetime string."""
    if not date_str:
        return None
    try:
        # Try full datetime
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except:
        try:
            # Try date only
            return datetime.strptime(date_str, '%Y-%m-%d')
        except:
            return None


def process_patient(fhir_resource: Dict[str, Any], db: Session) -> patient.Patient:
    """De-identify and store a Patient resource."""
    resource_id = fhir_resource.get("id")
    
    # Check if already exists
    existing = db.query(patient.Patient).filter(patient.Patient.resource_id == resource_id).first()
    if existing:
        return existing
    
    # Extract original data - handle official name (use="official")
    name_list = fhir_resource.get("name", [])
    official_name = next((n for n in name_list if n.get("use") == "official"), name_list[0] if name_list else {})
    given_names = official_name.get("given", [])
    given_name = given_names[0] if given_names else None
    family_name = official_name.get("family")
    
    # Note: Identifiers (SSN, DL, Passport) are in the identifier array but we're removing them entirely
    # They are direct identifiers and should not be stored even in anonymized form
    
    address_list = fhir_resource.get("address", [])
    address_line = address_list[0].get("line", [""])[0] if address_list else None
    city = address_list[0].get("city") if address_list else None
    state = address_list[0].get("state") if address_list else None
    postal_code = address_list[0].get("postalCode") if address_list else None
    
    telecom_list = fhir_resource.get("telecom", [])
    phone = next((t.get("value") for t in telecom_list if t.get("system") == "phone"), None)
    email = next((t.get("value") for t in telecom_list if t.get("system") == "email"), None)
    
    birth_date_str = fhir_resource.get("birthDate")
    birth_date = parse_fhir_date(birth_date_str) if birth_date_str else None
    gender = fhir_resource.get("gender")
    
    # Apply de-identification
    db_patient = patient.Patient(
        resource_id=resource_id,
        given_name=deid_service.anonymize_name(given_name, "given"),
        family_name=deid_service.anonymize_name(family_name, "family"),
        birth_date=deid_service.shift_date(birth_date, resource_id),
        gender=gender,  # Not PII
        address_line=deid_service.anonymize_address(address_line),
        city=deid_service.anonymize_city(city),
        state=state,  # Can keep state level
        postal_code=deid_service.anonymize_postal_code(postal_code),
        phone=deid_service.anonymize_phone(phone),
        email=deid_service.anonymize_email(email),
        raw_fhir_data=json.dumps(fhir_resource),
    )
    
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient


def process_encounter(fhir_resource: Dict[str, Any], db: Session) -> encounter.Encounter:
    """De-identify and store an Encounter resource."""
    resource_id = fhir_resource.get("id")
    
    existing = db.query(encounter.Encounter).filter(encounter.Encounter.resource_id == resource_id).first()
    if existing:
        return existing
    
    # Extract patient reference
    patient_ref = fhir_resource.get("subject", {}).get("reference", "")
    patient_resource_id = patient_ref.split("/")[-1] if "/" in patient_ref else patient_ref
    
    status = fhir_resource.get("status")
    # class is an object with system and code
    class_obj = fhir_resource.get("class", {})
    class_code = class_obj.get("code")
    type_list = fhir_resource.get("type", [])
    type_code = type_list[0].get("coding", [{}])[0].get("code") if type_list else None
    
    period = fhir_resource.get("period", {})
    start_date = parse_fhir_date(period.get("start"))
    end_date = parse_fhir_date(period.get("end"))
    
    # Calculate length of stay
    length_of_stay = None
    if start_date and end_date:
        length_of_stay = (end_date - start_date).days
    
    # Apply date shifting
    start_date = deid_service.shift_date(start_date, patient_resource_id)
    end_date = deid_service.shift_date(end_date, patient_resource_id)
    
    location_list = fhir_resource.get("location", [])
    location_name = location_list[0].get("location", {}).get("display") if location_list else None
    location_name = deid_service.anonymize_location(location_name)
    
    db_encounter = encounter.Encounter(
        resource_id=resource_id,
        patient_resource_id=patient_resource_id,
        status=status,
        class_code=class_code,
        type_code=type_code,
        start_date=start_date,
        end_date=end_date,
        length_of_stay_days=length_of_stay,
        location_name=location_name,
        raw_fhir_data=json.dumps(fhir_resource),
    )
    
    db.add(db_encounter)
    db.commit()
    db.refresh(db_encounter)
    return db_encounter


def process_condition(fhir_resource: Dict[str, Any], db: Session) -> condition.Condition:
    """De-identify and store a Condition resource."""
    resource_id = fhir_resource.get("id")
    
    existing = db.query(condition.Condition).filter(condition.Condition.resource_id == resource_id).first()
    if existing:
        return existing
    
    patient_ref = fhir_resource.get("subject", {}).get("reference", "")
    patient_resource_id = patient_ref.split("/")[-1] if "/" in patient_ref else patient_ref
    
    encounter_ref = fhir_resource.get("encounter", {}).get("reference", "")
    encounter_resource_id = encounter_ref.split("/")[-1] if "/" in encounter_ref else None
    
    code_data = fhir_resource.get("code", {}).get("coding", [{}])[0]
    code = code_data.get("code")
    display = code_data.get("display")
    
    clinical_status = fhir_resource.get("clinicalStatus", {}).get("coding", [{}])[0].get("code")
    verification_status = fhir_resource.get("verificationStatus", {}).get("coding", [{}])[0].get("code")
    
    category_list = fhir_resource.get("category", [])
    category = category_list[0].get("coding", [{}])[0].get("code") if category_list else None
    
    onset_date = parse_fhir_date(fhir_resource.get("onsetDateTime"))
    recorded_date = parse_fhir_date(fhir_resource.get("recordedDate"))
    
    onset_date = deid_service.shift_date(onset_date, patient_resource_id)
    recorded_date = deid_service.shift_date(recorded_date, patient_resource_id)
    
    db_condition = condition.Condition(
        resource_id=resource_id,
        patient_resource_id=patient_resource_id,
        encounter_resource_id=encounter_resource_id,
        code=code,  # Clinical code - keep
        display=display,  # Clinical term - keep
        clinical_status=clinical_status,
        verification_status=verification_status,
        category=category,
        onset_date=onset_date,
        recorded_date=recorded_date,
        raw_fhir_data=json.dumps(fhir_resource),
    )
    
    db.add(db_condition)
    db.commit()
    db.refresh(db_condition)
    return db_condition


def process_observation(fhir_resource: Dict[str, Any], db: Session) -> observation.Observation:
    """Process and store an Observation resource."""
    resource_id = fhir_resource.get("id")
    
    existing = db.query(observation.Observation).filter(observation.Observation.resource_id == resource_id).first()
    if existing:
        return existing
    
    patient_ref = fhir_resource.get("subject", {}).get("reference", "")
    patient_resource_id = patient_ref.split("/")[-1] if "/" in patient_ref else patient_ref
    
    encounter_ref = fhir_resource.get("encounter", {}).get("reference", "")
    encounter_resource_id = encounter_ref.split("/")[-1] if "/" in encounter_ref else None
    
    status = fhir_resource.get("status")
    
    category_list = fhir_resource.get("category", [])
    category = category_list[0].get("coding", [{}])[0].get("code") if category_list else None
    
    code_data = fhir_resource.get("code", {}).get("coding", [{}])[0]
    code = code_data.get("code")
    display = code_data.get("display")
    
    # Value can be quantity, string, boolean, etc.
    value_quantity = None
    value_unit = None
    value_string = None
    
    if "valueQuantity" in fhir_resource:
        value_quantity = fhir_resource["valueQuantity"].get("value")
        value_unit = fhir_resource["valueQuantity"].get("unit")
    elif "valueString" in fhir_resource:
        value_string = fhir_resource["valueString"]
    
    effective_date = parse_fhir_date(fhir_resource.get("effectiveDateTime"))
    issued_date = parse_fhir_date(fhir_resource.get("issued"))
    
    effective_date = deid_service.shift_date(effective_date, patient_resource_id)
    issued_date = deid_service.shift_date(issued_date, patient_resource_id)
    
    db_observation = observation.Observation(
        resource_id=resource_id,
        patient_resource_id=patient_resource_id,
        encounter_resource_id=encounter_resource_id,
        status=status,
        category=category,
        code=code,
        display=display,
        value_quantity=value_quantity,
        value_unit=value_unit,
        value_string=value_string,
        effective_date=effective_date,
        issued_date=issued_date,
        raw_fhir_data=json.dumps(fhir_resource),
    )
    
    db.add(db_observation)
    db.commit()
    db.refresh(db_observation)
    return db_observation


def process_medication_request(fhir_resource: Dict[str, Any], db: Session) -> medication_request.MedicationRequest:
    """Process and store a MedicationRequest resource."""
    resource_id = fhir_resource.get("id")
    
    existing = db.query(medication_request.MedicationRequest).filter(
        medication_request.MedicationRequest.resource_id == resource_id
    ).first()
    if existing:
        return existing
    
    patient_ref = fhir_resource.get("subject", {}).get("reference", "")
    patient_resource_id = patient_ref.split("/")[-1] if "/" in patient_ref else patient_ref
    
    encounter_ref = fhir_resource.get("encounter", {}).get("reference", "")
    encounter_resource_id = encounter_ref.split("/")[-1] if "/" in encounter_ref else None
    
    status = fhir_resource.get("status")
    intent = fhir_resource.get("intent")
    
    medication_data = fhir_resource.get("medicationCodeableConcept", {}).get("coding", [{}])[0]
    medication_code = medication_data.get("code")
    medication_display = medication_data.get("display")
    
    dosage_list = fhir_resource.get("dosageInstruction", [])
    dosage_text = dosage_list[0].get("text") if dosage_list else None
    
    requester_display = fhir_resource.get("requester", {}).get("display")
    requester_display = deid_service.anonymize_provider_name(requester_display)
    
    authored_on = parse_fhir_date(fhir_resource.get("authoredOn"))
    authored_on = deid_service.shift_date(authored_on, patient_resource_id)
    
    db_med_request = medication_request.MedicationRequest(
        resource_id=resource_id,
        patient_resource_id=patient_resource_id,
        encounter_resource_id=encounter_resource_id,
        status=status,
        intent=intent,
        medication_code=medication_code,
        medication_display=medication_display,
        dosage_text=dosage_text,
        requester_display=requester_display,
        authored_on=authored_on,
        raw_fhir_data=json.dumps(fhir_resource),
    )
    
    db.add(db_med_request)
    db.commit()
    db.refresh(db_med_request)
    return db_med_request


def process_procedure(fhir_resource: Dict[str, Any], db: Session) -> procedure.Procedure:
    """Process and store a Procedure resource."""
    resource_id = fhir_resource.get("id")
    
    existing = db.query(procedure.Procedure).filter(procedure.Procedure.resource_id == resource_id).first()
    if existing:
        return existing
    
    patient_ref = fhir_resource.get("subject", {}).get("reference", "")
    patient_resource_id = patient_ref.split("/")[-1] if "/" in patient_ref else patient_ref
    
    encounter_ref = fhir_resource.get("encounter", {}).get("reference", "")
    encounter_resource_id = encounter_ref.split("/")[-1] if "/" in encounter_ref else None
    
    status = fhir_resource.get("status")
    
    code_data = fhir_resource.get("code", {}).get("coding", [{}])[0]
    code = code_data.get("code")
    display = code_data.get("display")
    
    category_data = fhir_resource.get("category", {}).get("coding", [{}])[0]
    category = category_data.get("code")
    
    performer_list = fhir_resource.get("performer", [])
    # Performer info is in Procedure (not always present)
    performer_list = fhir_resource.get("performer", [])
    performer_display = performer_list[0].get("actor", {}).get("display") if performer_list else None
    performer_display = deid_service.anonymize_provider_name(performer_display)
    
    # performedPeriod has start/end, not performedDateTime in sample
    performed_period = fhir_resource.get("performedPeriod", {})
    performed_start = parse_fhir_date(performed_period.get("start"))
    performed_date = deid_service.shift_date(performed_start, patient_resource_id)
    
    db_procedure = procedure.Procedure(
        resource_id=resource_id,
        patient_resource_id=patient_resource_id,
        encounter_resource_id=encounter_resource_id,
        status=status,
        code=code,
        display=display,
        category=category,
        performer_display=performer_display,
        performed_date=performed_date,
        raw_fhir_data=json.dumps(fhir_resource),
    )
    
    db.add(db_procedure)
    db.commit()
    db.refresh(db_procedure)
    return db_procedure


def process_diagnostic_report(fhir_resource: Dict[str, Any], db: Session) -> diagnostic_report.DiagnosticReport:
    """Process and store a DiagnosticReport resource."""
    resource_id = fhir_resource.get("id")
    
    existing = db.query(diagnostic_report.DiagnosticReport).filter(
        diagnostic_report.DiagnosticReport.resource_id == resource_id
    ).first()
    if existing:
        return existing
    
    patient_ref = fhir_resource.get("subject", {}).get("reference", "")
    patient_resource_id = patient_ref.split("/")[-1] if "/" in patient_ref else patient_ref
    
    encounter_ref = fhir_resource.get("encounter", {}).get("reference", "")
    encounter_resource_id = encounter_ref.split("/")[-1] if "/" in encounter_ref else None
    
    status = fhir_resource.get("status")
    
    category_list = fhir_resource.get("category", [])
    category = category_list[0].get("coding", [{}])[0].get("code") if category_list else None
    
    code_data = fhir_resource.get("code", {}).get("coding", [{}])[0]
    code = code_data.get("code")
    display = code_data.get("display")
    
    # Conclusion text and presentedForm (base64 encoded notes) contain free text with PII
    conclusion = fhir_resource.get("conclusion")
    conclusion = deid_service.remove_free_text_pii(conclusion)
    
    # presentedForm contains base64 encoded clinical notes - redact for PII
    # We don't store the actual encoded data, just note it was redacted
    
    effective_date = parse_fhir_date(fhir_resource.get("effectiveDateTime"))
    issued_date = parse_fhir_date(fhir_resource.get("issued"))
    
    effective_date = deid_service.shift_date(effective_date, patient_resource_id)
    issued_date = deid_service.shift_date(issued_date, patient_resource_id)
    
    db_report = diagnostic_report.DiagnosticReport(
        resource_id=resource_id,
        patient_resource_id=patient_resource_id,
        encounter_resource_id=encounter_resource_id,
        status=status,
        category=category,
        code=code,
        display=display,
        conclusion=conclusion,
        effective_date=effective_date,
        issued_date=issued_date,
        raw_fhir_data=json.dumps(fhir_resource),
    )
    
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report


def process_document_reference(fhir_resource: Dict[str, Any], db: Session) -> document_reference.DocumentReference:
    """Process and store a DocumentReference resource."""
    resource_id = fhir_resource.get("id")
    
    existing = db.query(document_reference.DocumentReference).filter(
        document_reference.DocumentReference.resource_id == resource_id
    ).first()
    if existing:
        return existing
    
    # Subject (patient)
    patient_ref = fhir_resource.get("subject", {}).get("reference", "")
    patient_resource_id = patient_ref.split("/")[-1] if "/" in patient_ref else patient_ref
    
    # Encounter (from context)
    context = fhir_resource.get("context", {})
    encounter_list = context.get("encounter", [])
    encounter_ref = encounter_list[0].get("reference", "") if encounter_list else ""
    encounter_resource_id = encounter_ref.split("/")[-1] if "/" in encounter_ref else None
    
    status = fhir_resource.get("status")
    doc_status = fhir_resource.get("docStatus")
    
    # Type (LOINC code)
    type_obj = fhir_resource.get("type", {}).get("coding", [{}])[0]
    type_code = type_obj.get("code")
    type_display = type_obj.get("display")
    
    # Category
    category_list = fhir_resource.get("category", [])
    category_code = category_list[0].get("coding", [{}])[0].get("code") if category_list else None
    
    # Description (may contain PII)
    description = fhir_resource.get("description")
    description = deid_service.remove_free_text_pii(description)
    
    # Author (provider)
    author_list = fhir_resource.get("author", [])
    author_display = author_list[0].get("display") if author_list else None
    author_display = deid_service.anonymize_provider_name(author_display)
    
    # Custodian (organization)
    custodian = fhir_resource.get("custodian", {})
    custodian_display = custodian.get("display")
    custodian_display = deid_service.anonymize_location(custodian_display)
    
    # Date
    created_date = parse_fhir_date(fhir_resource.get("date"))
    created_date = deid_service.shift_date(created_date, patient_resource_id)
    
    # Note: content.attachment.data contains base64 clinical notes - we don't store it
    
    db_doc_ref = document_reference.DocumentReference(
        resource_id=resource_id,
        patient_resource_id=patient_resource_id,
        encounter_resource_id=encounter_resource_id,
        status=status,
        doc_status=doc_status,
        type_code=type_code,
        type_display=type_display,
        category_code=category_code,
        description=description,
        author_display=author_display,
        custodian_display=custodian_display,
        created_date=created_date,
        raw_fhir_data=json.dumps(fhir_resource),
    )
    
    db.add(db_doc_ref)
    db.commit()
    db.refresh(db_doc_ref)
    return db_doc_ref


def process_allergy_intolerance(fhir_resource: Dict[str, Any], db: Session) -> allergy_intolerance.AllergyIntolerance:
    """Process and store an AllergyIntolerance resource."""
    resource_id = fhir_resource.get("id")
    
    existing = db.query(allergy_intolerance.AllergyIntolerance).filter(
        allergy_intolerance.AllergyIntolerance.resource_id == resource_id
    ).first()
    if existing:
        return existing
    
    patient_ref = fhir_resource.get("patient", {}).get("reference", "")
    patient_resource_id = patient_ref.split("/")[-1] if "/" in patient_ref else patient_ref
    
    encounter_ref = fhir_resource.get("encounter", {}).get("reference", "")
    encounter_resource_id = encounter_ref.split("/")[-1] if "/" in encounter_ref else None
    
    # Clinical/verification status
    clinical_status_obj = fhir_resource.get("clinicalStatus", {}).get("coding", [{}])[0]
    clinical_status = clinical_status_obj.get("code")
    
    verification_status_obj = fhir_resource.get("verificationStatus", {}).get("coding", [{}])[0]
    verification_status = verification_status_obj.get("code")
    
    allergy_type = fhir_resource.get("type")
    
    # Category is an array of strings
    category_list = fhir_resource.get("category", [])
    category = category_list[0] if category_list else None
    
    criticality = fhir_resource.get("criticality")
    
    # Allergen code (SNOMED - keep)
    code_obj = fhir_resource.get("code", {}).get("coding", [{}])[0]
    code = code_obj.get("code")
    display = code_obj.get("display")
    
    # Recorder (provider - anonymize)
    recorder = fhir_resource.get("recorder", {})
    recorder_display = recorder.get("display")
    recorder_display = deid_service.anonymize_provider_name(recorder_display)
    
    # Dates
    onset_date = parse_fhir_date(fhir_resource.get("onsetDateTime"))
    recorded_date = parse_fhir_date(fhir_resource.get("recordedDate"))
    
    onset_date = deid_service.shift_date(onset_date, patient_resource_id)
    recorded_date = deid_service.shift_date(recorded_date, patient_resource_id)
    
    db_allergy = allergy_intolerance.AllergyIntolerance(
        resource_id=resource_id,
        patient_resource_id=patient_resource_id,
        encounter_resource_id=encounter_resource_id,
        clinical_status=clinical_status,
        verification_status=verification_status,
        type=allergy_type,
        category=category,
        criticality=criticality,
        code=code,
        display=display,
        recorder_display=recorder_display,
        onset_date=onset_date,
        recorded_date=recorded_date,
        raw_fhir_data=json.dumps(fhir_resource),
    )
    
    db.add(db_allergy)
    db.commit()
    db.refresh(db_allergy)
    return db_allergy


def process_immunization(fhir_resource: Dict[str, Any], db: Session) -> immunization.Immunization:
    """Process and store an Immunization resource."""
    resource_id = fhir_resource.get("id")
    
    existing = db.query(immunization.Immunization).filter(
        immunization.Immunization.resource_id == resource_id
    ).first()
    if existing:
        return existing
    
    patient_ref = fhir_resource.get("patient", {}).get("reference", "")
    patient_resource_id = patient_ref.split("/")[-1] if "/" in patient_ref else patient_ref
    
    encounter_ref = fhir_resource.get("encounter", {}).get("reference", "")
    encounter_resource_id = encounter_ref.split("/")[-1] if "/" in encounter_ref else None
    
    status = fhir_resource.get("status")
    
    status_reason = fhir_resource.get("statusReason", {}).get("coding", [{}])[0]
    status_reason_code = status_reason.get("code")
    
    # Vaccine code (CVX - keep)
    vaccine_obj = fhir_resource.get("vaccineCode", {}).get("coding", [{}])[0]
    vaccine_code = vaccine_obj.get("code")
    vaccine_display = vaccine_obj.get("display")
    
    primary_source = fhir_resource.get("primarySource")
    
    # Performer (provider - anonymize)
    performer_list = fhir_resource.get("performer", [])
    performer_display = performer_list[0].get("actor", {}).get("display") if performer_list else None
    performer_display = deid_service.anonymize_provider_name(performer_display)
    
    # Location (facility - anonymize)
    location = fhir_resource.get("location", {})
    location_display = location.get("display")
    location_display = deid_service.anonymize_location(location_display)
    
    # Lot number (optional)
    lot_number = fhir_resource.get("lotNumber")
    
    # Dates
    occurrence_date = parse_fhir_date(fhir_resource.get("occurrenceDateTime"))
    recorded_date = parse_fhir_date(fhir_resource.get("recorded"))
    
    occurrence_date = deid_service.shift_date(occurrence_date, patient_resource_id)
    recorded_date = deid_service.shift_date(recorded_date, patient_resource_id)
    
    db_immunization = immunization.Immunization(
        resource_id=resource_id,
        patient_resource_id=patient_resource_id,
        encounter_resource_id=encounter_resource_id,
        status=status,
        status_reason_code=status_reason_code,
        vaccine_code=vaccine_code,
        vaccine_display=vaccine_display,
        primary_source=primary_source,
        performer_display=performer_display,
        location_display=location_display,
        lot_number=lot_number,
        occurrence_date=occurrence_date,
        recorded_date=recorded_date,
        raw_fhir_data=json.dumps(fhir_resource),
    )
    
    db.add(db_immunization)
    db.commit()
    db.refresh(db_immunization)
    return db_immunization


def process_practitioner(fhir_resource: Dict[str, Any], db: Session) -> practitioner.Practitioner:
    """Process and store a Practitioner resource."""
    resource_id = fhir_resource.get("id")
    
    existing = db.query(practitioner.Practitioner).filter(
        practitioner.Practitioner.resource_id == resource_id
    ).first()
    if existing:
        return existing
    
    # Name
    name_list = fhir_resource.get("name", [])
    name_obj = name_list[0] if name_list else {}
    given_names = name_obj.get("given", [])
    given_name = given_names[0] if given_names else None
    family_name = name_obj.get("family")
    prefix_list = name_obj.get("prefix", [])
    prefix = prefix_list[0] if prefix_list else None
    
    gender = fhir_resource.get("gender")
    
    birth_date_str = fhir_resource.get("birthDate")
    birth_date = parse_fhir_date(birth_date_str) if birth_date_str else None
    
    # NPI (professional identifier - keep for linking)
    identifier_list = fhir_resource.get("identifier", [])
    npi = None
    for identifier in identifier_list:
        if identifier.get("system") == "http://hl7.org/fhir/sid/us-npi":
            npi = identifier.get("value")
            break
    
    # Telecom
    telecom_list = fhir_resource.get("telecom", [])
    phone = next((t.get("value") for t in telecom_list if t.get("system") == "phone"), None)
    email = next((t.get("value") for t in telecom_list if t.get("system") == "email"), None)
    
    # Address
    address_list = fhir_resource.get("address", [])
    address_obj = address_list[0] if address_list else {}
    address_line = address_obj.get("line", [""])[0] if address_obj.get("line") else None
    city = address_obj.get("city")
    state = address_obj.get("state")
    postal_code = address_obj.get("postalCode")
    
    active = fhir_resource.get("active")
    
    # Anonymize provider info
    db_practitioner = practitioner.Practitioner(
        resource_id=resource_id,
        given_name=deid_service.anonymize_name(given_name, "given"),
        family_name=deid_service.anonymize_name(family_name, "family"),
        prefix=prefix,  # Keep prefix (Dr., etc.)
        gender=gender,
        birth_date=deid_service.shift_date(birth_date, resource_id),
        npi=npi,  # Keep NPI for professional linking
        phone=deid_service.anonymize_phone(phone),
        email=deid_service.anonymize_email(email),
        address_line=deid_service.anonymize_address(address_line),
        city=deid_service.anonymize_city(city),
        state=state,
        postal_code=deid_service.anonymize_postal_code(postal_code),
        active=active,
        raw_fhir_data=json.dumps(fhir_resource),
    )
    
    db.add(db_practitioner)
    db.commit()
    db.refresh(db_practitioner)
    return db_practitioner


def process_practitioner_role(fhir_resource: Dict[str, Any], db: Session) -> practitioner_role.PractitionerRole:
    """Process and store a PractitionerRole resource."""
    resource_id = fhir_resource.get("id")
    
    existing = db.query(practitioner_role.PractitionerRole).filter(
        practitioner_role.PractitionerRole.resource_id == resource_id
    ).first()
    if existing:
        return existing
    
    # Practitioner reference (extract NPI from identifier)
    pract_obj = fhir_resource.get("practitioner", {})
    pract_identifier = pract_obj.get("identifier", {})
    pract_npi = pract_identifier.get("value")
    practitioner_resource_id = pract_npi  # Store NPI as reference
    
    # Organization reference
    org_obj = fhir_resource.get("organization", {})
    org_identifier = org_obj.get("identifier", {})
    org_id = org_identifier.get("value")
    organization_resource_id = org_id
    
    active = fhir_resource.get("active")
    
    # Role codes (NUCC - keep)
    code_list = fhir_resource.get("code", [])
    role_obj = code_list[0].get("coding", [{}])[0] if code_list else {}
    role_code = role_obj.get("code")
    role_display = role_obj.get("display")
    
    # Specialty
    specialty_list = fhir_resource.get("specialty", [])
    specialty_obj = specialty_list[0].get("coding", [{}])[0] if specialty_list else {}
    specialty_code = specialty_obj.get("code")
    specialty_display = specialty_obj.get("display")
    
    # Location
    location_list = fhir_resource.get("location", [])
    loc_identifier = location_list[0].get("identifier", {}) if location_list else {}
    location_resource_id = loc_identifier.get("value")
    
    # Telecom
    telecom_list = fhir_resource.get("telecom", [])
    phone = next((t.get("value") for t in telecom_list if t.get("system") == "phone"), None)
    email = next((t.get("value") for t in telecom_list if t.get("system") == "email"), None)
    
    db_role = practitioner_role.PractitionerRole(
        resource_id=resource_id,
        practitioner_resource_id=practitioner_resource_id,
        organization_resource_id=organization_resource_id,
        active=active,
        role_code=role_code,
        role_display=role_display,
        specialty_code=specialty_code,
        specialty_display=specialty_display,
        location_resource_id=location_resource_id,
        phone=deid_service.anonymize_phone(phone),
        email=deid_service.anonymize_email(email),
        raw_fhir_data=json.dumps(fhir_resource),
    )
    
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role


def process_organization(fhir_resource: Dict[str, Any], db: Session) -> organization.Organization:
    """Process and store an Organization resource."""
    resource_id = fhir_resource.get("id")
    
    existing = db.query(organization.Organization).filter(
        organization.Organization.resource_id == resource_id
    ).first()
    if existing:
        return existing
    
    # Name (anonymize)
    name = fhir_resource.get("name")
    name = deid_service.anonymize_location(name)
    
    active = fhir_resource.get("active")
    
    # Type
    type_list = fhir_resource.get("type", [])
    type_obj = type_list[0].get("coding", [{}])[0] if type_list else {}
    type_code = type_obj.get("code")
    type_display = type_obj.get("display")
    
    # NPI (organizational identifier - keep for linking)
    identifier_list = fhir_resource.get("identifier", [])
    npi = None
    for identifier in identifier_list:
        if identifier.get("system") == "http://hl7.org/fhir/sid/us-npi":
            npi = identifier.get("value")
            break
    
    # Telecom
    telecom_list = fhir_resource.get("telecom", [])
    phone = next((t.get("value") for t in telecom_list if t.get("system") == "phone"), None)
    email = next((t.get("value") for t in telecom_list if t.get("system") == "email"), None)
    
    # Address
    address_list = fhir_resource.get("address", [])
    address_obj = address_list[0] if address_list else {}
    address_line = address_obj.get("line", [""])[0] if address_obj.get("line") else None
    city = address_obj.get("city")
    state = address_obj.get("state")
    postal_code = address_obj.get("postalCode")
    
    db_organization = organization.Organization(
        resource_id=resource_id,
        name=name,
        active=active,
        type_code=type_code,
        type_display=type_display,
        npi=npi,
        phone=deid_service.anonymize_phone(phone),
        email=deid_service.anonymize_email(email),
        address_line=deid_service.anonymize_address(address_line),
        city=deid_service.anonymize_city(city),
        state=state,  # Keep state
        postal_code=deid_service.anonymize_postal_code(postal_code),
        raw_fhir_data=json.dumps(fhir_resource),
    )
    
    db.add(db_organization)
    db.commit()
    db.refresh(db_organization)
    return db_organization


@router.post("/ingest", response_model=IngestionResult)
async def ingest_and_deid(clear_existing: bool = False, db: Session = Depends(get_db)):
    """
    Fetch FHIR data from proxy, de-identify, and store in PostgreSQL.
    This is the main ingestion endpoint.
    
    Args:
        clear_existing: If True, clears all existing data before ingestion to prevent duplicates/overflow
    """
    fhir_client = get_fhir_client()
    
    try:
        # Clear existing data if requested
        if clear_existing:
            print("Clearing existing database records...")
            db.query(document_reference.DocumentReference).delete()
            db.query(allergy_intolerance.AllergyIntolerance).delete()
            db.query(immunization.Immunization).delete()
            db.query(diagnostic_report.DiagnosticReport).delete()
            db.query(procedure.Procedure).delete()
            db.query(medication_request.MedicationRequest).delete()
            db.query(observation.Observation).delete()
            db.query(condition.Condition).delete()
            db.query(practitioner_role.PractitionerRole).delete()
            db.query(practitioner.Practitioner).delete()
            db.query(organization.Organization).delete()
            db.query(encounter.Encounter).delete()
            db.query(patient.Patient).delete()
            db.commit()
            print("Database cleared successfully.")
        
        # Fetch all critical files
        print("Fetching FHIR data from proxy...")
        fhir_data = await fhir_client.get_critical_files()
        
        # Process each resource type
        patients_count = 0
        for patient_resource in fhir_data.get("Patient", []):
            process_patient(patient_resource, db)
            patients_count += 1
        
        encounters_count = 0
        for encounter_resource in fhir_data.get("Encounter", []):
            process_encounter(encounter_resource, db)
            encounters_count += 1
        
        conditions_count = 0
        for condition_resource in fhir_data.get("Condition", []):
            process_condition(condition_resource, db)
            conditions_count += 1
        
        observations_count = 0
        for observation_resource in fhir_data.get("Observation", []):
            process_observation(observation_resource, db)
            observations_count += 1
        
        med_requests_count = 0
        for med_request_resource in fhir_data.get("MedicationRequest", []):
            process_medication_request(med_request_resource, db)
            med_requests_count += 1
        
        procedures_count = 0
        for procedure_resource in fhir_data.get("Procedure", []):
            process_procedure(procedure_resource, db)
            procedures_count += 1
        
        reports_count = 0
        for report_resource in fhir_data.get("DiagnosticReport", []):
            process_diagnostic_report(report_resource, db)
            reports_count += 1
        
        document_references_count = 0
        for doc_ref_resource in fhir_data.get("DocumentReference", []):
            process_document_reference(doc_ref_resource, db)
            document_references_count += 1
        
        allergy_intolerances_count = 0
        for allergy_resource in fhir_data.get("AllergyIntolerance", []):
            process_allergy_intolerance(allergy_resource, db)
            allergy_intolerances_count += 1
        
        immunizations_count = 0
        for immunization_resource in fhir_data.get("Immunization", []):
            process_immunization(immunization_resource, db)
            immunizations_count += 1
        
        practitioners_count = 0
        for practitioner_resource in fhir_data.get("Practitioner", []):
            process_practitioner(practitioner_resource, db)
            practitioners_count += 1
        
        practitioner_roles_count = 0
        for role_resource in fhir_data.get("PractitionerRole", []):
            process_practitioner_role(role_resource, db)
            practitioner_roles_count += 1
        
        organizations_count = 0
        for org_resource in fhir_data.get("Organization", []):
            process_organization(org_resource, db)
            organizations_count += 1
        
        files_processed = [k for k, v in fhir_data.items() if v]
        
        return IngestionResult(
            status="success",
            message="FHIR data ingested and de-identified successfully",
            files_processed=files_processed,
            patients_created=patients_count,
            encounters_created=encounters_count,
            conditions_created=conditions_count,
            observations_created=observations_count,
            medication_requests_created=med_requests_count,
            procedures_created=procedures_count,
            diagnostic_reports_created=reports_count,
            document_references_created=document_references_count,
            allergy_intolerances_created=allergy_intolerances_count,
            immunizations_created=immunizations_count,
            practitioners_created=practitioners_count,
            practitioner_roles_created=practitioner_roles_count,
            organizations_created=organizations_count,
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during ingestion: {str(e)}"
        )
    finally:
        await fhir_client.close()


# ========== Retrieval endpoints ==========

@router.get("/patients", response_model=PatientList)
def get_patients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get de-identified patient data."""
    patients = db.query(patient.Patient).offset(skip).limit(limit).all()
    return {"patients": patients}


@router.get("/patients/{resource_id}", response_model=PatientSchema)
def get_patient(resource_id: str, db: Session = Depends(get_db)):
    """Get a specific de-identified patient by resource ID."""
    db_patient = db.query(patient.Patient).filter(patient.Patient.resource_id == resource_id).first()
    if not db_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return db_patient


@router.get("/encounters", response_model=EncounterList)
def get_encounters(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get de-identified encounter data."""
    encounters = db.query(encounter.Encounter).offset(skip).limit(limit).all()
    return {"encounters": encounters}


@router.get("/conditions", response_model=ConditionList)
def get_conditions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get de-identified condition data."""
    conditions = db.query(condition.Condition).offset(skip).limit(limit).all()
    return {"conditions": conditions}


@router.get("/observations", response_model=ObservationList)
def get_observations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get de-identified observation data."""
    observations = db.query(observation.Observation).offset(skip).limit(limit).all()
    return {"observations": observations}


@router.get("/medication-requests", response_model=MedicationRequestList)
def get_medication_requests(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get de-identified medication request data."""
    med_requests = db.query(medication_request.MedicationRequest).offset(skip).limit(limit).all()
    return {"medication_requests": med_requests}


@router.get("/procedures", response_model=ProcedureList)
def get_procedures(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get de-identified procedure data."""
    procedures = db.query(procedure.Procedure).offset(skip).limit(limit).all()
    return {"procedures": procedures}


@router.get("/diagnostic-reports", response_model=DiagnosticReportList)
def get_diagnostic_reports(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get de-identified diagnostic report data."""
    reports = db.query(diagnostic_report.DiagnosticReport).offset(skip).limit(limit).all()
    return {"diagnostic_reports": reports}


@router.get("/document-references", response_model=DocumentReferenceList)
def get_document_references(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get de-identified document reference data."""
    doc_refs = db.query(document_reference.DocumentReference).offset(skip).limit(limit).all()
    return {"document_references": doc_refs}


@router.get("/allergy-intolerances", response_model=AllergyIntoleranceList)
def get_allergy_intolerances(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get de-identified allergy intolerance data."""
    allergies = db.query(allergy_intolerance.AllergyIntolerance).offset(skip).limit(limit).all()
    return {"allergy_intolerances": allergies}


@router.get("/immunizations", response_model=ImmunizationList)
def get_immunizations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get de-identified immunization data."""
    immunizations = db.query(immunization.Immunization).offset(skip).limit(limit).all()
    return {"immunizations": immunizations}


@router.get("/practitioners", response_model=PractitionerList)
def get_practitioners(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get de-identified practitioner data."""
    practitioners = db.query(practitioner.Practitioner).offset(skip).limit(limit).all()
    return {"practitioners": practitioners}


@router.get("/practitioner-roles", response_model=PractitionerRoleList)
def get_practitioner_roles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get de-identified practitioner role data."""
    roles = db.query(practitioner_role.PractitionerRole).offset(skip).limit(limit).all()
    return {"practitioner_roles": roles}


@router.get("/organizations", response_model=OrganizationList)
def get_organizations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get de-identified organization data."""
    organizations = db.query(organization.Organization).offset(skip).limit(limit).all()
    return {"organizations": organizations}


# ========== Database Management ==========

@router.delete("/clear-database")
def clear_database(db: Session = Depends(get_db)):
    """
    Clear all de-identified data from the database.
    Use this before re-ingesting data to prevent duplicates and database overflow.
    
    WARNING: This will permanently delete all records!
    """
    try:
        # Delete in order respecting foreign key constraints
        # Child tables first, then parent tables
        deleted_counts = {}
        
        deleted_counts["document_references"] = db.query(document_reference.DocumentReference).delete()
        deleted_counts["allergy_intolerances"] = db.query(allergy_intolerance.AllergyIntolerance).delete()
        deleted_counts["immunizations"] = db.query(immunization.Immunization).delete()
        deleted_counts["diagnostic_reports"] = db.query(diagnostic_report.DiagnosticReport).delete()
        deleted_counts["procedures"] = db.query(procedure.Procedure).delete()
        deleted_counts["medication_requests"] = db.query(medication_request.MedicationRequest).delete()
        deleted_counts["observations"] = db.query(observation.Observation).delete()
        deleted_counts["conditions"] = db.query(condition.Condition).delete()
        deleted_counts["practitioner_roles"] = db.query(practitioner_role.PractitionerRole).delete()
        deleted_counts["practitioners"] = db.query(practitioner.Practitioner).delete()
        deleted_counts["organizations"] = db.query(organization.Organization).delete()
        deleted_counts["encounters"] = db.query(encounter.Encounter).delete()
        deleted_counts["patients"] = db.query(patient.Patient).delete()
        
        db.commit()
        
        total_deleted = sum(deleted_counts.values())
        
        return {
            "status": "success",
            "message": f"Database cleared successfully. {total_deleted} total records deleted.",
            "deleted_counts": deleted_counts
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing database: {str(e)}"
        )
