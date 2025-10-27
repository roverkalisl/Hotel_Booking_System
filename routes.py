from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from app import db, create_app
from app.models import User, Hotel, Room, Booking
from app.forms import LoginForm, RegistrationForm, HotelForm
from datetime import datetime

main_routes = Blueprint('routes', __name__)

@main_routes.route('/')
@main_routes.route('/home')
def home():
    return render_template('home.html')

@main_routes.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('සාර්ථකව පිවිසිය!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('routes.dashboard'))
        else:
            flash('පිවිසීම අසාර්ථකයි. කරුණාකර පරිශීලක නාමය සහ මුරපදය පරීක්ෂා කරන්න.', 'danger')
    
    return render_template('auth/login.html', form=form)

@main_routes.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            phone=form.phone.data,
            user_type=form.user_type.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('ඔබගේ ගිණුම සාර්ථකව නිර්මාණය කරන ලදී! දැන් ඔබට පිවිසිය හැකිය.', 'success')
        return redirect(url_for('routes.login'))
    
    return render_template('auth/register.html', form=form)

@main_routes.route('/logout')
def logout():
    logout_user()
    flash('ඔබ සාර්ථකව පිටවී ඇත.', 'info')
    return redirect(url_for('routes.login'))

@main_routes.route('/dashboard')
@login_required
def dashboard():
    if current_user.user_type == 'super_admin':
        return admin_dashboard()
    elif current_user.user_type == 'hotel_admin':
        return hotel_admin_dashboard()
    else:
        return customer_dashboard()

def admin_dashboard():
    total_users = User.query.count()
    total_hotels = Hotel.query.count()
    approved_hotels = Hotel.query.filter_by(is_approved=True).count()
    pending_hotels = Hotel.query.filter_by(is_approved=False).count()
    total_bookings = Booking.query.count()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_hotels=total_hotels,
                         approved_hotels=approved_hotels,
                         pending_hotels=pending_hotels,
                         total_bookings=total_bookings)

def hotel_admin_dashboard():
    hotel = Hotel.query.filter_by(owner_email=current_user.email).first()
    
    if not hotel:
        flash('ඔබට තවමත් හොටෙලයක් ලියාපදිංචි කර නොමැත.', 'warning')
        return render_template('hotel_admin/dashboard.html', hotel=None)
    
    total_rooms = Room.query.filter_by(hotel_id=hotel.id).count()
    available_rooms = Room.query.filter_by(hotel_id=hotel.id, is_available=True).count()
    total_bookings = Booking.query.filter_by(hotel_id=hotel.id).count()
    
    return render_template('hotel_admin/dashboard.html',
                         hotel=hotel,
                         total_rooms=total_rooms,
                         available_rooms=available_rooms,
                         total_bookings=total_bookings)

def customer_dashboard():
    return render_template('customer/dashboard.html')

@main_routes.route('/register_hotel', methods=['GET', 'POST'])
@login_required
def register_hotel():
    if current_user.user_type != 'hotel_admin':
        flash('ඔබට මෙම පිටුවට ප්‍රවේශය නොමැත.', 'danger')
        return redirect(url_for('routes.dashboard'))
    
    form = HotelForm()
    
    if form.validate_on_submit():
        hotel = Hotel(
            name=form.name.data,
            location=form.location.data,
            description=form.description.data,
            owner_name=form.owner_name.data,
            owner_email=form.owner_email.data,
            contact_number=form.contact_number.data,
            price_per_night=form.price_per_night.data,
            total_rooms=form.total_rooms.data,
            available_rooms=form.total_rooms.data,
            amenities=form.amenities.data
        )
        
        db.session.add(hotel)
        db.session.commit()
        
        # Create rooms for the hotel
        room_types = [
            {'type': 'Single', 'capacity': 1, 'base_price': 4000},
            {'type': 'Double', 'capacity': 2, 'base_price': 6000},
            {'type': 'Suite', 'capacity': 4, 'base_price': 10000},
            {'type': 'Deluxe', 'capacity': 3, 'base_price': 8000}
        ]
        
        for i in range(1, hotel.total_rooms + 1):
            room_type = room_types[i % len(room_types)]
            room = Room(
                hotel_id=hotel.id,
                room_number=f"{i:03d}",
                room_type=room_type['type'],
                capacity=room_type['capacity'],
                price_per_night=room_type['base_price'] + (i % 4) * 500,
                is_available=True,
                features=f"WiFi, AC, TV, {room_type['type']} Room"
            )
            db.session.add(room)
        
        db.session.commit()
        flash('ඔබගේ හොටෙල් සාර්ථකව ලියාපදිංචි කරන ලදී! සුපිරි පරිපාලකයා අනුමත කිරීමෙන් පසු එය සක්‍රිය වනු ඇත.', 'success')
        return redirect(url_for('routes.dashboard'))
    
    return render_template('hotel_admin/register_hotel.html', form=form)

@main_routes.route('/admin/hotels')
@login_required
def admin_hotels():
    if current_user.user_type != 'super_admin':
        flash('ඔබට මෙම පිටුවට ප්‍රවේශය නොමැත.', 'danger')
        return redirect(url_for('routes.dashboard'))
    
    hotels = Hotel.query.all()
    return render_template('admin/hotels.html', hotels=hotels)

@main_routes.route('/admin/approve_hotel/<int:hotel_id>')
@login_required
def approve_hotel(hotel_id):
    if current_user.user_type != 'super_admin':
        flash('ඔබට මෙම ක්‍රියාව සිදු කිරීමට අවසර නොමැත.', 'danger')
        return redirect(url_for('routes.dashboard'))
    
    hotel = Hotel.query.get_or_404(hotel_id)
    hotel.is_approved = True
    hotel.approved_by = current_user.id
    hotel.approved_at = datetime.utcnow()
    db.session.commit()
    
    flash(f'{hotel.name} හොටෙල් අනුමත කරන ලදී!', 'success')
    return redirect(url_for('routes.admin_hotels'))

@main_routes.route('/customer/hotels')
@login_required
def customer_hotels():
    if current_user.user_type != 'customer':
        flash('ඔබට මෙම පිටුවට ප්‍රවේශය නොමැත.', 'danger')
        return redirect(url_for('routes.dashboard'))
    
    hotels = Hotel.query.filter_by(is_approved=True).all()
    return render_template('customer/hotels.html', hotels=hotels)

# Initialize the database and create super admin
def initialize_database():
    app = create_app()
    with app.app_context():
        db.create_all()
        
        # Create super admin if not exists
        super_admin = User.query.filter_by(user_type='super_admin').first()
        if not super_admin:
            super_admin = User(
                username='superadmin',
                email='super@admin.com',
                user_type='super_admin',
                full_name='System Super Administrator',
                phone='0112345678',
                is_active=True
            )
            super_admin.set_password('admin123')
            db.session.add(super_admin)
            db.session.commit()
            print("✅ Super admin created successfully!")