package com.project.proxyfhir.controller;

import com.project.proxyfhir.model.FhirResource;
import com.project.proxyfhir.repository.FhirResourceRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/fhir")
public class FhirResourceController {

    @Autowired
    private FhirResourceRepository repository;

    /**
     * POST /fhir - Ingest a FHIR Bundle or single resource
     */
    @PostMapping
    public ResponseEntity<Map<String, Object>> ingestBundle(@RequestBody String fhirJson) {
        try {
            // Parse and save the FHIR resource/bundle
            FhirResource resource = new FhirResource();
            resource.setResourceType("Bundle"); // You can parse resourceType from JSON
            resource.setResourceId("auto-" + System.currentTimeMillis());
            resource.setData(fhirJson);
            resource.setLastUpdated(LocalDateTime.now());

            repository.save(resource);

            return ResponseEntity.status(HttpStatus.CREATED).body(Map.of(
                "status", "success",
                "message", "FHIR resource ingested",
                "resourceId", resource.getResourceId(),
                "timestamp", resource.getLastUpdated()
            ));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of(
                "status", "error",
                "message", e.getMessage()
            ));
        }
    }

    /**
     * GET /fhir - List all FHIR resources
     */
    @GetMapping
    public ResponseEntity<List<FhirResource>> listResources() {
        List<FhirResource> resources = repository.findAll();
        return ResponseEntity.ok(resources);
    }

    /**
     * GET /fhir/{id} - Get a specific FHIR resource by ID
     */
    @GetMapping("/{id}")
    public ResponseEntity<?> getResource(@PathVariable Long id) {
        Optional<FhirResource> resource = repository.findById(id);
        if (resource.isPresent()) {
            return ResponseEntity.ok(resource.get());
        }
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of(
            "error", "Resource not found",
            "id", id
        ));
    }

    /**
     * GET /fhir/type/{resourceType} - Get all resources of a specific type
     */
    @GetMapping("/type/{resourceType}")
    public ResponseEntity<List<FhirResource>> getResourcesByType(@PathVariable String resourceType) {
        List<FhirResource> resources = repository.findByResourceType(resourceType);
        return ResponseEntity.ok(resources);
    }

    /**
     * DELETE /fhir/{id} - Delete a FHIR resource
     */
    @DeleteMapping("/{id}")
    public ResponseEntity<Map<String, Object>> deleteResource(@PathVariable Long id) {
        if (repository.existsById(id)) {
            repository.deleteById(id);
            return ResponseEntity.ok(Map.of(
                "status", "success",
                "message", "Resource deleted",
                "id", id
            ));
        }
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of(
            "status", "error",
            "message", "Resource not found",
            "id", id
        ));
    }

    /**
     * GET /fhir/health - Simple health check
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        long count = repository.count();
        return ResponseEntity.ok(Map.of(
            "status", "UP",
            "service", "FHIR Proxy",
            "totalResources", count,
            "timestamp", LocalDateTime.now()
        ));
    }
}

