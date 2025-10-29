import os
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel_booking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    user_type = db.Column(db.String(20), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Hotel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    owner_name = db.Column(db.String(100))
    owner_email = db.Column(db.String(100))
    contact_number = db.Column(db.String(20))
    whatsapp_number = db.Column(db.String(20))
    price_per_night = db.Column(db.Float, nullable=False)
    total_rooms = db.Column(db.Integer, nullable=False)
    available_rooms = db.Column(db.Integer, nullable=False)
    amenities = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=True)

class HotelImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)
    room_number = db.Column(db.String(10), nullable=False)
    room_type = db.Column(db.String(50))
    capacity = db.Column(db.Integer, nullable=False)
    price_per_night = db.Column(db.Float, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    features = db.Column(db.Text)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=True)
    guest_name = db.Column(db.String(100), nullable=False)
    guest_email = db.Column(db.String(100))
    guest_phone = db.Column(db.String(20))
    guest_whatsapp = db.Column(db.String(20))
    check_in_date = db.Column(db.String(50), nullable=False)
    check_out_date = db.Column(db.String(50), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='confirmed')
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    number_of_guests = db.Column(db.Integer, default=1)
    special_requests = db.Column(db.Text)

class BookingCalendar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=True)
    date = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='available')
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# WhatsApp Service
class WhatsAppService:
    def send_booking_notification_to_owner(self, hotel, booking, customer):
        print(f"📱 WhatsApp to {hotel.whatsapp_number}: New Booking #{booking.id}")
        return {'success': True}
    
    def send_booking_confirmation_to_customer(self, hotel, booking):
        print(f"📱 WhatsApp to {booking.guest_whatsapp}: Booking Confirmed #{booking.id}")
        return {'success': True}

whatsapp_service = WhatsAppService()

# Image Service
class ImageService:
    def save_hotel_image(self, file, hotel_id):
        return f"/static/images/hotel_{hotel_id}_{datetime.now().timestamp()}.jpg"
    
    def save_room_image(self, file, room_id):
        return f"/static/images/room_{room_id}_{datetime.now().timestamp()}.jpg"

image_service = ImageService()

# Database initialization
def init_db():
    with app.app_context():
        db.create_all()
        
        # Create super admin
        if not User.query.filter_by(username='superadmin').first():
            super_admin = User(
                username='superadmin',
                email='super@admin.com',
                user_type='super_admin',
                full_name='System Super Administrator',
                phone='0112345678'
            )
            super_admin.set_password('admin123')
            db.session.add(super_admin)
            
            # Create sample hotels
            hotels_data = [
                {
                    'name': 'Colombo City Hotel',
                    'location': 'Colombo 07, Sri Lanka',
                    'description': 'Luxury hotel in the heart of Colombo with modern amenities',
                    'price_per_night': 12000.00,
                    'total_rooms': 50,
                    'amenities': 'WiFi, AC, Pool, Gym, Restaurant, Parking'
                },
                {
                    'name': 'Beachside Resort',
                    'location': 'Negombo, Sri Lanka', 
                    'description': 'Beautiful beachfront resort with ocean views',
                    'price_per_night': 15000.00,
                    'total_rooms': 30,
                    'amenities': 'WiFi, AC, Pool, Beach Access, Spa'
                },
                {
                    'name': 'Mountain View Hotel',
                    'location': 'Kandy, Sri Lanka',
                    'description': 'Serene hotel with mountain views and cool climate',
                    'price_per_night': 8000.00,
                    'total_rooms': 25,
                    'amenities': 'WiFi, AC, Garden, Restaurant'
                }
            ]
            
            for i, hotel_data in enumerate(hotels_data):
                hotel = Hotel(
                    name=hotel_data['name'],
                    location=hotel_data['location'],
                    description=hotel_data['description'],
                    owner_name=f'Owner {i+1}',
                    owner_email=f'owner{i+1}@example.com',
                    contact_number=f'011234567{i+1}',
                    whatsapp_number=f'071234567{i+1}',
                    price_per_night=hotel_data['price_per_night'],
                    total_rooms=hotel_data['total_rooms'],
                    available_rooms=hotel_data['total_rooms'],
                    amenities=hotel_data['amenities'],
                    is_approved=True
                )
                db.session.add(hotel)
            
            db.session.commit()
            print("✅ Database initialized successfully!")
            print("✅ Super admin created!")
            print("✅ Sample hotels added!")

# Utility functions
def get_today():
    return datetime.now().date().isoformat()

# Routes
@app.route('/')
def home():
    """මුල් පිටුව"""
    hotels = Hotel.query.filter_by(is_approved=True).limit(6).all()
    return render_template('index.html', hotels=hotels, today=get_today())

@app.route('/login', methods=['GET', 'POST'])
def login():
    """පිවිසීම"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('සාර්ථකව පිවිසිය!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('පිවිසීම අසාර්ථකයි. කරුණාකර පරිශීලක නාමය සහ මුරපදය පරීක්ෂා කරන්න.', 'danger')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """ලියාපදිංචි වීම"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        user_type = request.form.get('user_type', '').strip()
        
        if User.query.filter_by(username=username).first():
            flash('මෙම පරිශීලක නාමය දැනටමත් භාවිතා කර ඇත.', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('මෙම ඊමේල් ලිපිනය දැනටමත් භාවිතා කර ඇත.', 'danger')
            return redirect(url_for('register'))
        
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            phone=phone,
            user_type=user_type
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('ඔබගේ ගිණුම සාර්ථකව නිර්මාණය කරන ලදී! දැන් ඔබට පිවිසිය හැකිය.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    """පිටවීම"""
    logout_user()
    flash('ඔබ සාර්ථකව පිටවී ඇත.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """උපකරණ පුවරුව"""
    user_type = current_user.user_type
    
    if user_type == 'super_admin':
        total_users = User.query.count()
        total_hotels = Hotel.query.count()
        total_bookings = Booking.query.count()
        return render_template('dashboard/admin_dashboard.html',
                            total_users=total_users,
                            total_hotels=total_hotels,
                            total_bookings=total_bookings)
    
    elif user_type == 'hotel_admin':
        hotel = Hotel.query.filter_by(owner_email=current_user.email).first()
        if hotel:
            hotel_bookings = Booking.query.filter_by(hotel_id=hotel.id).count()
            return render_template('dashboard/hotel_admin_dashboard.html',
                                hotel=hotel,
                                total_bookings=hotel_bookings)
        else:
            return render_template('dashboard/hotel_admin_dashboard.html', hotel=None)
    
    else:
        user_bookings = Booking.query.filter_by(customer_id=current_user.id).count()
        return render_template('dashboard/customer_dashboard.html',
                            total_bookings=user_bookings)

@app.route('/hotels')
def view_hotels():
    """හොටෙල් බැලීම"""
    hotels = Hotel.query.filter_by(is_approved=True).all()
    return render_template('hotels/hotels.html', hotels=hotels)

@app.route('/hotel/<int:hotel_id>')
def hotel_details(hotel_id):
    """හොටෙල් විස්තර"""
    hotel = Hotel.query.get_or_404(hotel_id)
    rooms = Room.query.filter_by(hotel_id=hotel_id, is_available=True).all()
    images = HotelImage.query.filter_by(hotel_id=hotel_id).all()
    return render_template('hotels/hotel_details.html',
                         hotel=hotel,
                         rooms=rooms,
                         images=images,
                         today=get_today())

@app.route('/register_hotel', methods=['GET', 'POST'])
@login_required
def register_hotel():
    """හොටෙල් ලියාපදිංචි කිරීම"""
    if current_user.user_type != 'hotel_admin':
        flash('මෙම ක්‍රියාවට හොටෙල් අයිතිකරු අවසරය අවශ්‍යයි.', 'danger')
        return redirect(url_for('dashboard'))
    
    if Hotel.query.filter_by(owner_email=current_user.email).first():
        flash('ඔබට දැනටමත් හොටෙල් එකක් ලියාපදිංචි කර ඇත.', 'warning')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        description = request.form['description']
        contact_number = request.form['contact_number']
        whatsapp_number = request.form.get('whatsapp_number', contact_number)
        price_per_night = float(request.form['price_per_night'])
        total_rooms = int(request.form['total_rooms'])
        amenities = request.form['amenities']
        
        hotel = Hotel(
            name=name,
            location=location,
            description=description,
            owner_name=current_user.full_name,
            owner_email=current_user.email,
            contact_number=contact_number,
            whatsapp_number=whatsapp_number,
            price_per_night=price_per_night,
            total_rooms=total_rooms,
            available_rooms=total_rooms,
            amenities=amenities,
            is_approved=True
        )
        
        db.session.add(hotel)
        db.session.commit()
        
        flash('ඔබගේ හොටෙල් සාර්ථකව ලියාපදිංචි කරන ලදී!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('hotels/register_hotel.html')

@app.route('/hotel/<int:hotel_id>/add_room', methods=['GET', 'POST'])
@login_required
def add_room(hotel_id):
    """කාමරයක් ඇතුලත් කිරීම"""
    hotel = Hotel.query.get_or_404(hotel_id)
    
    if current_user.user_type == 'hotel_admin' and hotel.owner_email != current_user.email:
        flash('අවසරය නොමැත.', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        room_number = request.form['room_number']
        room_type = request.form['room_type']
        capacity = int(request.form['capacity'])
        price_per_night = float(request.form['price_per_night'])
        features = request.form.get('features', '')
        
        room = Room(
            hotel_id=hotel_id,
            room_number=room_number,
            room_type=room_type,
            capacity=capacity,
            price_per_night=price_per_night,
            features=features
        )
        
        db.session.add(room)
        db.session.commit()
        
        flash('කාමරය සාර්ථකව ඇතුලත් කරන ලදී!', 'success')
        return redirect(url_for('hotel_details', hotel_id=hotel_id))
    
    return render_template('hotels/add_room.html', hotel=hotel)

@app.route('/book_hotel/<int:hotel_id>', methods=['GET', 'POST'])
@login_required
def book_hotel(hotel_id):
    """හොටෙල් බුක් කිරීම"""
    if current_user.user_type != 'customer':
        flash('මෙම ක්‍රියාවට ගනුදෙනුකරු අවසරය අවශ්‍යයි.', 'danger')
        return redirect(url_for('dashboard'))
    
    hotel = Hotel.query.get_or_404(hotel_id)
    
    if request.method == 'POST':
        check_in_date = request.form['check_in_date']
        check_out_date = request.form['check_out_date']
        guest_name = request.form['guest_name']
        guest_phone = request.form['guest_phone']
        guest_whatsapp = request.form.get('guest_whatsapp', guest_phone)
        room_id = request.form.get('room_id', 0)
        number_of_guests = int(request.form.get('number_of_guests', 1))
        special_requests = request.form.get('special_requests', '')
        
        # Calculate nights and price
        check_in = datetime.strptime(check_in_date, '%Y-%m-%d')
        check_out = datetime.strptime(check_out_date, '%Y-%m-%d')
        nights = (check_out - check_in).days
        
        if nights <= 0:
            flash('කරුණාකර වලංගු රැස්වීමේ දින ඇතුලත් කරන්න.', 'danger')
            return redirect(url_for('book_hotel', hotel_id=hotel_id))
        
        # Calculate total price
        if room_id and room_id != '0':
            room = Room.query.get(room_id)
            price_per_night = room.price_per_night
        else:
            price_per_night = hotel.price_per_night
        
        total_price = price_per_night * nights
        
        # Create booking
        booking = Booking(
            hotel_id=hotel.id,
            room_id=room_id if room_id != '0' else None,
            guest_name=guest_name,
            guest_email=current_user.email,
            guest_phone=guest_phone,
            guest_whatsapp=guest_whatsapp,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            total_price=total_price,
            customer_id=current_user.id,
            number_of_guests=number_of_guests,
            special_requests=special_requests
        )
        
        db.session.add(booking)
        
        # Update available rooms
        if hotel.available_rooms > 0:
            hotel.available_rooms -= 1
        
        db.session.commit()
        
        # Send WhatsApp notifications
        whatsapp_service.send_booking_notification_to_owner(hotel, booking, current_user)
        whatsapp_service.send_booking_confirmation_to_customer(hotel, booking)
        
        flash(f'ඔබගේ බුකින්ග් සාර්ථකව සිදු කරන ලදී! බුකින්ග් ID: {booking.id}', 'success')
        return redirect(url_for('my_bookings'))
    
    rooms = Room.query.filter_by(hotel_id=hotel_id, is_available=True).all()
    return render_template('hotels/book_hotel.html',
                         hotel=hotel,
                         rooms=rooms,
                         today=get_today())

@app.route('/my_bookings')
@login_required
def my_bookings():
    """ගනුදෙනුකරුගේ බුකින්ග්"""
    if current_user.user_type != 'customer':
        flash('මෙම ක්‍රියාවට ගනුදෙනුකරු අවසරය අවශ්‍යයි.', 'danger')
        return redirect(url_for('dashboard'))
    
    bookings = Booking.query.filter_by(customer_id=current_user.id).order_by(Booking.booking_date.desc()).all()
    
    bookings_with_hotels = []
    for booking in bookings:
        hotel = Hotel.query.get(booking.hotel_id)
        room = Room.query.get(booking.room_id) if booking.room_id else None
        bookings_with_hotels.append({
            'booking': booking,
            'hotel': hotel,
            'room': room
        })
    
    return render_template('bookings/my_bookings.html', bookings_with_hotels=bookings_with_hotels)

@app.route('/hotel/<int:hotel_id>/calendar')
@login_required
def hotel_calendar(hotel_id):
    """බුකින්ග් කැලන්ඩරය"""
    hotel = Hotel.query.get_or_404(hotel_id)
    
    if current_user.user_type == 'hotel_admin' and hotel.owner_email != current_user.email:
        flash('අවසරය නොමැත.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get calendar events
    events = BookingCalendar.query.filter_by(hotel_id=hotel_id).all()
    rooms = Room.query.filter_by(hotel_id=hotel_id).all()
    
    return render_template('calendar/hotel_calendar.html',
                         hotel=hotel,
                         events=events,
                         rooms=rooms,
                         is_owner=current_user.user_type in ['super_admin', 'hotel_admin'])

# Image Upload Routes
@app.route('/hotel/<int:hotel_id>/upload_images', methods=['POST'])
@login_required
def upload_hotel_images(hotel_id):
    """හොටෙල් රූප ඇතුලත් කිරීම"""
    hotel = Hotel.query.get_or_404(hotel_id)
    
    if current_user.user_type == 'hotel_admin' and hotel.owner_email != current_user.email:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    if 'images' not in request.files:
        return jsonify({'success': False, 'message': 'No images selected'})
    
    files = request.files.getlist('images')
    
    uploaded_images = []
    for file in files:
        if file.filename == '':
            continue
            
        image_url = image_service.save_hotel_image(file, hotel_id)
        if image_url:
            hotel_image = HotelImage(
                hotel_id=hotel_id,
                image_url=image_url
            )
            db.session.add(hotel_image)
            uploaded_images.append(image_url)
    
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': f'{len(uploaded_images)} images uploaded successfully'
    })

# Error Handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

@app.route('/favicon.ico')
def favicon():
    return '', 204

if __name__ == '__main__':
    init_db()
    print("🚀 Hotel Booking System Started!")
    print("📍 Access your application at:")
    print("   → http://127.0.0.1:5000")
    print("   → http://localhost:5000")
    print("📧 Super Admin Login:")
    print("   → Username: superadmin")
    print("   → Password: admin123")
    app.run(debug=True, host='0.0.0.0', port=5000)