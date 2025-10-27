import os
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date
import urllib.parse
from models import db, User, Hotel, Room, Booking, HotelImage, RoomImage, BookingCalendar, Notification, Review, Payment, SystemSettings
from models import create_super_admin, init_default_settings, get_hotel_statistics, get_user_statistics, get_booking_calendar_events
from whatsapp_service import whatsapp_service
from image_utils import image_utils

# Flask app creation
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database configuration for production
if os.environ.get('DATABASE_URL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel_booking.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Initialize extensions
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Utility functions
def get_today():
    return datetime.now().date()

def format_currency(amount):
    return "රු. {:,.2f}".format(amount)

# Database initialization
def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create super admin
        create_super_admin()
        
        # Initialize default settings
        init_default_settings()
        
        print("✅ Database initialized successfully!")
        print("✅ Default settings created!")
        print("✅ Super admin user created!")

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
        
        if user and user.check_password(password) and user.is_active:
            login_user(user)
            flash('සාර්ථකව පිවිසිය!', 'success')
            
            # Redirect based on user type
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
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
        
        # Validation
        errors = []
        if not all([username, email, password, full_name, phone, user_type]):
            errors.append('කරුණාකර සියලුම ක්ෂේත්ර පුරවන්න.')
        
        if User.query.filter_by(username=username).first():
            errors.append('මෙම පරිශීලක නාමය දැනටමත් භාවිතා කර ඇත.')
        
        if User.query.filter_by(email=email).first():
            errors.append('මෙම ඊමේල් ලිපිනය දැනටමත් භාවිතා කර ඇත.')
        
        if len(password) < 6:
            errors.append('මුරපදය අවම වශයෙන් අකුරු 6ක් විය යුතුය.')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html')
        
        # Create user
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            phone=phone,
            user_type=user_type
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('ඔබගේ ගිණුම සාර්ථකව නිර්මාණය කරන ලදී! දැන් ඔබට පිවිසිය හැකිය.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('ලියාපදිංචි වීමේ දෝෂයක්. කරුණාකර පසුව උත්සාහ කරන්න.', 'danger')
    
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
        stats = get_user_statistics()
        total_hotels = Hotel.query.count()
        approved_hotels = Hotel.query.filter_by(is_approved=True).count()
        pending_hotels = Hotel.query.filter_by(is_approved=False).count()
        total_bookings = Booking.query.count()
        
        return render_template('dashboard/admin_dashboard.html',
                            stats=stats,
                            total_hotels=total_hotels,
                            approved_hotels=approved_hotels,
                            pending_hotels=pending_hotels,
                            total_bookings=total_bookings)
    
    elif user_type == 'hotel_admin':
        hotel = Hotel.query.filter_by(owner_email=current_user.email).first()
        
        if not hotel:
            return render_template('dashboard/hotel_admin_dashboard.html', hotel=None)
        
        stats = get_hotel_statistics(hotel.id)
        recent_bookings = Booking.query.filter_by(hotel_id=hotel.id).order_by(Booking.booking_date.desc()).limit(5).all()
        
        return render_template('dashboard/hotel_admin_dashboard.html',
                            hotel=hotel,
                            stats=stats,
                            recent_bookings=recent_bookings)
    
    else:  # customer
        user_bookings = Booking.query.filter_by(customer_id=current_user.id).order_by(Booking.booking_date.desc()).limit(5).all()
        return render_template('dashboard/customer_dashboard.html', recent_bookings=user_bookings)

# Hotel Routes
@app.route('/hotels')
def view_hotels():
    """හොටෙල් බැලීම"""
    hotels = Hotel.query.filter_by(is_approved=True).all()
    return render_template('hotels/hotels.html', hotels=hotels)

@app.route('/hotel/<int:hotel_id>')
def hotel_details(hotel_id):
    """හොටෙල් විස්තර"""
    hotel = Hotel.query.get_or_404(hotel_id)
    
    if not hotel.is_approved:
        flash('මෙම හොටෙල් තවම අනුමත කර නොමැත.', 'warning')
        return redirect(url_for('view_hotels'))
    
    rooms = Room.query.filter_by(hotel_id=hotel_id, is_available=True).all()
    return render_template('hotels/hotel_details.html', hotel=hotel, rooms=rooms, today=get_today())

@app.route('/register_hotel', methods=['GET', 'POST'])
@login_required
def register_hotel():
    """හොටෙල් ලියාපදිංචි කිරීම"""
    if current_user.user_type != 'hotel_admin':
        flash('මෙම ක්‍රියාවට හොටෙල් අයිතිකරු අවසරය අවශ්‍යයි.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Check if user already has a hotel
    existing_hotel = Hotel.query.filter_by(owner_email=current_user.email).first()
    if existing_hotel:
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
            is_approved=False
        )
        
        try:
            db.session.add(hotel)
            db.session.commit()
            flash('ඔබගේ හොටෙල් සාර්ථකව ලියාපදිංචි කරන ලදී! සුපිරි පරිපාලක අනුමත කිරීමෙන් පසු එය පෙන්වනු ඇත.', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('හොටෙල් ලියාපදිංචි කිරීමේ දෝෂයක්. කරුණාකර පසුව උත්සාහ කරන්න.', 'danger')
    
    return render_template('hotels/register_hotel.html')

# Room Management
@app.route('/hotel/<int:hotel_id>/rooms')
@login_required
def hotel_rooms(hotel_id):
    """හොටෙල් කාමර පාලනය"""
    hotel = Hotel.query.get_or_404(hotel_id)
    
    # Check authorization
    if current_user.user_type == 'hotel_admin' and hotel.owner_email != current_user.email:
        flash('අවසරය නොමැත.', 'danger')
        return redirect(url_for('dashboard'))
    
    rooms = Room.query.filter_by(hotel_id=hotel_id).all()
    return render_template('hotels/rooms.html', hotel=hotel, rooms=rooms)

@app.route('/hotel/<int:hotel_id>/add_room', methods=['GET', 'POST'])
@login_required
def add_room(hotel_id):
    """නව කාමරයක් ඇතුලත් කිරීම"""
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
        description = request.form.get('description', '')
        size = request.form.get('size', '')
        bed_type = request.form.get('bed_type', '')
        
        room = Room(
            hotel_id=hotel_id,
            room_number=room_number,
            room_type=room_type,
            capacity=capacity,
            price_per_night=price_per_night,
            features=features,
            description=description,
            size=size,
            bed_type=bed_type
        )
        
        try:
            db.session.add(room)
            db.session.commit()
            flash('කාමරය සාර්ථකව ඇතුලත් කරන ලදී!', 'success')
            return redirect(url_for('hotel_rooms', hotel_id=hotel_id))
        except Exception as e:
            db.session.rollback()
            flash('කාමරය ඇතුලත් කිරීමේ දෝෂයක්.', 'danger')
    
    return render_template('hotels/add_room.html', hotel=hotel)

# Image Upload Routes
@app.route('/hotel/<int:hotel_id>/upload_images', methods=['POST'])
@login_required
def upload_hotel_images(hotel_id):
    """බහු රූප ඇතුලත් කිරීම (උපරිම 4)"""
    hotel = Hotel.query.get_or_404(hotel_id)
    
    # Check authorization
    if current_user.user_type == 'hotel_admin' and hotel.owner_email != current_user.email:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    if 'images' not in request.files:
        return jsonify({'success': False, 'message': 'No images selected'})
    
    files = request.files.getlist('images')
    set_primary = request.form.get('set_primary') == 'true'
    
    if len(files) > 4:
        return jsonify({'success': False, 'message': 'Maximum 4 images allowed'})
    
    uploaded_images = []
    
    try:
        for i, file in enumerate(files):
            if file.filename == '':
                continue
                
            image_url = image_utils.save_hotel_image(file, hotel_id)
            if image_url:
                # First image becomes primary if set_primary is true
                is_primary = set_primary and i == 0
                
                # If setting as primary, unset other primary images
                if is_primary:
                    HotelImage.query.filter_by(hotel_id=hotel_id, is_primary=True).update({'is_primary': False})
                
                hotel_image = HotelImage(
                    hotel_id=hotel_id,
                    image_url=image_url,
                    is_primary=is_primary
                )
                db.session.add(hotel_image)
                uploaded_images.append(image_url)
        
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'{len(uploaded_images)} images uploaded successfully',
            'images': uploaded_images
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/hotel/image/<int:image_id>/set_primary', methods=['POST'])
@login_required
def set_primary_image(image_id):
    """ප්‍රධාන රූපයක් සකසන්න"""
    image = HotelImage.query.get_or_404(image_id)
    hotel = Hotel.query.get(image.hotel_id)
    
    # Check authorization
    if current_user.user_type == 'hotel_admin' and hotel.owner_email != current_user.email:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        # Unset all primary images for this hotel
        HotelImage.query.filter_by(hotel_id=hotel.id, is_primary=True).update({'is_primary': False})
        
        # Set this image as primary
        image.is_primary = True
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Primary image set successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/hotel/image/<int:image_id>/delete', methods=['DELETE'])
@login_required
def delete_hotel_image(image_id):
    """හොටෙල් රූපය මකාදැමීම"""
    image = HotelImage.query.get_or_404(image_id)
    hotel = Hotel.query.get(image.hotel_id)
    
    # Check authorization
    if current_user.user_type == 'hotel_admin' and hotel.owner_email != current_user.email:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        # If deleting primary image, set another image as primary
        if image.is_primary:
            other_image = HotelImage.query.filter(
                HotelImage.hotel_id == hotel.id,
                HotelImage.id != image_id
            ).first()
            
            if other_image:
                other_image.is_primary = True
        
        db.session.delete(image)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Image deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/room/<int:room_id>/upload_image', methods=['POST'])
@login_required
def upload_room_image(room_id):
    """කාමර රූපය ඇතුලත් කිරීම"""
    room = Room.query.get_or_404(room_id)
    hotel = Hotel.query.get(room.hotel_id)
    
    if current_user.user_type == 'hotel_admin' and hotel.owner_email != current_user.email:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'No image selected'})
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No image selected'})
    
    image_url = image_utils.save_room_image(file, room_id)
    if image_url:
        is_primary = request.form.get('is_primary') == 'true'
        
        if is_primary:
            RoomImage.query.filter_by(room_id=room_id, is_primary=True).update({'is_primary': False})
        
        room_image = RoomImage(
            room_id=room_id,
            image_url=image_url,
            is_primary=is_primary
        )
        
        try:
            db.session.add(room_image)
            db.session.commit()
            return jsonify({'success': True, 'image_url': image_url})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Database error'})
    
    return jsonify({'success': False, 'message': 'Invalid image'})

# Booking System with Enhanced WhatsApp Notifications
@app.route('/book_hotel/<int:hotel_id>', methods=['GET', 'POST'])
@login_required
def book_hotel(hotel_id):
    """හොටෙල් බුක් කිරීම - Enhanced with WhatsApp"""
    if current_user.user_type != 'customer':
        flash('මෙම ක්‍රියාවට ගනුදෙනුකරු අවසරය අවශ්‍යයි.', 'danger')
        return redirect(url_for('dashboard'))
    
    hotel = Hotel.query.get_or_404(hotel_id)
    
    if not hotel.is_approved:
        flash('මෙම හොටෙල් තවම අනුමත කර නොමැත.', 'warning')
        return redirect(url_for('view_hotels'))
    
    if request.method == 'POST':
        check_in_date = request.form['check_in_date']
        check_out_date = request.form['check_out_date']
        guest_name = request.form['guest_name']
        guest_phone = request.form['guest_phone']
        guest_whatsapp = request.form.get('guest_whatsapp', guest_phone)
        room_id = request.form.get('room_id', 0)
        number_of_guests = int(request.form.get('number_of_guests', 1))
        special_requests = request.form.get('special_requests', '')
        
        # Calculate total price
        check_in = datetime.strptime(check_in_date, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_date, '%Y-%m-%d').date()
        nights = (check_out - check_in).days
        
        if nights <= 0:
            flash('කරුණාකර වලංගු රැස්වීමේ දින ඇතුලත් කරන්න.', 'danger')
            return redirect(url_for('book_hotel', hotel_id=hotel_id))
        
        # Get room price if room is selected
        if room_id and room_id != '0':
            room = Room.query.get(room_id)
            price_per_night = room.price_per_night
        else:
            price_per_night = hotel.price_per_night
        
        total_price = price_per_night * nights
        
        # Create booking
        booking = Booking(
            hotel_id=hotel.id,
            room_id=room_id if room_id and room_id != '0' else None,
            guest_name=guest_name,
            guest_email=current_user.email,
            guest_phone=guest_phone,
            guest_whatsapp=guest_whatsapp,
            check_in_date=check_in,
            check_out_date=check_out,
            total_price=total_price,
            customer_id=current_user.id,
            status='confirmed',
            number_of_guests=number_of_guests,
            special_requests=special_requests
        )
        
        try:
            db.session.add(booking)
            db.session.flush()  # Get booking ID without committing
            
            # Update available rooms
            if hotel.available_rooms > 0:
                hotel.available_rooms -= 1
            
            # Create calendar entries
            current_date = check_in
            while current_date < check_out:
                calendar_entry = BookingCalendar(
                    hotel_id=hotel.id,
                    room_id=room_id if room_id and room_id != '0' else 0,
                    date=current_date,
                    status='booked',
                    booking_id=booking.id,
                    updated_by=current_user.id
                )
                db.session.add(calendar_entry)
                current_date += timedelta(days=1)
            
            db.session.commit()
            
            # Send Enhanced WhatsApp notifications
            notification_results = []
            
            try:
                # Send to hotel owner
                owner_result = whatsapp_service.send_booking_notification_to_owner(hotel, booking, current_user)
                notification_results.append(owner_result)
                
                # Send to customer
                customer_result = whatsapp_service.send_booking_confirmation_to_customer(hotel, booking)
                notification_results.append(customer_result)
                
                successful_notifications = sum(1 for r in notification_results if r.get('success'))
                
                if successful_notifications == 2:
                    flash('බුකින්ග් සාර්ථකයි! WhatsApp දන්වීම් දෙකම යවන ලදී.', 'success')
                elif successful_notifications == 1:
                    flash('බුකින්ග් සාර්ථකයි! WhatsApp දන්වීම් එකක් යවන ලදී.', 'warning')
                else:
                    flash('බුකින්ග් සාර්ථකයි! (WhatsApp දන්වීම් යැවීම අසාර්ථකයි)', 'warning')
                    
            except Exception as e:
                flash(f'බුකින්ග් සාර්ථකයි! (WhatsApp දෝෂය: {e})', 'warning')
            
            return redirect(url_for('my_bookings'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'බුකින්ග් අසාර්ථකයි: {str(e)}', 'danger')
    
    rooms = Room.query.filter_by(hotel_id=hotel_id, is_available=True).all()
    today = datetime.now().date().isoformat()
    return render_template('hotels/book_hotel.html', hotel=hotel, rooms=rooms, today=today)

@app.route('/my_bookings')
@login_required
def my_bookings():
    """ගනුදෙනුකරුගේ බුකින්ග්"""
    if current_user.user_type != 'customer':
        flash('මෙම ක්‍රියාවට ගනුදෙනුකරු අවසරය අවශ්‍යයි.', 'danger')
        return redirect(url_for('dashboard'))
    
    bookings = Booking.query.filter_by(customer_id=current_user.id).order_by(Booking.booking_date.desc()).all()
    
    # Get hotel details for each booking
    bookings_with_details = []
    for booking in bookings:
        hotel = Hotel.query.get(booking.hotel_id)
        room = Room.query.get(booking.room_id) if booking.room_id else None
        bookings_with_details.append({
            'booking': booking,
            'hotel': hotel,
            'room': room
        })
    
    return render_template('bookings/my_bookings.html', bookings_with_details=bookings_with_details)

# Calendar Routes
@app.route('/hotel/<int:hotel_id>/calendar')
@login_required
def hotel_calendar(hotel_id):
    """හොටෙල් බුකින්ග් කැලන්ඩරය"""
    hotel = Hotel.query.get_or_404(hotel_id)
    
    # Check access rights
    if current_user.user_type == 'hotel_admin' and hotel.owner_email != current_user.email:
        flash('අවසරය නොමැත.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get calendar data
    start_date = request.args.get('start', datetime.now().date().isoformat())
    end_date = request.args.get('end', (datetime.now() + timedelta(days=60)).date().isoformat())
    
    events = get_booking_calendar_events(hotel_id, start_date, end_date)
    
    rooms = Room.query.filter_by(hotel_id=hotel_id).all()
    
    return render_template('calendar/hotel_calendar.html', 
                         hotel=hotel, 
                         events=events,
                         rooms=rooms,
                         is_owner=current_user.user_type in ['super_admin', 'hotel_admin'])

@app.route('/api/calendar/update', methods=['POST'])
@login_required
def update_calendar():
    """කැලන්ඩරය යාවත්කාලීන කිරීම"""
    data = request.get_json()
    date_str = data.get('date')
    room_id = data.get('room_id')
    status = data.get('status')
    hotel_id = data.get('hotel_id')
    notes = data.get('notes', '')
    
    hotel = Hotel.query.get_or_404(hotel_id)
    
    # Verify ownership
    if current_user.user_type == 'hotel_admin' and hotel.owner_email != current_user.email:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Find or create calendar entry
        calendar_entry = BookingCalendar.query.filter_by(
            hotel_id=hotel_id,
            room_id=room_id,
            date=date
        ).first()
        
        if not calendar_entry:
            calendar_entry = BookingCalendar(
                hotel_id=hotel_id,
                room_id=room_id,
                date=date,
                updated_by=current_user.id
            )
        
        calendar_entry.status = status
        calendar_entry.notes = notes
        calendar_entry.updated_at = datetime.utcnow()
        
        if status == 'available':
            calendar_entry.booking_id = None
        
        db.session.add(calendar_entry)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Calendar updated successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

# Admin Routes
@app.route('/admin/hotels')
@login_required
def admin_hotels():
    """සුපිරි පරිපාලක - හොටෙල් පාලනය"""
    if current_user.user_type != 'super_admin':
        flash('මෙම ක්‍රියාවට සුපිරි පරිපාලක අවසරය අවශ්‍යයි.', 'danger')
        return redirect(url_for('dashboard'))
    
    hotels = Hotel.query.all()
    return render_template('admin/manage_hotels.html', hotels=hotels)

@app.route('/admin/approve_hotel/<int:hotel_id>')
@login_required
def approve_hotel(hotel_id):
    """හොටෙල් අනුමත කිරීම"""
    if current_user.user_type != 'super_admin':
        flash('මෙම ක්‍රියාවට සුපිරි පරිපාලක අවසරය අවශ්‍යයි.', 'danger')
        return redirect(url_for('dashboard'))
    
    hotel = Hotel.query.get_or_404(hotel_id)
    hotel.is_approved = True
    hotel.approved_by = current_user.id
    hotel.approved_at = datetime.utcnow()
    
    db.session.commit()
    
    flash(f'{hotel.name} හොටෙල් සාර්ථකව අනුමත කරන ලදී!', 'success')
    return redirect(url_for('admin_hotels'))

@app.route('/admin/delete_hotel/<int:hotel_id>')
@login_required
def delete_hotel(hotel_id):
    """හොටෙල් මකාදැමීම"""
    if current_user.user_type != 'super_admin':
        flash('මෙම ක්‍රියාවට සුපිරි පරිපාලක අවසරය අවශ්‍යයි.', 'danger')
        return redirect(url_for('dashboard'))
    
    hotel = Hotel.query.get_or_404(hotel_id)
    
    try:
        db.session.delete(hotel)
        db.session.commit()
        flash(f'{hotel.name} හොටෙල් සාර්ථකව මකා දමන ලදී!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('හොටෙල් මකාදැමීමේ දෝෂයක්.', 'danger')
    
    return redirect(url_for('admin_hotels'))

# Profile Routes
@app.route('/profile')
@login_required
def profile():
    """පරිශීලක පැතිකඩ"""
    return render_template('auth/profile.html', user=current_user)

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    """පැතිකඩ යාවත්කාලීන කිරීම"""
    full_name = request.form.get('full_name', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip().lower()
    
    # Validation
    if not full_name or not phone or not email:
        flash('කරුණාකර සියලුම ක්ෂේත්ර පුරවන්න.', 'danger')
        return redirect(url_for('profile'))
    
    # Check if email is already taken by another user
    existing_user = User.query.filter_by(email=email).first()
    if existing_user and existing_user.id != current_user.id:
        flash('මෙම ඊමේල් ලිපිනය දැනටමත් භාවිතා කර ඇත.', 'danger')
        return redirect(url_for('profile'))
    
    # Update user profile
    current_user.full_name = full_name
    current_user.phone = phone
    current_user.email = email
    
    try:
        db.session.commit()
        flash('පැතිකඩ සාර්ථකව යාවත්කාලීන කරන ලදී!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('යාවත්කාලීන කිරීමේ දෝෂයක්.', 'danger')
    
    return redirect(url_for('profile'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """මුරපදය වෙනස් කිරීම"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # Validation
        if not current_password or not new_password or not confirm_password:
            flash('කරුණාකර සියලුම ක්ෂේත්ර පුරවන්න.', 'danger')
            return render_template('auth/change_password.html')
        
        if not current_user.check_password(current_password):
            flash('වත්මන් මුරපදය වැරදියි.', 'danger')
            return render_template('auth/change_password.html')
        
        if len(new_password) < 6:
            flash('මුරපදය අවම වශයෙන් අකුරු 6ක් විය යුතුය.', 'danger')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('නව මුරපදය සහ තහවුරු කිරීම නොගැලපේ.', 'danger')
            return render_template('auth/change_password.html')
        
        # Update password
        current_user.set_password(new_password)
        db.session.commit()
        
        flash('මුරපදය සාර්ථකව වෙනස් කරන ලදී!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('auth/change_password