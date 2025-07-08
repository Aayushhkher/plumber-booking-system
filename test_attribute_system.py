#!/usr/bin/env python3
"""
Test script to demonstrate the dynamic attribute system for plumber matching
"""

from attribute_system import DynamicAttributeSystem, AttributeCategory
import json

def test_attribute_system():
    """Test the dynamic attribute system"""
    
    print("🔧 Testing Dynamic Attribute System for Plumber Matching")
    print("=" * 60)
    
    # Initialize the system
    attribute_system = DynamicAttributeSystem()
    
    # Load the enhanced dataset
    try:
        df = attribute_system.load_dataset('enhanced_plumbers_dataset.csv')
        print(f"✅ Loaded enhanced dataset with {len(df)} plumbers")
    except FileNotFoundError:
        print("❌ Enhanced dataset not found. Please create it first.")
        return
    
    # Test 1: Get available attributes
    print("\n📋 Available Attributes by Category:")
    print("-" * 40)
    
    for category in AttributeCategory:
        attributes = attribute_system.get_attributes_by_category(category)
        print(f"\n{category.value.upper()}:")
        for name, attr in attributes.items():
            print(f"  • {attr.name}: {attr.description}")
    
    # Test 2: Simple matching
    print("\n🔍 Test 1: Simple Matching")
    print("-" * 30)
    
    simple_preferences = {
        'work_type': 'Leak Repair',
        'district': 'Surat',
        'language': 'English',
        'client_lat': 21.1702,
        'client_lon': 72.8311
    }
    
    print("Customer Preferences:")
    for key, value in simple_preferences.items():
        print(f"  • {key}: {value}")
    
    matched_plumbers = attribute_system.match_plumbers(simple_preferences, max_results=5)
    print(f"\nFound {len(matched_plumbers)} matching plumbers:")
    
    for i, plumber in enumerate(matched_plumbers, 1):
        print(f"\n{i}. {plumber['Name']}")
        print(f"   Match Score: {plumber['Match_Score']}/10")
        print(f"   Specialization: {plumber['Work_Specialization']}")
        print(f"   Distance: {plumber.get('Distance_km', 'N/A')} km")
        print(f"   Rating: {plumber.get('Rating', 'N/A')} ⭐")
    
    # Test 3: Advanced matching with multiple attributes
    print("\n🔍 Test 2: Advanced Matching")
    print("-" * 30)
    
    advanced_preferences = {
        'work_type': 'Kitchen Plumbing',
        'district': 'Ahmedabad',
        'language': 'Hindi',
        'experience_years': 8,
        'license_type': 'Licensed',
        'insurance_status': 'Insured',
        'min_rating': 4.0,
        'emergency_service': 'Yes',
        'max_cost': 500,
        'client_lat': 23.0300,
        'client_lon': 72.5800
    }
    
    print("Advanced Customer Preferences:")
    for key, value in advanced_preferences.items():
        print(f"  • {key}: {value}")
    
    matched_plumbers = attribute_system.match_plumbers(advanced_preferences, max_results=5)
    print(f"\nFound {len(matched_plumbers)} matching plumbers:")
    
    for i, plumber in enumerate(matched_plumbers, 1):
        print(f"\n{i}. {plumber['Name']}")
        print(f"   Match Score: {plumber['Match_Score']}/10")
        print(f"   Specialization: {plumber['Work_Specialization']}")
        print(f"   Experience: {plumber.get('Experience_Years', 'N/A')} years")
        print(f"   License: {plumber.get('License_Type', 'N/A')}")
        print(f"   Insurance: {plumber.get('Insurance_Status', 'N/A')}")
        print(f"   Rating: {plumber.get('Rating', 'N/A')} ⭐")
        print(f"   Emergency Service: {plumber.get('Emergency_Service', 'N/A')}")
        print(f"   Distance: {plumber.get('Distance_km', 'N/A')} km")
        
        # Show attribute scores
        if 'Attribute_Scores' in plumber:
            print("   Attribute Scores:")
            for attr, score in plumber['Attribute_Scores'].items():
                if score > 0:
                    print(f"     • {attr}: {score:.2f}")
    
    # Test 4: Generate matching report
    print("\n📊 Test 3: Matching Report")
    print("-" * 30)
    
    report = attribute_system.generate_matching_report(advanced_preferences, matched_plumbers)
    
    print(f"Total plumbers found: {report['total_plumbers_found']}")
    print(f"Preferences used: {', '.join(report['preferences_used'])}")
    
    print("\nTop matches:")
    for match in report['top_matches']:
        print(f"  • {match['name']} (Score: {match['score']}, Distance: {match['distance']} km)")
    
    print("\nAttribute analysis:")
    for attr, analysis in report['attribute_analysis'].items():
        print(f"  • {attr}: Avg={analysis['average_score']}, Max={analysis['max_score']}, Min={analysis['min_score']}")
    
    print("\nRecommendations:")
    for rec in report['recommendations']:
        print(f"  • {rec}")
    
    # Test 5: Attribute suggestions
    print("\n💡 Test 4: Attribute Suggestions")
    print("-" * 30)
    
    suggestions = attribute_system.get_attribute_suggestions("experience")
    print(f"Suggestions for 'experience': {suggestions}")
    
    value_suggestions = attribute_system.get_value_suggestions("license_type")
    print(f"Values for 'license_type': {value_suggestions}")
    
    print("\n✅ All tests completed successfully!")

def demo_customer_scenarios():
    """Demonstrate different customer scenarios"""
    
    print("\n🎭 Customer Scenario Demonstrations")
    print("=" * 50)
    
    attribute_system = DynamicAttributeSystem()
    attribute_system.load_dataset('enhanced_plumbers_dataset.csv')
    
    scenarios = [
        {
            'name': 'Budget-Conscious Customer',
            'description': 'Looking for affordable plumbing work',
            'preferences': {
                'work_type': 'Leak Repair',
                'max_cost': 300,
                'district': 'Any',
                'client_lat': 22.3039,
                'client_lon': 73.1812
            }
        },
        {
            'name': 'Quality-Focused Customer',
            'description': 'Willing to pay more for high-quality service',
            'preferences': {
                'work_type': 'Bathroom Fitting',
                'min_rating': 4.5,
                'experience_years': 10,
                'license_type': 'Licensed',
                'insurance_status': 'Insured',
                'guarantee_period': 30,
                'client_lat': 21.1702,
                'client_lon': 72.8311
            }
        },
        {
            'name': 'Emergency Customer',
            'description': 'Needs immediate service for urgent repair',
            'preferences': {
                'work_type': 'Leak Repair',
                'emergency_service': 'Yes',
                'response_time': 15,
                'weekend_available': 'Yes',
                'client_lat': 23.2185,
                'client_lon': 72.6348
            }
        },
        {
            'name': 'Commercial Customer',
            'description': 'Business owner needing commercial plumbing',
            'preferences': {
                'work_type': 'Kitchen Plumbing',
                'specialization_level': 'Expert',
                'certifications': 'Commercial Plumbing License',
                'required_equipment': 'Professional Tools',
                'payment_methods': 'Card',
                'client_lat': 22.5726,
                'client_lon': 72.9505
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"\n👤 {scenario['name']}")
        print(f"   {scenario['description']}")
        print("   Preferences:")
        for key, value in scenario['preferences'].items():
            print(f"     • {key}: {value}")
        
        matched_plumbers = attribute_system.match_plumbers(scenario['preferences'], max_results=3)
        
        print(f"   Top matches:")
        for i, plumber in enumerate(matched_plumbers[:3], 1):
            print(f"     {i}. {plumber['Name']} (Score: {plumber['Match_Score']}/10)")
            print(f"        Specialization: {plumber['Work_Specialization']}")
            print(f"        Rating: {plumber.get('Rating', 'N/A')} ⭐")
            print(f"        Cost: ₹{plumber.get('Min_Order_Value', 'N/A')}")

if __name__ == "__main__":
    test_attribute_system()
    demo_customer_scenarios() 