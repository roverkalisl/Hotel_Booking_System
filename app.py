from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os

# Flask app creation
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-12345-change-in-production'
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
    is_active = db.Column(db.Boolean, default=True)
    
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
    price_per_night = db.Column(db.Float, nullable=False)
    total_rooms = db.Column(db.Integer, nullable=False)
    available_rooms = db.Column(db.Integer, nullable=False)
    amenities = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=False)
    approved_by = db.Column(db.Integer, nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, nullable=False)
    room_number = db.Column(db.String(10), nullable=False)
    room_type = db.Column(db.String(50))
    capacity = db.Column(db.Integer, nullable=False)
    price_per_night = db.Column(db.Float, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    features = db.Column(db.Text)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, nullable=False)
    room_id = db.Column(db.Integer, nullable=False)
    guest_name = db.Column(db.String(100), nullable=False)
    guest_email = db.Column(db.String(100))
    guest_phone = db.Column(db.String(20))
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='confirmed')
    customer_id = db.Column(db.Integer, nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# WhatsApp Service
def send_whatsapp_notification(hotel_phone, guest_name, check_in, check_out, hotel_name):
    """WhatsApp notification testing function"""
    message = f"""
🆕 නව බුකින්ග් ඇලර්ම්! 🏨

හොටෙල්: {hotel_name}
අමුත්තන්: {guest_name}
Check-in: {check_in}
Check-out: {check_out}

බුකින්ග් තොරතුරු සම්පූර්ණයෙන් බැලීමට ඔබගේ උපකරණ පුවරුවට පිවිසෙන්න.
    """
    print(f"📱 WhatsApp Notification to {hotel_phone}:")
    print(message)
    return True

# Database initialization
def init_db():
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

# Routes
@app.route('/')
def home():
    """මුල් පිටුව"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """පිවිසීම"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
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
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['full_name']
        phone = request.form['phone']
        user_type = request.form['user_type']
        
        # Check if user exists
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
        approved_hotels = Hotel.query.filter_by(is_approved=True).count()
        pending_hotels = Hotel.query.filter_by(is_approved=False).count()
        
        return render_template('dashboard/admin_dashboard.html',
                            total_users=total_users,
                            total_hotels=total_hotels,
                            approved_hotels=approved_hotels,
                            pending_hotels=pending_hotels)
    
    elif user_type == 'hotel_admin':
        hotel = Hotel.query.filter_by(owner_email=current_user.email).first()
        
        if not hotel:
            return render_template('dashboard/hotel_admin_dashboard.html', hotel=None)
        
        # Hotel exists - show statistics
        total_rooms = Room.query.filter_by(hotel_id=hotel.id).count()
        available_rooms = Room.query.filter_by(hotel_id=hotel.id, is_available=True).count()
        total_bookings = Booking.query.filter_by(hotel_id=hotel.id).count()
        
        return render_template('dashboard/hotel_admin_dashboard.html',
                            hotel=hotel,
                            total_rooms=total_rooms,
                            available_rooms=available_rooms,
                            total_bookings=total_bookings)
    
    else:
        return render_template('dashboard/customer_dashboard.html')

@app.route('/register_hotel', methods=['GET', 'POST'])
@login_required
def register_hotel():
    """හොටෙල් ලියාපදිංචි කිරීම"""
    if current_user.user_type != 'hotel_admin':
        flash('මෙම ක්‍රියාවට හොටෙල් අයිතිකරු අවසරය අවශ්‍යයි.', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        description = request.form['description']
        contact_number = request.form['contact_number']
        price_per_night = float(request.form['price_per_night'])
        total_rooms = int(request.form['total_rooms'])
        amenities = request.form['amenities']
        
        # Check if hotel already exists for this user
        existing_hotel = Hotel.query.filter_by(owner_email=current_user.email).first()
        if existing_hotel:
            flash('ඔබට දැනටමත් හොටෙල් එකක් ලියාපදිංචි කර ඇත.', 'warning')
            return redirect(url_for('dashboard'))
        
        hotel = Hotel(
            name=name,
            location=location,
            description=description,
            owner_name=current_user.full_name,
            owner_email=current_user.email,
            contact_number=contact_number,
            price_per_night=price_per_night,
            total_rooms=total_rooms,
            available_rooms=total_rooms,
            amenities=amenities,
            is_approved=False
        )
        
        db.session.add(hotel)
        db.session.commit()
        
        flash('ඔබගේ හොටෙල් සාර්ථකව ලියාපදිංචි කරන ලදී! සුපිරි පරිපාලක අනුමත කිරීමෙන් පසු එය පෙන්වනු ඇත.', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('hotels/register_hotel.html')

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
    db.session.delete(hotel)
    db.session.commit()
    
    flash(f'{hotel.name} හොටෙල් සාර්ථකව මකා දමන ලදී!', 'success')
    return redirect(url_for('admin_hotels'))

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
    
    return render_template('hotels/hotel_details.html', hotel=hotel)

@app.route('/book_hotel/<int:hotel_id>', methods=['GET', 'POST'])
@login_required
def book_hotel(hotel_id):
    """හොටෙල් බුක් කිරීම"""
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
        
        # Calculate total price
        check_in = datetime.strptime(check_in_date, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_date, '%Y-%m-%d').date()
        nights = (check_out - check_in).days
        
        if nights <= 0:
            flash('කරුණාකර වලංගු රැස්වීමේ දින ඇතුලත් කරන්න.', 'danger')
            return redirect(url_for('book_hotel', hotel_id=hotel_id))
        
        total_price = hotel.price_per_night * nights
        
        # Create booking
        booking = Booking(
            hotel_id=hotel.id,
            room_id=0,  # Simple implementation - you can enhance this with room selection
            guest_name=guest_name,
            guest_email=current_user.email,
            guest_phone=guest_phone,
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
        
        db.session.commit()
        
        # Send WhatsApp notification
        send_whatsapp_notification(
            hotel_phone=hotel.contact_number,
            guest_name=guest_name,
            check_in=check_in_date,
            check_out=check_out_date,
            hotel_name=hotel.name
        )
        
        flash(f'ඔබගේ බුකින්ග් සාර්ථකව සිදු කරන ලදී! බුකින්ග් ID: {booking.id}', 'success')
        return redirect(url_for('my_bookings'))
    
    return render_template('hotels/book_hotel.html', hotel=hotel)

@app.route('/my_bookings')
@login_required
def my_bookings():
    """ගනුදෙනුකරුගේ බුකින්ග්"""
    if current_user.user_type != 'customer':
        flash('මෙම ක්‍රියාවට ගනුදෙනුකරු අවසරය අවශ්‍යයි.', 'danger')
        return redirect(url_for('dashboard'))
    
    bookings = Booking.query.filter_by(customer_id=current_user.id).all()
    
    # Get hotel details for each booking
    bookings_with_hotels = []
    for booking in bookings:
        hotel = Hotel.query.get(booking.hotel_id)
        bookings_with_hotels.append({
            'booking': booking,
            'hotel': hotel
        })
    
    return render_template('bookings/my_bookings.html', bookings_with_hotels=bookings_with_hotels)

# Error Handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# Main execution
if __name__ == '__main__':
    init_db()
    print("🚀 Hotel Booking System Started!")
    print("📍 Access your application at:")
    print("   → http://127.0.0.1:5000")
    print("   → http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)