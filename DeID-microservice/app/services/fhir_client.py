import httpx
from typing import List, Dict, Any
from app.core.config import settings


class FHIRClient:
    """Client to interact with FHIR Proxy service."""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.fhir_proxy_base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def get_manifest(self) -> Dict[str, Any]:
        """
        Fetch the bulk export manifest from FHIR Proxy.
        Returns: {
            "files": [{"fileName": "...", "url": "..."}],
            "exportId": "..."
        }
        """
        url = f"{self.base_url}/bulk/manifest"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()
    
    async def get_file_data(self, file_url: str) -> List[Dict[str, Any]]:
        """
        Fetch NDJSON file data from FHIR Proxy.
        Args:
            file_url: Relative URL like "/bulk/files/Patient.000.ndjson"
        Returns:
            List of FHIR resource dicts (one per line of NDJSON)
        """
        full_url = f"{self.base_url}{file_url}"
        response = await self.client.get(full_url)
        response.raise_for_status()
        
        # Parse NDJSON (newline-delimited JSON)
        lines = response.text.strip().split('\n')
        resources = []
        for line in lines:
            if line.strip():
                import json
                resources.append(json.loads(line))
        
        return resources
    
    async def get_critical_files(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch all critical FHIR files for de-identification.
        Returns dict with resource type as key and list of resources as value.
        """
        manifest = await self.get_manifest()
        
        # Map of file patterns to resource types
        critical_files = {
            "Patient": [],
            "Encounter": [],
            "Condition": [],
            "Observation": [],
            "MedicationRequest": [],
            "Procedure": [],
            "DiagnosticReport": [],
            "DocumentReference": [],
            "AllergyIntolerance": [],
            "Immunization": [],
            "Practitioner": [],
            "PractitionerRole": [],
            "Organization": [],
        }
        
        for file_info in manifest.get("files", []):
            file_name = file_info["fileName"]
            file_url = file_info["url"]
            
            # Match file name to resource type
            for resource_type in critical_files.keys():
                if file_name.startswith(resource_type):
                    print(f"Fetching {file_name}...")
                    data = await self.get_file_data(file_url)
                    critical_files[resource_type].extend(data)
                    break
        
        return critical_files


# Singleton factory
def get_fhir_client() -> FHIRClient:
    """Dependency for FastAPI routes."""
    return FHIRClient()
