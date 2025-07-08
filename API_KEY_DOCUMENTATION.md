# API Key System Documentation

## Overview

The Plumber Booking System now includes a comprehensive API key system that allows third-party applications to securely access and manage the attribute system for plumber-customer matching. This enables external integrations, mobile apps, and other services to leverage the sophisticated matching algorithm.

## Features

### 🔐 Secure Authentication
- **API Key Generation**: Cryptographically secure random keys
- **Key Hashing**: Keys are hashed before storage for security
- **Permission-Based Access**: Granular permissions for different operations
- **Rate Limiting**: Configurable request limits per hour

### 🛠️ Admin Management
- **Web Interface**: Full admin dashboard for API key management
- **Key Creation**: Generate new API keys with custom permissions
- **Key Monitoring**: Track usage and last access times
- **Key Lifecycle**: Activate/deactivate keys as needed

### 🔌 Third-Party Integration
- **RESTful API**: Standard HTTP endpoints for all operations
- **JSON Responses**: Consistent response format
- **Error Handling**: Comprehensive error messages and status codes
- **Batch Operations**: Efficient bulk attribute management

## API Endpoints

### Authentication
All API endpoints require authentication via API key. Include the key in the request header:

```
X-API-Key: your_api_key_here
```

Or as a query parameter:

```
?api_key=your_api_key_here
```

### 1. Get All Attributes
**GET** `/api/v1/attributes`

**Permissions Required**: `read_attributes`

**Response**:
```json
{
  "success": true,
  "data": {
    "basic": [
      {
        "name": "experience_years",
        "description": "Years of experience in plumbing",
        "possible_values": ["0-2", "3-5", "5-10", "10+"],
        "min_value": null,
        "max_value": null,
        "unit": "years",
        "type": "preferred",
        "weight": 0.8
      }
    ],
    "professional": [...],
    "logistical": [...],
    "quality": [...],
    "financial": [...]
  },
  "total_attributes": 15
}
```

### 2. Create New Attribute
**POST** `/api/v1/attributes`

**Permissions Required**: `write_attributes`

**Request Body**:
```json
{
  "name": "emergency_response_time",
  "description": "Time to respond to emergency calls",
  "category": "professional",
  "type": "preferred",
  "weight": 0.8,
  "possible_values": ["< 15 min", "15-30 min", "30-60 min", "> 60 min"],
  "min_value": null,
  "max_value": null,
  "unit": "minutes"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Attribute \"emergency_response_time\" created successfully",
  "attribute": {
    "name": "emergency_response_time",
    "category": "professional",
    "type": "preferred",
    "weight": 0.8
  }
}
```

### 3. Update Attribute
**PUT** `/api/v1/attributes/{attr_name}`

**Permissions Required**: `write_attributes`

**Request Body**:
```json
{
  "weight": 0.9,
  "description": "Updated description"
}
```

### 4. Delete Attribute
**DELETE** `/api/v1/attributes/{attr_name}`

**Permissions Required**: `write_attributes`

### 5. Batch Update Attributes
**POST** `/api/v1/attributes/batch`

**Permissions Required**: `write_attributes`

**Request Body**:
```json
{
  "attributes": [
    {
      "name": "experience_years",
      "weight": 0.85,
      "description": "Updated experience weight"
    },
    {
      "name": "response_time",
      "weight": 0.9,
      "description": "Updated response time weight"
    }
  ]
}
```

**Response**:
```json
{
  "success": true,
  "results": [
    {"name": "experience_years", "status": "updated"},
    {"name": "response_time", "status": "updated"}
  ],
  "summary": {
    "total": 2,
    "updated": 2,
    "errors": 0
  }
}
```

### 6. Match Plumbers
**POST** `/api/v1/match`

**Permissions Required**: `read_attributes`, `match_plumbers`

**Request Body**:
```json
{
  "preferences": {
    "client_lat": 23.0225,
    "client_lon": 72.5714,
    "district": "Ahmedabad",
    "work_type": "leak repair",
    "language": "Gujarati",
    "emergency_response_time": "< 15 min",
    "experience_years": "5-10"
  },
  "max_results": 10
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "plumbers": [
      {
        "Name": "Rajesh Patel",
        "District": "Ahmedabad",
        "Work_Specialization": "leak repair",
        "Languages": "Gujarati, Hindi",
        "match_score": 0.95,
        "Distance_km": 2.3
      }
    ],
    "total_found": 5,
    "preferences_used": ["client_lat", "client_lon", "district", "work_type", "language"]
  }
}
```

### 7. Export Attributes Configuration
**GET** `/api/v1/attributes/export`

**Permissions Required**: `read_attributes`

**Response**:
```json
{
  "success": true,
  "data": {
    "attributes": {
      "experience_years": {
        "name": "experience_years",
        "description": "Years of experience",
        "category": "professional",
        "type": "preferred",
        "weight": 0.8,
        "possible_values": ["0-2", "3-5", "5-10", "10+"]
      }
    }
  },
  "exported_at": "2024-01-15T10:30:00Z"
}
```

### 8. Import Attributes Configuration
**POST** `/api/v1/attributes/import`

**Permissions Required**: `write_attributes`

**Request Body**:
```json
{
  "attributes": {
    "experience_years": {
      "name": "experience_years",
      "description": "Years of experience",
      "category": "professional",
      "type": "preferred",
      "weight": 0.8,
      "possible_values": ["0-2", "3-5", "5-10", "10+"]
    }
  }
}
```

## Permission System

### Available Permissions
- `read_attributes`: View all attributes and their configurations
- `write_attributes`: Create, update, and delete attributes
- `match_plumbers`: Use the matching algorithm to find plumbers
- `export_attributes`: Export attribute configurations
- `import_attributes`: Import attribute configurations
- `batch_operations`: Perform batch updates on multiple attributes

### Permission Combinations
Different use cases may require different permission sets:

**Read-Only Integration**:
```json
["read_attributes", "match_plumbers"]
```

**Full Management Integration**:
```json
["read_attributes", "write_attributes", "match_plumbers", "export_attributes", "import_attributes", "batch_operations"]
```

**Configuration Management**:
```json
["read_attributes", "write_attributes", "export_attributes", "import_attributes"]
```

## Error Handling

### HTTP Status Codes
- `200 OK`: Request successful
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Missing or invalid API key
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Error Response Format
```json
{
  "error": "Detailed error message",
  "code": "ERROR_CODE",
  "details": {
    "field": "Additional error details"
  }
}
```

### Common Error Scenarios
1. **Missing API Key**: `401 Unauthorized`
2. **Invalid API Key**: `401 Unauthorized`
3. **Insufficient Permissions**: `403 Forbidden`
4. **Rate Limit Exceeded**: `429 Too Many Requests`
5. **Invalid Attribute Name**: `404 Not Found`
6. **Missing Required Fields**: `400 Bad Request`

## Rate Limiting

Each API key has a configurable rate limit (default: 1000 requests per hour). When the limit is exceeded, the API returns a `429 Too Many Requests` status code.

### Rate Limit Headers
The API includes rate limit information in response headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642233600
```

## Admin Dashboard

### Accessing API Key Management
1. Login as admin user
2. Navigate to Admin Dashboard
3. Click on "API Keys" tab
4. Manage API keys through the web interface

### Creating New API Keys
1. Click "Create New API Key"
2. Fill in the form:
   - **Name**: Descriptive name for the key
   - **Description**: Optional description
   - **Rate Limit**: Requests per hour (1-10,000)
   - **Permissions**: Select required permissions
3. Click "Create API Key"
4. **Important**: Copy the generated key immediately (it's only shown once)

### Managing Existing Keys
- **View Details**: See key information, permissions, and usage
- **Activate/Deactivate**: Toggle key status
- **Delete**: Permanently remove keys
- **Monitor Usage**: Track last used time and request count

## Security Best Practices

### For API Key Holders
1. **Secure Storage**: Store API keys securely, never in client-side code
2. **Key Rotation**: Regularly rotate API keys
3. **Minimal Permissions**: Request only necessary permissions
4. **HTTPS Only**: Always use HTTPS for API calls
5. **Error Handling**: Implement proper error handling for API responses

### For System Administrators
1. **Regular Audits**: Review API key usage regularly
2. **Permission Reviews**: Ensure keys have appropriate permissions
3. **Key Expiration**: Consider implementing key expiration policies
4. **Monitoring**: Monitor for unusual API usage patterns
5. **Backup**: Keep secure backups of API key configurations

## Integration Examples

### Python Example
```python
import requests

API_KEY = "your_api_key_here"
BASE_URL = "http://localhost:5000"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Get all attributes
response = requests.get(f"{BASE_URL}/api/v1/attributes", headers=headers)
attributes = response.json()

# Create new attribute
new_attribute = {
    "name": "certification_level",
    "description": "Professional certification level",
    "category": "professional",
    "type": "preferred",
    "weight": 0.7,
    "possible_values": ["Basic", "Advanced", "Expert", "Master"]
}

response = requests.post(f"{BASE_URL}/api/v1/attributes", 
                        headers=headers, 
                        json=new_attribute)

# Match plumbers
preferences = {
    "client_lat": 23.0225,
    "client_lon": 72.5714,
    "district": "Ahmedabad",
    "work_type": "leak repair",
    "certification_level": "Expert"
}

response = requests.post(f"{BASE_URL}/api/v1/match", 
                        headers=headers, 
                        json={"preferences": preferences})
```

### JavaScript Example
```javascript
const API_KEY = 'your_api_key_here';
const BASE_URL = 'http://localhost:5000';

const headers = {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
};

// Get all attributes
fetch(`${BASE_URL}/api/v1/attributes`, { headers })
    .then(response => response.json())
    .then(data => console.log('Attributes:', data));

// Create new attribute
const newAttribute = {
    name: 'response_time',
    description: 'Average response time',
    category: 'professional',
    type: 'preferred',
    weight: 0.8,
    possible_values: ['< 30 min', '30-60 min', '1-2 hours', '> 2 hours']
};

fetch(`${BASE_URL}/api/v1/attributes`, {
    method: 'POST',
    headers,
    body: JSON.stringify(newAttribute)
})
.then(response => response.json())
.then(data => console.log('Created:', data));
```

### cURL Examples
```bash
# Get all attributes
curl -H "X-API-Key: your_api_key_here" \
     http://localhost:5000/api/v1/attributes

# Create new attribute
curl -X POST \
     -H "X-API-Key: your_api_key_here" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "availability_24_7",
       "description": "24/7 availability",
       "category": "logistical",
       "type": "preferred",
       "weight": 0.6,
       "possible_values": ["Yes", "No"]
     }' \
     http://localhost:5000/api/v1/attributes

# Match plumbers
curl -X POST \
     -H "X-API-Key: your_api_key_here" \
     -H "Content-Type: application/json" \
     -d '{
       "preferences": {
         "client_lat": 23.0225,
         "client_lon": 72.5714,
         "district": "Ahmedabad",
         "work_type": "installation"
       }
     }' \
     http://localhost:5000/api/v1/match
```

## Testing

Use the provided test script to verify API functionality:

```bash
python test_api_keys.py
```

This script tests:
- API key authentication
- Attribute management operations
- Plumber matching functionality
- Export/import operations
- Error handling

## Support

For technical support or questions about the API key system:

1. Check the error messages and status codes
2. Verify API key permissions
3. Review rate limiting settings
4. Test with the provided examples
5. Contact system administrators for additional help

## Changelog

### Version 1.0.0 (Current)
- Initial API key system implementation
- Complete attribute management API
- Admin dashboard integration
- Comprehensive documentation
- Test suite and examples 