from faker import Faker
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import random
import hashlib

fake = Faker()
Faker.seed(42)  # For reproducibility in testing


class DeIdentificationService:
    """Service to anonymize/de-identify FHIR resource data using Faker."""
    
    def __init__(self):
        self.fake = Faker()
        # Maintain consistent mapping for same original values (deterministic)
        self._name_cache: Dict[str, str] = {}
        self._address_cache: Dict[str, str] = {}
        self._phone_cache: Dict[str, str] = {}
        self._email_cache: Dict[str, str] = {}
        
        # Date shift strategy: consistent shift per patient
        self._date_shift_cache: Dict[str, int] = {}
    
    def _get_deterministic_shift(self, patient_id: str) -> int:
        """Get a consistent date shift (in days) for a patient based on their ID."""
        if patient_id not in self._date_shift_cache:
            # Hash patient ID to get consistent random shift between -365 and +365 days
            hash_val = int(hashlib.sha256(patient_id.encode()).hexdigest(), 16)
            shift_days = (hash_val % 731) - 365  # Range: -365 to +365
            self._date_shift_cache[patient_id] = shift_days
        return self._date_shift_cache[patient_id]
    
    def anonymize_name(self, original_name: str, name_type: str = "given") -> str:
        """Anonymize a name (first or last) consistently."""
        if not original_name:
            return None
        
        cache_key = f"{name_type}:{original_name}"
        if cache_key not in self._name_cache:
            if name_type == "given":
                self._name_cache[cache_key] = self.fake.first_name()
            else:
                self._name_cache[cache_key] = self.fake.last_name()
        return self._name_cache[cache_key]
    
    def anonymize_address(self, original_address: str) -> str:
        """Anonymize an address consistently."""
        if not original_address:
            return None
        
        if original_address not in self._address_cache:
            self._address_cache[original_address] = self.fake.street_address()
        return self._address_cache[original_address]
    
    def anonymize_city(self, original_city: str) -> str:
        """Generate a fake city name."""
        if not original_city:
            return None
        return self.fake.city()
    
    def anonymize_postal_code(self, original_postal: str) -> str:
        """Generate a fake postal code or generalize to first 3 digits."""
        if not original_postal:
            return None
        # Option 1: Completely fake
        return self.fake.zipcode()
        # Option 2: Generalize (keep first 3 digits)
        # return original_postal[:3] + "XX" if len(original_postal) >= 3 else "XXXXX"
    
    def anonymize_phone(self, original_phone: str) -> str:
        """Anonymize phone number consistently."""
        if not original_phone:
            return None
        
        if original_phone not in self._phone_cache:
            self._phone_cache[original_phone] = self.fake.phone_number()
        return self._phone_cache[original_phone]
    
    def anonymize_email(self, original_email: str) -> str:
        """Anonymize email consistently."""
        if not original_email:
            return None
        
        if original_email not in self._email_cache:
            self._email_cache[original_email] = self.fake.email()
        return self._email_cache[original_email]
    
    def shift_date(self, original_date: Optional[datetime], patient_id: str) -> Optional[datetime]:
        """Shift a date by a consistent amount for a given patient."""
        if not original_date:
            return None
        
        shift_days = self._get_deterministic_shift(patient_id)
        return original_date + timedelta(days=shift_days)
    
    def anonymize_provider_name(self, original_name: str) -> str:
        """Anonymize provider/practitioner name."""
        if not original_name:
            return None
        return self.fake.name()
    
    def anonymize_location(self, original_location: str) -> str:
        """Anonymize location/facility name."""
        if not original_location:
            return None
        # Generate generic hospital/facility name
        return f"{self.fake.city()} Medical Center"
    
    def generalize_age(self, birth_date: Optional[datetime]) -> Optional[int]:
        """Calculate age from birth date (useful for ML features)."""
        if not birth_date:
            return None
        today = datetime.now()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
    
    def keep_clinical_codes(self, code: str) -> str:
        """Clinical codes (ICD-10, SNOMED, LOINC) are NOT PII - keep as is."""
        return code
    
    def remove_free_text_pii(self, text: str) -> str:
        """
        Placeholder for NLP-based PII removal from free text.
        In production, use libraries like Presidio, spaCy, or AWS Comprehend Medical.
        For now, return as-is or redact completely.
        """
        if not text:
            return None
        # Simple redaction for demo
        return "[REDACTED - Clinical Note]"


# Singleton instance
deid_service = DeIdentificationService()
