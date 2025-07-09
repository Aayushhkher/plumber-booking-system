from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, render_template_string, session
import pandas as pd
from flask_cors import CORS
import math
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, PlumberProfile, Booking, Review, APIKey
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from sqlalchemy import and_, or_
from collections import defaultdict, Counter
from attribute_system import DynamicAttributeSystem, AttributeCategory, AttributeDefinition, AttributeType
import json
import functools

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Config for SQLite and secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///plumber_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize dynamic attribute system
attribute_system = DynamicAttributeSystem()

# Create tables if not exist
with app.app_context():
    db.create_all()

# Load enhanced dataset
try:
    df = pd.read_csv('enhanced_plumbers_dataset.csv')
    attribute_system.load_dataset('enhanced_plumbers_dataset.csv')
except FileNotFoundError:
    # Fallback to original dataset
    df = pd.read_csv('gujarat_plumbers_dataset.csv')
    print("Warning: Using original dataset. Enhanced dataset not found.")

# Custom Jinja2 filter to parse JSON strings
@app.template_filter('from_json')
def from_json_filter(s):
    try:
        return json.loads(s) if s else []
    except Exception:
        return []

# API Key Authentication Decorator
def require_api_key(permissions=None):
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
            
            if not api_key:
                return jsonify({'error': 'API key required'}), 401
            
            # Find the API key
            api_key_obj = APIKey.query.filter_by(is_active=True).all()
            valid_key = None
            
            for key_obj in api_key_obj:
                if key_obj.check_key(api_key):
                    valid_key = key_obj
                    break
            
            if not valid_key:
                return jsonify({'error': 'Invalid API key'}), 401
            
            # Check rate limiting
            if valid_key.last_used:
                time_diff = datetime.utcnow() - valid_key.last_used
                if time_diff < timedelta(hours=1):
                    # Simple rate limiting - in production, use Redis or similar
                    return jsonify({'error': 'Rate limit exceeded'}), 429
            
            # Check permissions if specified
            if permissions:
                key_permissions = json.loads(valid_key.permissions or '[]')
                if not any(perm in key_permissions for perm in permissions):
                    return jsonify({'error': 'Insufficient permissions'}), 403
            
            # Update last used timestamp
            valid_key.last_used = datetime.utcnow()
            db.session.commit()
            
            # Add API key info to request context
            request.api_key = valid_key
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Third-party API endpoints for attribute allocation
@app.route('/api/v1/attributes', methods=['GET'])
@require_api_key(['read_attributes'])
def api_get_attributes():
    """Get all available attributes"""
    try:
        categories = {}
        for category in AttributeCategory:
            attributes = attribute_system.get_attributes_by_category(category)
            categories[category.value] = [
                {
                    'name': attr.name,
                    'description': attr.description,
                    'possible_values': attr.possible_values,
                    'min_value': attr.min_value,
                    'max_value': attr.max_value,
                    'unit': attr.unit,
                    'type': attr.type.value,
                    'weight': attr.weight
                }
                for attr in attributes.values()
            ]
        return jsonify({
            'success': True,
            'data': categories,
            'total_attributes': sum(len(attrs) for attrs in categories.values())
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/attributes', methods=['POST'])
@require_api_key(['write_attributes'])
def api_create_attribute():
    """Create a new attribute"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['name', 'category', 'type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create attribute definition
        attr_def = AttributeDefinition(
            name=data['name'],
            description=data.get('description', ''),
            category=AttributeCategory(data['category']),
            type=AttributeType(data['type']),
            weight=float(data.get('weight', 1.0)),
            possible_values=data.get('possible_values', []),
            min_value=data.get('min_value'),
            max_value=data.get('max_value'),
            unit=data.get('unit')
        )
        
        # Add to attribute system
        attribute_system.add_attribute(attr_def)
        
        return jsonify({
            'success': True,
            'message': f'Attribute "{data["name"]}" created successfully',
            'attribute': {
                'name': attr_def.name,
                'category': attr_def.category.value,
                'type': attr_def.type.value,
                'weight': attr_def.weight
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/attributes/<attr_name>', methods=['PUT'])
@require_api_key(['write_attributes'])
def api_update_attribute(attr_name):
    """Update an existing attribute"""
    try:
        data = request.json
        
        # Get existing attribute
        existing_attr = attribute_system.get_attribute(attr_name)
        if not existing_attr:
            return jsonify({'error': f'Attribute "{attr_name}" not found'}), 404
        
        # Update fields
        if 'description' in data:
            existing_attr.description = data['description']
        if 'weight' in data:
            existing_attr.weight = float(data['weight'])
        if 'possible_values' in data:
            existing_attr.possible_values = data['possible_values']
        if 'min_value' in data:
            existing_attr.min_value = data['min_value']
        if 'max_value' in data:
            existing_attr.max_value = data['max_value']
        if 'unit' in data:
            existing_attr.unit = data['unit']
        
        # Update in attribute system
        attribute_system.update_attribute(attr_name, existing_attr)
        
        return jsonify({
            'success': True,
            'message': f'Attribute "{attr_name}" updated successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/attributes/<attr_name>', methods=['DELETE'])
@require_api_key(['write_attributes'])
def api_delete_attribute(attr_name):
    """Delete an attribute"""
    try:
        # Check if attribute exists
        existing_attr = attribute_system.get_attribute(attr_name)
        if not existing_attr:
            return jsonify({'error': f'Attribute "{attr_name}" not found'}), 404
        
        # Delete from attribute system
        attribute_system.remove_attribute(attr_name)
        
        return jsonify({
            'success': True,
            'message': f'Attribute "{attr_name}" deleted successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/attributes/batch', methods=['POST'])
@require_api_key(['write_attributes'])
def api_batch_update_attributes():
    """Batch update multiple attributes"""
    try:
        data = request.json
        
        if 'attributes' not in data:
            return jsonify({'error': 'Missing attributes array'}), 400
        
        results = []
        for attr_data in data['attributes']:
            try:
                attr_name = attr_data.get('name')
                if not attr_name:
                    results.append({'name': 'unknown', 'status': 'error', 'message': 'Missing name'})
                    continue
                
                existing_attr = attribute_system.get_attribute(attr_name)
                if existing_attr:
                    # Update existing attribute
                    if 'weight' in attr_data:
                        existing_attr.weight = float(attr_data['weight'])
                    if 'description' in attr_data:
                        existing_attr.description = attr_data['description']
                    
                    attribute_system.update_attribute(attr_name, existing_attr)
                    results.append({'name': attr_name, 'status': 'updated'})
                else:
                    results.append({'name': attr_name, 'status': 'error', 'message': 'Attribute not found'})
            except Exception as e:
                results.append({'name': attr_name, 'status': 'error', 'message': str(e)})
        
        return jsonify({
            'success': True,
            'results': results,
            'summary': {
                'total': len(results),
                'updated': len([r for r in results if r['status'] == 'updated']),
                'errors': len([r for r in results if r['status'] == 'error'])
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/match', methods=['POST'])
@require_api_key(['read_attributes', 'match_plumbers'])
def api_match_plumbers():
    """Match plumbers based on customer preferences"""
    try:
        data = request.json
        
        if 'preferences' not in data:
            return jsonify({'error': 'Missing preferences object'}), 400
        
        customer_preferences = data['preferences']
        max_results = data.get('max_results', 10)
        
        # Use the dynamic attribute system to match plumbers
        matched_plumbers = attribute_system.match_plumbers(customer_preferences, max_results=max_results)
        
        return jsonify({
            'success': True,
            'data': {
                'plumbers': matched_plumbers,
                'total_found': len(matched_plumbers),
                'preferences_used': list(customer_preferences.keys())
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/attributes/export', methods=['GET'])
@require_api_key(['read_attributes'])
def api_export_attributes():
    """Export all attributes configuration"""
    try:
        config = attribute_system.export_configuration()
        return jsonify({
            'success': True,
            'data': config,
            'exported_at': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/attributes/import', methods=['POST'])
@require_api_key(['write_attributes'])
def api_import_attributes():
    """Import attributes configuration"""
    try:
        data = request.json
        
        if 'attributes' not in data:
            return jsonify({'error': 'Missing attributes configuration'}), 400
        
        # Import configuration
        attribute_system.import_configuration(data)
        
        return jsonify({
            'success': True,
            'message': 'Attributes imported successfully',
            'imported_at': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Admin API key management endpoints
@app.route('/admin/api_keys', methods=['GET'])
@login_required
def admin_api_keys():
    """Admin page for managing API keys"""
    if current_user.role != 'admin':
        return redirect(url_for('admin_dashboard'))
    
    api_keys = APIKey.query.all()
    return render_template('admin_api_keys.html', api_keys=api_keys)

@app.route('/admin/api_keys', methods=['POST'])
@login_required
def create_api_key():
    """Create a new API key"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        data = request.json
        
        # Generate new API key
        api_key_value = APIKey.generate_key()
        key_hash = APIKey.hash_key(api_key_value)
        
        # Create API key record
        api_key = APIKey(
            name=data['name'],
            key_hash=key_hash,
            description=data.get('description', ''),
            permissions=json.dumps(data.get('permissions', [])),
            rate_limit=int(data.get('rate_limit', 1000)),
            created_by=current_user.id
        )
        
        db.session.add(api_key)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'api_key': api_key_value,  # Only returned once
            'message': 'API key created successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api_keys/<int:key_id>', methods=['DELETE'])
@login_required
def delete_api_key(key_id):
    """Delete an API key"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        api_key = APIKey.query.get_or_404(key_id)
        db.session.delete(api_key)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'API key deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api_keys/<int:key_id>/toggle', methods=['POST'])
@login_required
def toggle_api_key(key_id):
    """Toggle API key active status"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        api_key = APIKey.query.get_or_404(key_id)
        api_key.is_active = not api_key.is_active
        db.session.commit()
        
        return jsonify({
            'success': True,
            'is_active': api_key.is_active,
            'message': f'API key {"activated" if api_key.is_active else "deactivated"} successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Haversine formula to calculate distance between two lat/lon points in km
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Pricing model: base price per work type
WORK_TYPE_PRICING = {
    'leak repair': 300,
    'installation': 500,
    'maintenance': 400,
    'inspection': 200,
    # Add more as needed
}

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/dynamic_booking')
@login_required
def dynamic_booking():
    """New dynamic booking interface"""
    if current_user.role != 'customer':
        return redirect(url_for('login'))
    return render_template('dynamic_booking.html')

@app.route('/api/time_slots')
def api_time_slots():
    """API endpoint to get available time slots"""
    time_slots = sorted(set(slot.strip() for slots in df['Free_Time_Slots'] for slot in str(slots).split(',')))
    return jsonify({'time_slots': time_slots})

@app.route('/api/districts')
def api_districts():
    """API endpoint to get available districts"""
    districts = sorted(df['District'].unique())
    return jsonify({'districts': districts})

@app.route('/api/attribute_categories')
def api_attribute_categories():
    """API endpoint to get attribute categories"""
    categories = {}
    for category in AttributeCategory:
        attributes = attribute_system.get_attributes_by_category(category)
        categories[category.value] = [
            {
                'name': attr.name,
                'description': attr.description,
                'possible_values': attr.possible_values,
                'min_value': attr.min_value,
                'max_value': attr.max_value,
                'unit': attr.unit,
                'type': attr.type.value
            }
            for attr in attributes.values()
        ]
    return jsonify({'categories': categories})

@app.route('/api/dynamic_match_plumbers', methods=['POST'])
def api_dynamic_match_plumbers():
    """API endpoint for dynamic plumber matching"""
    try:
        print("🔍 API called: /api/dynamic_match_plumbers")
        data = request.json
        print(f"📋 Received data: {data}")
        
        # Extract basic requirements
        customer_preferences = {
            'client_lat': float(data.get('client_lat', 0)),
            'client_lon': float(data.get('client_lon', 0))
        }
        
        # Add work_type if specified
        if data.get('work_type'):
            customer_preferences['work_type'] = data.get('work_type')
        
        # Add district if specified
        if data.get('district') and data.get('district') != '':
            customer_preferences['district'] = data.get('district')
        
        # Add language if specified
        if data.get('language') and data.get('language') != '':
            customer_preferences['language'] = data.get('language')
        
        # Add dynamic attributes
        for key, value in data.items():
            if key not in ['date', 'time_slot', 'work_type', 'district', 'language', 'client_lat', 'client_lon']:
                if value and value != '':
                    customer_preferences[key] = value
        
        print(f"🎯 Customer preferences: {customer_preferences}")
        
        # Use the dynamic attribute system to match plumbers
        matched_plumbers = attribute_system.match_plumbers(customer_preferences, max_results=20)
        print(f"✅ Found {len(matched_plumbers)} plumbers")
        
        # Add additional information for display
        for plumber in matched_plumbers:
            # Calculate ETA
            if customer_preferences.get('client_lat') and customer_preferences.get('client_lon'):
                distance = plumber.get('Distance_km', 0)
                plumber['eta'] = int(distance / 40 * 60)  # 40 km/h average speed
            
            # Calculate cost estimate
            work_type = plumber.get('Work_Specialization', '').lower()
            base_price = WORK_TYPE_PRICING.get(work_type, 400)
            distance = plumber.get('Distance_km', 0)
            cost_estimate = int(base_price + 10 * distance)
            plumber['cost_estimate'] = cost_estimate
        
        response_data = {
            'plumbers': matched_plumbers,
            'total_found': len(matched_plumbers)
        }
        print(f"📤 Sending response with {len(matched_plumbers)} plumbers")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Error in API: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400

@app.route('/api/confirm_booking', methods=['POST'])
@login_required
def api_confirm_booking():
    """API endpoint to confirm booking"""
    try:
        data = request.json
        
        # Find the plumber by name
        plumber_name = data.get('plumber_name')
        plumber_row = df[df['Name'] == plumber_name]
        
        if plumber_row.empty:
            return jsonify({'success': False, 'error': 'Plumber not found'})
        
        plumber_data = plumber_row.iloc[0]
        
        # Create booking
        booking = Booking(
            customer_id=current_user.id,
            plumber_id=1,  # You might need to map this properly
            date=datetime.strptime(data.get('date'), '%Y-%m-%d').date(),
            time_slot=data.get('time_slot'),
            service_type=data.get('work_type'),
            client_lat=float(data.get('client_lat', 0)),
            client_lon=float(data.get('client_lon', 0)),
            status='pending'
        )
        
        db.session.add(booking)
        db.session.commit()
        
        return jsonify({'success': True, 'booking_id': booking.id})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/find_plumbers', methods=['POST'])
def find_plumbers():
    data = request.json
    location = data.get('location')
    work_type = data.get('work_type')
    time_slot = data.get('time_slot')
    language = data.get('language')
    client_lat = float(data.get('client_lat'))
    client_lon = float(data.get('client_lon'))

    filtered = df[df['District'] == location]
    filtered = filtered[filtered['Work_Specialization'] == work_type]
    filtered = filtered[filtered['Free_Time_Slots'].str.contains(time_slot)]
    if language and language != 'Any':
        filtered = filtered[filtered['Languages_Spoken'].str.contains(language)]

    # Calculate distance and ETA for each plumber
    plumbers = []
    for _, row in filtered.iterrows():
        dist = haversine(client_lat, client_lon, row['Latitude'], row['Longitude'])
        eta = dist / 40 * 60  # 40 km/h, ETA in minutes
        plumber = row.to_dict()
        plumber['Distance_km'] = round(dist, 2)
        plumber['ETA_min'] = int(round(eta))
        plumbers.append(plumber)
    plumbers = sorted(plumbers, key=lambda x: x['Distance_km'])
    return jsonify({'plumbers': plumbers})

@app.route('/options', methods=['GET'])
def get_options():
    locations = sorted(df['District'].unique())
    work_types = sorted(df['Work_Specialization'].unique())
    time_slots = sorted(set(slot.strip() for slots in df['Free_Time_Slots'] for slot in str(slots).split(',')))
    languages = sorted(set(lang.strip() for langs in df['Languages_Spoken'] for lang in str(langs).split(',')))
    return jsonify({
        'locations': locations,
        'work_types': work_types,
        'time_slots': time_slots,
        'languages': languages
    })

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('register.html')
        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role=role
        )
        db.session.add(user)
        db.session.commit()
        if role == 'plumber':
            district = request.form.get('district')
            specialization = request.form.get('specialization')
            languages = request.form.get('languages')
            free_time_slots = request.form.get('free_time_slots')
            lat = request.form.get('lat')
            lon = request.form.get('lon')
            plumber_profile = PlumberProfile(
                user_id=user.id,
                district=district,
                specialization=specialization,
                languages=languages,
                free_time_slots=free_time_slots,
                lat=float(lat) if lat else None,
                lon=float(lon) if lon else None
            )
            db.session.add(plumber_profile)
            db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            if user.role == 'customer':
                return redirect(url_for('customer_dashboard'))
            elif user.role == 'plumber':
                return redirect(url_for('plumber_dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Unknown user role.', 'danger')
                return redirect(url_for('login'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/customer_dashboard')
@login_required
def customer_dashboard():
    if current_user.role != 'customer':
        return redirect(url_for('login'))
    # Get bookings for this customer
    bookings = Booking.query.filter_by(customer_id=current_user.id).order_by(Booking.date.desc()).all()
    booking_list = []
    for b in bookings:
        plumber = PlumberProfile.query.get(b.plumber_id)
        review = Review.query.filter_by(booking_id=b.id).first()
        # Cost estimate logic
        work_type_norm = (b.service_type or '').strip().lower()
        base_price = WORK_TYPE_PRICING.get(work_type_norm, 400)
        dist = None
        if b.client_lat is not None and b.client_lon is not None and plumber and plumber.lat is not None and plumber.lon is not None:
            dist = haversine(b.client_lat, b.client_lon, plumber.lat, plumber.lon)
        if dist is not None:
            cost_estimate = int(base_price + 10 * dist)
        else:
            cost_estimate = base_price
        booking_list.append({
            'id': b.id,
            'plumber_name': plumber.user.name if plumber and plumber.user else 'N/A',
            'date': b.date.strftime('%Y-%m-%d'),
            'time_slot': b.time_slot,
            'status': b.status,
            'service_type': b.service_type,
            'reviewed': bool(review),
            'cost_estimate': cost_estimate,
            'client_lat': b.client_lat,
            'client_lon': b.client_lon,
            'plumber_lat': plumber.lat if plumber else None,
            'plumber_lon': plumber.lon if plumber else None
        })
    return render_template('customer_dashboard.html', bookings=booking_list)

@app.route('/plumber_dashboard', methods=['GET'])
@login_required
def plumber_dashboard():
    if current_user.role != 'plumber':
        return redirect(url_for('login'))
    plumber_profile = PlumberProfile.query.filter_by(user_id=current_user.id).first()
    if not plumber_profile:
        flash('No plumber profile found.', 'danger')
        return redirect(url_for('logout'))
    # Get bookings for this plumber
    bookings = Booking.query.filter_by(plumber_id=plumber_profile.id).order_by(Booking.date.desc()).all()
    booking_list = []
    for b in bookings:
        customer = User.query.get(b.customer_id)
        booking_list.append({
            'id': b.id,
            'customer_name': customer.name if customer else 'N/A',
            'date': b.date.strftime('%Y-%m-%d'),
            'time_slot': b.time_slot,
            'status': b.status,
            'service_type': b.service_type,
            'client_lat': b.client_lat,
            'client_lon': b.client_lon
        })
    # Get reviews for this plumber
    reviews = Review.query.filter_by(plumber_id=plumber_profile.id).order_by(Review.created_at.desc()).all()
    review_list = []
    for r in reviews:
        customer = User.query.get(r.customer_id)
        review_list.append({
            'rating': r.rating,
            'comment': r.comment,
            'customer_name': customer.name if customer else 'N/A',
            'date': r.created_at.strftime('%Y-%m-%d')
        })
    plumber_notification = session.pop('plumber_notification', None)
    return render_template('plumber_dashboard.html', bookings=booking_list, reviews=review_list, free_time_slots=plumber_profile.free_time_slots or '', plumber_notification=plumber_notification)

@app.route('/admin_dashboard', methods=['GET'])
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    users = User.query.all()
    plumbers = PlumberProfile.query.all()
    bookings = Booking.query.order_by(Booking.date.desc()).all()
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    # Prepare data for template
    booking_list = []
    bookings_per_month = defaultdict(int)
    plumber_counter = Counter()
    for b in bookings:
        customer = User.query.get(b.customer_id)
        plumber = PlumberProfile.query.get(b.plumber_id)
        booking_list.append({
            'id': b.id,
            'customer_name': customer.name if customer else 'N/A',
            'plumber_name': plumber.user.name if plumber and plumber.user else 'N/A',
            'date': b.date.strftime('%Y-%m-%d'),
            'time_slot': b.time_slot,
            'status': b.status,
            'service_type': b.service_type
        })
        # Analytics: Bookings per month
        month = b.date.strftime('%Y-%m')
        bookings_per_month[month] += 1
        # Analytics: Top plumbers by completed bookings
        if b.status == 'completed' and plumber and plumber.user:
            plumber_counter[plumber.user.name] += 1
    # Top 5 plumbers
    top_plumbers = [{'name': name, 'count': count} for name, count in plumber_counter.most_common(5)]
    review_list = []
    for r in reviews:
        customer = User.query.get(r.customer_id)
        plumber = PlumberProfile.query.get(r.plumber_id)
        review_list.append({
            'id': r.id,
            'booking_id': r.booking_id,
            'customer_name': customer.name if customer else 'N/A',
            'plumber_name': plumber.user.name if plumber and plumber.user else 'N/A',
            'rating': r.rating,
            'comment': r.comment
        })
    admin_notification = session.pop('admin_notification', None)
    return render_template('admin_dashboard.html', users=users, plumbers=plumbers, bookings=booking_list, reviews=review_list, bookings_per_month=dict(bookings_per_month), top_plumbers=top_plumbers, admin_notification=admin_notification)

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash('Cannot delete admin user.', 'danger')
        return redirect(url_for('admin_dashboard'))
    db.session.delete(user)
    db.session.commit()
    flash('User deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_booking/<int:booking_id>', methods=['POST'])
@login_required
def delete_booking(booking_id):
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    booking = Booking.query.get_or_404(booking_id)
    db.session.delete(booking)
    db.session.commit()
    flash('Booking deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_review/<int:review_id>', methods=['POST'])
@login_required
def delete_review(review_id):
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()
    flash('Review deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/book_plumber', methods=['GET', 'POST'])
@login_required
def book_plumber():
    if current_user.role != 'customer':
        return redirect(url_for('login'))
    if request.method == 'POST':
        plumber_id = int(request.form['plumber_id'])
        date = request.form['date']
        time_slot = request.form['time_slot']
        work_type = request.form['work_type']
        language = request.form['language']
        client_lat = float(request.form['client_lat'])
        client_lon = float(request.form['client_lon'])
        plumber = PlumberProfile.query.get(plumber_id)
        # Double-check plumber is available (atomic)
        already_booked = Booking.query.filter_by(plumber_id=plumber_id, date=date, time_slot=time_slot).with_for_update().first()
        if already_booked:
            flash('Plumber is no longer available for this slot.', 'danger')
            return redirect(url_for('book_plumber'))
        booking = Booking(
            customer_id=current_user.id,
            plumber_id=plumber_id,
            date=datetime.strptime(date, '%Y-%m-%d').date(),
            time_slot=time_slot,
            status='pending',
            service_type=work_type,
            client_lat=client_lat,
            client_lon=client_lon,
            plumber_lat=plumber.lat,
            plumber_lon=plumber.lon
        )
        db.session.add(booking)
        db.session.commit()
        session['plumber_notification'] = f'New booking from {current_user.name} for {date} ({time_slot})!'
        session['admin_notification'] = f'New booking: {current_user.name} scheduled {plumber.user.name} for {date} ({time_slot})!'
        flash('Booking created! Await plumber confirmation.', 'success')
        return redirect(url_for('customer_dashboard'))
    # GET: just render the booking page
    work_types = sorted(set(p.specialization for p in PlumberProfile.query.all() if p.specialization))
    time_slots = sorted(set(slot.strip() for p in PlumberProfile.query.all() for slot in (p.free_time_slots or '').split(',') if slot.strip()))
    languages = sorted(set(lang.strip() for p in PlumberProfile.query.all() for lang in (p.languages or '').split(',') if lang.strip()))
    return render_template('book_plumber.html', work_types=work_types, time_slots=time_slots, languages=languages, plumbers=None, form_data=None)

@app.route('/cancel_booking/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.customer_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('customer_dashboard'))
    if booking.status not in ['pending', 'confirmed']:
        flash('Cannot cancel this booking.', 'warning')
        return redirect(url_for('customer_dashboard'))
    booking.status = 'cancelled'
    db.session.commit()
    flash('Booking cancelled.', 'success')
    return redirect(url_for('customer_dashboard'))

@app.route('/review_booking/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def review_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.customer_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('customer_dashboard'))
    if booking.status != 'completed':
        flash('You can only review completed bookings.', 'warning')
        return redirect(url_for('customer_dashboard'))
    if Review.query.filter_by(booking_id=booking_id).first():
        flash('You have already reviewed this booking.', 'info')
        return redirect(url_for('customer_dashboard'))
    if request.method == 'POST':
        rating = int(request.form['rating'])
        comment = request.form['comment']
        review = Review(
            booking_id=booking_id,
            customer_id=current_user.id,
            plumber_id=booking.plumber_id,
            rating=rating,
            comment=comment
        )
        db.session.add(review)
        db.session.commit()
        flash('Review submitted. Thank you!', 'success')
        return redirect(url_for('customer_dashboard'))
    # Simple inline review form
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Review Booking</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
    <div class="container mt-5">
        <h2>Review Plumber</h2>
        <form method="POST">
            <div class="mb-3">
                <label for="rating" class="form-label">Rating (1-5)</label>
                <input type="number" class="form-control" id="rating" name="rating" min="1" max="5" required>
            </div>
            <div class="mb-3">
                <label for="comment" class="form-label">Comment</label>
                <textarea class="form-control" id="comment" name="comment" rows="3"></textarea>
            </div>
            <button type="submit" class="btn btn-success">Submit Review</button>
            <a href="/customer_dashboard" class="btn btn-link">Back</a>
        </form>
    </div>
    </body>
    </html>
    ''')

@app.route('/accept_booking/<int:booking_id>', methods=['POST'])
@login_required
def accept_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    plumber_profile = PlumberProfile.query.filter_by(user_id=current_user.id).first()
    if booking.plumber_id != plumber_profile.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('plumber_dashboard'))
    if booking.status != 'pending':
        flash('Cannot accept this booking.', 'warning')
        return redirect(url_for('plumber_dashboard'))
    booking.status = 'confirmed'
    db.session.commit()
    flash('Booking accepted.', 'success')
    return redirect(url_for('plumber_dashboard'))

@app.route('/reject_booking/<int:booking_id>', methods=['POST'])
@login_required
def reject_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    plumber_profile = PlumberProfile.query.filter_by(user_id=current_user.id).first()
    if booking.plumber_id != plumber_profile.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('plumber_dashboard'))
    if booking.status != 'pending':
        flash('Cannot reject this booking.', 'warning')
        return redirect(url_for('plumber_dashboard'))
    booking.status = 'cancelled'
    db.session.commit()
    flash('Booking rejected.', 'info')
    return redirect(url_for('plumber_dashboard'))

@app.route('/complete_booking/<int:booking_id>', methods=['POST'])
@login_required
def complete_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    plumber_profile = PlumberProfile.query.filter_by(user_id=current_user.id).first()
    if booking.plumber_id != plumber_profile.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('plumber_dashboard'))
    if booking.status != 'confirmed':
        flash('Cannot complete this booking.', 'warning')
        return redirect(url_for('plumber_dashboard'))
    booking.status = 'completed'
    db.session.commit()
    flash('Booking marked as completed.', 'success')
    return redirect(url_for('plumber_dashboard'))

@app.route('/update_availability', methods=['POST'])
@login_required
def update_availability():
    if current_user.role != 'plumber':
        return redirect(url_for('login'))
    plumber_profile = PlumberProfile.query.filter_by(user_id=current_user.id).first()
    if not plumber_profile:
        flash('No plumber profile found.', 'danger')
        return redirect(url_for('logout'))
    free_time_slots = request.form['free_time_slots']
    plumber_profile.free_time_slots = free_time_slots
    db.session.commit()
    flash('Availability updated.', 'success')
    return redirect(url_for('plumber_dashboard'))

def create_sample_plumbers():
    sample_data = [
        {"name": "Ramesh Patel", "email": "ramesh1@example.com", "password": "plumber1", "district": "Ahmedabad", "specialization": "Leak Repair", "languages": "Gujarati, Hindi", "free_time_slots": "9am-12pm, 2pm-5pm", "lat": 23.0225, "lon": 72.5714},
        {"name": "Suresh Shah", "email": "suresh2@example.com", "password": "plumber2", "district": "Surat", "specialization": "Installation", "languages": "Gujarati, English", "free_time_slots": "10am-1pm, 4pm-7pm", "lat": 21.1702, "lon": 72.8311},
        {"name": "Mahesh Mehta", "email": "mahesh3@example.com", "password": "plumber3", "district": "Vadodara", "specialization": "Maintenance", "languages": "Gujarati, Hindi", "free_time_slots": "8am-11am, 3pm-6pm", "lat": 22.3072, "lon": 73.1812},
        {"name": "Jignesh Desai", "email": "jignesh4@example.com", "password": "plumber4", "district": "Rajkot", "specialization": "Inspection", "languages": "Gujarati, English", "free_time_slots": "9am-12pm, 1pm-4pm", "lat": 22.3039, "lon": 70.8022},
        {"name": "Paresh Joshi", "email": "paresh5@example.com", "password": "plumber5", "district": "Bhavnagar", "specialization": "Leak Repair", "languages": "Gujarati, Hindi", "free_time_slots": "10am-1pm, 5pm-8pm", "lat": 21.7645, "lon": 72.1519},
        {"name": "Nilesh Trivedi", "email": "nilesh6@example.com", "password": "plumber6", "district": "Jamnagar", "specialization": "Installation", "languages": "Gujarati, Hindi", "free_time_slots": "8am-11am, 2pm-5pm", "lat": 22.4707, "lon": 70.0577},
        {"name": "Dipak Pandya", "email": "dipak7@example.com", "password": "plumber7", "district": "Gandhinagar", "specialization": "Maintenance", "languages": "Gujarati, English", "free_time_slots": "9am-12pm, 3pm-6pm", "lat": 23.2156, "lon": 72.6369},
        {"name": "Kiran Solanki", "email": "kiran8@example.com", "password": "plumber8", "district": "Junagadh", "specialization": "Inspection", "languages": "Gujarati, Hindi", "free_time_slots": "10am-1pm, 4pm-7pm", "lat": 21.5222, "lon": 70.4579},
        {"name": "Vikas Parmar", "email": "vikas9@example.com", "password": "plumber9", "district": "Anand", "specialization": "Leak Repair", "languages": "Gujarati, Hindi", "free_time_slots": "8am-11am, 1pm-4pm", "lat": 22.5645, "lon": 72.9289},
        {"name": "Manish Chauhan", "email": "manish10@example.com", "password": "plumber10", "district": "Navsari", "specialization": "Installation", "languages": "Gujarati, English", "free_time_slots": "9am-12pm, 2pm-5pm", "lat": 20.9467, "lon": 72.9520},
        {"name": "Harshad Rana", "email": "harshad11@example.com", "password": "plumber11", "district": "Bharuch", "specialization": "Maintenance", "languages": "Gujarati, Hindi", "free_time_slots": "10am-1pm, 5pm-8pm", "lat": 21.7051, "lon": 72.9959},
        {"name": "Sanjay Bhatt", "email": "sanjay12@example.com", "password": "plumber12", "district": "Mehsana", "specialization": "Inspection", "languages": "Gujarati, English", "free_time_slots": "8am-11am, 3pm-6pm", "lat": 23.5879, "lon": 72.3693},
        {"name": "Ravi Gohil", "email": "ravi13@example.com", "password": "plumber13", "district": "Patan", "specialization": "Leak Repair", "languages": "Gujarati, Hindi", "free_time_slots": "9am-12pm, 1pm-4pm", "lat": 23.8506, "lon": 72.1261},
        {"name": "Ajay Dave", "email": "ajay14@example.com", "password": "plumber14", "district": "Porbandar", "specialization": "Installation", "languages": "Gujarati, Hindi", "free_time_slots": "10am-1pm, 4pm-7pm", "lat": 21.6417, "lon": 69.6293}
    ]
    for p in sample_data:
        if not User.query.filter_by(email=p["email"]).first():
            user = User(
                name=p["name"],
                email=p["email"],
                password_hash=generate_password_hash(p["password"]),
                role="plumber"
            )
            db.session.add(user)
            db.session.commit()
            plumber_profile = PlumberProfile(
                user_id=user.id,
                district=p["district"],
                specialization=p["specialization"],
                languages=p["languages"],
                free_time_slots=p["free_time_slots"],
                lat=p["lat"],
                lon=p["lon"]
            )
            db.session.add(plumber_profile)
    db.session.commit()

# Flask CLI command to populate sample plumbers
@app.cli.command("create-sample-plumbers")
def create_sample_plumbers_command():
    """Populate the database with 10-15 sample plumbers."""
    with app.app_context():
        create_sample_plumbers()
    print("Sample plumbers created.")

@app.route('/calendar')
@login_required
def calendar_view():
    # Render the calendar page for the current user
    return render_template('calendar.html', user_role=current_user.role)

@app.route('/api/calendar_events')
@login_required
def calendar_events():
    events = []
    if current_user.role == 'customer':
        bookings = Booking.query.filter_by(customer_id=current_user.id).all()
        for b in bookings:
            plumber = PlumberProfile.query.get(b.plumber_id)
            events.append({
                'title': f"{b.service_type} with {plumber.user.name if plumber and plumber.user else 'Plumber'}",
                'start': b.date.strftime('%Y-%m-%d'),
                'allDay': True,
                'status': b.status,
                'time_slot': b.time_slot,
                'plumber': plumber.user.name if plumber and plumber.user else 'N/A',
            })
    elif current_user.role == 'plumber':
        plumber_profile = PlumberProfile.query.filter_by(user_id=current_user.id).first()
        if plumber_profile:
            bookings = Booking.query.filter_by(plumber_id=plumber_profile.id).all()
            for b in bookings:
                customer = User.query.get(b.customer_id)
                events.append({
                    'title': f"{b.service_type} for {customer.name if customer else 'Customer'}",
                    'start': b.date.strftime('%Y-%m-%d'),
                    'allDay': True,
                    'status': b.status,
                    'time_slot': b.time_slot,
                    'customer': customer.name if customer else 'N/A',
                })
    return jsonify(events)

@app.route('/all_emails')
def all_emails():
    users = User.query.all()
    emails = [user.email for user in users]
    return jsonify(emails)

# Attribute System Management Routes
@app.route('/admin/get_attributes', methods=['GET'])
@login_required
def get_attributes():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        from attribute_system import DynamicAttributeSystem
        attr_system = DynamicAttributeSystem()
        
        # Load dataset if not already loaded
        try:
            # Try to load enhanced dataset first
            attr_system.load_dataset('enhanced_plumbers_dataset.csv')
        except FileNotFoundError:
            try:
                # Fallback to original dataset
                attr_system.load_dataset('gujarat_plumbers_dataset.csv')
            except FileNotFoundError:
                # If no dataset is available, still return attributes (they exist in the system)
                pass
        
        attributes = attr_system.get_available_attributes()
        
        # Convert to JSON-serializable format
        attr_list = []
        for name, attr_def in attributes.items():
            attr_data = {
                'name': attr_def.name,
                'category': attr_def.category.value,
                'type': attr_def.type.value,
                'weight': attr_def.weight,
                'description': attr_def.description,
                'possible_values': attr_def.possible_values,
                'min_value': attr_def.min_value,
                'max_value': attr_def.max_value,
                'unit': attr_def.unit
            }
            attr_list.append(attr_data)
        
        return jsonify({'attributes': attr_list})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/get_attribute/<attr_name>', methods=['GET'])
@login_required
def get_attribute(attr_name):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        from attribute_system import DynamicAttributeSystem
        attr_system = DynamicAttributeSystem()
        
        # Load dataset if not already loaded
        try:
            # Try to load enhanced dataset first
            attr_system.load_dataset('enhanced_plumbers_dataset.csv')
        except FileNotFoundError:
            try:
                # Fallback to original dataset
                attr_system.load_dataset('gujarat_plumbers_dataset.csv')
            except FileNotFoundError:
                # If no dataset is available, still return attributes (they exist in the system)
                pass
        
        attributes = attr_system.get_available_attributes()
        
        if attr_name not in attributes:
            return jsonify({'error': 'Attribute not found'}), 404
        
        attr_def = attributes[attr_name]
        attr_data = {
            'name': attr_def.name,
            'category': attr_def.category.value,
            'type': attr_def.type.value,
            'weight': attr_def.weight,
            'description': attr_def.description,
            'possible_values': attr_def.possible_values,
            'min_value': attr_def.min_value,
            'max_value': attr_def.max_value,
            'unit': attr_def.unit
        }
        
        return jsonify(attr_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/add_attribute', methods=['POST'])
@login_required
def add_attribute():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        attr_system = DynamicAttributeSystem()
        
        # Get form data
        name = request.form.get('name').strip()
        category = request.form.get('category')
        attr_type = request.form.get('type')
        weight = float(request.form.get('weight'))
        description = request.form.get('description').strip()
        possible_values_str = request.form.get('possible_values', '').strip()
        min_value_str = request.form.get('min_value', '').strip()
        max_value_str = request.form.get('max_value', '').strip()
        unit = request.form.get('unit', '').strip()
        
        # Validate required fields
        if not name or not description:
            return jsonify({'error': 'Name and description are required'}), 400
        
        # Parse possible values
        possible_values = None
        if possible_values_str:
            possible_values = [v.strip() for v in possible_values_str.split(',') if v.strip()]
        
        # Parse numeric values
        min_value = None
        max_value = None
        if min_value_str:
            try:
                min_value = float(min_value_str)
            except ValueError:
                return jsonify({'error': 'Invalid min value'}), 400
        
        if max_value_str:
            try:
                max_value = float(max_value_str)
            except ValueError:
                return jsonify({'error': 'Invalid max value'}), 400
        
        # Validate weight range
        if weight < 0 or weight > 2:
            return jsonify({'error': 'Weight must be between 0 and 2'}), 400
        
        # Create attribute definition
        attr_def = AttributeDefinition(
            name=name,
            category=AttributeCategory(category),
            type=AttributeType(attr_type),
            weight=weight,
            description=description,
            possible_values=possible_values,
            min_value=min_value,
            max_value=max_value,
            unit=unit if unit else None
        )
        
        # Add to attribute system
        attr_system.attributes[name] = attr_def
        
        # Save to persistent storage (you might want to implement this)
        # For now, we'll just return success
        session['admin_notification'] = f'Attribute "{name}" added successfully!'
        
        return jsonify({'success': True, 'message': f'Attribute "{name}" added successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/update_attribute', methods=['POST'])
@login_required
def update_attribute():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        attr_system = DynamicAttributeSystem()
        
        # Get form data
        name = request.form.get('name').strip()
        category = request.form.get('category')
        attr_type = request.form.get('type')
        weight = float(request.form.get('weight'))
        description = request.form.get('description').strip()
        possible_values_str = request.form.get('possible_values', '').strip()
        min_value_str = request.form.get('min_value', '').strip()
        max_value_str = request.form.get('max_value', '').strip()
        unit = request.form.get('unit', '').strip()
        
        # Validate required fields
        if not name or not description:
            return jsonify({'error': 'Name and description are required'}), 400
        
        # Parse possible values
        possible_values = None
        if possible_values_str:
            possible_values = [v.strip() for v in possible_values_str.split(',') if v.strip()]
        
        # Parse numeric values
        min_value = None
        max_value = None
        if min_value_str:
            try:
                min_value = float(min_value_str)
            except ValueError:
                return jsonify({'error': 'Invalid min value'}), 400
        
        if max_value_str:
            try:
                max_value = float(max_value_str)
            except ValueError:
                return jsonify({'error': 'Invalid max value'}), 400
        
        # Validate weight range
        if weight < 0 or weight > 2:
            return jsonify({'error': 'Weight must be between 0 and 2'}), 400
        
        # Update attribute definition
        if name not in attr_system.attributes:
            return jsonify({'error': 'Attribute not found'}), 404
        
        attr_def = AttributeDefinition(
            name=name,
            category=AttributeCategory(category),
            type=AttributeType(attr_type),
            weight=weight,
            description=description,
            possible_values=possible_values,
            min_value=min_value,
            max_value=max_value,
            unit=unit if unit else None
        )
        
        attr_system.attributes[name] = attr_def
        
        session['admin_notification'] = f'Attribute "{name}" updated successfully!'
        
        return jsonify({'success': True, 'message': f'Attribute "{name}" updated successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/delete_attribute', methods=['POST'])
@login_required
def delete_attribute():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        attr_system = DynamicAttributeSystem()
        
        data = request.get_json()
        name = data.get('name')
        
        if not name:
            return jsonify({'error': 'Attribute name is required'}), 400
        
        if name not in attr_system.attributes:
            return jsonify({'error': 'Attribute not found'}), 404
        
        # Check if it's a core attribute that shouldn't be deleted
        core_attributes = ['work_type', 'district', 'language']  # Add more as needed
        if name in core_attributes:
            return jsonify({'error': f'Cannot delete core attribute "{name}"'}), 400
        
        # Remove the attribute
        del attr_system.attributes[name]
        
        session['admin_notification'] = f'Attribute "{name}" deleted successfully!'
        
        return jsonify({'success': True, 'message': f'Attribute "{name}" deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/attribute_stats', methods=['GET'])
@login_required
def attribute_stats():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        from attribute_system import DynamicAttributeSystem
        attr_system = DynamicAttributeSystem()
        
        # Load dataset if not already loaded
        try:
            # Try to load enhanced dataset first
            attr_system.load_dataset('enhanced_plumbers_dataset.csv')
        except FileNotFoundError:
            try:
                # Fallback to original dataset
                attr_system.load_dataset('gujarat_plumbers_dataset.csv')
            except FileNotFoundError:
                # If no dataset is available, still return attributes (they exist in the system)
                pass
        
        attributes = attr_system.get_available_attributes()
        
        # Calculate statistics
        stats = {
            'total_attributes': len(attributes),
            'by_category': {},
            'by_type': {},
            'weight_distribution': {
                'low': 0,    # 0-0.5
                'medium': 0, # 0.5-1.0
                'high': 0    # 1.0-2.0
            }
        }
        
        for attr_def in attributes.values():
            # Category stats
            category = attr_def.category.value
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
            
            # Type stats
            attr_type = attr_def.type.value
            stats['by_type'][attr_type] = stats['by_type'].get(attr_type, 0) + 1
            
            # Weight distribution
            if attr_def.weight <= 0.5:
                stats['weight_distribution']['low'] += 1
            elif attr_def.weight <= 1.0:
                stats['weight_distribution']['medium'] += 1
            else:
                stats['weight_distribution']['high'] += 1
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/import_attributes', methods=['POST'])
@login_required
def import_attributes():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        data = request.get_json()
        
        if not data or 'attributes' not in data:
            return jsonify({'error': 'Invalid configuration format'}), 400
        
        from attribute_system import DynamicAttributeSystem, AttributeDefinition, AttributeCategory, AttributeType
        
        attr_system = DynamicAttributeSystem()
        
        # Clear existing attributes (except core ones)
        core_attributes = ['work_type', 'district', 'language']
        attributes_to_remove = [name for name in attr_system.attributes.keys() if name not in core_attributes]
        for name in attributes_to_remove:
            del attr_system.attributes[name]
        
        # Import new attributes
        imported_count = 0
        for attr_data in data['attributes']:
            try:
                # Skip core attributes to avoid conflicts
                if attr_data['name'] in core_attributes:
                    continue
                
                attr_def = AttributeDefinition(
                    name=attr_data['name'],
                    category=AttributeCategory(attr_data['category']),
                    type=AttributeType(attr_data['type']),
                    weight=float(attr_data['weight']),
                    description=attr_data['description'],
                    possible_values=attr_data.get('possible_values'),
                    min_value=attr_data.get('min_value'),
                    max_value=attr_data.get('max_value'),
                    unit=attr_data.get('unit')
                )
                
                attr_system.attributes[attr_data['name']] = attr_def
                imported_count += 1
                
            except Exception as e:
                print(f"Error importing attribute {attr_data.get('name', 'unknown')}: {str(e)}")
                continue
        
        session['admin_notification'] = f'Successfully imported {imported_count} attributes!'
        
        return jsonify({
            'success': True, 
            'message': f'Successfully imported {imported_count} attributes',
            'imported_count': imported_count
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/reset_attributes', methods=['POST'])
@login_required
def reset_attributes():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        from attribute_system import DynamicAttributeSystem
        
        # Create a fresh attribute system instance
        attr_system = DynamicAttributeSystem()
        
        # The _initialize_attributes method will restore default configuration
        attr_system.attributes = attr_system._initialize_attributes()
        
        session['admin_notification'] = 'Attribute system reset to default configuration!'
        
        return jsonify({
            'success': True, 
            'message': 'Attribute system reset to default configuration',
            'total_attributes': len(attr_system.attributes)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/test_attribute_system', methods=['POST'])
@login_required
def test_attribute_system():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        from attribute_system import DynamicAttributeSystem
        
        # Get test parameters
        customer_preferences = {}
        
        # Basic preferences
        if request.form.get('work_type'):
            customer_preferences['work_type'] = request.form.get('work_type')
        if request.form.get('district'):
            customer_preferences['district'] = request.form.get('district')
        if request.form.get('language'):
            customer_preferences['language'] = request.form.get('language')
        
        # Numeric preferences
        if request.form.get('experience_years'):
            customer_preferences['experience_years'] = int(request.form.get('experience_years'))
        if request.form.get('max_cost'):
            customer_preferences['max_cost'] = int(request.form.get('max_cost'))
        
        # Location
        if request.form.get('client_lat') and request.form.get('client_lon'):
            customer_preferences['client_lat'] = float(request.form.get('client_lat'))
            customer_preferences['client_lon'] = float(request.form.get('client_lon'))
        
        # Test the attribute system
        attr_system = DynamicAttributeSystem()
        
        # Load dataset if not already loaded
        try:
            # Try to load enhanced dataset first
            attr_system.load_dataset('enhanced_plumbers_dataset.csv')
        except FileNotFoundError:
            try:
                # Fallback to original dataset
                attr_system.load_dataset('gujarat_plumbers_dataset.csv')
            except FileNotFoundError:
                return jsonify({'error': 'No plumber dataset found. Please ensure either enhanced_plumbers_dataset.csv or gujarat_plumbers_dataset.csv is available.'}), 400
        
        matched_plumbers = attr_system.match_plumbers(customer_preferences, max_results=10)
        
        # Generate test report
        report = attr_system.generate_matching_report(customer_preferences, matched_plumbers)
        
        # Format results for display
        results_html = f"""
        <div class="mb-3">
            <h6 class="text-primary">Test Parameters:</h6>
            <ul class="list-unstyled">
                {''.join([f'<li><strong>{k}:</strong> {v}</li>' for k, v in customer_preferences.items()])}
            </ul>
        </div>
        
        <div class="mb-3">
            <h6 class="text-success">Matching Results:</h6>
            <p><strong>Total Plumbers Found:</strong> {len(matched_plumbers)}</p>
            <p><strong>Average Match Score:</strong> {report.get('average_score', 0):.2f}</p>
            <p><strong>Best Match Score:</strong> {report.get('best_score', 0):.2f}</p>
        </div>
        
        <div class="mb-3">
            <h6 class="text-info">Top 5 Matches:</h6>
            <div class="table-responsive">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Name</th>
                            <th>Score</th>
                            <th>District</th>
                            <th>Specialization</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for i, plumber in enumerate(matched_plumbers[:5], 1):
            results_html += f"""
                        <tr>
                            <td>{i}</td>
                            <td>{plumber.get('Name', 'N/A')}</td>
                            <td><span class="badge bg-success">{plumber.get('match_score', 0):.2f}</span></td>
                            <td>{plumber.get('District', 'N/A')}</td>
                            <td>{plumber.get('Work_Specialization', 'N/A')}</td>
                        </tr>
            """
        
        results_html += """
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="mb-3">
            <h6 class="text-warning">Attribute Analysis:</h6>
            <ul class="list-unstyled">
        """
        
        for attr_name, score_info in report.get('attribute_scores', {}).items():
            results_html += f'<li><strong>{attr_name}:</strong> {score_info.get("average_score", 0):.2f}</li>'
        
        results_html += """
            </ul>
        </div>
        """
        
        return jsonify({
            'success': True,
            'results': results_html,
            'total_matches': len(matched_plumbers),
            'average_score': report.get('average_score', 0)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False) 