from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from auth import auth_bp
import re


# Import your models and db instance from main app
from app import db, login_manager
from models import User

# Register the blueprint
app.register_blueprint(auth_bp)

# Update your routes to use the blueprint
# Change login, register, logout routes to use auth_bp
# Create Blueprint for auth routes
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    return User.query.get(int(user_id))

def validate_email(email):
    """Email validation function"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Phone number validation for Sri Lankan numbers"""
    pattern = r'^07[0-9]{8}$'
    return re.match(pattern, phone) is not None

def validate_password(password):
    """Password validation"""
    if len(password) < 6:
        return False, "මුරපදය අවම වශයෙන් අකුරු 6ක් විය යුතුය"
    return True, ""

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """පිවිසීම"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # Input validation
        if not username or not password:
            flash('කරුණාකර සියලුම ක්ෂේත්ර පුරවන්න.', 'danger')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user)
            flash('සාර්ථකව පිවිසිය!', 'success')
            
            # Redirect based on user type
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.dashboard'))
        else:
            flash('පිවිසීම අසාර්ථකයි. කරුණාකර පරිශීලක නාමය සහ මුරපදය පරීක්ෂා කරන්න.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """ලියාපදිංචි වීම"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        user_type = request.form.get('user_type', '').strip()
        
        # Input validation
        errors = []
        
        if not all([username, email, password, full_name, phone, user_type]):
            errors.append('කරුණාකර සියලුම ක්ෂේත්ර පුරවන්න.')
        
        if len(username) < 3:
            errors.append('පරිශීලක නාමය අවම වශයෙන් අකුරු 3ක් විය යුතුය.')
        
        if not validate_email(email):
            errors.append('කරුණාකර වලංගු ඊමේල් ලිපිනයක් ඇතුලත් කරන්න.')
        
        password_valid, password_msg = validate_password(password)
        if not password_valid:
            errors.append(password_msg)
        
        if not validate_phone(phone):
            errors.append('කරුණාකර වලංගු දුරකථන අංකයක් ඇතුලත් කරන්න (07XXXXXXXX).')
        
        if user_type not in ['hotel_admin', 'customer']:
            errors.append('කරුණාකර වලංගු ගිණුම් වර්ගයක් තෝරන්න.')
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            errors.append('මෙම පරිශීලක නාමය දැනටමත් භාවිතා කර ඇත.')
        
        if User.query.filter_by(email=email).first():
            errors.append('මෙම ඊමේල් ලිපිනය දැනටමත් භාවිතා කර ඇත.')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html',
                                username=username,
                                email=email,
                                full_name=full_name,
                                phone=phone,
                                user_type=user_type)
        
        # Create new user
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
            
            # Auto-login after registration
            login_user(user)
            
            flash('ඔබගේ ගිණුම සාර්ථකව නිර්මාණය කරන ලදී!', 'success')
            return redirect(url_for('main.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash('ලියාපදිංචි වීමේ දෝෂයක්. කරුණාකර පසුව උත්සාහ කරන්න.', 'danger')
            return render_template('auth/register.html')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """පිටවීම"""
    logout_user()
    flash('ඔබ සාර්ථකව පිටවී ඇත.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    """පරිශීලක පැතිකඩ"""
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/change_password', methods=['GET', 'POST'])
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
        
        password_valid, password_msg = validate_password(new_password)
        if not password_valid:
            flash(password_msg, 'danger')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('නව මුරපදය සහ තහවුරු කිරීම නොගැලපේ.', 'danger')
            return render_template('auth/change_password.html')
        
        if current_password == new_password:
            flash('නව මුරපදය වත්මන් මුරපදයට සමාන විය නොහැක.', 'warning')
            return render_template('auth/change_password.html')
        
        # Update password
        current_user.set_password(new_password)
        db.session.commit()
        
        flash('මුරපදය සාර්ථකව වෙනස් කරන ලදී!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html')

@auth_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    """පැතිකඩ යාවත්කාලීන කිරීම"""
    full_name = request.form.get('full_name', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip().lower()
    
    # Validation
    errors = []
    
    if not full_name or not phone or not email:
        errors.append('කරුණාකර සියලුම ක්ෂේත්ර පුරවන්න.')
    
    if not validate_email(email):
        errors.append('කරුණාකර වලංගු ඊමේල් ලිපිනයක් ඇතුලත් කරන්න.')
    
    if not validate_phone(phone):
        errors.append('කරුණාකර වලංගු දුරකථන අංකයක් ඇතුලත් කරන්න (07XXXXXXXX).')
    
    # Check if email is already taken by another user
    existing_user = User.query.filter_by(email=email).first()
    if existing_user and existing_user.id != current_user.id:
        errors.append('මෙම ඊමේල් ලිපිනය දැනටමත් භාවිතා කර ඇත.')
    
    if errors:
        for error in errors:
            flash(error, 'danger')
        return redirect(url_for('auth.profile'))
    
    # Update user profile
    current_user.full_name = full_name
    current_user.phone = phone
    current_user.email = email
    
    try:
        db.session.commit()
        flash('පැතිකඩ සාර්ථකව යාවත්කාලීන කරන ලදී!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('යාවත්කාලීන කිරීමේ දෝෂයක්. කරුණාකර පසුව උත්සාහ කරන්න.', 'danger')
    
    return redirect(url_for('auth.profile'))

# Error handlers for authentication
@auth_bp.app_errorhandler(401)
def unauthorized_error(error):
    """Handle 401 Unauthorized errors"""
    flash('මෙම පිටුවට ප්‍රවේශය ලබා ගැනීම සඳහා ඔබ පිවිසීම අවශ්‍ය වේ.', 'warning')
    return redirect(url_for('auth.login'))

# Utility functions
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

def get_user_statistics():
    """Get user statistics for admin dashboard"""
    total_users = User.query.count()
    hotel_admins = User.query.filter_by(user_type='hotel_admin').count()
    customers = User.query.filter_by(user_type='customer').count()
    super_admins = User.query.filter_by(user_type='super_admin').count()
    
    return {
        'total_users': total_users,
        'hotel_admins': hotel_admins,
        'customers': customers,
        'super_admins': super_admins
    }

def deactivate_user(user_id):
    """Deactivate a user account"""
    user = User.query.get(user_id)
    if user:
        user.is_active = False
        db.session.commit()
        return True
    return False

def activate_user(user_id):
    """Activate a user account"""
    user = User.query.get(user_id)
    if user:
        user.is_active = True
        db.session.commit()
        return True
    return False
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from models import db, User, Hotel, Room, Booking, HotelImage, RoomImage, BookingCalendar
from whatsapp_service import whatsapp_service
from image_utils import image_utils
from datetime import datetime, timedelta
import os

# ... existing imports and setup ...

# New Routes for Images
@app.route('/hotel/<int:hotel_id>/upload_image', methods=['POST'])
@login_required
def upload_hotel_image(hotel_id):
    """Upload hotel image"""
    if current_user.user_type not in ['super_admin', 'hotel_admin']:
        flash('අවසරය නොමැත.', 'danger')
        return redirect(url_for('hotel_details', hotel_id=hotel_id))
    
    hotel = Hotel.query.get_or_404(hotel_id)
    
    # Check if user owns the hotel or is super admin
    if current_user.user_type == 'hotel_admin' and hotel.owner_email != current_user.email:
        flash('ඔබට මෙම හොටෙල් සඳහා රූප ඇතුලත් කිරීමට අවසරය නොමැත.', 'danger')
        return redirect(url_for('hotel_details', hotel_id=hotel_id))
    
    if 'image' not in request.files:
        flash('කරුණාකර රූපයක් තෝරන්න.', 'danger')
        return redirect(url_for('hotel_details', hotel_id=hotel_id))
    
    file = request.files['image']
    if file.filename == '':
        flash('කරුණාකර රූපයක් තෝරන්න.', 'danger')
        return redirect(url_for('hotel_details', hotel_id=hotel_id))
    
    image_url = image_utils.save_hotel_image(file, hotel_id)
    if image_url:
        is_primary = request.form.get('is_primary') == 'true'
        
        # If setting as primary, unset other primary images
        if is_primary:
            HotelImage.query.filter_by(hotel_id=hotel_id, is_primary=True).update({'is_primary': False})
        
        hotel_image = HotelImage(
            hotel_id=hotel_id,
            image_url=image_url,
            is_primary=is_primary
        )
        db.session.add(hotel_image)
        db.session.commit()
        
        flash('රූපය සාර්ථකව ඇතුලත් කරන ලදී!', 'success')
    else:
        flash('රූපය ඇතුලත් කිරීම අසාර්ථකයි. කරුණාකර වලංගු රූපයක් තෝරන්න.', 'danger')
    
    return redirect(url_for('hotel_details', hotel_id=hotel_id))

@app.route('/room/<int:room_id>/upload_image', methods=['POST'])
@login_required
def upload_room_image(room_id):
    """Upload room image"""
    room = Room.query.get_or_404(room_id)
    hotel = Hotel.query.get(room.hotel_id)
    
    if current_user.user_type not in ['super_admin', 'hotel_admin']:
        flash('අවසරය නොමැත.', 'danger')
        return redirect(url_for('room_details', room_id=room_id))
    
    if current_user.user_type == 'hotel_admin' and hotel.owner_email != current_user.email:
        flash('අවසරය නොමැත.', 'danger')
        return redirect(url_for('room_details', room_id=room_id))
    
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
        db.session.add(room_image)
        db.session.commit()
        
        return jsonify({'success': True, 'image_url': image_url})
    
    return jsonify({'success': False, 'message': 'Invalid image'})

# New Routes for Booking Calendar
@app.route('/hotel/<int:hotel_id>/calendar')
@login_required
def hotel_calendar(hotel_id):
    """Hotel booking calendar"""
    hotel = Hotel.query.get_or_404(hotel_id)
    
    # Check access rights
    if current_user.user_type == 'hotel_admin' and hotel.owner_email != current_user.email:
        flash('අවසරය නොමැත.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get calendar data
    start_date = request.args.get('start', datetime.now().date().isoformat())
    end_date = request.args.get('end', (datetime.now() + timedelta(days=30)).date().isoformat())
    
    calendar_entries = BookingCalendar.query.filter(
        BookingCalendar.hotel_id == hotel_id,
        BookingCalendar.date >= start_date,
        BookingCalendar.date <= end_date
    ).all()
    
    # Format for fullcalendar
    events = []
    for entry in calendar_entries:
        if entry.status == 'booked':
            color = '#dc3545'  # Red
            title = f"Booked - {entry.room.room_number}"
        elif entry.status == 'blocked':
            color = '#ffc107'  # Yellow
            title = f"Blocked - {entry.room.room_number}"
        else:
            color = '#28a745'  # Green
            title = f"Available - {entry.room.room_number}"
        
        events.append({
            'id': entry.id,
            'title': title,
            'start': entry.date.isoformat(),
            'end': entry.date.isoformat(),
            'color': color,
            'extendedProps': {
                'room_number': entry.room.room_number,
                'status': entry.status,
                'booking_id': entry.booking_id
            }
        })
    
    return render_template('calendar/hotel_calendar.html', 
                         hotel=hotel, 
                         events=events,
                         is_owner=current_user.user_type in ['super_admin', 'hotel_admin'])

@app.route('/api/calendar/update', methods=['POST'])
@login_required
def update_calendar():
    """Update calendar entry (for hotel owners)"""
    data = request.get_json()
    date_str = data.get('date')
    room_id = data.get('room_id')
    status = data.get('status')
    hotel_id = data.get('hotel_id')
    
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
        calendar_entry.updated_at = datetime.utcnow()
        
        if status == 'available':
            calendar_entry.booking_id = None
        
        db.session.add(calendar_entry)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Calendar updated'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

# Updated Booking Route with WhatsApp Notifications
@app.route('/book_hotel/<int:hotel_id>', methods=['GET', 'POST'])
@login_required
def book_hotel(hotel_id):
    """Book hotel with WhatsApp notifications"""
    if current_user.user_type != 'customer':
        flash('ගනුදෙනුකරු ගිණුමක් අවශ්‍යයි.', 'danger')
        return redirect(url_for('dashboard'))
    
    hotel = Hotel.query.get_or_404(hotel_id)
    
    if not hotel.is_approved:
        flash('හොටෙල් තවම අනුමත කර නොමැත.', 'warning')
        return redirect(url_for('view_hotels'))
    
    if request.method == 'POST':
        check_in_date = request.form['check_in_date']
        check_out_date = request.form['check_out_date']
        guest_name = request.form['guest_name']
        guest_phone = request.form['guest_phone']
        guest_whatsapp = request.form.get('guest_whatsapp', guest_phone)  # WhatsApp number
        
        # Calculate total price
        check_in = datetime.strptime(check_in_date, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_date, '%Y-%m-%d').date()
        nights = (check_out - check_in).days
        
        if nights <= 0:
            flash('වලංගු දින ඇතුලත් කරන්න.', 'danger')
            return redirect(url_for('book_hotel', hotel_id=hotel_id))
        
        total_price = hotel.price_per_night * nights
        
        # Create booking
        booking = Booking(
            hotel_id=hotel.id,
            room_id=0,  # Simple implementation
            guest_name=guest_name,
            guest_email=current_user.email,
            guest_phone=guest_phone,
            guest_whatsapp=guest_whatsapp,
            check_in_date=check_in,
            check_out_date=check_out,
            total_price=total_price,
            customer_id=current_user.id,
            status='confirmed'
        )
        
        db.session.add(booking)
        
        # Update available rooms
        if hotel.available_rooms > 0:
            hotel.available_rooms -= 1
        
        # Create calendar entries
        current_date = check_in
        while current_date < check_out:
            calendar_entry = BookingCalendar(
                hotel_id=hotel.id,
                room_id=0,  # Simple implementation
                date=current_date,
                status='booked',
                booking_id=booking.id,
                updated_by=current_user.id
            )
            db.session.add(calendar_entry)
            current_date += timedelta(days=1)
        
        db.session.commit()
        
        # Send WhatsApp notifications
        try:
            # To hotel owner
            whatsapp_service.send_booking_notification_to_owner(hotel, booking, current_user)
            
            # To customer
            whatsapp_service.send_booking_confirmation_to_customer(hotel, booking)
            
            flash('බුකින්ග් සාර්ථකයි! WhatsApp දන්වීම් යවන ලදී.', 'success')
        except Exception as e:
            flash(f'බුකින්ග් සාර්ථකයි! (WhatsApp දෝෂය: {e})', 'warning')
        
        return redirect(url_for('my_bookings'))
    
    today = datetime.now().date().isoformat()
    return render_template('hotels/book_hotel.html', hotel=hotel, today=today)

# Room Management Routes
@app.route('/hotel/<int:hotel_id>/rooms')
@login_required
def hotel_rooms(hotel_id):
    """Manage hotel rooms"""
    hotel = Hotel.query.get_or_404(hotel_id)
    
    if current_user.user_type not in ['super_admin', 'hotel_admin']:
        flash('අවසරය නොමැත.', 'danger')
        return redirect(url_for('dashboard'))
    
    if current_user.user_type == 'hotel_admin' and hotel.owner_email != current_user.email:
        flash('අවසරය නොමැත.', 'danger')
        return redirect(url_for('dashboard'))
    
    rooms = Room.query.filter_by(hotel_id=hotel_id).all()
    return render_template('hotels/rooms.html', hotel=hotel, rooms=rooms)

@app.route('/hotel/<int:hotel_id>/add_room', methods=['GET', 'POST'])
@login_required
def add_room(hotel_id):
    """Add new room to hotel"""
    hotel = Hotel.query.get_or_404(hotel_id)
    
    if current_user.user_type not in ['super_admin', 'hotel_admin']:
        flash('අවසරය නොමැත.', 'danger')
        return redirect(url_for('dashboard'))
    
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
        return redirect(url_for('hotel_rooms', hotel_id=hotel_id))
    
    return render_template('hotels/add_room.html', hotel=hotel)