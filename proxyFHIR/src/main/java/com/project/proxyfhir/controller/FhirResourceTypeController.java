package com.project.proxyfhir.controller;

import com.project.proxyfhir.model.FhirResource;
import com.project.proxyfhir.repository.FhirResourceRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * FHIR Resource-specific REST endpoints
 * Supports: Patient, Condition, Observation, Encounter, Procedure, MedicationRequest,
 * DiagnosticReport, DocumentReference, Immunization, Device, Location, Organization,
 * Practitioner, PractitionerRole
 */
@RestController
@RequestMapping("/api/fhir")
public class FhirResourceTypeController {

    @Autowired
    private FhirResourceRepository repository;

    // ============== Patient Endpoints ==============

    @GetMapping("/Patient")
    public ResponseEntity<Map<String, Object>> listPatients(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        Pageable pageable = PageRequest.of(page, size);
        List<FhirResource> patients = repository.findByResourceType("Patient");
        return buildBundleResponse("Patient", patients, page, size);
    }

    @GetMapping("/Patient/{id}")
    public ResponseEntity<?> getPatient(@PathVariable String id) {
        return getResourceByTypeAndId("Patient", id);
    }

    // ============== Condition Endpoints ==============

    @GetMapping("/Condition")
    public ResponseEntity<Map<String, Object>> listConditions(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String patient) {
        if (patient != null) {
            // Filter by patient reference
            return searchResourcesByPatient("Condition", patient, page, size);
        }
        List<FhirResource> conditions = repository.findByResourceType("Condition");
        return buildBundleResponse("Condition", conditions, page, size);
    }

    @GetMapping("/Condition/{id}")
    public ResponseEntity<?> getCondition(@PathVariable String id) {
        return getResourceByTypeAndId("Condition", id);
    }

    // ============== Observation Endpoints ==============

    @GetMapping("/Observation")
    public ResponseEntity<Map<String, Object>> listObservations(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String patient,
            @RequestParam(required = false) String code) {
        if (patient != null) {
            return searchResourcesByPatient("Observation", patient, page, size);
        }
        List<FhirResource> observations = repository.findByResourceType("Observation");
        return buildBundleResponse("Observation", observations, page, size);
    }

    @GetMapping("/Observation/{id}")
    public ResponseEntity<?> getObservation(@PathVariable String id) {
        return getResourceByTypeAndId("Observation", id);
    }

    // ============== Encounter Endpoints ==============

    @GetMapping("/Encounter")
    public ResponseEntity<Map<String, Object>> listEncounters(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String patient) {
        if (patient != null) {
            return searchResourcesByPatient("Encounter", patient, page, size);
        }
        List<FhirResource> encounters = repository.findByResourceType("Encounter");
        return buildBundleResponse("Encounter", encounters, page, size);
    }

    @GetMapping("/Encounter/{id}")
    public ResponseEntity<?> getEncounter(@PathVariable String id) {
        return getResourceByTypeAndId("Encounter", id);
    }

    // ============== Procedure Endpoints ==============

    @GetMapping("/Procedure")
    public ResponseEntity<Map<String, Object>> listProcedures(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String patient) {
        if (patient != null) {
            return searchResourcesByPatient("Procedure", patient, page, size);
        }
        List<FhirResource> procedures = repository.findByResourceType("Procedure");
        return buildBundleResponse("Procedure", procedures, page, size);
    }

    @GetMapping("/Procedure/{id}")
    public ResponseEntity<?> getProcedure(@PathVariable String id) {
        return getResourceByTypeAndId("Procedure", id);
    }

    // ============== MedicationRequest Endpoints ==============

    @GetMapping("/MedicationRequest")
    public ResponseEntity<Map<String, Object>> listMedicationRequests(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String patient) {
        if (patient != null) {
            return searchResourcesByPatient("MedicationRequest", patient, page, size);
        }
        List<FhirResource> meds = repository.findByResourceType("MedicationRequest");
        return buildBundleResponse("MedicationRequest", meds, page, size);
    }

    @GetMapping("/MedicationRequest/{id}")
    public ResponseEntity<?> getMedicationRequest(@PathVariable String id) {
        return getResourceByTypeAndId("MedicationRequest", id);
    }

    // ============== DiagnosticReport Endpoints ==============

    @GetMapping("/DiagnosticReport")
    public ResponseEntity<Map<String, Object>> listDiagnosticReports(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String patient) {
        if (patient != null) {
            return searchResourcesByPatient("DiagnosticReport", patient, page, size);
        }
        List<FhirResource> reports = repository.findByResourceType("DiagnosticReport");
        return buildBundleResponse("DiagnosticReport", reports, page, size);
    }

    @GetMapping("/DiagnosticReport/{id}")
    public ResponseEntity<?> getDiagnosticReport(@PathVariable String id) {
        return getResourceByTypeAndId("DiagnosticReport", id);
    }

    // ============== DocumentReference Endpoints ==============

    @GetMapping("/DocumentReference")
    public ResponseEntity<Map<String, Object>> listDocumentReferences(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String patient) {
        if (patient != null) {
            return searchResourcesByPatient("DocumentReference", patient, page, size);
        }
        List<FhirResource> docs = repository.findByResourceType("DocumentReference");
        return buildBundleResponse("DocumentReference", docs, page, size);
    }

    @GetMapping("/DocumentReference/{id}")
    public ResponseEntity<?> getDocumentReference(@PathVariable String id) {
        return getResourceByTypeAndId("DocumentReference", id);
    }

    // ============== Immunization Endpoints ==============

    @GetMapping("/Immunization")
    public ResponseEntity<Map<String, Object>> listImmunizations(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String patient) {
        if (patient != null) {
            return searchResourcesByPatient("Immunization", patient, page, size);
        }
        List<FhirResource> immunizations = repository.findByResourceType("Immunization");
        return buildBundleResponse("Immunization", immunizations, page, size);
    }

    @GetMapping("/Immunization/{id}")
    public ResponseEntity<?> getImmunization(@PathVariable String id) {
        return getResourceByTypeAndId("Immunization", id);
    }

    // ============== Device Endpoints ==============

    @GetMapping("/Device")
    public ResponseEntity<Map<String, Object>> listDevices(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        List<FhirResource> devices = repository.findByResourceType("Device");
        return buildBundleResponse("Device", devices, page, size);
    }

    @GetMapping("/Device/{id}")
    public ResponseEntity<?> getDevice(@PathVariable String id) {
        return getResourceByTypeAndId("Device", id);
    }

    // ============== Location Endpoints ==============

    @GetMapping("/Location")
    public ResponseEntity<Map<String, Object>> listLocations(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        List<FhirResource> locations = repository.findByResourceType("Location");
        return buildBundleResponse("Location", locations, page, size);
    }

    @GetMapping("/Location/{id}")
    public ResponseEntity<?> getLocation(@PathVariable String id) {
        return getResourceByTypeAndId("Location", id);
    }

    // ============== Organization Endpoints ==============

    @GetMapping("/Organization")
    public ResponseEntity<Map<String, Object>> listOrganizations(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        List<FhirResource> orgs = repository.findByResourceType("Organization");
        return buildBundleResponse("Organization", orgs, page, size);
    }

    @GetMapping("/Organization/{id}")
    public ResponseEntity<?> getOrganization(@PathVariable String id) {
        return getResourceByTypeAndId("Organization", id);
    }

    // ============== Practitioner Endpoints ==============

    @GetMapping("/Practitioner")
    public ResponseEntity<Map<String, Object>> listPractitioners(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        List<FhirResource> practitioners = repository.findByResourceType("Practitioner");
        return buildBundleResponse("Practitioner", practitioners, page, size);
    }

    @GetMapping("/Practitioner/{id}")
    public ResponseEntity<?> getPractitioner(@PathVariable String id) {
        return getResourceByTypeAndId("Practitioner", id);
    }

    // ============== PractitionerRole Endpoints ==============

    @GetMapping("/PractitionerRole")
    public ResponseEntity<Map<String, Object>> listPractitionerRoles(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        List<FhirResource> roles = repository.findByResourceType("PractitionerRole");
        return buildBundleResponse("PractitionerRole", roles, page, size);
    }

    @GetMapping("/PractitionerRole/{id}")
    public ResponseEntity<?> getPractitionerRole(@PathVariable String id) {
        return getResourceByTypeAndId("PractitionerRole", id);
    }

    // ============== Helper Methods ==============

    private ResponseEntity<?> getResourceByTypeAndId(String resourceType, String resourceId) {
        List<FhirResource> resources = repository.findByResourceType(resourceType);
        Optional<FhirResource> found = resources.stream()
                .filter(r -> resourceId.equals(r.getResourceId()))
                .findFirst();

        if (found.isPresent()) {
            return ResponseEntity.ok(found.get());
        }
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of(
            "resourceType", "OperationOutcome",
            "issue", List.of(Map.of(
                "severity", "error",
                "code", "not-found",
                "diagnostics", resourceType + "/" + resourceId + " not found"
            ))
        ));
    }

    private ResponseEntity<Map<String, Object>> searchResourcesByPatient(
            String resourceType, String patientId, int page, int size) {
        // Simple filter - in production you'd query JSON content
        List<FhirResource> allResources = repository.findByResourceType(resourceType);
        List<FhirResource> filtered = allResources.stream()
                .filter(r -> r.getContent() != null && r.getContent().contains("Patient/" + patientId))
                .toList();
        return buildBundleResponse(resourceType, filtered, page, size);
    }

    private ResponseEntity<Map<String, Object>> buildBundleResponse(
            String resourceType, List<FhirResource> resources, int page, int size) {
        int start = page * size;
        int end = Math.min(start + size, resources.size());
        List<FhirResource> pageResources = (start < resources.size())
                ? resources.subList(start, end)
                : List.of();

        Map<String, Object> bundle = new HashMap<>();
        bundle.put("resourceType", "Bundle");
        bundle.put("type", "searchset");
        bundle.put("total", resources.size());
        bundle.put("entry", pageResources.stream()
                .map(r -> Map.of(
                    "fullUrl", "/api/fhir/" + resourceType + "/" + r.getResourceId(),
                    "resource", r
                ))
                .toList());
        bundle.put("link", List.of(
            Map.of("relation", "self", "url", "/api/fhir/" + resourceType + "?page=" + page + "&size=" + size)
        ));

        return ResponseEntity.ok(bundle);
    }

    // ============== Statistics Endpoint ==============

    @GetMapping("/stats")
    public ResponseEntity<Map<String, Object>> getStats() {
        List<String> resourceTypes = List.of(
            "Patient", "Condition", "Observation", "Encounter", "Procedure",
            "MedicationRequest", "DiagnosticReport", "DocumentReference", "Immunization",
            "Device", "Location", "Organization", "Practitioner", "PractitionerRole"
        );

        Map<String, Long> counts = new HashMap<>();
        long total = 0;
        for (String type : resourceTypes) {
            long count = repository.findByResourceType(type).size();
            counts.put(type, count);
            total += count;
        }

        return ResponseEntity.ok(Map.of(
            "total", total,
            "byResourceType", counts,
            "timestamp", LocalDateTime.now()
        ));
    }
}

