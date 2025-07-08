#!/usr/bin/env python3

from attribute_system import DynamicAttributeSystem

# Initialize the system
attribute_system = DynamicAttributeSystem()

# Load the enhanced dataset
df = attribute_system.load_dataset('enhanced_plumbers_dataset.csv')
print(f"Loaded dataset with {len(df)} plumbers")

# Test simple matching
preferences = {
    'work_type': 'Leak Repair',
    'district': 'Surat',
    'client_lat': 21.1702,
    'client_lon': 72.8311
}

print("\nTesting with preferences:", preferences)
matched_plumbers = attribute_system.match_plumbers(preferences, max_results=3)

print(f"\nFound {len(matched_plumbers)} matching plumbers:")
for i, plumber in enumerate(matched_plumbers, 1):
    print(f"{i}. {plumber['Name']} - Score: {plumber['Match_Score']}/10")
    print(f"   Specialization: {plumber['Work_Specialization']}")
    print(f"   District: {plumber['District']}")
    print(f"   Rating: {plumber.get('Rating', 'N/A')}")

print("\n✅ Test completed!") 