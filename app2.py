import os
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Flask app creation
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel_booking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Simple Models
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
    whatsapp_number = db.Column(db.String(20))  # This will be created fresh
    price_per_night = db.Column(db.Float, nullable=False)
    total_rooms = db.Column(db.Integer, nullable=False)
    available_rooms = db.Column(db.Integer, nullable=False)
    amenities = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=False)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, nullable=False)
    guest_name = db.Column(db.String(100), nullable=False)
    guest_email = db.Column(db.String(100))
    guest_phone = db.Column(db.String(20))
    guest_whatsapp = db.Column(db.String(20))
    check_in_date = db.Column(db.String(50), nullable=False)
    check_out_date = db.Column(db.String(50), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='confirmed')
    customer_id = db.Column(db.Integer, nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Database initialization
def init_db():
    with app.app_context():
        # Drop all tables and recreate
        db.drop_all()
        db.create_all()
        
        # Create super admin
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
            print("✅ Database created successfully!")
            print("✅ Super admin created!")

# Routes
@app.route('/')
def home():
    """මුල් පිටුව"""
    try:
        hotels = Hotel.query.filter_by(is_approved=True).limit(6).all()
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Hotel Booking System</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <nav class="navbar navbar-dark bg-primary">
                <div class="container">
                    <a class="navbar-brand" href="/">🏨 Hotel Booking System</a>
                </div>
            </nav>
            
            <div class="container mt-5">
                <div class="alert alert-success">
                    <h1>✅ System Working!</h1>
                    <p>Hotel Booking System is running successfully</p>
                </div>
                
                <div class="row">
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
                                <h5>Register</h5>
                                <p>Create new account</p>
                                <a href="/register" class="btn btn-success">Register</a>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body text-center">
                                <h5>Hotels</h5>
                                <p>View available hotels</p>
                                <a href="/hotels" class="btn btn-info">View Hotels</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    except Exception as e:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <div class="alert alert-danger">
                    <h1>Database Error</h1>
                    <p>Please delete the database file and restart the application.</p>
                    <p>Error: {str(e)}</p>
                    <a href="/" class="btn btn-warning">Restart</a>
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
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user)
            flash('සාර්ථකව පිවිසිය!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('පිවිසීම අසාර්ථකයි.', 'danger')
    
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login</title>
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
                            <p class="text-center">
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
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        user_type = request.form.get('user_type', '').strip()
        
        if User.query.filter_by(username=username).first():
            flash('මෙම පරිශීලක නාමය දැනටමත් භාවිතා කර ඇත.', 'danger')
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
        
        flash('ඔබගේ ගිණුම සාර්ථකව නිර්මාණය කරන ලදී!', 'success')
        return redirect(url_for('login'))
    
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Register</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-dark bg-success">
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
                            <p class="text-center">
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

@app.route('/dashboard')
@login_required
def dashboard():
    """උපකරණ පුවරුව"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-dark bg-primary">
            <div class="container">
                <a class="navbar-brand" href="/">🏨 Hotel Booking</a>
                <div class="navbar-nav ms-auto">
                    <span class="navbar-text text-white me-3">
                        👤 {current_user.full_name}
                    </span>
                    <a class="nav-link text-white" href="/logout">පිටවීම</a>
                </div>
            </div>
        </nav>
        
        <div class="container mt-5">
            <div class="alert alert-info">
                <h1>උපකරණ පුවරුව</h1>
                <p>Welcome, {current_user.full_name}!</p>
            </div>
            
            <div class="card">
                <div class="card-body text-center">
                    <h5>System Ready!</h5>
                    <p>Your hotel booking system is working correctly.</p>
                    <a href="/" class="btn btn-primary">මුල් පිටුව</a>
                    <a href="/hotels" class="btn btn-success">හොටෙල් බලන්න</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/logout')
@login_required
def logout():
    """පිටවීම"""
    logout_user()
    flash('ඔබ සාර්ථකව පිටවී ඇත.', 'info')
    return redirect(url_for('login'))

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
                        📍 {hotel.location}<br>
                        💰 රු. {hotel.price_per_night:,.2f} per night<br>
                        🛏️ {hotel.available_rooms} කාමර තිබේ
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
        <title>Hotels</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-dark bg-primary">
            <div class="container">
                <a class="navbar-brand" href="/">🏨 Hotel Booking</a>
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

# Error Handlers
@app.errorhandler(404)
def not_found_error(error):
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>404 - Page Not Found</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <div class="alert alert-danger text-center">
                <h1>404 - Page Not Found</h1>
                <p>The page you are looking for does not exist.</p>
                <a href="/" class="btn btn-primary">Go Home</a>
            </div>
        </div>
    </body>
    </html>
    """, 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>500 - Internal Server Error</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <div class="alert alert-danger text-center">
                <h1>500 - Internal Server Error</h1>
                <p>Something went wrong on our server. Please try again later.</p>
                <a href="/" class="btn btn-primary">Go Home</a>
            </div>
        </div>
    </body>
    </html>
    """, 500

@app.route('/favicon.ico')
def favicon():
    return '', 204

# Main execution
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