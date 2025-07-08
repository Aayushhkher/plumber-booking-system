#!/usr/bin/env python3
"""
Test script for the enhanced admin dashboard attribute system functionality
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:5001"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"

def login_as_admin():
    """Login as admin and return session"""
    session = requests.Session()
    
    # Get login page to get CSRF token if needed
    login_response = session.get(f"{BASE_URL}/login")
    
    # Login
    login_data = {
        'email': ADMIN_EMAIL,
        'password': ADMIN_PASSWORD
    }
    
    response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
    
    if response.status_code == 302:  # Redirect after successful login
        print("✅ Admin login successful")
        return session
    else:
        print("❌ Admin login failed")
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def test_get_attributes(session):
    """Test getting all attributes"""
    print("\n🔍 Testing: Get all attributes")
    
    response = session.get(f"{BASE_URL}/admin/get_attributes")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Successfully retrieved {len(data.get('attributes', []))} attributes")
        
        # Print first few attributes
        for attr in data.get('attributes', [])[:3]:
            print(f"  - {attr['name']} ({attr['category']}, {attr['type']}, weight: {attr['weight']})")
        
        return data.get('attributes', [])
    else:
        print(f"❌ Failed to get attributes: {response.status_code}")
        print(f"Response: {response.text}")
        return []

def test_add_attribute(session):
    """Test adding a new attribute"""
    print("\n➕ Testing: Add new attribute")
    
    new_attribute = {
        'name': 'test_emergency_service',
        'category': 'logistical',
        'type': 'preferred',
        'weight': 0.8,
        'description': 'Test emergency service availability',
        'possible_values': 'Yes, No',
        'min_value': '',
        'max_value': '',
        'unit': ''
    }
    
    response = session.post(f"{BASE_URL}/admin/add_attribute", data=new_attribute)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("✅ Successfully added test attribute")
            return True
        else:
            print(f"❌ Failed to add attribute: {data.get('error')}")
            return False
    else:
        print(f"❌ Failed to add attribute: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_update_attribute(session):
    """Test updating an attribute"""
    print("\n✏️ Testing: Update attribute")
    
    update_data = {
        'name': 'test_emergency_service',
        'category': 'logistical',
        'type': 'required',
        'weight': 1.0,
        'description': 'Updated test emergency service availability',
        'possible_values': 'Yes, No, Maybe',
        'min_value': '',
        'max_value': '',
        'unit': ''
    }
    
    response = session.post(f"{BASE_URL}/admin/update_attribute", data=update_data)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("✅ Successfully updated test attribute")
            return True
        else:
            print(f"❌ Failed to update attribute: {data.get('error')}")
            return False
    else:
        print(f"❌ Failed to update attribute: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_get_attribute_stats(session):
    """Test getting attribute statistics"""
    print("\n📊 Testing: Get attribute statistics")
    
    response = session.get(f"{BASE_URL}/admin/attribute_stats")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Successfully retrieved attribute statistics")
        print(f"  - Total attributes: {data.get('total_attributes', 0)}")
        print(f"  - By category: {data.get('by_category', {})}")
        print(f"  - By type: {data.get('by_type', {})}")
        return True
    else:
        print(f"❌ Failed to get attribute stats: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_delete_attribute(session):
    """Test deleting an attribute"""
    print("\n🗑️ Testing: Delete test attribute")
    
    delete_data = {
        'name': 'test_emergency_service'
    }
    
    response = session.post(
        f"{BASE_URL}/admin/delete_attribute", 
        json=delete_data,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("✅ Successfully deleted test attribute")
            return True
        else:
            print(f"❌ Failed to delete attribute: {data.get('error')}")
            return False
    else:
        print(f"❌ Failed to delete attribute: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_attribute_system(session):
    """Test the attribute system with sample data"""
    print("\n🧪 Testing: Attribute system matching")
    
    test_data = {
        'work_type': 'Leak Repair',
        'district': 'Ahmedabad',
        'language': 'Gujarati',
        'experience_years': '5',
        'max_cost': '1000',
        'client_lat': '23.0225',
        'client_lon': '72.5714'
    }
    
    response = session.post(f"{BASE_URL}/admin/test_attribute_system", data=test_data)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"✅ Successfully tested attribute system")
            print(f"  - Total matches: {data.get('total_matches', 0)}")
            print(f"  - Average score: {data.get('average_score', 0):.2f}")
            return True
        else:
            print(f"❌ Failed to test attribute system: {data.get('error')}")
            return False
    else:
        print(f"❌ Failed to test attribute system: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Admin Dashboard Attribute System Tests")
    print("=" * 50)
    
    # Login as admin
    session = login_as_admin()
    if not session:
        print("❌ Cannot proceed without admin login")
        sys.exit(1)
    
    # Run tests
    tests = [
        ("Get Attributes", test_get_attributes),
        ("Add Attribute", test_add_attribute),
        ("Update Attribute", test_update_attribute),
        ("Get Stats", test_get_attribute_stats),
        ("Test System", test_attribute_system),
        ("Delete Attribute", test_delete_attribute)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func(session):
                passed += 1
        except Exception as e:
            print(f"❌ Exception in {test_name}: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"📋 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Admin dashboard attribute system is working correctly.")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 