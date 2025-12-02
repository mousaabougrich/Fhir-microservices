"""
Test script to validate FHIR parsing with sample data.
Run this to verify the de-identification logic works with real FHIR structure.
"""

import json
from datetime import datetime

# Sample data path
SAMPLE_FILE = "samples.ndjson"


def parse_ndjson(file_path: str):
    """Parse NDJSON file - handles both proper NDJSON and comma-separated multi-line JSON."""
    resources = []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Try to parse as array of objects (comma-separated)
    # Remove trailing comma if present
    content = content.strip()
    if content.endswith(','):
        content = content[:-1]
    
    # Wrap in array if not already
    if not content.startswith('['):
        content = '[' + content + ']'
    
    try:
        resources = json.loads(content)
        if not isinstance(resources, list):
            resources = [resources]
    except json.JSONDecodeError:
        # Fall back to line-by-line parsing
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and line != ',' and not line.startswith(('{', '}')):
                    try:
                        resources.append(json.loads(line.rstrip(',')))
                    except:
                        continue
    
    return resources


def test_patient_parsing(patient_resource):
    """Test Patient resource extraction."""
    print("\n=== Patient Resource ===")
    print(f"ID: {patient_resource.get('id')}")
    
    # Names
    name_list = patient_resource.get("name", [])
    official_name = next((n for n in name_list if n.get("use") == "official"), name_list[0] if name_list else {})
    given_names = official_name.get("given", [])
    family_name = official_name.get("family")
    print(f"Name: {' '.join(given_names)} {family_name}")
    
    # Identifiers (PII - should be removed)
    identifiers = patient_resource.get("identifier", [])
    for identifier in identifiers:
        id_type = identifier.get("type", {}).get("coding", [{}])[0].get("display", "Unknown")
        value = identifier.get("value")
        print(f"  Identifier ({id_type}): {value} [WILL BE REMOVED]")
    
    # Contact
    telecom = patient_resource.get("telecom", [])
    for contact in telecom:
        print(f"  {contact.get('system')}: {contact.get('value')}")
    
    # Address
    address = patient_resource.get("address", [{}])[0]
    print(f"  Address: {address.get('line', [''])[0]}, {address.get('city')}, {address.get('state')} {address.get('postalCode')}")
    
    print(f"  Birth Date: {patient_resource.get('birthDate')}")
    print(f"  Gender: {patient_resource.get('gender')}")


def test_encounter_parsing(encounter_resource):
    """Test Encounter resource extraction."""
    print("\n=== Encounter Resource ===")
    print(f"ID: {encounter_resource.get('id')}")
    print(f"Status: {encounter_resource.get('status')}")
    
    # Class is an object
    class_obj = encounter_resource.get("class", {})
    print(f"Class: {class_obj.get('code')}")
    
    # Period
    period = encounter_resource.get("period", {})
    print(f"Period: {period.get('start')} to {period.get('end')}")
    
    # Patient reference
    subject = encounter_resource.get("subject", {})
    print(f"Patient: {subject.get('reference')}")
    
    # Location
    location = encounter_resource.get("location", [{}])[0]
    loc_display = location.get("location", {}).get("display")
    print(f"Location: {loc_display} [WILL BE ANONYMIZED]")
    
    # Participant (provider)
    participant = encounter_resource.get("participant", [{}])[0]
    provider = participant.get("individual", {}).get("display")
    print(f"Provider: {provider} [WILL BE ANONYMIZED]")


def test_observation_parsing(observation_resource):
    """Test Observation resource extraction."""
    print("\n=== Observation Resource ===")
    print(f"ID: {observation_resource.get('id')}")
    print(f"Status: {observation_resource.get('status')}")
    
    # Code
    code = observation_resource.get("code", {}).get("coding", [{}])[0]
    print(f"Code: {code.get('code')} - {code.get('display')}")
    
    # Components (multiple values in one observation)
    components = observation_resource.get("component", [])
    if components:
        print(f"  Components: {len(components)}")
        for comp in components[:3]:  # Show first 3
            comp_code = comp.get("code", {}).get("coding", [{}])[0]
            comp_value = comp.get("valueCodeableConcept", comp.get("valueQuantity", comp.get("valueString")))
            print(f"    - {comp_code.get('display', 'N/A')[:50]}")
    
    # Effective date
    print(f"Effective: {observation_resource.get('effectiveDateTime')}")


def test_procedure_parsing(procedure_resource):
    """Test Procedure resource extraction."""
    print("\n=== Procedure Resource ===")
    print(f"ID: {procedure_resource.get('id')}")
    print(f"Status: {procedure_resource.get('status')}")
    
    # Code
    code = procedure_resource.get("code", {}).get("coding", [{}])[0]
    print(f"Code: {code.get('code')} - {code.get('display')}")
    
    # performedPeriod (not performedDateTime in sample)
    period = procedure_resource.get("performedPeriod", {})
    print(f"Performed: {period.get('start')} to {period.get('end')}")
    
    # Location
    location = procedure_resource.get("location", {})
    print(f"Location: {location.get('display')} [WILL BE ANONYMIZED]")


def test_diagnostic_report_parsing(report_resource):
    """Test DiagnosticReport resource extraction."""
    print("\n=== DiagnosticReport Resource ===")
    print(f"ID: {report_resource.get('id')}")
    print(f"Status: {report_resource.get('status')}")
    
    # Code
    code = report_resource.get("code", {}).get("coding", [{}])[0]
    print(f"Code: {code.get('code')} - {code.get('display')}")
    
    # presentedForm contains base64 clinical notes
    presented_form = report_resource.get("presentedForm", [])
    if presented_form:
        form = presented_form[0]
        print(f"  Presented Form: {form.get('contentType')}")
        print(f"  Data Length: {len(form.get('data', ''))} chars (base64)")
        print(f"  [CONTAINS CLINICAL NOTES - WILL BE REDACTED]")
    
    # Performer
    performer = report_resource.get("performer", [{}])[0]
    print(f"Performer: {performer.get('display')} [WILL BE ANONYMIZED]")


def test_medication_request_parsing(med_resource):
    """Test MedicationRequest resource extraction."""
    print("\n=== MedicationRequest Resource ===")
    print(f"ID: {med_resource.get('id')}")
    print(f"Status: {med_resource.get('status')}")
    print(f"Intent: {med_resource.get('intent')}")
    
    # Medication
    med = med_resource.get("medicationCodeableConcept", {}).get("coding", [{}])[0]
    print(f"Medication: {med.get('display')}")
    
    # Category (array)
    category = med_resource.get("category", [{}])[0]
    cat_code = category.get("coding", [{}])[0]
    print(f"Category: {cat_code.get('display')}")
    
    # Requester
    requester = med_resource.get("requester", {})
    print(f"Requester: {requester.get('display')} [WILL BE ANONYMIZED]")
    
    print(f"Authored: {med_resource.get('authoredOn')}")


def main():
    print("=" * 60)
    print("FHIR Sample Data Parsing Test")
    print("=" * 60)
    
    resources = parse_ndjson(SAMPLE_FILE)
    print(f"\nTotal resources parsed: {len(resources)}")
    
    # Group by resource type
    by_type = {}
    for resource in resources:
        if not isinstance(resource, dict):
            continue  # Skip non-dict items
        res_type = resource.get("resourceType")
        if res_type not in by_type:
            by_type[res_type] = []
        by_type[res_type].append(resource)
    
    print("\nResource counts:")
    for res_type, items in by_type.items():
        print(f"  {res_type}: {len(items)}")
    
    # Test each type
    if "Patient" in by_type:
        test_patient_parsing(by_type["Patient"][0])
    
    if "Encounter" in by_type:
        test_encounter_parsing(by_type["Encounter"][0])
    
    if "Observation" in by_type:
        test_observation_parsing(by_type["Observation"][0])
    
    if "Procedure" in by_type:
        test_procedure_parsing(by_type["Procedure"][0])
    
    if "DiagnosticReport" in by_type:
        test_diagnostic_report_parsing(by_type["DiagnosticReport"][0])
    
    if "MedicationRequest" in by_type:
        test_medication_request_parsing(by_type["MedicationRequest"][0])
    
    print("\n" + "=" * 60)
    print("✅ All parsing tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
