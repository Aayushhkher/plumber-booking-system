import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import math

class AttributeType(Enum):
    """Types of attributes for matching"""
    REQUIRED = "required"
    PREFERRED = "preferred"
    OPTIONAL = "optional"
    NEGATIVE = "negative"  # Attributes that reduce score

class AttributeCategory(Enum):
    """Categories of attributes"""
    BASIC = "basic"
    PROFESSIONAL = "professional"
    LOGISTICAL = "logistical"
    QUALITY = "quality"
    FINANCIAL = "financial"

@dataclass
class AttributeDefinition:
    """Definition of an attribute for matching"""
    name: str
    category: AttributeCategory
    type: AttributeType
    weight: float
    description: str
    possible_values: List[str] = None
    min_value: float = None
    max_value: float = None
    unit: str = None

class DynamicAttributeSystem:
    """Dynamic attribute system for plumber matching"""
    
    def __init__(self):
        self.attributes = self._initialize_attributes()
        self.df = None
        
    def _initialize_attributes(self) -> Dict[str, AttributeDefinition]:
        """Initialize all available attributes"""
        return {
            # Basic Attributes
            'work_type': AttributeDefinition(
                name='Work Type',
                category=AttributeCategory.BASIC,
                type=AttributeType.REQUIRED,
                weight=1.0,
                description='Type of plumbing work needed',
                possible_values=['Bathroom Fitting', 'Kitchen Plumbing', 'Leak Repair', 'Pipe Installation', 'Water Tank Cleaning']
            ),
            'district': AttributeDefinition(
                name='District',
                category=AttributeCategory.BASIC,
                type=AttributeType.PREFERRED,
                weight=0.8,
                description='Preferred district for the plumber',
                possible_values=['Ahmedabad', 'Surat', 'Vadodara', 'Rajkot', 'Bhavnagar', 'Jamnagar', 'Anand', 'Gandhinagar', 'Patan', 'Mehsana', 'Banaskantha', 'Sabarkantha', 'Aravalli', 'Mahisagar', 'Dahod', 'Panchmahal', 'Chhota Udaipur', 'Vadodara', 'Narmada', 'Bharuch', 'Surat', 'Tapi', 'Dang', 'Navsari', 'Valsad', 'Amreli', 'Bhavnagar', 'Botad', 'Surendranagar', 'Morbi', 'Rajkot', 'Jamnagar', 'Devbhoomi Dwarka', 'Porbandar', 'Junagadh', 'Gir Somnath', 'Amreli', 'Bhavnagar', 'Anand', 'Kheda', 'Mahisagar', 'Panchmahal', 'Dahod', 'Chhota Udaipur', 'Vadodara', 'Narmada', 'Bharuch', 'Surat', 'Tapi', 'Dang', 'Navsari', 'Valsad']
            ),
            'language': AttributeDefinition(
                name='Language',
                category=AttributeCategory.BASIC,
                type=AttributeType.PREFERRED,
                weight=0.6,
                description='Preferred language for communication',
                possible_values=['Gujarati', 'Hindi', 'English', 'Marathi']
            ),
            
            # Professional Attributes
            'experience_years': AttributeDefinition(
                name='Experience Years',
                category=AttributeCategory.PROFESSIONAL,
                type=AttributeType.PREFERRED,
                weight=0.7,
                description='Minimum years of experience required',
                min_value=0,
                max_value=20,
                unit='years'
            ),
            'license_type': AttributeDefinition(
                name='License Type',
                category=AttributeCategory.PROFESSIONAL,
                type=AttributeType.PREFERRED,
                weight=0.8,
                description='Required license type',
                possible_values=['Licensed', 'Unlicensed']
            ),
            'insurance_status': AttributeDefinition(
                name='Insurance Status',
                category=AttributeCategory.PROFESSIONAL,
                type=AttributeType.PREFERRED,
                weight=0.7,
                description='Insurance coverage requirement',
                possible_values=['Insured', 'Not Insured']
            ),
            'specialization_level': AttributeDefinition(
                name='Specialization Level',
                category=AttributeCategory.PROFESSIONAL,
                type=AttributeType.PREFERRED,
                weight=0.6,
                description='Required specialization level',
                possible_values=['Beginner', 'Intermediate', 'Expert']
            ),
            
            # Logistical Attributes
            'response_time': AttributeDefinition(
                name='Response Time',
                category=AttributeCategory.LOGISTICAL,
                type=AttributeType.PREFERRED,
                weight=0.9,
                description='Maximum response time acceptable',
                min_value=5,
                max_value=60,
                unit='minutes'
            ),
            'max_distance': AttributeDefinition(
                name='Maximum Distance',
                category=AttributeCategory.LOGISTICAL,
                type=AttributeType.PREFERRED,
                weight=0.8,
                description='Maximum distance willing to travel',
                min_value=5,
                max_value=100,
                unit='km'
            ),
            'weekend_available': AttributeDefinition(
                name='Weekend Availability',
                category=AttributeCategory.LOGISTICAL,
                type=AttributeType.OPTIONAL,
                weight=0.5,
                description='Weekend work availability',
                possible_values=['Yes', 'No']
            ),
            'emergency_service': AttributeDefinition(
                name='Emergency Service',
                category=AttributeCategory.LOGISTICAL,
                type=AttributeType.PREFERRED,
                weight=0.8,
                description='Emergency service availability',
                possible_values=['Yes', 'No']
            ),
            
            # Quality Attributes
            'min_rating': AttributeDefinition(
                name='Minimum Rating',
                category=AttributeCategory.QUALITY,
                type=AttributeType.PREFERRED,
                weight=0.7,
                description='Minimum rating required',
                min_value=1.0,
                max_value=5.0,
                unit='stars'
            ),
            'min_success_rate': AttributeDefinition(
                name='Minimum Success Rate',
                category=AttributeCategory.QUALITY,
                type=AttributeType.PREFERRED,
                weight=0.6,
                description='Minimum success rate required',
                min_value=50,
                max_value=100,
                unit='%'
            ),
            'guarantee_period': AttributeDefinition(
                name='Guarantee Period',
                category=AttributeCategory.QUALITY,
                type=AttributeType.OPTIONAL,
                weight=0.5,
                description='Minimum guarantee period required',
                min_value=0,
                max_value=365,
                unit='days'
            ),
            
            # Financial Attributes
            'max_cost': AttributeDefinition(
                name='Maximum Cost',
                category=AttributeCategory.FINANCIAL,
                type=AttributeType.PREFERRED,
                weight=0.8,
                description='Maximum cost willing to pay',
                min_value=100,
                max_value=2000,
                unit='₹'
            ),
            'payment_methods': AttributeDefinition(
                name='Payment Methods',
                category=AttributeCategory.FINANCIAL,
                type=AttributeType.OPTIONAL,
                weight=0.4,
                description='Preferred payment methods',
                possible_values=['Cash', 'Card', 'UPI', 'Net Banking']
            ),
            
            # Equipment and Specializations
            'required_equipment': AttributeDefinition(
                name='Required Equipment',
                category=AttributeCategory.PROFESSIONAL,
                type=AttributeType.OPTIONAL,
                weight=0.6,
                description='Required equipment for the job',
                possible_values=['Basic Tools', 'Advanced Equipment', 'Professional Tools', 'Specialized Equipment', 'Industrial Tools']
            ),
            'certifications': AttributeDefinition(
                name='Certifications',
                category=AttributeCategory.PROFESSIONAL,
                type=AttributeType.OPTIONAL,
                weight=0.5,
                description='Required certifications',
                possible_values=['Plumbing License', 'Advanced Plumbing License', 'Master Plumber License', 'Commercial Plumbing License', 'Industrial Plumbing License']
            )
        }
    
    def load_dataset(self, file_path: str):
        """Load the plumber dataset"""
        self.df = pd.read_csv(file_path)
        return self.df
    
    def get_available_attributes(self) -> Dict[str, AttributeDefinition]:
        """Get all available attributes for selection"""
        return self.attributes
    
    def get_attributes_by_category(self, category: AttributeCategory) -> Dict[str, AttributeDefinition]:
        """Get attributes filtered by category"""
        return {name: attr for name, attr in self.attributes.items() 
                if attr.category == category}
    
    def validate_attribute_values(self, attribute_name: str, value: Any) -> bool:
        """Validate if a value is valid for a given attribute"""
        if attribute_name not in self.attributes:
            return False
        
        attr = self.attributes[attribute_name]
        
        if attr.possible_values and value not in attr.possible_values:
            return False
        
        if attr.min_value is not None and value < attr.min_value:
            return False
        
        if attr.max_value is not None and value > attr.max_value:
            return False
        
        return True
    
    def calculate_attribute_score(self, plumber_data: Dict, attribute_name: str, 
                                customer_value: Any, attribute_type: AttributeType) -> float:
        """Calculate score for a specific attribute"""
        if attribute_name not in self.attributes:
            return 0.0
        
        attr = self.attributes[attribute_name]
        
        # Map attribute names to actual column names in the dataset
        column_mapping = {
            'work_type': 'Work_Specialization',
            'district': 'District',
            'language': 'Languages_Spoken',
            'experience_years': 'Experience_Years',
            'license_type': 'License_Type',
            'insurance_status': 'Insurance_Status',
            'specialization_level': 'Specialization_Level',
            'response_time': 'Response_Time_Minutes',
            'max_distance': 'Max_Distance_km',
            'weekend_available': 'Weekend_Available',
            'emergency_service': 'Emergency_Service',
            'min_rating': 'Rating',
            'min_success_rate': 'Success_Rate',
            'guarantee_period': 'Guarantee_Period_Days',
            'max_cost': 'Min_Order_Value',
            'payment_methods': 'Payment_Methods',
            'required_equipment': 'Equipment_Available',
            'certifications': 'Certifications'
        }
        
        # Get the actual column name
        column_name = column_mapping.get(attribute_name, attribute_name)
        plumber_value = plumber_data.get(column_name)
        
        if plumber_value is None:
            return 0.0
        
        # Handle different data types
        if attr.possible_values:  # Categorical attribute
            if customer_value == 'Any' or customer_value == plumber_value:
                return attr.weight
            elif isinstance(plumber_value, str) and customer_value in plumber_value:
                return attr.weight * 0.8
            elif isinstance(customer_value, str) and isinstance(plumber_value, str):
                # Case-insensitive comparison
                if customer_value.lower() in plumber_value.lower():
                    return attr.weight * 0.6
                # For work_type, be more strict - check if it's the primary specialization
                elif attribute_name == 'work_type':
                    # Check if the work type is in the detailed specializations
                    detailed_specs = plumber_data.get('Specializations_Detailed', '')
                    if customer_value.lower() in detailed_specs.lower():
                        return attr.weight * 0.7
            else:
                return 0.0
        
        elif attr.min_value is not None:  # Numerical attribute
            try:
                plumber_val = float(plumber_value)
                customer_val = float(customer_value)
                
                if attribute_name in ['response_time', 'max_distance']:
                    # Lower is better
                    if plumber_val <= customer_val:
                        return attr.weight
                    else:
                        return max(0, attr.weight * (1 - (plumber_val - customer_val) / customer_val))
                
                elif attribute_name in ['experience_years', 'min_rating', 'min_success_rate', 'guarantee_period']:
                    # Higher is better
                    if plumber_val >= customer_val:
                        return attr.weight
                    else:
                        return max(0, attr.weight * (plumber_val / customer_val))
                
                elif attribute_name == 'max_cost':
                    # Lower is better
                    if plumber_val <= customer_val:
                        return attr.weight
                    else:
                        return max(0, attr.weight * (1 - (plumber_val - customer_val) / customer_val))
                
            except (ValueError, TypeError):
                return 0.0
        
        return 0.0
    
    def match_plumbers(self, customer_preferences: Dict[str, Any], 
                      max_results: int = 10) -> List[Dict]:
        """Match plumbers based on customer preferences"""
        if self.df is None:
            raise ValueError("Dataset not loaded. Call load_dataset() first.")
        
        results = []
        
        for _, plumber in self.df.iterrows():
            plumber_dict = plumber.to_dict()
            total_score = 0.0
            attribute_scores = {}
            
            # Calculate scores for each attribute
            for attr_name, customer_value in customer_preferences.items():
                if attr_name in self.attributes and customer_value is not None:
                    score = self.calculate_attribute_score(
                        plumber_dict, attr_name, customer_value, 
                        self.attributes[attr_name].type
                    )
                    attribute_scores[attr_name] = score
                    total_score += score
            
            # Apply distance penalty
            if 'client_lat' in customer_preferences and 'client_lon' in customer_preferences:
                distance = self._calculate_distance(
                    customer_preferences['client_lat'],
                    customer_preferences['client_lon'],
                    plumber_dict['Latitude'],
                    plumber_dict['Longitude']
                )
                # Don't apply distance penalty if no other attributes matched
                if total_score > 0:
                    distance_penalty = max(0.1, 1 - (distance / 100))  # Less aggressive penalty
                    total_score *= distance_penalty
                plumber_dict['Distance_km'] = round(distance, 2)
            
            # Add to results if meets minimum requirements OR if no specific preferences were given
            if total_score > 0 or len([k for k, v in customer_preferences.items() if k not in ['client_lat', 'client_lon'] and v is not None]) == 0:
                # If no specific preferences, give a base score
                if total_score == 0:
                    total_score = 0.1  # Minimum score for showing results
                plumber_dict['Match_Score'] = round(total_score, 2)
                plumber_dict['Attribute_Scores'] = attribute_scores
                results.append(plumber_dict) 
                
        # Sort by match score and return top results
        results.sort(key=lambda x: x['Match_Score'], reverse=True)
        return results[:max_results]
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        R = 6371  # Earth radius in km
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
    
    def get_attribute_suggestions(self, partial_input: str) -> List[str]:
        """Get attribute suggestions based on partial input"""
        suggestions = []
        partial_lower = partial_input.lower()
        
        for attr_name, attr_def in self.attributes.items():
            if (partial_lower in attr_name.lower() or 
                partial_lower in attr_def.name.lower() or
                partial_lower in attr_def.description.lower()):
                suggestions.append(attr_name)
        
        return suggestions[:10]  # Limit to 10 suggestions
    
    def get_value_suggestions(self, attribute_name: str, partial_input: str = "") -> List[str]:
        """Get value suggestions for a specific attribute"""
        if attribute_name not in self.attributes:
            return []
        
        attr = self.attributes[attribute_name]
        
        if attr.possible_values:
            if partial_input:
                return [val for val in attr.possible_values 
                       if partial_input.lower() in val.lower()]
            else:
                return attr.possible_values
        
        return []
    
    def generate_matching_report(self, customer_preferences: Dict[str, Any], 
                               matched_plumbers: List[Dict]) -> Dict:
        """Generate a detailed matching report"""
        report = {
            'total_plumbers_found': len(matched_plumbers),
            'preferences_used': list(customer_preferences.keys()),
            'top_matches': [],
            'attribute_analysis': {},
            'recommendations': []
        }
        
        if matched_plumbers:
            # Top matches
            report['top_matches'] = [
                {
                    'name': p['Name'],
                    'score': p['Match_Score'],
                    'specialization': p['Work_Specialization'],
                    'distance': p.get('Distance_km', 'N/A'),
                    'rating': p.get('Rating', 'N/A')
                }
                for p in matched_plumbers[:5]
            ]
            
            # Attribute analysis
            for attr_name in customer_preferences.keys():
                if attr_name in self.attributes:
                    scores = [p['Attribute_Scores'].get(attr_name, 0) 
                             for p in matched_plumbers]
                    report['attribute_analysis'][attr_name] = {
                        'average_score': round(np.mean(scores), 2),
                        'max_score': round(max(scores), 2),
                        'min_score': round(min(scores), 2)
                    }
            
            # Recommendations
            if len(matched_plumbers) < 5:
                report['recommendations'].append(
                    "Consider relaxing some preferences to find more plumbers"
                )
            
            if any(p.get('Distance_km', 0) > 30 for p in matched_plumbers):
                report['recommendations'].append(
                    "Some plumbers are far away. Consider expanding your search area"
                )
        
        return report 