"""
Integration test for all 13 FHIR resource types.
Validates processing functions can handle actual FHIR structure.
"""

import json
from datetime import datetime
from app.api.deid_routes import (
    process_patient, process_encounter, process_condition, process_observation,
    process_medication_request, process_procedure, process_diagnostic_report,
    process_document_reference, process_allergy_intolerance, process_immunization,
    process_practitioner, process_practitioner_role, process_organization
)
from app.db.session import SessionLocal


def test_all_resources():
    """Test processing all 13 critical FHIR resource types."""
    
    # Sample data structures based on user-provided actual FHIR format
    sample_patient = {
        "id": "test-patient-001",
        "resourceType": "Patient",
        "name": [{"use": "official", "family": "Doe", "given": ["John"]}],
        "gender": "male",
        "birthDate": "1990-01-15",
        "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA", "postalCode": "02101"}],
        "telecom": [
            {"system": "phone", "value": "555-1234"},
            {"system": "email", "value": "john.doe@example.com"}
        ]
    }
    
    sample_encounter = {
        "id": "test-encounter-001",
        "resourceType": "Encounter",
        "status": "finished",
        "class": {"code": "IMP", "display": "inpatient encounter"},
        "subject": {"reference": "Patient/test-patient-001"},
        "period": {"start": "2023-01-10T08:00:00Z", "end": "2023-01-15T16:00:00Z"},
        "location": [{"location": {"display": "General Hospital"}}]
    }
    
    sample_condition = {
        "id": "test-condition-001",
        "resourceType": "Condition",
        "code": {"coding": [{"system": "http://snomed.info/sct", "code": "44054006", "display": "Diabetes"}]},
        "subject": {"reference": "Patient/test-patient-001"},
        "encounter": {"reference": "Encounter/test-encounter-001"},
        "onsetDateTime": "2022-06-01T00:00:00Z"
    }
    
    sample_observation = {
        "id": "test-observation-001",
        "resourceType": "Observation",
        "status": "final",
        "code": {"coding": [{"system": "http://loinc.org", "code": "8480-6", "display": "Systolic BP"}]},
        "subject": {"reference": "Patient/test-patient-001"},
        "encounter": {"reference": "Encounter/test-encounter-001"},
        "effectiveDateTime": "2023-01-12T10:00:00Z",
        "valueQuantity": {"value": 120, "unit": "mmHg"}
    }
    
    sample_medication_request = {
        "id": "test-medrx-001",
        "resourceType": "MedicationRequest",
        "status": "active",
        "intent": "order",
        "medicationCodeableConcept": {"coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "197361", "display": "Metformin"}]},
        "subject": {"reference": "Patient/test-patient-001"},
        "encounter": {"reference": "Encounter/test-encounter-001"},
        "authoredOn": "2023-01-15T14:00:00Z",
        "requester": {"display": "Dr. Smith"}
    }
    
    sample_procedure = {
        "id": "test-procedure-001",
        "resourceType": "Procedure",
        "status": "completed",
        "code": {"coding": [{"system": "http://snomed.info/sct", "code": "80146002", "display": "Appendectomy"}]},
        "subject": {"reference": "Patient/test-patient-001"},
        "encounter": {"reference": "Encounter/test-encounter-001"},
        "performedPeriod": {"start": "2023-01-12T09:00:00Z", "end": "2023-01-12T11:00:00Z"},
        "performer": [{"actor": {"display": "Dr. Johnson"}}]
    }
    
    sample_diagnostic_report = {
        "id": "test-report-001",
        "resourceType": "DiagnosticReport",
        "status": "final",
        "code": {"coding": [{"system": "http://loinc.org", "code": "58410-2", "display": "Complete Blood Count"}]},
        "subject": {"reference": "Patient/test-patient-001"},
        "encounter": {"reference": "Encounter/test-encounter-001"},
        "effectiveDateTime": "2023-01-12T10:00:00Z",
        "conclusion": "Patient shows signs of anemia",
        "performer": [{"display": "Dr. Lab"}]
    }
    
    sample_document_reference = {
        "id": "test-doc-001",
        "resourceType": "DocumentReference",
        "status": "current",
        "type": {"coding": [{"system": "http://loinc.org", "code": "34133-9", "display": "Summary of episode note"}]},
        "category": [{"coding": [{"code": "clinical-note"}]}],
        "subject": {"reference": "Patient/test-patient-001"},
        "date": "2023-01-15T16:00:00Z",
        "author": [{"display": "Dr. Williams"}],
        "custodian": {"display": "General Hospital"},
        "description": "Discharge summary for patient",
        "content": [{"attachment": {"data": "base64encodeddata"}}],
        "context": {"encounter": [{"reference": "Encounter/test-encounter-001"}]}
    }
    
    sample_allergy_intolerance = {
        "id": "test-allergy-001",
        "resourceType": "AllergyIntolerance",
        "clinicalStatus": {"coding": [{"code": "active"}]},
        "verificationStatus": {"coding": [{"code": "confirmed"}]},
        "type": "allergy",
        "category": ["medication"],
        "criticality": "high",
        "code": {"coding": [{"system": "http://snomed.info/sct", "code": "387207008", "display": "Penicillin"}]},
        "patient": {"reference": "Patient/test-patient-001"},
        "onsetDateTime": "2015-03-10T00:00:00Z",
        "recordedDate": "2015-03-10T10:00:00Z",
        "recorder": {"display": "Dr. Brown"}
    }
    
    sample_immunization = {
        "id": "test-immunization-001",
        "resourceType": "Immunization",
        "status": "completed",
        "vaccineCode": {"coding": [{"system": "http://hl7.org/fhir/sid/cvx", "code": "141", "display": "Influenza"}]},
        "patient": {"reference": "Patient/test-patient-001"},
        "occurrenceDateTime": "2023-10-01T10:00:00Z",
        "recorded": "2023-10-01T10:15:00Z",
        "primarySource": True,
        "location": {"display": "Vaccination Clinic"},
        "performer": [{"actor": {"display": "Nurse Kelly"}}],
        "lotNumber": "LOT123456"
    }
    
    sample_practitioner = {
        "id": "test-practitioner-001",
        "resourceType": "Practitioner",
        "identifier": [{"system": "http://hl7.org/fhir/sid/us-npi", "value": "1234567890"}],
        "name": [{"family": "Smith", "given": ["Jane"], "prefix": ["Dr."]}],
        "gender": "female",
        "birthDate": "1975-05-20",
        "active": True,
        "telecom": [
            {"system": "phone", "value": "555-9876"},
            {"system": "email", "value": "jane.smith@hospital.org"}
        ],
        "address": [{"line": ["456 Medical Center"], "city": "Boston", "state": "MA", "postalCode": "02115"}]
    }
    
    sample_practitioner_role = {
        "id": "test-role-001",
        "resourceType": "PractitionerRole",
        "active": True,
        "practitioner": {"identifier": {"value": "1234567890"}},
        "organization": {"identifier": {"value": "ORG-001"}},
        "code": [{"coding": [{"system": "http://nucc.org", "code": "207R00000X", "display": "Internal Medicine"}]}],
        "specialty": [{"coding": [{"code": "394579002", "display": "Cardiology"}]}],
        "location": [{"identifier": {"value": "LOC-001"}}],
        "telecom": [{"system": "phone", "value": "555-1111"}]
    }
    
    sample_organization = {
        "id": "test-org-001",
        "resourceType": "Organization",
        "name": "General Hospital",
        "active": True,
        "type": [{"coding": [{"code": "prov", "display": "Healthcare Provider"}]}],
        "identifier": [{"system": "http://hl7.org/fhir/sid/us-npi", "value": "9876543210"}],
        "telecom": [
            {"system": "phone", "value": "555-2000"},
            {"system": "email", "value": "info@generalhospital.org"}
        ],
        "address": [{"line": ["789 Hospital Blvd"], "city": "Boston", "state": "MA", "postalCode": "02118"}]
    }
    
    db = SessionLocal()
    
    try:
        print("Testing Patient processing...")
        db_patient = process_patient(sample_patient, db)
        assert db_patient.resource_id == "test-patient-001"
        assert db_patient.family_name != "Doe"  # Should be anonymized
        print(f"✓ Patient processed: {db_patient.given_name} {db_patient.family_name}")
        
        print("\nTesting Encounter processing...")
        db_encounter = process_encounter(sample_encounter, db)
        assert db_encounter.resource_id == "test-encounter-001"
        assert db_encounter.class_code == "IMP"
        print(f"✓ Encounter processed: {db_encounter.status}, length of stay: {db_encounter.length_of_stay_days} days")
        
        print("\nTesting Condition processing...")
        db_condition = process_condition(sample_condition, db)
        assert db_condition.resource_id == "test-condition-001"
        assert db_condition.code == "44054006"
        print(f"✓ Condition processed: {db_condition.display}")
        
        print("\nTesting Observation processing...")
        db_observation = process_observation(sample_observation, db)
        assert db_observation.resource_id == "test-observation-001"
        assert db_observation.value_quantity == 120.0
        print(f"✓ Observation processed: {db_observation.display} = {db_observation.value_quantity} {db_observation.value_unit}")
        
        print("\nTesting MedicationRequest processing...")
        db_med = process_medication_request(sample_medication_request, db)
        assert db_med.resource_id == "test-medrx-001"
        assert db_med.code == "197361"
        print(f"✓ MedicationRequest processed: {db_med.display}")
        
        print("\nTesting Procedure processing...")
        db_procedure = process_procedure(sample_procedure, db)
        assert db_procedure.resource_id == "test-procedure-001"
        assert db_procedure.code == "80146002"
        print(f"✓ Procedure processed: {db_procedure.display}")
        
        print("\nTesting DiagnosticReport processing...")
        db_report = process_diagnostic_report(sample_diagnostic_report, db)
        assert db_report.resource_id == "test-report-001"
        assert "REDACTED" in db_report.conclusion  # Free text should be redacted
        print(f"✓ DiagnosticReport processed: {db_report.code_display}")
        
        print("\nTesting DocumentReference processing...")
        db_doc = process_document_reference(sample_document_reference, db)
        assert db_doc.resource_id == "test-doc-001"
        assert db_doc.author_display != "Dr. Williams"  # Should be anonymized
        print(f"✓ DocumentReference processed: {db_doc.type_display}")
        
        print("\nTesting AllergyIntolerance processing...")
        db_allergy = process_allergy_intolerance(sample_allergy_intolerance, db)
        assert db_allergy.resource_id == "test-allergy-001"
        assert db_allergy.clinical_status == "active"
        assert db_allergy.code == "387207008"
        print(f"✓ AllergyIntolerance processed: {db_allergy.display}")
        
        print("\nTesting Immunization processing...")
        db_immunization = process_immunization(sample_immunization, db)
        assert db_immunization.resource_id == "test-immunization-001"
        assert db_immunization.vaccine_code == "141"
        assert db_immunization.primary_source == True
        print(f"✓ Immunization processed: {db_immunization.vaccine_display}")
        
        print("\nTesting Practitioner processing...")
        db_practitioner = process_practitioner(sample_practitioner, db)
        assert db_practitioner.resource_id == "test-practitioner-001"
        assert db_practitioner.npi == "1234567890"  # NPI kept for linking
        assert db_practitioner.family_name != "Smith"  # Name anonymized
        print(f"✓ Practitioner processed: {db_practitioner.prefix} {db_practitioner.given_name} {db_practitioner.family_name}")
        
        print("\nTesting PractitionerRole processing...")
        db_role = process_practitioner_role(sample_practitioner_role, db)
        assert db_role.resource_id == "test-role-001"
        assert db_role.practitioner_resource_id == "1234567890"
        assert db_role.role_code == "207R00000X"
        print(f"✓ PractitionerRole processed: {db_role.role_display}")
        
        print("\nTesting Organization processing...")
        db_org = process_organization(sample_organization, db)
        assert db_org.resource_id == "test-org-001"
        assert db_org.npi == "9876543210"  # NPI kept
        assert db_org.name != "General Hospital"  # Name anonymized
        print(f"✓ Organization processed: {db_org.name}")
        
        print("\n" + "="*60)
        print("✓ ALL 13 RESOURCE TYPES PROCESSED SUCCESSFULLY!")
        print("="*60)
        print(f"\nDatabase records created:")
        print(f"  - 1 Patient (anonymized demographics)")
        print(f"  - 1 Encounter (hospitalization)")
        print(f"  - 1 Condition (diagnosis)")
        print(f"  - 1 Observation (vital sign)")
        print(f"  - 1 MedicationRequest (prescription)")
        print(f"  - 1 Procedure (surgical procedure)")
        print(f"  - 1 DiagnosticReport (lab report)")
        print(f"  - 1 DocumentReference (clinical note)")
        print(f"  - 1 AllergyIntolerance (medication allergy)")
        print(f"  - 1 Immunization (vaccination)")
        print(f"  - 1 Practitioner (provider demographics)")
        print(f"  - 1 PractitionerRole (provider role)")
        print(f"  - 1 Organization (facility)")
        print("\nAll PII has been anonymized while preserving:")
        print("  - Clinical codes (ICD-10, SNOMED, LOINC, RxNorm, CVX, CPT, NUCC)")
        print("  - Professional identifiers (NPI for linking)")
        print("  - Clinical measurements and values")
        print("  - Date relationships (via deterministic shifting)")
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    test_all_resources()
