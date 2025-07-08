#!/usr/bin/env python3

import requests
import json

def test_api():
    print("🌐 Testing API Endpoints")
    print("=" * 30)
    
    base_url = "http://localhost:5001"
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ Server running (Status: {response.status_code})")
    except:
        print("❌ Server not running on port 5001")
        print("Please start the server with: python3 app.py")
        return
    
    # Test 2: Test the plumber matching API
    test_data = {
        "client_lat": 21.1702,
        "client_lon": 72.8311,
        "date": "2024-01-15",
        "time_slot": "9AM-11AM"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/dynamic_match_plumbers",
            headers={"Content-Type": "application/json"},
            data=json.dumps(test_data)
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API working - Found {data.get('total_found', 0)} plumbers")
            
            if data.get('plumbers'):
                print("Sample plumbers:")
                for i, plumber in enumerate(data['plumbers'][:3], 1):
                    print(f"  {i}. {plumber.get('Name')} - {plumber.get('Work_Specialization')} - Score: {plumber.get('Match_Score')}")
        else:
            print(f"❌ API failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ API error: {e}")
    
    print("\n🎉 API test completed!")

if __name__ == "__main__":
    test_api() 