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
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hotel Booking System</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    </head>
    <body>
        <nav class="navbar navbar-dark bg-primary">
            <div class="container">
                <a class="navbar-brand" href="/">
                    <i class="fas fa-hotel"></i> Hotel Booking System
                </a>
                <div class="navbar-nav ms-auto">
                    <a class="nav-link text-white" href="/hotels"><i class="fas fa-hotel"></i> හොටෙල්</a>
                    <a class="nav-link text-white" href="/login"><i class="fas fa-sign-in-alt"></i> පිවිසීම</a>
                    <a class="nav-link text-white" href="/register"><i class="fas fa-user-plus"></i> ලියාපදිංචි වීම</a>
                </div>
            </div>
        </nav>
        
        <div class="container mt-5">
            <div class="alert alert-success">
                <h1>✅ Hotel Booking System WORKING!</h1>
                <p>Flask application is running successfully on port 5000</p>
            </div>
            
            <div class="row mt-4">
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body text-center">
                            <h5>Super Admin</h5>
                            <p>Username: <code>superadmin</code></p>
                            <p>Password: <code>admin123</code></p>
                            <a href="/login" class="btn btn-primary">Login</a>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body text-center">
                            <h5>Test Hotels</h5>
                            <p>Login නොකර හොටෙල් බලන්න</p>
                            <a href="/hotels" class="btn btn-success">View Hotels</a>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body text-center">
                            <h5>Register</h5>
                            <p>නව ගිණුමක් තනන්න</p>
                            <a href="/register" class="btn btn-info">Register</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

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
            return redirect(url_for('login'))
    
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - Hotel Booking</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-dark bg-primary">
            <div class="container">
                <a class="navbar-brand" href="/">🏨 Hotel Booking</a>
            </div>
        </nav>
        
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-primary text-white">
                            <h4 class="mb-0">පිවිසීම</h4>
                        </div>
                        <div class="card-body">
                            <form method="POST">
                                <div class="mb-3">
                                    <label class="form-label">පරිශීලක නාමය</label>
                                    <input type="text" class="form-control" name="username" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">මුරපදය</label>
                                    <input type="password" class="form-control" name="password" required>
                                </div>
                                <button type="submit" class="btn btn-primary w-100">පිවිසෙන්න</button>
                            </form>
                            <hr>
                            <p class="text-center mb-0">
                                <a href="/register">ලියාපදිංචි වන්න</a> | 
                                <a href="/">මුල් පිටුව</a>
                            </p>
                        </div>
                    </div>
                    
                    <div class="card mt-3">
                        <div class="card-body">
                            <h6>පරීක්ෂා කිරීම සඳහා:</h6>
                            <p class="mb-1">පරිශීලක නාමය: <code>superadmin</code></p>
                            <p class="mb-0">මුරපදය: <code>admin123</code></p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

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
    
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Register - Hotel Booking</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-dark bg-primary">
            <div class="container">
                <a class="navbar-brand" href="/">🏨 Hotel Booking</a>
            </div>
        </nav>
        
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header bg-success text-white">
                            <h4 class="mb-0">ලියාපදිංචි වීම</h4>
                        </div>
                        <div class="card-body">
                            <form method="POST">
                                <div class="row">
                                    <div class="col-md-6 mb-3">
                                        <label class="form-label">පරිශීලක නාමය</label>
                                        <input type="text" class="form-control" name="username" required>
                                    </div>
                                    <div class="col-md-6 mb-3">
                                        <label class="form-label">ඊමේල්</label>
                                        <input type="email" class="form-control" name="email" required>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-6 mb-3">
                                        <label class="form-label">මුරපදය</label>
                                        <input type="password" class="form-control" name="password" required>
                                    </div>
                                    <div class="col-md-6 mb-3">
                                        <label class="form-label">දුරකථන අංකය</label>
                                        <input type="text" class="form-control" name="phone" required>
                                    </div>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">සම්පූර්ණ නම</label>
                                    <input type="text" class="form-control" name="full_name" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">ගිණුමේ වර්ගය</label>
                                    <select class="form-control" name="user_type" required>
                                        <option value="">තෝරන්න...</option>
                                        <option value="hotel_admin">හොටෙල් අයිතිකරු</option>
                                        <option value="customer">ගනුදෙනුකරු</option>
                                    </select>
                                </div>
                                <button type="submit" class="btn btn-success w-100">ලියාපදිංචි වන්න</button>
                            </form>
                            <hr>
                            <p class="text-center mb-0">
                                <a href="/login">පිවිසෙන්න</a> | 
                                <a href="/">මුල් පිටුව</a>
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/logout')
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
        return admin_dashboard()
    elif user_type == 'hotel_admin':
        return hotel_admin_dashboard()
    else:
        return customer_dashboard()

def admin_dashboard():
    """සුපිරි පරිපාලක උපකරණ පුවරුව"""
    total_users = User.query.count()
    total_hotels = Hotel.query.count()
    approved_hotels = Hotel.query.filter_by(is_approved=True).count()
    pending_hotels = Hotel.query.filter_by(is_approved=False).count()
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Dashboard - Hotel Booking</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    </head>
    <body>
        <nav class="navbar navbar-dark bg-primary">
            <div class="container">
                <a class="navbar-brand" href="/">
                    <i class="fas fa-hotel"></i> Hotel Booking System
                </a>
                <div class="navbar-nav ms-auto">
                    <span class="navbar-text text-white me-3">
                        <i class="fas fa-user"></i> {current_user.full_name}
                    </span>
                    <a class="nav-link text-white" href="/logout">පිටවීම</a>
                </div>
            </div>
        </nav>
        
        <div class="container mt-5">
            <div class="alert alert-primary">
                <h1><i class="fas fa-shield-alt"></i> සුපිරි පරිපාලක උපකරණ පුවරුව</h1>
                <p>Welcome, {current_user.full_name}!</p>
            </div>
            
            <div class="row">
                <div class="col-md-3 mb-4">
                    <div class="card text-white bg-primary">
                        <div class="card-body text-center">
                            <h3>{total_users}</h3>
                            <p>පරිශීලකයන්</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 mb-4">
                    <div class="card text-white bg-success">
                        <div class="card-body text-center">
                            <h3>{total_hotels}</h3>
                            <p>හොටෙල්</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 mb-4">
                    <div class="card text-white bg-warning">
                        <div class="card-body text-center">
                            <h3>{approved_hotels}</h3>
                            <p>අනුමත හොටෙල්</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 mb-4">
                    <div class="card text-white bg-info">
                        <div class="card-body text-center">
                            <h3>{pending_hotels}</h3>
                            <p>අනුමත කිරීමට</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card mt-4">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0"><i class="fas fa-cogs"></i> ක්‍රියාමාර්ග</h5>
                </div>
                <div class="card-body">
                    <div class="d-grid gap-2">
                        <a href="/admin/hotels" class="btn btn-outline-primary btn-lg">
                            <i class="fas fa-hotel"></i> හොටෙල් පාලනය
                        </a>
                        <a href="/hotels" class="btn btn-outline-success btn-lg">
                            <i class="fas fa-eye"></i> හොටෙල් බලන්න
                        </a>
                        <a href="/" class="btn btn-outline-info btn-lg">
                            <i class="fas fa-home"></i> මුල් පිටුව
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

def hotel_admin_dashboard():
    """හොටෙල් අයිතිකරු උපකරණ පුවරුව"""
    hotel = Hotel.query.filter_by(owner_email=current_user.email).first()
    
    if not hotel:
        # No hotel registered yet
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Hotel Admin Dashboard</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        </head>
        <body>
            <nav class="navbar navbar-dark bg-success">
                <div class="container">
                    <a class="navbar-brand" href="/">
                        <i class="fas fa-hotel"></i> Hotel Booking System
                    </a>
                    <div class="navbar-nav ms-auto">
                        <span class="navbar-text text-white me-3">
                            <i class="fas fa-user"></i> {current_user.full_name}
                        </span>
                        <a class="nav-link text-white" href="/logout">පිටවීම</a>
                    </div>
                </div>
            </nav>
            
            <div class="container mt-5">
                <div class="alert alert-warning">
                    <h1><i class="fas fa-hotel"></i> හොටෙල් අයිතිකරු උපකරණ පුවරුව</h1>
                    <p>Welcome, {current_user.full_name}!</p>
                </div>
                
                <div class="card">
                    <div class="card-body text-center py-5">
                        <i class="fas fa-hotel fa-5x text-warning mb-4"></i>
                        <h4 class="text-warning">ඔබගේ හොටෙල් තවම ලියාපදිංචි කර නොමැත</h4>
                        <p class="lead mb-4">
                            ඔබගේ හොටෙල් ලියාපදිංචි කිරීමෙන් පසු එය සුපිරි පරිපාලකයා අනුමත කිරීමෙන් පසු 
                            ගනුදෙනුකරුවන්ට පෙනෙනු ඇත.
                        </p>
                        <a href="/register_hotel" class="btn btn-success btn-lg">
                            <i class="fas fa-plus-circle"></i> හොටෙල් ලියාපදිංචි කරන්න
                        </a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    
    # Hotel exists - show statistics
    total_rooms = Room.query.filter_by(hotel_id=hotel.id).count()
    available_rooms = Room.query.filter_by(hotel_id=hotel.id, is_available=True).count()
    total_bookings = Booking.query.filter_by(hotel_id=hotel.id).count()
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hotel Admin Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    </head>
    <body>
        <nav class="navbar navbar-dark bg-success">
            <div class="container">
                <a class="navbar-brand" href="/">
                    <i class="fas fa-hotel"></i> Hotel Booking System
                </a>
                <div class="navbar-nav ms-auto">
                    <span class="navbar-text text-white me-3">
                        <i class="fas fa-user"></i> {current_user.full_name}
                    </span>
                    <a class="nav-link text-white" href="/logout">පිටවීම</a>
                </div>
            </div>
        </nav>
        
        <div class="container mt-5">
            <div class="alert alert-success">
                <h1><i class="fas fa-hotel"></i> හොටෙල් අයිතිකරු උපකරණ පුවරුව</h1>
                <p>Welcome, {current_user.full_name}! - {hotel.name}</p>
            </div>
            
            <div class="row">
                <div class="col-md-3 mb-4">
                    <div class="card text-white bg-success">
                        <div class="card-body text-center">
                            <h3>{total_rooms}</h3>
                            <p>මුළු කාමර</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 mb-4">
                    <div class="card text-white bg-info">
                        <div class="card-body text-center">
                            <h3>{available_rooms}</h3>
                            <p>තිබෙන කාමර</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 mb-4">
                    <div class="card text-white bg-warning">
                        <div class="card-body text-center">
                            <h3>{total_bookings}</h3>
                            <p>බුකින්ග්</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 mb-4">
                    <div class="card text-white bg-primary">
                        <div class="card-body text-center">
                            <h3>{'අනුමතයි' if hotel.is_approved else 'අනුමත කිරීමට'}</h3>
                            <p>තත්වය</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card mt-4">
                <div class="card-header bg-success text-white">
                    <h5 class="mb-0"><i class="fas fa-cogs"></i> ක්‍රියාමාර්ග</h5>
                </div>
                <div class="card-body">
                    <div class="d-grid gap-2">
                        <a href="/hotel_admin/calendar" class="btn btn-outline-success btn-lg">
                            <i class="fas fa-calendar-alt"></i> කැලන්ඩරය
                        </a>
                        <a href="/hotel_admin/bookings" class="btn btn-outline-primary btn-lg">
                            <i class="fas fa-calendar-check"></i> බුකින්ග්
                        </a>
                        <a href="/register_hotel" class="btn btn-outline-info btn-lg">
                            <i class="fas fa-edit"></i> හොටෙල් යාවත්කාලීන කරන්න
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

def customer_dashboard():
    """ගනුදෙනුකරු උපකරණ පුවරුව"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Customer Dashboard - Hotel Booking</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    </head>
    <body>
        <nav class="navbar navbar-dark bg-info">
            <div class="container">
                <a class="navbar-brand" href="/">
                    <i class="fas fa-hotel"></i> Hotel Booking System
                </a>
                <div class="navbar-nav ms-auto">
                    <span class="navbar-text text-white me-3">
                        <i class="fas fa-user"></i> {current_user.full_name}
                    </span>
                    <a class="nav-link text-white" href="/logout">පිටවීම</a>
                </div>
            </div>
        </nav>
        
        <div class="container mt-5">
            <div class="alert alert-info">
                <h1><i class="fas fa-user"></i> ගනුදෙනුකරු උපකරණ පුවරුව</h1>
                <p>Welcome, {current_user.full_name}!</p>
            </div>
            
            <div class="card">
                <div class="card-header bg-info text-white">
                    <h5 class="mb-0"><i class="fas fa-cogs"></i> ක්‍රියාමාර්ග</h5>
                </div>
                <div class="card-body">
                    <div class="d-grid gap-2">
                        <a href="/hotels" class="btn btn-outline-info btn-lg">
                            <i class="fas fa-hotel"></i> හොටෙල් සොයන්න
                        </a>
                        <a href="/my_bookings" class="btn btn-outline-success btn-lg">
                            <i class="fas fa-history"></i> මගේ බුකින්ග්
                        </a>
                        <a href="/" class="btn btn-outline-primary btn-lg">
                            <i class="fas fa-home"></i> මුල් පිටුව
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/hotels')
def view_hotels():
    """හොටෙල් බැලීම"""
    hotels = Hotel.query.filter_by(is_approved=True).all()
    
    hotels_html = ""
    for hotel in hotels:
        hotels_html += f"""
        <div class="col-md-4 mb-4">
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">{hotel.name}</h5>
                    <p class="card-text">
                        <i class="fas fa-map-marker-alt"></i> {hotel.location}<br>
                        <i class="fas fa-money-bill-wave"></i> රු. {hotel.price_per_night:,.2f} per night<br>
                        <i class="fas fa-bed"></i> {hotel.available_rooms} කාමර තිබේ
                    </p>
                    <a href="/hotel/{hotel.id}" class="btn btn-primary">View Details</a>
                </div>
            </div>
        </div>
        """
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hotels - Hotel Booking</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    </head>
    <body>
        <nav class="navbar navbar-dark bg-primary">
            <div class="container">
                <a class="navbar-brand" href="/">
                    <i class="fas fa-hotel"></i> Hotel Booking System
                </a>
                <div class="navbar-nav ms-auto">
                    <a class="nav-link text-white" href="/">Home</a>
                    <a class="nav-link text-white" href="/login">Login</a>
                </div>
            </div>
        </nav>
        
        <div class="container mt-5">
            <h1>Available Hotels</h1>
            <div class="row">
                {hotels_html if hotels else '<div class="col-12"><p>No hotels available</p></div>'}
            </div>
        </div>
    </body>
    </html>
    """

# Add other routes as needed...

# Main execution
if __name__ == '__main__':
    init_db()
    print("🚀 Hotel Booking System Started!")
    print("📍 Access your application at:")
    print("   → http://127.0.0.1:5000")
    print("   → http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)