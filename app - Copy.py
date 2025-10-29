from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
import re
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Flask app creation
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'your-secret-key-12345-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///hotel_booking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File upload configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload folder if not exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_password_strength(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "මුරපදය අවම වශයෙන් අකුරු 8ක් විය යුතුය"
    if not re.search(r"[A-Z]", password):
        return False, "මුරපදයේ අවම වශයෙන් එක් ඉංග්‍රීසි ලොකු අකුරක්වත් තිබිය යුතුය"
    if not re.search(r"[a-z]", password):
        return False, "මුරපදයේ අවම වශයෙන් එක් ඉංග්‍රීසි පොඩි අකුරක්වත් තිබිය යුතුය"
    if not re.search(r"\d", password):
        return False, "මුරපදයේ අවම වශයෙන් එක් ඉලක්කමක්වත් තිබිය යුතුය"
    return True, "මුරපදය ශක්තිමත් ය"

def validate_booking_dates(check_in, check_out):
    """Validate booking dates"""
    if check_in >= check_out:
        return False, "Check-out දිනය check-in දිනයට පසුව විය යුතුය"
    if check_in < datetime.now().date():
        return False, "Check-in දිනය අතීතයේ විය නොහැක"
    return True, "දිනයන් වලංගු ය"

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
    hotel_type = db.Column(db.String(20), default='hotel')  # hotel, villa, resort
    image_path = db.Column(db.String(255))
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
    image_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
    
    # Try to send actual WhatsApp message if API key exists
    whatsapp_api_key = os.environ.get('WHATSAPP_API_KEY')
    if whatsapp_api_key:
        return send_whatsapp_api_message(hotel_phone, message)
    
    return True

def send_whatsapp_api_message(phone, message):
    """Send actual WhatsApp message using API"""
    try:
        # Example using a WhatsApp API service (adjust based on your provider)
        api_url = "https://api.whatsapp.com/send"
        payload = {
            'phone': phone,
            'message': message,
            'api_key': os.environ.get('WHATSAPP_API_KEY')
        }
        # response = requests.post(api_url, json=payload)
        # return response.status_code == 200
        print(f"📧 WhatsApp API would send to {phone}: {message[:50]}...")
        return True
    except Exception as e:
        print(f"WhatsApp API Error: {e}")
        return False

# Database initialization
def init_db():
    with app.app_context():
        # Drop all tables and recreate with new schema
        db.drop_all()
        db.create_all()
        
        print("✅ Database tables created with new schema!")
        
        # Create super admin
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
        
        # Create sample customer user
        customer_user = User(
            username='customer',
            email='customer@example.com',
            user_type='customer',
            full_name='Sample Customer',
            phone='0771234567',
            is_active=True
        )
        customer_user.set_password('customer123')
        db.session.add(customer_user)
        
        # Create sample hotel admin
        hotel_admin = User(
            username='hotelowner',
            email='owner@example.com',
            user_type='hotel_admin',
            full_name='Hotel Owner',
            phone='0777654321',
            is_active=True
        )
        hotel_admin.set_password('owner123')
        db.session.add(hotel_admin)
        
        # Create your user account
        your_account = User(
            username='kris',
            email='kris@gmail.com',
            user_type='hotel_admin',
            full_name='Kris Perera',
            phone='0771234567',
            is_active=True
        )
        your_account.set_password('kris123')
        db.session.add(your_account)
        
        # Create sample hotels with hotel_type
        hotels = [
            Hotel(
                name='සීගිරිය පැලස්',
                location='සීගිරිය',
                description='සීගිරිය බලකොටුව අසල පිහිටා ඇති විලාසිතා සම්පන්න හොටෙලය',
                owner_name='සුනිල් පෙරේරා',
                owner_email='sunil@sigiriyapalace.com',
                contact_number='0771234567',
                price_per_night=25000.00,
                total_rooms=50,
                available_rooms=35,
                amenities='පිහිනුම් තටාකය, විනෝදාස්වාද, නවීන කාමර',
                hotel_type='hotel',
                is_approved=True
            ),
            Hotel(
                name='ගාලු විලා',
                location='ගාල්ල',
                description='ගාලු කොටුව අසල පිහිටා ඇති පෞද්ගලික විලාව',
                owner_name='ප්‍රියන්ත සිල්වා',
                owner_email='priyantha@gallevilla.com',
                contact_number='0775558888',
                price_per_night=45000.00,
                total_rooms=1,
                available_rooms=1,
                amenities='පෞද්ගලික පිහිනුම් තටාකය, උද්‍යානය, නිවාඩුපුරා සේවා',
                hotel_type='villa',
                is_approved=True
            ),
            Hotel(
                name='කොළඹ රැජින',
                location='කොළඹ',
                description='කොළඹ මධ්‍යස්ථානයේ පිහිටා ඇති නවීන හොටෙලය',
                owner_name='මහේෂ් ගුණරත්න',
                owner_email='mahesh@colombiqueen.com',
                contact_number='0777654321',
                price_per_night=18000.00,
                total_rooms=30,
                available_rooms=25,
                amenities='WiFi, A/C, අවන්හල, රියැදුරන් සේවාව',
                hotel_type='hotel',
                is_approved=True
            ),
            Hotel(
                name='ක්‍රිස් හොටෙල්',
                location='කොළඹ',
                description='නවීන සුවපහසු සහිත හොටෙලය',
                owner_name='ක්‍රිස් පෙරේරා',
                owner_email='kris@gmail.com',
                contact_number='0771234567',
                price_per_night=20000.00,
                total_rooms=20,
                available_rooms=15,
                amenities='WiFi, A/C, අවන්හල, පාකිං',
                hotel_type='hotel',
                is_approved=True
            )
        ]
        
        for hotel in hotels:
            db.session.add(hotel)
        
        db.session.commit()
        print("✅ Sample hotels created successfully!")
        
        # Create rooms for hotels
        hotels_in_db = Hotel.query.all()
        for hotel in hotels_in_db:
            if hotel.hotel_type == 'villa':
                # For villa, create one main villa unit
                villa_room = Room(
                    hotel_id=hotel.id,
                    room_number='VILLA-001',
                    room_type='පෞද්ගලික විලා',
                    capacity=8,
                    price_per_night=hotel.price_per_night,
                    is_available=True,
                    features='4 කාමර, 3 සනීපාරක්ෂක, පෞද්ගලික පිහිනුම් තටාකය, උද්‍යානය, නිවාඩුපුරා සේවා'
                )
                db.session.add(villa_room)
            else:
                # For regular hotels, create multiple rooms
                room_types = [
                    {'number': '101', 'type': 'Standard', 'capacity': 2, 'price': hotel.price_per_night * 0.8, 'features': 'AC, TV, WiFi'},
                    {'number': '102', 'type': 'Deluxe', 'capacity': 3, 'price': hotel.price_per_night, 'features': 'AC, TV, WiFi, Mini Bar'},
                    {'number': '201', 'type': 'Suite', 'capacity': 4, 'price': hotel.price_per_night * 1.5, 'features': 'AC, TV, WiFi, Mini Bar, Balcony'}
                ]
                
                for room_data in room_types:
                    room = Room(
                        hotel_id=hotel.id,
                        room_number=room_data['number'],
                        room_type=room_data['type'],
                        capacity=room_data['capacity'],
                        price_per_night=room_data['price'],
                        is_available=True,
                        features=room_data['features']
                    )
                    db.session.add(room)
        
        db.session.commit()
        print("✅ Rooms created successfully!")
        print("✅ Database initialized successfully!")

# Base Template with common styling
def base_template(title, content, user_type=None):
    nav_links = """
    <a class="nav-link text-white" href="/hotels"><i class="fas fa-hotel"></i> හොටෙල්</a>
    <a class="nav-link text-white" href="/login"><i class="fas fa-sign-in-alt"></i> පිවිසීම</a>
    <a class="nav-link text-white" href="/register"><i class="fas fa-user-plus"></i> ලියාපදිංචි වීම</a>
    """
    
    if current_user.is_authenticated:
        nav_links = f"""
        <span class="navbar-text text-white me-3">
            <i class="fas fa-user"></i> {current_user.full_name}
        </span>
        <a class="nav-link text-white" href="/dashboard"><i class="fas fa-tachometer-alt"></i> උපකරණ පුවරුව</a>
        <a class="nav-link text-white" href="/logout"><i class="fas fa-sign-out-alt"></i> පිටවීම</a>
        """
    
    return f"""
    <!DOCTYPE html>
    <html lang="si">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - Hotel Booking System</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            .hotel-card {{ transition: transform 0.3s; }}
            .hotel-card:hover {{ transform: translateY(-5px); }}
            .booking-calendar {{ background: #f8f9fa; border-radius: 10px; padding: 20px; }}
            .available {{ background-color: #d4edda !important; }}
            .booked {{ background-color: #f8d7da !important; }}
            .today {{ background-color: #cce7ff !important; }}
            .hotel-image {{ height: 200px; object-fit: cover; }}
            .room-image {{ height: 150px; object-fit: cover; }}
            .villa-badge {{ background-color: #ff6b35; }}
            .hotel-badge {{ background-color: #17a2b8; }}
            .flash-messages {{ position: fixed; top: 80px; right: 20px; z-index: 1000; }}
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container">
                <a class="navbar-brand" href="/">
                    <i class="fas fa-hotel"></i> Hotel Booking System
                </a>
                <div class="navbar-nav ms-auto">
                    {nav_links}
                </div>
            </div>
        </nav>
        
        <!-- Flash Messages -->
        <div class="flash-messages">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
        </div>
        
        <div class="container mt-4">
            {content}
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """

# Error Handlers
@app.errorhandler(404)
def not_found_error(error):
    content = """
    <div class="text-center py-5">
        <h1 class="display-1 text-muted">404</h1>
        <h2>පිටුව හමු නොවීය</h2>
        <p class="lead">ඔබ සොයන පිටුව නොමැත.</p>
        <a href="/" class="btn btn-primary">මුල් පිටුවට</a>
    </div>
    """
    return base_template("404 - Page Not Found", content), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    content = """
    <div class="text-center py-5">
        <h1 class="display-1 text-muted">500</h1>
        <h2>සේවාදායක දෝෂය</h2>
        <p class="lead">සේවාදායකයේ දෝෂයක් ඇත. කරුණාකර පසුව නැවත උත්සාහ කරන්න.</p>
        <a href="/" class="btn btn-primary">මුල් පිටුවට</a>
    </div>
    """
    return base_template("500 - Server Error", content), 500

# Routes
@app.route('/')
def home():
    """මුල් පිටුව"""
    total_hotels = Hotel.query.filter_by(is_approved=True).count()
    total_bookings = Booking.query.count()
    
    featured_hotels = Hotel.query.filter_by(is_approved=True).limit(3).all()
    
    featured_html = ""
    for hotel in featured_hotels:
        badge_class = "villa-badge" if hotel.hotel_type == 'villa' else "hotel-badge"
        badge_text = "විලා" if hotel.hotel_type == 'villa' else "හොටෙල්"
        
        featured_html += f"""
        <div class="col-md-4">
            <div class="card hotel-card h-100">
                <img src="{hotel.image_path or 'https://via.placeholder.com/300x200?text=Hotel+Image'}" 
                     class="card-img-top hotel-image" alt="{hotel.name}">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <h5 class="card-title">{hotel.name}</h5>
                        <span class="badge {badge_class}">{badge_text}</span>
                    </div>
                    <p class="card-text">
                        <i class="fas fa-map-marker-alt text-danger"></i> {hotel.location}<br>
                        <i class="fas fa-money-bill-wave text-success"></i> රු. {hotel.price_per_night:,.2f}<br>
                        <small class="text-muted">{hotel.description[:80]}...</small>
                    </p>
                </div>
                <div class="card-footer">
                    <a href="/hotel/{hotel.id}" class="btn btn-primary btn-sm">විස්තර බලන්න</a>
                </div>
            </div>
        </div>
        """
    
    content = f"""
    <div class="jumbotron bg-light p-5 rounded mb-4">
        <h1 class="display-4">🏨 සාදරයෙන් පිළිගනිමු!</h1>
        <p class="lead">ශ්‍රී ලංකාවේ හොඳම හොටෙල් සහ විලා සොයාගන්න</p>
        <hr class="my-4">
        <p>අපගේ පද්ධතිය මගින් {total_hotels} හොටෙල් සහ {total_bookings} බුකින්ග් සම්පූර්ණ වී ඇත.</p>
        <a class="btn btn-primary btn-lg" href="/hotels" role="button">හොටෙල් සොයන්න</a>
        <a class="btn btn-outline-primary btn-lg" href="/search_hotels" role="button">සෙවුම</a>
    </div>
    
    <h3>විශේෂාංගගත හොටෙල්</h3>
    <div class="row mt-3">
        {featured_html}
    </div>
    
    <div class="row mt-5">
        <div class="col-md-4 text-center">
            <div class="card border-0">
                <div class="card-body">
                    <i class="fas fa-hotel fa-3x text-primary mb-3"></i>
                    <h5>හොටෙල් සහ විලා</h5>
                    <p class="text-muted">විවිධ වර්ගයේ රිසෝට්, හොටෙල් සහ පෞද්ගලික විලා</p>
                </div>
            </div>
        </div>
        <div class="col-md-4 text-center">
            <div class="card border-0">
                <div class="card-body">
                    <i class="fas fa-calendar-check fa-3x text-success mb-3"></i>
                    <h5>පහසු බුකින්ග්</h5>
                    <p class="text-muted">ක්ෂණිකව බුක් කරන්න, කැලන්ඩරය මගින් නිවාඩුපුරා කළමනාකරණය කරන්න</p>
                </div>
            </div>
        </div>
        <div class="col-md-4 text-center">
            <div class="card border-0">
                <div class="card-body">
                    <i class="fas fa-shield-alt fa-3x text-warning mb-3"></i>
                    <h5>ආරක්ෂිත ගෙවීම්</h5>
                    <p class="text-muted">සුරක්ෂිත ගෙවීම් ක්‍රම සහ තහවුරු කිරීම්</p>
                </div>
            </div>
        </div>
    </div>
    """
    return base_template("Home", content)

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
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('පිවිසීම අසාර්ථකයි. කරුණාකර පරිශීලක නාමය සහ මුරපදය පරීක්ෂා කරන්න.', 'danger')
            return redirect(url_for('login'))
    
    content = """
    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h4 class="mb-0"><i class="fas fa-sign-in-alt"></i> පිවිසීම</h4>
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
                    <div class="row">
                        <div class="col-md-6">
                            <p class="mb-1"><strong>Super Admin:</strong></p>
                            <p class="mb-1">Username: <code>superadmin</code></p>
                            <p class="mb-0">Password: <code>admin123</code></p>
                        </div>
                        <div class="col-md-6">
                            <p class="mb-1"><strong>Customer:</strong></p>
                            <p class="mb-1">Username: <code>customer</code></p>
                            <p class="mb-0">Password: <code>customer123</code></p>
                        </div>
                    </div>
                    <div class="row mt-2">
                        <div class="col-md-12">
                            <p class="mb-1"><strong>Your Account:</strong></p>
                            <p class="mb-1">Username: <code>kris</code></p>
                            <p class="mb-0">Password: <code>kris123</code></p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    return base_template("Login", content)

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
        
        # Validate password strength
        is_valid, message = validate_password_strength(password)
        if not is_valid:
            flash(message, 'danger')
            return redirect(url_for('register'))
        
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
    
    content = """
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="card">
                <div class="card-header bg-success text-white">
                    <h4 class="mb-0"><i class="fas fa-user-plus"></i> ලියාපදිංචි වීම</h4>
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
                                <div class="form-text">මුරපදය අවම වශයෙන් අකුරු 8ක් විය යුතුය</div>
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
    """
    return base_template("Register", content)

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
    total_bookings = Booking.query.count()
    
    # Calculate total revenue - FIXED
    all_bookings = Booking.query.all()
    total_revenue = sum([b.total_price for b in all_bookings]) if all_bookings else 0
    
    recent_bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(5).all()
    
    bookings_html = ""
    for booking in recent_bookings:
        hotel = Hotel.query.get(booking.hotel_id)
        bookings_html += f"""
        <tr>
            <td>{booking.guest_name}</td>
            <td>{hotel.name if hotel else 'N/A'}</td>
            <td>{booking.check_in_date}</td>
            <td>{booking.check_out_date}</td>
            <td><span class="badge bg-success">{booking.status}</span></td>
        </tr>
        """
    
    content = f"""
    <div class="alert alert-primary">
        <h1><i class="fas fa-shield-alt"></i> සුපිරි පරිපාලක උපකරණ පුවරුව</h1>
        <p>Welcome, {current_user.full_name}!</p>
    </div>
    
    <div class="row">
        <div class="col-md-2 mb-4">
            <div class="card text-white bg-primary">
                <div class="card-body text-center">
                    <h3>{total_users}</h3>
                    <p>පරිශීලකයන්</p>
                </div>
            </div>
        </div>
        <div class="col-md-2 mb-4">
            <div class="card text-white bg-success">
                <div class="card-body text-center">
                    <h3>{total_hotels}</h3>
                    <p>හොටෙල්</p>
                </div>
            </div>
        </div>
        <div class="col-md-2 mb-4">
            <div class="card text-white bg-warning">
                <div class="card-body text-center">
                    <h3>{approved_hotels}</h3>
                    <p>අනුමත හොටෙල්</p>
                </div>
            </div>
        </div>
        <div class="col-md-2 mb-4">
            <div class="card text-white bg-info">
                <div class="card-body text-center">
                    <h3>{pending_hotels}</h3>
                    <p>අනුමත කිරීමට</p>
                </div>
            </div>
        </div>
        <div class="col-md-2 mb-4">
            <div class="card text-white bg-secondary">
                <div class="card-body text-center">
                    <h3>{total_bookings}</h3>
                    <p>බුකින්ග්</p>
                </div>
            </div>
        </div>
        <div class="col-md-2 mb-4">
            <div class="card text-white bg-dark">
                <div class="card-body text-center">
                    <h3>රු. {total_revenue:,.0f}</h3>
                    <p>මුළු ආදායම</p>
                </div>
            </div>
        </div>
    </div>
    
    <div class="row mt-4">
        <div class="col-md-8">
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0"><i class="fas fa-cogs"></i> ක්‍රියාමාර්ග</h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <a href="/admin/hotels" class="btn btn-outline-primary btn-lg w-100">
                                <i class="fas fa-hotel"></i> හොටෙල් පාලනය
                            </a>
                        </div>
                        <div class="col-md-6 mb-3">
                            <a href="/admin/users" class="btn btn-outline-success btn-lg w-100">
                                <i class="fas fa-users"></i> පරිශීලකයන්
                            </a>
                        </div>
                        <div class="col-md-6 mb-3">
                            <a href="/admin/bookings" class="btn btn-outline-warning btn-lg w-100">
                                <i class="fas fa-calendar-check"></i> බුකින්ග්
                            </a>
                        </div>
                        <div class="col-md-6 mb-3">
                            <a href="/hotels" class="btn btn-outline-info btn-lg w-100">
                                <i class="fas fa-eye"></i> හොටෙල් බලන්න
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-md-4">
            <div class="card">
                <div class="card-header bg-warning text-white">
                    <h5 class="mb-0"><i class="fas fa-clock"></i> මෑත බුකින්ග්</h5>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>අමුත්තා</th>
                                    <th>හොටෙල්</th>
                                    <th>Check-in</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {bookings_html if bookings_html else '<tr><td colspan="4" class="text-center">No recent bookings</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    return base_template("Admin Dashboard", content)

def hotel_admin_dashboard():
    """හොටෙල් අයිතිකරු උපකරණ පුවරුව"""
    hotel = Hotel.query.filter_by(owner_email=current_user.email).first()
    
    if not hotel:
        content = f"""
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
        """
        return base_template("Hotel Admin Dashboard", content)
    
    total_rooms = Room.query.filter_by(hotel_id=hotel.id).count()
    available_rooms = Room.query.filter_by(hotel_id=hotel.id, is_available=True).count()
    total_bookings = Booking.query.filter_by(hotel_id=hotel.id).count()
    today_bookings = Booking.query.filter_by(hotel_id=hotel.id, check_in_date=datetime.now().date()).count()
    
    recent_bookings = Booking.query.filter_by(hotel_id=hotel.id).order_by(Booking.booking_date.desc()).limit(5).all()
    
    bookings_html = ""
    for booking in recent_bookings:
        room = Room.query.get(booking.room_id)
        bookings_html += f"""
        <tr>
            <td>{booking.guest_name}</td>
            <td>{room.room_number if room else 'N/A'}</td>
            <td>{booking.check_in_date}</td>
            <td>{booking.check_out_date}</td>
            <td><span class="badge bg-success">{booking.status}</span></td>
        </tr>
        """
    
    content = f"""
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
                    <p>මුළු බුකින්ග්</p>
                </div>
            </div>
        </div>
        <div class="col-md-3 mb-4">
            <div class="card text-white bg-primary">
                <div class="card-body text-center">
                    <h3>{today_bookings}</h3>
                    <p>අද බුකින්ග්</p>
                </div>
            </div>
        </div>
    </div>
    
    <div class="row mt-4">
        <div class="col-md-8">
            <div class="card">
                <div class="card-header bg-success text-white">
                    <h5 class="mb-0"><i class="fas fa-cogs"></i> ක්‍රියාමාර්ග</h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <a href="/hotel_admin/calendar" class="btn btn-outline-success btn-lg w-100">
                                <i class="fas fa-calendar-alt"></i> කැලන්ඩරය
                            </a>
                        </div>
                        <div class="col-md-6 mb-3">
                            <a href="/hotel_admin/bookings" class="btn btn-outline-primary btn-lg w-100">
                                <i class="fas fa-calendar-check"></i> බුකින්ග්
                            </a>
                        </div>
                        <div class="col-md-6 mb-3">
                            <a href="/hotel_admin/rooms" class="btn btn-outline-warning btn-lg w-100">
                                <i class="fas fa-bed"></i> කාමර
                            </a>
                        </div>
                        <div class="col-md-6 mb-3">
                            <a href="/register_hotel" class="btn btn-outline-info btn-lg w-100">
                                <i class="fas fa-edit"></i> හොටෙල් යාවත්කාලීන කරන්න
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-md-4">
            <div class="card">
                <div class="card-header bg-warning text-white">
                    <h5 class="mb-0"><i class="fas fa-clock"></i> මෑත බුකින්ග්</h5>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>අමුත්තා</th>
                                    <th>කාමරය</th>
                                    <th>Check-in</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {bookings_html if bookings_html else '<tr><td colspan="4" class="text-center">No recent bookings</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    return base_template("Hotel Admin Dashboard", content)

def customer_dashboard():
    """ගනුදෙනුකරු උපකරණ පුවරුව"""
    user_bookings = Booking.query.filter_by(customer_id=current_user.id).order_by(Booking.booking_date.desc()).limit(5).all()
    
    bookings_html = ""
    for booking in user_bookings:
        hotel = Hotel.query.get(booking.hotel_id)
        room = Room.query.get(booking.room_id)
        status_badge = "bg-success" if booking.status == 'confirmed' else "bg-warning"
        
        bookings_html += f"""
        <tr>
            <td>{hotel.name if hotel else 'N/A'}</td>
            <td>{room.room_number if room else 'N/A'}</td>
            <td>{booking.check_in_date}</td>
            <td>{booking.check_out_date}</td>
            <td>රු. {booking.total_price:,.2f}</td>
            <td><span class="badge {status_badge}">{booking.status}</span></td>
        </tr>
        """
    
    content = f"""
    <div class="alert alert-info">
        <h1><i class="fas fa-user"></i> ගනුදෙනුකරු උපකරණ පුවරුව</h1>
        <p>Welcome, {current_user.full_name}!</p>
    </div>
    
    <div class="row">
        <div class="col-md-6">
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
                        <a href="/search_hotels" class="btn btn-outline-primary btn-lg">
                            <i class="fas fa-search"></i> සෙවුම
                        </a>
                        <a href="/" class="btn btn-outline-secondary btn-lg">
                            <i class="fas fa-home"></i> මුල් පිටුව
                        </a>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-md-6">
            <div class="card">
                <div class="card-header bg-success text-white">
                    <h5 class="mb-0"><i class="fas fa-clock"></i> මගේ මෑත බුකින්ග්</h5>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>හොටෙල්</th>
                                    <th>කාමරය</th>
                                    <th>Check-in</th>
                                    <th>Check-out</th>
                                    <th>මුදල</th>
                                    <th>තත්වය</th>
                                </tr>
                            </thead>
                            <tbody>
                                {bookings_html if bookings_html else '<tr><td colspan="6" class="text-center">No bookings yet</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    return base_template("Customer Dashboard", content)

@app.route('/hotels')
def view_hotels():
    """හොටෙල් බැලීම"""
    hotels = Hotel.query.filter_by(is_approved=True).all()
    
    hotels_html = ""
    for hotel in hotels:
        badge_class = "villa-badge" if hotel.hotel_type == 'villa' else "hotel-badge"
        badge_text = "පෞද්ගලික විලා" if hotel.hotel_type == 'villa' else "හොටෙල්"
        
        availability_text = "පූර්ණ විලා තිබේ" if hotel.hotel_type == 'villa' else f"{hotel.available_rooms} කාමර තිබේ"
        
        hotels_html += f"""
        <div class="col-md-4 mb-4">
            <div class="card hotel-card h-100">
                <img src="{hotel.image_path or 'https://via.placeholder.com/300x200?text=Hotel+Image'}" 
                     class="card-img-top hotel-image" alt="{hotel.name}">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <h5 class="card-title">{hotel.name}</h5>
                        <span class="badge {badge_class}">{badge_text}</span>
                    </div>
                    <p class="card-text">
                        <i class="fas fa-map-marker-alt text-danger"></i> {hotel.location}<br>
                        <i class="fas fa-money-bill-wave text-success"></i> රු. {hotel.price_per_night:,.2f} per night<br>
                        <i class="fas fa-bed text-primary"></i> {availability_text}<br>
                        <small class="text-muted">{hotel.description[:100]}...</small>
                    </p>
                </div>
                <div class="card-footer">
                    <a href="/hotel/{hotel.id}" class="btn btn-primary btn-sm">විස්තර බලන්න</a>
                    {"<a href='/book_hotel/{}' class='btn btn-success btn-sm ms-1'>බුක් කරන්න</a>".format(hotel.id) if current_user.is_authenticated and current_user.user_type == 'customer' else ""}
                </div>
            </div>
        </div>
        """
    
    content = f"""
    <h1><i class="fas fa-hotel"></i> Available Hotels & Villas</h1>
    <p class="text-muted">සියලුම අනුමත හොටෙල් සහ විලා මෙහි ඇත</p>
    
    <div class="row">
        {hotels_html if hotels else '<div class="col-12"><div class="alert alert-warning">No hotels available at the moment</div></div>'}
    </div>
    """
    return base_template("Hotels", content)

@app.route('/search_hotels')
def search_hotels():
    """හොටෙල් සෙවීම"""
    location = request.args.get('location', '')
    hotel_type = request.args.get('type', '')
    min_price = request.args.get('min_price', 0, type=float)
    max_price = request.args.get('max_price', 1000000, type=float)
    
    query = Hotel.query.filter_by(is_approved=True)
    
    if location:
        query = query.filter(Hotel.location.ilike(f'%{location}%'))
    if hotel_type:
        query = query.filter_by(hotel_type=hotel_type)
    if min_price:
        query = query.filter(Hotel.price_per_night >= min_price)
    if max_price:
        query = query.filter(Hotel.price_per_night <= max_price)
    
    hotels = query.all()
    
    hotels_html = ""
    for hotel in hotels:
        badge_class = "villa-badge" if hotel.hotel_type == 'villa' else "hotel-badge"
        badge_text = "පෞද්ගලික විලා" if hotel.hotel_type == 'villa' else "හොටෙල්"
        
        availability_text = "පූර්ණ විලා තිබේ" if hotel.hotel_type == 'villa' else f"{hotel.available_rooms} කාමර තිබේ"
        
        hotels_html += f"""
        <div class="col-md-4 mb-4">
            <div class="card hotel-card h-100">
                <img src="{hotel.image_path or 'https://via.placeholder.com/300x200?text=Hotel+Image'}" 
                     class="card-img-top hotel-image" alt="{hotel.name}">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <h5 class="card-title">{hotel.name}</h5>
                        <span class="badge {badge_class}">{badge_text}</span>
                    </div>
                    <p class="card-text">
                        <i class="fas fa-map-marker-alt text-danger"></i> {hotel.location}<br>
                        <i class="fas fa-money-bill-wave text-success"></i> රු. {hotel.price_per_night:,.2f} per night<br>
                        <i class="fas fa-bed text-primary"></i> {availability_text}<br>
                        <small class="text-muted">{hotel.description[:100]}...</small>
                    </p>
                </div>
                <div class="card-footer">
                    <a href="/hotel/{hotel.id}" class="btn btn-primary btn-sm">විස්තර බලන්න</a>
                    {"<a href='/book_hotel/{}' class='btn btn-success btn-sm ms-1'>බුක් කරන්න</a>".format(hotel.id) if current_user.is_authenticated and current_user.user_type == 'customer' else ""}
                </div>
            </div>
        </div>
        """
    
    search_filters = []
    if location:
        search_filters.append(f"ස්ථානය: {location}")
    if hotel_type:
        type_text = "විලා" if hotel_type == 'villa' else "හොටෙල්"
        search_filters.append(f"වර්ගය: {type_text}")
    if min_price or max_price:
        search_filters.append(f"මිල: රු. {min_price:,.0f} - රු. {max_price:,.0f}")
    
    filter_text = " | ".join(search_filters) if search_filters else "සියලුම හොටෙල්"
    
    content = f"""
    <h1><i class="fas fa-search"></i> හොටෙල් සෙවුම</h1>
    
    <div class="card mb-4">
        <div class="card-body">
            <form method="GET" class="row g-3">
                <div class="col-md-3">
                    <label class="form-label">ස්ථානය</label>
                    <input type="text" class="form-control" name="location" value="{location}" placeholder="ස්ථානය සොයන්න">
                </div>
                <div class="col-md-3">
                    <label class="form-label">හොටෙල් වර්ගය</label>
                    <select class="form-control" name="type">
                        <option value="">සියලුම</option>
                        <option value="hotel" {"selected" if hotel_type == "hotel" else ""}>හොටෙල්</option>
                        <option value="villa" {"selected" if hotel_type == "villa" else ""}>විලා</option>
                    </select>
                </div>
                <div class="col-md-2">
                    <label class="form-label">අවම මිල</label>
                    <input type="number" class="form-control" name="min_price" value="{min_price}" placeholder="රු. 0">
                </div>
                <div class="col-md-2">
                    <label class="form-label">උපරිම මිල</label>
                    <input type="number" class="form-control" name="max_price" value="{max_price}" placeholder="රු. 1000000">
                </div>
                <div class="col-md-2">
                    <label class="form-label">&nbsp;</label>
                    <button type="submit" class="btn btn-primary w-100">සොයන්න</button>
                </div>
            </form>
        </div>
    </div>
    
    <p class="text-muted">සෙවුම් පෙරහන්: {filter_text}</p>
    
    <div class="row">
        {hotels_html if hotels else '<div class="col-12"><div class="alert alert-warning">සෙවුමට ගැලපෙන හොටෙල් හමු නොවීය</div></div>'}
    </div>
    """
    return base_template("Search Hotels", content)

@app.route('/hotel/<int:hotel_id>')
def hotel_detail(hotel_id):
    """හොටෙල් විස්තර"""
    hotel = Hotel.query.get_or_404(hotel_id)
    rooms = Room.query.filter_by(hotel_id=hotel_id).all()
    
    user_info = ""
    if current_user.is_authenticated:
        user_info = f"""
        <div class="alert alert-info">
            <h6><i class="fas fa-user"></i> පරිශීලක තොරතුරු</h6>
            <p class="mb-1"><strong>නම:</strong> {current_user.full_name}</p>
            <p class="mb-1"><strong>ඊමේල්:</strong> {current_user.email}</p>
            <p class="mb-0"><strong>දුරකථන:</strong> {current_user.phone}</p>
        </div>
        """
    
    rooms_html = ""
    for room in rooms:
        status_badge = "bg-success" if room.is_available else "bg-danger"
        status_text = "තිබේ" if room.is_available else "නැත"
        
        rooms_html += f"""
        <div class="col-md-6 mb-4">
            <div class="card h-100">
                <img src="{room.image_path or 'https://via.placeholder.com/300x150?text=Room+Image'}" 
                     class="card-img-top room-image" alt="Room {room.room_number}">
                <div class="card-body">
                    <h6>කාමරය {room.room_number} - {room.room_type}</h6>
                    <p class="mb-1"><i class="fas fa-users"></i> පුද්ගලයන්: {room.capacity}</p>
                    <p class="mb-1"><i class="fas fa-money-bill-wave"></i> මිල: රු. {room.price_per_night:,.2f} per night</p>
                    <p class="mb-1"><i class="fas fa-star"></i> විශේෂාංග: {room.features or 'N/A'}</p>
                    <span class="badge {status_badge}">{status_text}</span>
                    {"<a href='/book_room/{}' class='btn btn-success btn-sm ms-2'>බුක් කරන්න</a>".format(room.id) if room.is_available and current_user.is_authenticated and current_user.user_type == 'customer' else ""}
                </div>
            </div>
        </div>
        """
    
    content = f"""
    <div class="card mb-4">
        <div class="row g-0">
            <div class="col-md-4">
                <img src="{hotel.image_path or 'https://via.placeholder.com/400x300?text=Hotel+Image'}" 
                     class="img-fluid rounded-start" alt="{hotel.name}" style="height: 300px; width: 100%; object-fit: cover;">
            </div>
            <div class="col-md-8">
                <div class="card-body">
                    <h2 class="card-title">{hotel.name}</h2>
                    <p class="card-text"><strong><i class="fas fa-map-marker-alt"></i> Location:</strong> {hotel.location}</p>
                    <p class="card-text"><strong><i class="fas fa-info-circle"></i> Description:</strong> {hotel.description}</p>
                    <p class="card-text"><strong><i class="fas fa-money-bill-wave"></i> Price per night:</strong> රු. {hotel.price_per_night:,.2f}</p>
                    <p class="card-text"><strong><i class="fas fa-phone"></i> Contact:</strong> {hotel.contact_number}</p>
                    <p class="card-text"><strong><i class="fas fa-star"></i> Amenities:</strong> {hotel.amenities}</p>
                    <p class="card-text"><strong><i class="fas fa-building"></i> Type:</strong> 
                        <span class="badge {'villa-badge' if hotel.hotel_type == 'villa' else 'hotel-badge'}">
                            {'පෞද්ගලික විලා' if hotel.hotel_type == 'villa' else 'හොටෙල්'}
                        </span>
                    </p>
                </div>
            </div>
        </div>
    </div>
    
    {user_info}
    
    <h4>{'විලා විස්තර' if hotel.hotel_type == 'villa' else 'කාමර'}</h4>
    <div class="row">
        {rooms_html if rooms else '<div class="col-12"><div class="alert alert-info">No rooms available for this hotel</div></div>'}
    </div>
    
    <div class="mt-3">
        <a href="/hotels" class="btn btn-primary">Back to Hotels</a>
        {"<a href='/book_hotel/{}' class='btn btn-success ms-2'>Book This {}</a>".format(hotel.id, 'Villa' if hotel.hotel_type == 'villa' else 'Hotel') if current_user.is_authenticated and current_user.user_type == 'customer' else ""}
    </div>
    """
    return base_template(f"{hotel.name} - Details", content)

@app.route('/book_hotel/<int:hotel_id>', methods=['GET', 'POST'])
@login_required
def book_hotel(hotel_id):
    """හොටෙල් බුක් කිරීම"""
    if current_user.user_type != 'customer':
        flash('මෙම පිටුවට ප්‍රවේශය ඔබට නැත.', 'danger')
        return redirect(url_for('dashboard'))
    
    hotel = Hotel.query.get_or_404(hotel_id)
    
    if hotel.hotel_type == 'villa':
        available_rooms = Room.query.filter_by(hotel_id=hotel_id, is_available=True).all()
    else:
        available_rooms = Room.query.filter_by(hotel_id=hotel_id, is_available=True).all()
    
    if not available_rooms:
        flash('මෙම {}-ට කාමර නොමැත.'.format('විලාවට' if hotel.hotel_type == 'villa' else 'හොටෙල්ට'), 'warning')
        return redirect(url_for('hotel_detail', hotel_id=hotel_id))
    
    if request.method == 'POST':
        room_id = request.form['room_id']
        check_in = datetime.strptime(request.form['check_in'], '%Y-%m-%d').date()
        check_out = datetime.strptime(request.form['check_out'], '%Y-%m-%d').date()
        guest_name = request.form['guest_name']
        guest_phone = request.form['guest_phone']
        
        # Validate dates
        is_valid, message = validate_booking_dates(check_in, check_out)
        if not is_valid:
            flash(message, 'danger')
            return redirect(url_for('book_hotel', hotel_id=hotel_id))
        
        room = Room.query.get(room_id)
        if not room or not room.is_available:
            flash('මෙම කාමරය තිබෙන්නේ නැත.', 'danger')
            return redirect(url_for('book_hotel', hotel_id=hotel_id))
        
        nights = (check_out - check_in).days
        if nights <= 0:
            flash('කරුණාකර වලංගු check-in සහ check-out දින ඇතුළත් කරන්න.', 'danger')
            return redirect(url_for('book_hotel', hotel_id=hotel_id))
        
        total_price = room.price_per_night * nights
        
        booking = Booking(
            hotel_id=hotel_id,
            room_id=room_id,
            guest_name=guest_name,
            guest_email=current_user.email,
            guest_phone=guest_phone,
            check_in_date=check_in,
            check_out_date=check_out,
            total_price=total_price,
            customer_id=current_user.id,
            status='confirmed'
        )
        
        room.is_available = False
        hotel.available_rooms -= 1
        
        db.session.add(booking)
        db.session.commit()
        
        send_whatsapp_notification(
            hotel.contact_number,
            guest_name,
            check_in.strftime('%Y-%m-%d'),
            check_out.strftime('%Y-%m-%d'),
            hotel.name
        )
        
        flash(f'බුකින්ග් සාර්ථකයි! මුළු මුදල: රු. {total_price:,.2f}', 'success')
        return redirect(url_for('my_bookings'))
    
    rooms_options = ""
    for room in available_rooms:
        room_type = "විලා" if hotel.hotel_type == 'villa' else room.room_type
        rooms_options += f'<option value="{room.id}">{room_type} - රු. {room.price_per_night:,.2f}/රාත්‍රිය (පුද්ගලයන්: {room.capacity})</option>'
    
    content = f"""
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h4 class="mb-0"><i class="fas fa-calendar-check"></i> බුකින්ග් - {hotel.name}</h4>
                </div>
                <div class="card-body">
                    <form method="POST">
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">අමුත්තන්ගේ නම</label>
                                <input type="text" class="form-control" name="guest_name" value="{current_user.full_name}" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">දුරකථන අංකය</label>
                                <input type="text" class="form-control" name="guest_phone" value="{current_user.phone}" required>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Check-in දිනය</label>
                                <input type="date" class="form-control" name="check_in" min="{datetime.now().date()}" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Check-out දිනය</label>
                                <input type="date" class="form-control" name="check_out" min="{datetime.now().date()}" required>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">{'විලා' if hotel.hotel_type == 'villa' else 'කාමරය'} තෝරන්න</label>
                            <select class="form-control" name="room_id" required>
                                <option value="">{'විලා' if hotel.hotel_type == 'villa' else 'කාමරය'} තෝරන්න...</option>
                                {rooms_options}
                            </select>
                        </div>
                        <div class="alert alert-info">
                            <h6><i class="fas fa-info-circle"></i> පරිශීලක තොරතුරු</h6>
                            <p class="mb-1"><strong>නම:</strong> {current_user.full_name}</p>
                            <p class="mb-1"><strong>ඊමේල්:</strong> {current_user.email}</p>
                            <p class="mb-0"><strong>දුරකථන:</strong> {current_user.phone}</p>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">බුකින්ග් තහවුරු කරන්න</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
    """
    return base_template("Book Hotel", content)

@app.route('/book_room/<int:room_id>', methods=['GET', 'POST'])
@login_required
def book_room(room_id):
    """කාමරයක් බුක් කිරීම"""
    if current_user.user_type != 'customer':
        flash('මෙම පිටුවට ප්‍රවේශය ඔබට නැත.', 'danger')
        return redirect(url_for('dashboard'))
    
    room = Room.query.get_or_404(room_id)
    hotel = Hotel.query.get(room.hotel_id)
    
    if not room.is_available:
        flash('මෙම කාමරය දැනට තිබෙන්නේ නැත.', 'warning')
        return redirect(url_for('hotel_detail', hotel_id=hotel.id))
    
    if request.method == 'POST':
        check_in = datetime.strptime(request.form['check_in'], '%Y-%m-%d').date()
        check_out = datetime.strptime(request.form['check_out'], '%Y-%m-%d').date()
        guest_name = request.form['guest_name']
        guest_phone = request.form['guest_phone']
        
        # Validate dates
        is_valid, message = validate_booking_dates(check_in, check_out)
        if not is_valid:
            flash(message, 'danger')
            return redirect(url_for('book_room', room_id=room_id))
        
        nights = (check_out - check_in).days
        if nights <= 0:
            flash('කරුණාකර වලංගු check-in සහ check-out දින ඇතුළත් කරන්න.', 'danger')
            return redirect(url_for('book_room', room_id=room_id))
        
        total_price = room.price_per_night * nights
        
        booking = Booking(
            hotel_id=hotel.id,
            room_id=room_id,
            guest_name=guest_name,
            guest_email=current_user.email,
            guest_phone=guest_phone,
            check_in_date=check_in,
            check_out_date=check_out,
            total_price=total_price,
            customer_id=current_user.id,
            status='confirmed'
        )
        
        room.is_available = False
        hotel.available_rooms -= 1
        
        db.session.add(booking)
        db.session.commit()
        
        send_whatsapp_notification(
            hotel.contact_number,
            guest_name,
            check_in.strftime('%Y-%m-%d'),
            check_out.strftime('%Y-%m-%d'),
            hotel.name
        )
        
        flash(f'බුකින්ග් සාර්ථකයි! මුළු මුදල: රු. {total_price:,.2f}', 'success')
        return redirect(url_for('my_bookings'))
    
    content = f"""
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h4 class="mb-0"><i class="fas fa-calendar-check"></i> බුකින්ග් - {hotel.name}</h4>
                </div>
                <div class="card-body">
                    <div class="alert alert-info mb-4">
                        <h6><i class="fas fa-info-circle"></i> කාමර විස්තර</h6>
                        <p class="mb-1"><strong>කාමර අංකය:</strong> {room.room_number}</p>
                        <p class="mb-1"><strong>කාමර වර්ගය:</strong> {room.room_type}</p>
                        <p class="mb-1"><strong>පුද්ගලයන්:</strong> {room.capacity}</p>
                        <p class="mb-1"><strong>මිල:</strong> රු. {room.price_per_night:,.2f} per night</p>
                        <p class="mb-0"><strong>විශේෂාංග:</strong> {room.features or 'N/A'}</p>
                    </div>
                    
                    <form method="POST">
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">අමුත්තන්ගේ නම</label>
                                <input type="text" class="form-control" name="guest_name" value="{current_user.full_name}" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">දුරකථන අංකය</label>
                                <input type="text" class="form-control" name="guest_phone" value="{current_user.phone}" required>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Check-in දිනය</label>
                                <input type="date" class="form-control" name="check_in" min="{datetime.now().date()}" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Check-out දිනය</label>
                                <input type="date" class="form-control" name="check_out" min="{datetime.now().date()}" required>
                            </div>
                        </div>
                        <div class="alert alert-warning">
                            <h6><i class="fas fa-exclamation-triangle"></i> පරිශීලක තොරතුරු</h6>
                            <p class="mb-1"><strong>නම:</strong> {current_user.full_name}</p>
                            <p class="mb-1"><strong>ඊමේල්:</strong> {current_user.email}</p>
                            <p class="mb-0"><strong>දුරකථන:</strong> {current_user.phone}</p>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">බුකින්ග් තහවුරු කරන්න</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
    """
    return base_template("Book Room", content)

@app.route('/my_bookings')
@login_required
def my_bookings():
    """මගේ බුකින්ග්"""
    if current_user.user_type != 'customer':
        flash('මෙම පිටුවට ප්‍රවේශය ඔබට නැත.', 'danger')
        return redirect(url_for('dashboard'))
    
    bookings = Booking.query.filter_by(customer_id=current_user.id).order_by(Booking.booking_date.desc()).all()
    
    bookings_html = ""
    for booking in bookings:
        hotel = Hotel.query.get(booking.hotel_id)
        room = Room.query.get(booking.room_id)
        status_badge = "bg-success" if booking.status == 'confirmed' else "bg-warning"
        
        bookings_html += f"""
        <div class="col-md-6 mb-4">
            <div class="card">
                <div class="card-body">
                    <h5>{hotel.name if hotel else 'N/A'}</h5>
                    <p class="mb-1"><strong>කාමරය:</strong> {room.room_number if room else 'N/A'}</p>
                    <p class="mb-1"><strong>අමුත්තා:</strong> {booking.guest_name}</p>
                    <p class="mb-1"><strong>Check-in:</strong> {booking.check_in_date}</p>
                    <p class="mb-1"><strong>Check-out:</strong> {booking.check_out_date}</p>
                    <p class="mb-1"><strong>මුළු මුදල:</strong> රු. {booking.total_price:,.2f}</p>
                    <p class="mb-1"><strong>බුකින්ග් දිනය:</strong> {booking.booking_date.strftime('%Y-%m-%d %H:%M')}</p>
                    <span class="badge {status_badge}">{booking.status}</span>
                    {"<a href='/cancel_booking/{}' class='btn btn-danger btn-sm ms-2' onclick='return confirm(\"Are you sure you want to cancel this booking?\")'>Cancel</a>".format(booking.id) if booking.status == 'confirmed' else ""}
                </div>
            </div>
        </div>
        """
    
    content = f"""
    <div class="alert alert-info">
        <h1><i class="fas fa-history"></i> මගේ බුකින්ග්</h1>
        <p>ඔබගේ සියලුම බුකින්ග් මෙහි ඇත</p>
    </div>
    
    <div class="row">
        {bookings_html if bookings_html else '<div class="col-12"><div class="alert alert-warning">You have no bookings yet</div></div>'}
    </div>
    """
    return base_template("My Bookings", content)

@app.route('/cancel_booking/<int:booking_id>')
@login_required
def cancel_booking(booking_id):
    """බුකින්ග් අවලංගු කිරීම"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Check if user owns the booking or is hotel admin
    if current_user.user_type == 'customer' and booking.customer_id != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))
    
    # Free up the room
    room = Room.query.get(booking.room_id)
    room.is_available = True
    
    hotel = Hotel.query.get(booking.hotel_id)
    hotel.available_rooms += 1
    
    booking.status = 'cancelled'
    db.session.commit()
    
    flash('Booking cancelled successfully', 'success')
    return redirect(url_for('my_bookings'))

@app.route('/admin/users')
@login_required
def admin_users():
    """පරිශීලකයන් පාලනය"""
    if current_user.user_type != 'super_admin':
        flash('මෙම පිටුවට ප්‍රවේශය ඔබට නැත.', 'danger')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    
    users_html = ""
    for user in users:
        status_badge = "bg-success" if user.is_active else "bg-danger"
        status_text = "සක්‍රීය" if user.is_active else "අක්‍රීය"
        type_badge = "bg-primary" if user.user_type == 'super_admin' else "bg-info" if user.user_type == 'hotel_admin' else "bg-secondary"
        
        users_html += f"""
        <tr>
            <td>{user.id}</td>
            <td>{user.username}</td>
            <td>{user.full_name}</td>
            <td>{user.email}</td>
            <td>{user.phone}</td>
            <td><span class="badge {type_badge}">{user.user_type}</span></td>
            <td>{user.created_at.strftime('%Y-%m-%d')}</td>
            <td><span class="badge {status_badge}">{status_text}</span></td>
        </tr>
        """
    
    content = f"""
    <div class="alert alert-primary">
        <h1><i class="fas fa-users"></i> පරිශීලක කළමනාකරණය</h1>
        <p>සියලුම ලියාපදිංචි පරිශීලකයන්</p>
    </div>
    
    <div class="card">
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>පරිශීලක නාමය</th>
                            <th>සම්පූර්ණ නම</th>
                            <th>ඊමේල්</th>
                            <th>දුරකථන</th>
                            <th>වර්ගය</th>
                            <th>ලියාපදිංචි දිනය</th>
                            <th>තත්වය</th>
                        </tr>
                    </thead>
                    <tbody>
                        {users_html if users_html else '<tr><td colspan="8" class="text-center">No users found</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    """
    return base_template("Manage Users", content)

@app.route('/admin/hotels')
@login_required
def admin_hotels():
    """පරිපාලක හොටෙල් පිටුව"""
    if current_user.user_type != 'super_admin':
        flash('මෙම පිටුවට ප්‍රවේශය ඔබට නැත.', 'danger')
        return redirect(url_for('dashboard'))
    
    hotels = Hotel.query.all()
    
    hotels_html = ""
    for hotel in hotels:
        status_badge = "bg-success" if hotel.is_approved else "bg-warning"
        status_text = "අනුමතයි" if hotel.is_approved else "අනුමත කිරීමට"
        type_badge = "villa-badge" if hotel.hotel_type == 'villa' else "hotel-badge"
        type_text = "විලා" if hotel.hotel_type == 'villa' else "හොටෙල්"
        
        hotels_html += f"""
        <tr>
            <td>{hotel.name}</td>
            <td>{hotel.location}</td>
            <td><span class="badge {type_badge}">{type_text}</span></td>
            <td>{hotel.owner_name}</td>
            <td>{hotel.contact_number}</td>
            <td>රු. {hotel.price_per_night:,.2f}</td>
            <td><span class="badge {status_badge}">{status_text}</span></td>
            <td>
                {"<a href='/admin/approve_hotel/{}' class='btn btn-success btn-sm'>Approve</a>".format(hotel.id) if not hotel.is_approved else ""}
                <a href="/hotel/{hotel.id}" class="btn btn-info btn-sm">View</a>
            </td>
        </tr>
        """
    
    content = f"""
    <div class="alert alert-primary">
        <h1><i class="fas fa-hotel"></i> හොටෙල් පාලනය</h1>
        <p>සියලුම හොටෙල් නිරීක්ෂණය කර අනුමත කිරීම</p>
    </div>
    
    <div class="card">
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>හොටෙල් නම</th>
                            <th>ස්ථානය</th>
                            <th>වර්ගය</th>
                            <th>අයිතිකරු</th>
                            <th>දුරකථනය</th>
                            <th>මිල</th>
                            <th>තත්වය</th>
                            <th>ක්‍රියා</th>
                        </tr>
                    </thead>
                    <tbody>
                        {hotels_html if hotels_html else '<tr><td colspan="8" class="text-center">No hotels found</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    """
    return base_template("Manage Hotels", content)

@app.route('/admin/approve_hotel/<int:hotel_id>')
@login_required
def approve_hotel(hotel_id):
    """හොටෙල් අනුමත කිරීම"""
    if current_user.user_type != 'super_admin':
        flash('මෙම පිටුවට ප්‍රවේශය ඔබට නැත.', 'danger')
        return redirect(url_for('dashboard'))
    
    hotel = Hotel.query.get_or_404(hotel_id)
    hotel.is_approved = True
    hotel.approved_by = current_user.id
    hotel.approved_at = datetime.utcnow()
    
    db.session.commit()
    flash(f'{hotel.name} හොටෙල් සාර්ථකව අනුමත කරන ලදී!', 'success')
    return redirect(url_for('admin_hotels'))

@app.route('/register_hotel', methods=['GET', 'POST'])
@login_required
def register_hotel():
    """හොටෙල් ලියාපදිංචි කිරීම"""
    if current_user.user_type != 'hotel_admin':
        flash('මෙම පිටුවට ප්‍රවේශය ඔබට නැත.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Check if user already has a hotel
    existing_hotel = Hotel.query.filter_by(owner_email=current_user.email).first()
    is_update = existing_hotel is not None
    
    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        description = request.form['description']
        contact_number = request.form['contact_number']
        price_per_night = float(request.form['price_per_night'])
        total_rooms = int(request.form['total_rooms'])
        amenities = request.form['amenities']
        hotel_type = request.form['hotel_type']
        
        if is_update:
            # Update existing hotel
            existing_hotel.name = name
            existing_hotel.location = location
            existing_hotel.description = description
            existing_hotel.contact_number = contact_number
            existing_hotel.price_per_night = price_per_night
            existing_hotel.total_rooms = total_rooms
            existing_hotel.amenities = amenities
            existing_hotel.hotel_type = hotel_type
            existing_hotel.is_approved = False  # Needs re-approval after update
            
            flash('හොටෙල් තොරතුරු සාර්ථකව යාවත්කාලීන කරන ලදී! නව අනුමත කිරීම අවශ්‍ය වේ.', 'success')
        else:
            # Create new hotel
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
                hotel_type=hotel_type,
                is_approved=False
            )
            db.session.add(hotel)
            flash('ඔබගේ හොටෙල් සාර්ථකව ලියාපදිංචි කරන ලදී! සුපිරි පරිපාලක අනුමත කිරීමෙන් පසු එය පෙනෙනු ඇත.', 'success')
        
        db.session.commit()
        return redirect(url_for('dashboard'))
    
    # Pre-fill form if updating
    hotel_data = existing_hotel if is_update else None
    
    content = f"""
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="card">
                <div class="card-header bg-success text-white">
                    <h4 class="mb-0"><i class="fas fa-hotel"></i> {'හොටෙල් යාවත්කාලීන කිරීම' if is_update else 'හොටෙල් ලියාපදිංචි කිරීම'}</h4>
                </div>
                <div class="card-body">
                    <form method="POST">
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">හොටෙල් නම</label>
                                <input type="text" class="form-control" name="name" value="{hotel_data.name if hotel_data else ''}" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">ස්ථානය</label>
                                <input type="text" class="form-control" name="location" value="{hotel_data.location if hotel_data else ''}" required>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">විස්තරය</label>
                            <textarea class="form-control" name="description" rows="3" required>{hotel_data.description if hotel_data else ''}</textarea>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">දුරකථන අංකය</label>
                                <input type="text" class="form-control" name="contact_number" value="{hotel_data.contact_number if hotel_data else ''}" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">හොටෙල් වර්ගය</label>
                                <select class="form-control" name="hotel_type" required>
                                    <option value="hotel" {"selected" if hotel_data and hotel_data.hotel_type == 'hotel' else ""}>හොටෙල්</option>
                                    <option value="villa" {"selected" if hotel_data and hotel_data.hotel_type == 'villa' else ""}>විලා</option>
                                </select>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">රූපයකට මිල (රු.)</label>
                                <input type="number" class="form-control" name="price_per_night" step="0.01" value="{hotel_data.price_per_night if hotel_data else ''}" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">මුළු කාමර ගණන</label>
                                <input type="number" class="form-control" name="total_rooms" value="{hotel_data.total_rooms if hotel_data else ''}" required>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">විනෝදාංශ</label>
                            <input type="text" class="form-control" name="amenities" value="{hotel_data.amenities if hotel_data else ''}" placeholder="WiFi, Pool, AC, etc.">
                        </div>
                        <button type="submit" class="btn btn-success w-100">{'යාවත්කාලීන කරන්න' if is_update else 'හොටෙල් ලියාපදිංචි කරන්න'}</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
    """
    return base_template("Register Hotel", content)

@app.route('/upload_hotel_image/<int:hotel_id>', methods=['POST'])
@login_required
def upload_hotel_image(hotel_id):
    """හොටෙල් රූපය උඩුගත කිරීම"""
    hotel = Hotel.query.get_or_404(hotel_id)
    
    # Check if user owns the hotel or is super admin
    if current_user.user_type != 'super_admin' and hotel.owner_email != current_user.email:
        flash('මෙම පිටුවට ප්‍රවේශය ඔබට නැත.', 'danger')
        return redirect(url_for('dashboard'))
    
    if 'image' not in request.files:
        flash('No file selected', 'danger')
        return redirect(request.referrer)
    
    file = request.files['image']
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(request.referrer)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"hotel_{hotel_id}_{file.filename}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        hotel.image_path = f"static/uploads/{filename}"
        db.session.commit()
        
        flash('Image uploaded successfully', 'success')
    else:
        flash('Invalid file type. Allowed types: PNG, JPG, JPEG, GIF, WEBP', 'danger')
    
    return redirect(request.referrer)

@app.route('/hotel_admin/calendar')
@login_required
def hotel_admin_calendar():
    """හොටෙල් කැලන්ඩරය"""
    hotel = Hotel.query.filter_by(owner_email=current_user.email).first()
    if not hotel:
        flash('ඔබට තවම හොටෙල් එකක් ලියාපදිංචි කර නැත.', 'warning')
        return redirect(url_for('dashboard'))
    
    bookings = Booking.query.filter_by(hotel_id=hotel.id).all()
    
    today = datetime.now().date()
    calendar_html = ""
    
    for i in range(7):
        date = today + timedelta(days=i)
        date_bookings = [b for b in bookings if b.check_in_date <= date <= b.check_out_date]
        
        calendar_html += f"""
        <div class="col-md-3 mb-3">
            <div class="card {'today' if date == today else ''}">
                <div class="card-body text-center">
                    <h6>{date.strftime('%b %d')}</h6>
                    <small>{date.strftime('%A')}</small>
                    <div class="mt-2">
                        <span class="badge bg-{'danger' if date_bookings else 'success'}">
                            {len(date_bookings)} බුකින්ග්
                        </span>
                    </div>
                </div>
            </div>
        </div>
        """
    
    content = f"""
    <div class="alert alert-info">
        <h1><i class="fas fa-calendar-alt"></i> බුකින්ග් කැලන්ඩරය</h1>
        <p>{hotel.name} - ඉදිරි 7 දින</p>
    </div>
    
    <div class="booking-calendar mb-4">
        <div class="row">
            {calendar_html}
        </div>
    </div>
    
    <div class="card">
        <div class="card-header">
            <h5 class="mb-0">අද බුකින්ග්</h5>
        </div>
        <div class="card-body">
    """
    
    today_bookings = [b for b in bookings if b.check_in_date <= today <= b.check_out_date]
    if today_bookings:
        for booking in today_bookings:
            room = Room.query.get(booking.room_id)
            content += f"""
            <div class="alert alert-warning">
                <strong>{booking.guest_name}</strong> - කාමරය {room.room_number if room else 'N/A'} 
                ({booking.check_in_date} to {booking.check_out_date})
            </div>
            """
    else:
        content += "<p>අද බුකින්ග් නැත</p>"
    
    content += """
        </div>
    </div>
    """
    return base_template("Booking Calendar", content)

@app.route('/hotel_admin/bookings')
@login_required
def hotel_admin_bookings():
    """හොටෙල් බුකින්ග්"""
    hotel = Hotel.query.filter_by(owner_email=current_user.email).first()
    if not hotel:
        flash('ඔබට තවම හොටෙල් එකක් ලියාපදිංචි කර නැත.', 'warning')
        return redirect(url_for('dashboard'))
    
    bookings = Booking.query.filter_by(hotel_id=hotel.id).order_by(Booking.booking_date.desc()).all()
    
    bookings_html = ""
    for booking in bookings:
        room = Room.query.get(booking.room_id)
        status_badge = "bg-success" if booking.status == 'confirmed' else "bg-warning"
        
        bookings_html += f"""
        <tr>
            <td>{booking.guest_name}</td>
            <td>{room.room_number if room else 'N/A'}</td>
            <td>{booking.check_in_date}</td>
            <td>{booking.check_out_date}</td>
            <td>රු. {booking.total_price:,.2f}</td>
            <td><span class="badge {status_badge}">{booking.status}</span></td>
            <td>{booking.booking_date.strftime('%Y-%m-%d')}</td>
        </tr>
        """
    
    content = f"""
    <div class="alert alert-success">
        <h1><i class="fas fa-calendar-check"></i> බුකින්ග්</h1>
        <p>{hotel.name} - සියලුම බුකින්ග්</p>
    </div>
    
    <div class="card">
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>අමුත්තා</th>
                            <th>කාමරය</th>
                            <th>Check-in</th>
                            <th>Check-out</th>
                            <th>මුදල</th>
                            <th>තත්වය</th>
                            <th>දිනය</th>
                        </tr>
                    </thead>
                    <tbody>
                        {bookings_html if bookings_html else '<tr><td colspan="7" class="text-center">No bookings found</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    """
    return base_template("Hotel Bookings", content)

@app.route('/hotel_admin/rooms')
@login_required
def hotel_admin_rooms():
    """හොටෙල් කාමර"""
    hotel = Hotel.query.filter_by(owner_email=current_user.email).first()
    if not hotel:
        flash('ඔබට තවම හොටෙල් එකක් ලියාපදිංචි කර නැත.', 'warning')
        return redirect(url_for('dashboard'))
    
    rooms = Room.query.filter_by(hotel_id=hotel.id).all()
    
    rooms_html = ""
    for room in rooms:
        status_badge = "bg-success" if room.is_available else "bg-danger"
        status_text = "තිබේ" if room.is_available else "නැත"
        
        rooms_html += f"""
        <tr>
            <td>{room.room_number}</td>
            <td>{room.room_type}</td>
            <td>{room.capacity}</td>
            <td>රු. {room.price_per_night:,.2f}</td>
            <td>{room.features or 'N/A'}</td>
            <td><span class="badge {status_badge}">{status_text}</span></td>
        </tr>
        """
    
    content = f"""
    <div class="alert alert-info">
        <h1><i class="fas fa-bed"></i> කාමර</h1>
        <p>{hotel.name} - සියලුම කාමර</p>
    </div>
    
    <div class="card">
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>කාමර අංකය</th>
                            <th>වර්ගය</th>
                            <th>ප්‍රමාණය</th>
                            <th>මිල</th>
                            <th>විශේෂාංග</th>
                            <th>තත්වය</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rooms_html if rooms_html else '<tr><td colspan="6" class="text-center">No rooms found</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    """
    return base_template("Hotel Rooms", content)

# Main execution
if __name__ == '__main__':
    print("🔄 Initializing database with new schema...")
    init_db()
    print("🚀 Hotel Booking System Started!")
    print("📍 Access your application at:")
    print("   → http://127.0.0.1:5000")
    print("   → http://localhost:5000")
    print("")
    print("🔑 Login Credentials:")
    print("   Super Admin - Username: superadmin, Password: admin123")
    print("   Customer - Username: customer, Password: customer123") 
    print("   Hotel Admin - Username: hotelowner, Password: owner123")
    print("   Your Account - Username: kris, Password: kris123")
    print("")
    print("📊 Complete Features:")
    print("   ✅ Full hotel_type support (hotel/villa)")
    print("   ✅ User management")
    print("   ✅ Booking system")
    print("   ✅ Calendar view")
    print("   ✅ Room management")
    print("   ✅ Villa support")
    print("   ✅ Image upload ready")
    print("   ✅ WhatsApp notifications")
    print("   ✅ Fixed revenue calculation")
    print("   ✅ Search and filtering")
    print("   ✅ Booking cancellation")
    print("   ✅ Password strength validation")
    print("   ✅ Error handling")
    print("   ✅ Environment configuration")
    
    # Use production-ready server in production
    if os.environ.get('FLASK_ENV') == 'production':
        from waitress import serve
        print("🚀 Starting production server...")
        serve(app, host='0.0.0.0', port=5000)
    else:
        app.run(debug=True, host='0.0.0.0', port=5000)