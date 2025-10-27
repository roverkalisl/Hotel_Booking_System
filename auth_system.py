from models import Session, User, Hotel
from datetime import date

class AuthSystem:
    def __init__(self):
        self.session = Session()
        self.current_user = None
    
    def create_super_admin(self):
        """Super admin user create කිරීම"""
        # Check if super admin already exists
        existing_admin = self.session.query(User).filter(User.user_type == 'super_admin').first()
        if existing_admin:
            return existing_admin
        
        super_admin = User(
            username='superadmin',
            email='super@admin.com',
            user_type='super_admin',
            full_name='System Super Administrator',
            phone='0112345678'
        )
        super_admin.set_password('admin123')
        
        self.session.add(super_admin)
        self.session.commit()
        print("✅ Super admin account created successfully!")
        return super_admin
    
    def register_user(self):
        """නව user register කිරීම"""
        print("\n" + "="*50)
        print("නව ගිණුම ලියාපදිංචි කිරීම")
        print("="*50)
        
        print("ඔබගේ ගිණුමේ වර්ගය තෝරන්න:")
        print("1. හොටෙල් අයිතිකරු (Hotel Admin)")
        print("2. ගනුදෙනුකරු (Customer)")
        
        user_type_choice = input("තේරීම (1/2): ")
        
        if user_type_choice == '1':
            user_type = 'hotel_admin'
        elif user_type_choice == '2':
            user_type = 'customer'
        else:
            print("❌ වලංගු නොවන තේරීම!")
            return None
        
        username = input("පරිශීලක නාමය: ")
        password = input("මුරපදය: ")
        email = input("ඊමේල්: ")
        full_name = input("සම්පූර්ණ නම: ")
        phone = input("දුරකථන අංකය: ")
        
        # Check if username or email already exists
        existing_user = self.session.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            print("❌ පරිශීලක නාමය හෝ ඊමේල් දැනටමත් පවතී!")
            return None
        
        user = User(
            username=username,
            email=email,
            user_type=user_type,
            full_name=full_name,
            phone=phone
        )
        user.set_password(password)
        
        self.session.add(user)
        self.session.commit()
        
        print(f"✅ {full_name} ගිණුම සාර්ථකව ලියාපදිංචි කරන ලදී!")
        return user
    
    def login(self):
        """User login කිරීම"""
        print("\n" + "="*50)
        print("පද්ධතියට පිවිසීම")
        print("="*50)
        
        username = input("පරිශීලක නාමය: ")
        password = input("මුරපදය: ")
        
        user = self.session.query(User).filter(
            User.username == username,
            User.is_active == True
        ).first()
        
        if user and user.check_password(password):
            self.current_user = user
            print(f"✅ සාර්ථකව පිවිසිය! පිළිගනිමු {user.full_name}!")
            return user
        else:
            print("❌ වලංගු නොවන පරිශීලක නාමය හෝ මුරපදය!")
            return None
    
    def logout(self):
        """Logout කිරීම"""
        if self.current_user:
            print(f"👋 {self.current_user.full_name} පද්ධතියෙන් පිටවෙමින්...")
            self.current_user = None
        else:
            print("❌ කිසිවෙකු පිවිස නොමැත!")
    
    def get_current_user(self):
        """වර්තමාන user ලබා ගැනීම"""
        return self.current_user
    
    def has_permission(self, required_type):
        """Permissions check කිරීම"""
        if not self.current_user:
            return False
        
        if self.current_user.user_type == 'super_admin':
            return True
        
        if required_type == 'hotel_admin' and self.current_user.user_type in ['hotel_admin', 'super_admin']:
            return True
        
        if required_type == 'customer' and self.current_user.user_type in ['customer', 'super_admin']:
            return True
        
        return False
    
    def close(self):
        """Session close කිරීම"""
        self.session.close()