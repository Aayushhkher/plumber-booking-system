#!/usr/bin/env python3
"""
Quick test script to verify the admin dashboard attribute system
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:5001"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"

def test_admin_dashboard():
    """Test the admin dashboard attribute system"""
    print("🚀 Testing Admin Dashboard Attribute System")
    print("=" * 50)
    
    # Create session
    session = requests.Session()
    
    # Test 1: Login
    print("1. Testing admin login...")
    login_data = {
        'email': ADMIN_EMAIL,
        'password': ADMIN_PASSWORD
    }
    
    response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
    if response.status_code == 302:
        print("✅ Admin login successful")
    else:
        print(f"❌ Admin login failed: {response.status_code}")
        return False
    
    # Test 2: Get attributes
    print("\n2. Testing get attributes...")
    response = session.get(f"{BASE_URL}/admin/get_attributes")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Retrieved {len(data.get('attributes', []))} attributes")
        
        # Show first few attributes
        for attr in data.get('attributes', [])[:3]:
            print(f"   - {attr['name']} ({attr['category']}, {attr['type']})")
    else:
        print(f"❌ Failed to get attributes: {response.status_code}")
        return False
    
    # Test 3: Get attribute statistics
    print("\n3. Testing attribute statistics...")
    response = session.get(f"{BASE_URL}/admin/attribute_stats")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Retrieved statistics:")
        print(f"   - Total attributes: {data.get('total_attributes', 0)}")
        print(f"   - By type: {data.get('by_type', {})}")
    else:
        print(f"❌ Failed to get statistics: {response.status_code}")
        return False
    
    # Test 4: Test attribute system
    print("\n4. Testing attribute system matching...")
    test_data = {
        'work_type': 'Leak Repair',
        'district': 'Ahmedabad',
        'language': 'Gujarati',
        'client_lat': '23.0225',
        'client_lon': '72.5714'
    }
    
    response = session.post(f"{BASE_URL}/admin/test_attribute_system", data=test_data)
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"✅ Attribute system test successful")
            print(f"   - Total matches: {data.get('total_matches', 0)}")
            print(f"   - Average score: {data.get('average_score', 0):.2f}")
        else:
            print(f"❌ Attribute system test failed: {data.get('error')}")
            return False
    else:
        print(f"❌ Failed to test attribute system: {response.status_code}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! Admin dashboard attribute system is working correctly.")
    return True

if __name__ == "__main__":
    # Wait a moment for the app to start
    print("Waiting for application to start...")
    time.sleep(3)
    
    success = test_admin_dashboard()
    if not success:
        print("❌ Some tests failed. Please check the application.")
        exit(1) 