// ...existing code...
package com.project.proxyfhir.repository;

import com.project.proxyfhir.model.FhirResource;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface FhirResourceRepository extends JpaRepository<FhirResource, Long> {
    List<FhirResource> findByResourceType(String resourceType);
}
