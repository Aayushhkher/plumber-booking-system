from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # customer, plumber, admin
    plumber_profile = db.relationship('PlumberProfile', backref='user', uselist=False)
    bookings = db.relationship('Booking', backref='customer', foreign_keys='Booking.customer_id')

class PlumberProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    district = db.Column(db.String(100))
    specialization = db.Column(db.String(100))
    languages = db.Column(db.String(200))
    free_time_slots = db.Column(db.String(200))
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    bookings = db.relationship('Booking', backref='plumber_profile', foreign_keys='Booking.plumber_id')

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plumber_id = db.Column(db.Integer, db.ForeignKey('plumber_profile.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time_slot = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, completed, cancelled
    service_type = db.Column(db.String(100))
    client_lat = db.Column(db.Float)
    client_lon = db.Column(db.Float)
    plumber_lat = db.Column(db.Float)
    plumber_lon = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    review = db.relationship('Review', backref='booking', uselist=False)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plumber_id = db.Column(db.Integer, db.ForeignKey('plumber_profile.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow) 