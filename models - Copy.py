from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import os

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # super_admin, hotel_admin, customer
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    bookings = db.relationship('Booking', backref='customer', lazy=True)
    calendar_updates = db.relationship('BookingCalendar', backref='updater', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Hotel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    owner_name = db.Column(db.String(100))
    owner_email = db.Column(db.String(100))
    contact_number = db.Column(db.String(20))
    whatsapp_number = db.Column(db.String(20))  # New field for WhatsApp notifications
    price_per_night = db.Column(db.Float, nullable=False)
    total_rooms = db.Column(db.Integer, nullable=False)
    available_rooms = db.Column(db.Integer, nullable=False)
    amenities = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    images = db.relationship('HotelImage', backref='hotel', lazy=True, cascade="all, delete-orphan")
    rooms = db.relationship('Room', backref='hotel', lazy=True, cascade="all, delete-orphan")
    bookings = db.relationship('Booking', backref='hotel', lazy=True)
    calendar_entries = db.relationship('BookingCalendar', backref='hotel', lazy=True)
    
    def __repr__(self):
        return f'<Hotel {self.name}>'

class HotelImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<HotelImage {self.id} for Hotel {self.hotel_id}>'

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)
    room_number = db.Column(db.String(10), nullable=False)
    room_type = db.Column(db.String(50))  # Single, Double, Suite, Deluxe, etc.
    capacity = db.Column(db.Integer, nullable=False)
    price_per_night = db.Column(db.Float, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    features = db.Column(db.Text)  # AC, WiFi, TV, etc.
    description = db.Column(db.Text)
    size = db.Column(db.String(20))  # Room size in sq ft
    bed_type = db.Column(db.String(50))  # King, Queen, Twin, etc.
    
    # Relationships
    images = db.relationship('RoomImage', backref='room', lazy=True, cascade="all, delete-orphan")
    bookings = db.relationship('Booking', backref='room', lazy=True)
    calendar_entries = db.relationship('BookingCalendar', backref='room', lazy=True)
    
    def __repr__(self):
        return f'<Room {self.room_number} in Hotel {self.hotel_id}>'

class RoomImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<RoomImage {self.id} for Room {self.room_id}>'

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    guest_name = db.Column(db.String(100), nullable=False)
    guest_email = db.Column(db.String(100))
    guest_phone = db.Column(db.String(20))
    guest_whatsapp = db.Column(db.String(20))  # Customer WhatsApp for notifications
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='confirmed')  # confirmed, cancelled, completed
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    special_requests = db.Column(db.Text)  # Special requests from customer
    number_of_guests = db.Column(db.Integer, default=1)
    
    # Relationships
    calendar_entries = db.relationship('BookingCalendar', backref='booking', lazy=True)
    
    def __repr__(self):
        return f'<Booking {self.id} for {self.guest_name}>'
    
    def get_nights(self):
        """Calculate number of nights"""
        return (self.check_out_date - self.check_in_date).days
    
    def get_total_amount(self):
        """Calculate total amount"""
        return self.total_price

class BookingCalendar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='available')  # available, booked, blocked, maintenance
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)  # Additional notes for blocked/maintenance dates
    
    def __repr__(self):
        return f'<BookingCalendar {self.date} - {self.status}>'

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50))  # booking, system, update, etc.
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    related_booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='notifications', lazy=True)
    booking = db.relationship('Booking', backref='notifications', lazy=True)
    
    def __repr__(self):
        return f'<Notification {self.title}>'

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    title = db.Column(db.String(200))
    comment = db.Column(db.Text)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    hotel = db.relationship('Hotel', backref='reviews', lazy=True)
    user = db.relationship('User', backref='reviews', lazy=True)
    booking = db.relationship('Booking', backref='review', lazy=True)
    
    def __repr__(self):
        return f'<Review {self.id} for Hotel {self.hotel_id}>'

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50))  # cash, card, online, etc.
    payment_status = db.Column(db.String(20), default='pending')  # pending, completed, failed, refunded
    transaction_id = db.Column(db.String(100))
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    # Relationships
    booking = db.relationship('Booking', backref='payments', lazy=True)
    
    def __repr__(self):
        return f'<Payment {self.id} for Booking {self.booking_id}>'

class SystemSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemSettings {self.setting_key}>'

# Utility functions for the models
def init_default_settings():
    """Initialize default system settings"""
    default_settings = [
        {'key': 'whatsapp_enabled', 'value': 'true', 'description': 'Enable WhatsApp notifications'},
        {'key': 'booking_advance_days', 'value': '365', 'description': 'Maximum days in advance for booking'},
        {'key': 'cancellation_hours', 'value': '24', 'description': 'Hours before check-in for free cancellation'},
        {'key': 'tax_rate', 'value': '10', 'description': 'Tax rate percentage'},
        {'key': 'currency', 'value': 'LKR', 'description': 'Default currency'},
        {'key': 'check_in_time', 'value': '14:00', 'description': 'Default check-in time'},
        {'key': 'check_out_time', 'value': '11:00', 'description': 'Default check-out time'},
    ]
    
    for setting in default_settings:
        existing = SystemSettings.query.filter_by(setting_key=setting['key']).first()
        if not existing:
            new_setting = SystemSettings(
                setting_key=setting['key'],
                setting_value=setting['value'],
                description=setting['description']
            )
            db.session.add(new_setting)
    
    db.session.commit()

def create_super_admin():
    """Create super admin user if not exists"""
    super_admin = User.query.filter_by(user_type='super_admin').first()
    if not super_admin:
        super_admin = User(
            username='superadmin',
            email='super@admin.com',
            user_type='super_admin',
            full_name='System Super Administrator',
            phone='0712345678',
            is_active=True
        )
        super_admin.set_password('admin123')
        db.session.add(super_admin)
        db.session.commit()
        print("✅ Super admin created successfully!")
    return super_admin

def get_hotel_statistics(hotel_id):
    """Get statistics for a specific hotel"""
    hotel = Hotel.query.get(hotel_id)
    if not hotel:
        return None
    
    total_rooms = Room.query.filter_by(hotel_id=hotel_id).count()
    available_rooms = Room.query.filter_by(hotel_id=hotel_id, is_available=True).count()
    total_bookings = Booking.query.filter_by(hotel_id=hotel_id).count()
    active_bookings = Booking.query.filter_by(hotel_id=hotel_id, status='confirmed').count()
    
    # Calculate occupancy rate
    total_room_nights = db.session.query(db.func.sum(Booking.total_price / Room.price_per_night)).\
        join(Room, Booking.room_id == Room.id).\
        filter(Booking.hotel_id == hotel_id, Booking.status == 'confirmed').scalar() or 0
    
    max_room_nights = total_rooms * 30  # Assuming 30 days month
    
    occupancy_rate = (total_room_nights / max_room_nights * 100) if max_room_nights > 0 else 0
    
    return {
        'total_rooms': total_rooms,
        'available_rooms': available_rooms,
        'total_bookings': total_bookings,
        'active_bookings': active_bookings,
        'occupancy_rate': round(occupancy_rate, 2)
    }

def get_user_statistics():
    """Get user statistics for admin dashboard"""
    total_users = User.query.count()
    hotel_admins = User.query.filter_by(user_type='hotel_admin').count()
    customers = User.query.filter_by(user_type='customer').count()
    super_admins = User.query.filter_by(user_type='super_admin').count()
    active_users = User.query.filter_by(is_active=True).count()
    
    return {
        'total_users': total_users,
        'hotel_admins': hotel_admins,
        'customers': customers,
        'super_admins': super_admins,
        'active_users': active_users
    }

def get_booking_calendar_events(hotel_id, start_date, end_date):
    """Get calendar events for a specific hotel and date range"""
    events = BookingCalendar.query.filter(
        BookingCalendar.hotel_id == hotel_id,
        BookingCalendar.date >= start_date,
        BookingCalendar.date <= end_date
    ).all()
    
    calendar_events = []
    for event in events:
        if event.status == 'booked':
            color = '#dc3545'  # Red
            title = f"Booked - Room {event.room.room_number}"
        elif event.status == 'blocked':
            color = '#ffc107'  # Yellow
            title = f"Blocked - Room {event.room.room_number}"
        elif event.status == 'maintenance':
            color = '#6c757d'  # Gray
            title = f"Maintenance - Room {event.room.room_number}"
        else:
            color = '#28a745'  # Green
            title = f"Available - Room {event.room.room_number}"
        
        calendar_events.append({
            'id': event.id,
            'title': title,
            'start': event.date.isoformat(),
            'end': event.date.isoformat(),
            'color': color,
            'extendedProps': {
                'room_id': event.room_id,
                'room_number': event.room.room_number,
                'status': event.status,
                'booking_id': event.booking_id,
                'notes': event.notes
            }
        })
    
    return calendar_events

def update_room_availability(room_id, is_available):
    """Update room availability status"""
    room = Room.query.get(room_id)
    if room:
        room.is_available = is_available
        db.session.commit()
        return True
    return False

def create_booking_calendar_entries(booking):
    """Create calendar entries for a booking"""
    current_date = booking.check_in_date
    while current_date < booking.check_out_date:
        calendar_entry = BookingCalendar(
            hotel_id=booking.hotel_id,
            room_id=booking.room_id,
            date=current_date,
            status='booked',
            booking_id=booking.id,
            updated_by=booking.customer_id
        )
        db.session.add(calendar_entry)
        current_date = current_date + timedelta(days=1)
    
    db.session.commit()

def cancel_booking_calendar_entries(booking_id):
    """Remove or update calendar entries for a cancelled booking"""
    calendar_entries = BookingCalendar.query.filter_by(booking_id=booking_id).all()
    for entry in calendar_entries:
        entry.status = 'available'
        entry.booking_id = None
        entry.updated_at = datetime.utcnow()
    
    db.session.commit()