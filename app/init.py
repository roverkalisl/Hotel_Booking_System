from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    login_manager.init_app(app)
    
    from app.auth import auth as auth_blueprint
    from app.routes import main as main_blueprint
    
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(main_blueprint)
    
    with app.app_context():
        db.create_all()
        # Create super admin if not exists
        from app.models import User
        from werkzeug.security import generate_password_hash
        
        super_admin = User.query.filter_by(user_type='super_admin').first()
        if not super_admin:
            super_admin = User(
                username='superadmin',
                email='super@admin.com',
                password=generate_password_hash('admin123'),
                user_type='super_admin',
                full_name='System Super Administrator',
                phone='0112345678',
                is_active=True
            )
            db.session.add(super_admin)
            db.session.commit()
    
    return app