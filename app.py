from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, render_template_string, session
import pandas as pd
from flask_cors import CORS
import math
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, PlumberProfile, Booking, Review
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import and_, or_
from collections import defaultdict, Counter

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

# Create tables if not exist
with app.app_context():
    db.create_all()

df = pd.read_csv('gujarat_plumbers_dataset.csv')

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

@app.route('/')
def index():
    return redirect(url_for('login'))

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
        booking_list.append({
            'id': b.id,
            'plumber_name': plumber.user.name if plumber and plumber.user else 'N/A',
            'date': b.date.strftime('%Y-%m-%d'),
            'time_slot': b.time_slot,
            'status': b.status,
            'service_type': b.service_type,
            'reviewed': bool(review)
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

@app.route('/api/available_plumbers', methods=['POST'])
def api_available_plumbers():
    data = request.get_json()
    date = data.get('date')
    time_slot = data.get('time_slot')
    work_type = data.get('work_type')
    language = data.get('language')
    client_lat = data.get('client_lat')
    client_lon = data.get('client_lon')
    if not all([date, time_slot, work_type, client_lat, client_lon]):
        return jsonify({'error': 'Missing required fields.'}), 400
    work_type_norm = work_type.strip().lower()
    time_slot_norm = time_slot.strip().lower()
    language_norm = language.strip().lower() if language else None
    matching_plumbers = []
    for p in PlumberProfile.query.all():
        # Specialization match
        if not p.specialization or p.specialization.strip().lower() != work_type_norm:
            continue
        # Time slot match
        slots = [s.strip().lower() for s in (p.free_time_slots or '').split(',')]
        if not p.free_time_slots or time_slot_norm not in slots:
            continue
        # Language match (if not Any)
        if language and language != 'Any':
            langs = [l.strip().lower() for l in (p.languages or '').split(',')]
            if language_norm not in langs:
                continue
        # Already booked?
        if Booking.query.filter_by(plumber_id=p.id, date=date, time_slot=time_slot).first():
            continue
        # Distance/ETA
        if p.lat is not None and p.lon is not None:
            dist = haversine(float(client_lat), float(client_lon), p.lat, p.lon)
            eta = int(round(dist / 40 * 60))
        else:
            dist = None
            eta = None
        # Rating (average)
        reviews = Review.query.filter_by(plumber_id=p.id).all()
        avg_rating = round(sum(r.rating for r in reviews)/len(reviews), 1) if reviews else None
        matching_plumbers.append({
            'id': p.id,
            'name': p.user.name if p.user else 'N/A',
            'specialization': p.specialization,
            'languages': p.languages,
            'eta': eta if eta is not None else 'N/A',
            'distance': round(dist, 2) if dist is not None else 'N/A',
            'rating': avg_rating
        })
    matching_plumbers = sorted(matching_plumbers, key=lambda x: (x['eta'] if x['eta'] != 'N/A' else 9999))
    return jsonify({'plumbers': matching_plumbers})

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

if __name__ == '__main__':
    app.run(debug=True) 