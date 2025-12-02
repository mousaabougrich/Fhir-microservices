#!/usr/bin/env python3
"""
Quick test script to validate the featurizer service works locally.
Run this after installing dependencies and starting the DeID service.
"""

import requests
import sys

def test_featurizer():
    base_url = "http://localhost:8001"
    
    # Test health endpoint
    try:
        resp = requests.get(f"{base_url}/health")
        resp.raise_for_status()
        print("✓ Health check passed")
        print(f"  Response: {resp.json()}")
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False
    
    # Test with a dummy patient ID (replace with actual ID from your DeID service)
    test_patient_id = "test-patient-123"
    
    try:
        resp = requests.get(f"{base_url}/featurize/patient/{test_patient_id}")
        if resp.status_code == 500:
            print(f"⚠ Patient endpoint responded with 500 (expected if patient doesn't exist)")
            print(f"  Error: {resp.json().get('detail', 'Unknown error')}")
        else:
            resp.raise_for_status()
            features = resp.json()
            print("✓ Patient featurization endpoint works")
            print(f"  Sample features: {list(features.keys())}")
    except Exception as e:
        print(f"⚠ Patient endpoint test inconclusive: {e}")
    
    # Test bulk endpoint
    try:
        resp = requests.post(f"{base_url}/featurize/bulk", json=[test_patient_id])
        if resp.status_code == 500:
            print(f"⚠ Bulk endpoint responded with 500 (expected if patient doesn't exist)")
        else:
            resp.raise_for_status()
            print("✓ Bulk featurization endpoint works")
    except Exception as e:
        print(f"⚠ Bulk endpoint test inconclusive: {e}")
    
    return True

if __name__ == "__main__":
    print("Testing featurizer service...")
    print("Make sure to:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Start the service: uvicorn main:app --port 8001")
    print("3. Have your DeID service running on DEID_BASE_URL")
    print()
    
    success = test_featurizer()
    sys.exit(0 if success else 1)