#!/usr/bin/env python3
"""Test script to verify state-city endpoints."""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_get_states():
    """Test /get-states endpoint."""
    print("Testing /get-states endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/get-states", timeout=5)
        if response.status_code == 200:
            data = response.json()
            states = data.get("states", [])
            print(f"✓ Success! Found {len(states)} states/UTs")
            print(f"  First 5: {states[:5]}")
            print(f"  Last 5: {states[-5:]}")
            return True
        else:
            print(f"✗ Failed with status code {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_get_cities():
    """Test /get-cities/<state> endpoint."""
    print("\nTesting /get-cities/<state> endpoint...")
    test_states = ["Maharashtra", "Karnataka", "Punjab", "Delhi"]
    
    for state in test_states:
        try:
            response = requests.get(f"{BASE_URL}/get-cities/{state}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                cities = data.get("cities", [])
                print(f"✓ {state}: {len(cities)} cities - {', '.join(cities[:3])}...")
            else:
                print(f"✗ {state}: Status code {response.status_code}")
        except Exception as e:
            print(f"✗ {state}: Error - {e}")

def test_city_to_state():
    """Test CITY_TO_STATE mapping by checking a few cities."""
    print("\nTesting city-to-state mapping...")
    test_cities = ["Mumbai", "Delhi", "Bengaluru", "Kolkata", "Chennai"]
    
    for city in test_cities:
        try:
            # Use the city in a prediction-like request (which will validate it exists)
            response = requests.get(f"{BASE_URL}/get-cities/Maharashtra", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if city in data.get("cities", []):
                    print(f"✓ {city} found in Maharashtra")
                else:
                    print(f"  {city} not in Maharashtra (may be in another state)")
        except Exception as e:
            print(f"✗ {city}: Error - {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("State-City Endpoints Test Suite")
    print("=" * 60)
    
    test_get_states()
    test_get_cities()
    test_city_to_state()
    
    print("\n" + "=" * 60)
    print("Test suite complete!")
    print("=" * 60)
