from models import Session, User, Hotel, Booking
from datetime import date

class SuperAdminSystem:
    def __init__(self, auth_system):
        self.session = Session()
        self.auth = auth_system
    
    def dashboard(self):
        """Super admin dashboard"""
        while True:
            print("\n" + "="*60)
            print("🛡️ SUPER ADMIN DASHBOARD")
            print("="*60)
            print("1. 👥 පරිශීලකයන් පාලනය")
            print("2. 🏨 හොටෙල් අනුමත කිරීම")
            print("3. 📊 පද්ධති සංඛ්‍යාලේඛන")
            print("4. 📋 සියලුම හොටෙල්")
            print("5. 📅 සියලුම බුකින්ග්")
            print("6. 🔙 ප්‍රධාන මෙනුව")
            
            choice = input("\nතේරීම (1-6): ")
            
            if choice == '1':
                self.manage_users()
            elif choice == '2':
                self.approve_hotels()
            elif choice == '3':
                self.view_statistics()
            elif choice == '4':
                self.view_all_hotels()
            elif choice == '5':
                self.view_all_bookings()
            elif choice == '6':
                break
            else:
                print("❌ වලංගු නොවන තේරීම!")
    
    def manage_users(self):
        """පරිශීලකයන් පාලනය කිරීම"""
        users = self.session.query(User).all()
        
        print(f"\n👥 පරිශීලකයන් ({len(users)})")
        print("="*50)
        
        for user in users:
            status = "✅ Active" if user.is_active else "❌ Inactive"
            hotel_info = f" (Hotel ID: {user.hotel_id})" if user.hotel_id else ""
            print(f"ID: {user.id} | {user.username} | {user.full_name} | {user.user_type}{hotel_info} | {status}")
        
        print("\nවිකල්ප:")
        print("1. පරිශීලකයා activate/deactivate කිරීම")
        print("2. පරිශීලකයා ඉවත් කිරීම")
        print("3. ආපසු")
        
        choice = input("තේරීම (1-3): ")
        
        if choice == '1':
            self.toggle_user_status()
        elif choice == '2':
            self.delete_user()
    
    def toggle_user_status(self):
        """පරිශීලක status change කිරීම"""
        user_id = input("පරිශීලක ID: ")
        
        try:
            user_id = int(user_id)
            user = self.session.query(User).filter(User.id == user_id).first()
            
            if user:
                user.is_active = not user.is_active
                status = "activated" if user.is_active else "deactivated"
                self.session.commit()
                print(f"✅ {user.username} {status}!")
            else:
                print("❌ පරිශීලකයා හමු නොවීය!")
        except ValueError:
            print("❌ වලංගු නොවන ID!")
    
    def delete_user(self):
        """පරිශීලකයා ඉවත් කිරීම"""
        user_id = input("ඉවත් කිරීමට අවශ්‍ය පරිශීලක ID: ")
        
        try:
            user_id = int(user_id)
            user = self.session.query(User).filter(User.id == user_id).first()
            
            if user and user.user_type != 'super_admin':
                confirmation = input(f"'{user.username}' ඉවත් කිරීමට තහවුරු කරන්න (y/n): ")
                if confirmation.lower() == 'y':
                    self.session.delete(user)
                    self.session.commit()
                    print("✅ පරිශීලකයා ඉවත් කරන ලදී!")
            else:
                print("❌ පරිශීලකයා හමු නොවීය හෝ super admin ඉවත් කළ නොහැක!")
        except ValueError:
            print("❌ වලංගු නොවන ID!")
    
    def approve_hotels(self):
        """හොටෙල් අනුමත කිරීම"""
        pending_hotels = self.session.query(Hotel).filter(Hotel.is_approved == False).all()
        
        if not pending_hotels:
            print("\n✅ අනුමත කිරීමට ලැබුණු හොටෙල් නොමැත!")
            return
        
        print(f"\n🏨 අනුමත කිරීමට ලැබුණු හො𝑇ෙල් ({len(pending_hotels)})")
        print("="*50)
        
        for hotel in pending_hotels:
            print(f"\nID: {hotel.id} | {hotel.name}")
            print(f"📍 {hotel.location}")
            print(f"👤 {hotel.owner_name} | 📞 {hotel.contact_number}")
            print(f"💰 රු. {hotel.price_per_night:,.2f} | 🛏️ {hotel.total_rooms} කාමර")
            
            approve = input("\nමෙම හොටෙල් අනුමත කිරීමට අවශ්‍යද? (y/n): ")
            if approve.lower() == 'y':
                hotel.is_approved = True
                hotel.approved_by = self.auth.current_user.id
                hotel.approved_at = date.today()
                self.session.commit()
                print(f"✅ {hotel.name} අනුමත කරන ලදී!")
            else:
                print(f"❌ {hotel.name} අනුමත නොකළා!")
    
    def view_statistics(self):
        """පද්ධති සංඛ්‍යාලේඛන"""
        total_users = self.session.query(User).count()
        total_hotels = self.session.query(Hotel).count()
        approved_hotels = self.session.query(Hotel).filter(Hotel.is_approved == True).count()
        pending_hotels = self.session.query(Hotel).filter(Hotel.is_approved == False).count()
        total_bookings = self.session.query(Booking).count()
        
        print("\n" + "="*50)
        print("📊 පද්ධති සංඛ්‍යාලේඛන")
        print("="*50)
        print(f"👥 මුළු පරිශීලකයන්: {total_users}")
        print(f"🏨 මුළු හොටෙල්: {total_hotels}")
        print(f"✅ අනුමත හොටෙල්: {approved_hotels}")
        print(f"⏳ අනුමත කිරීමට ඇති: {pending_hotels}")
        print(f"📅 මුළු බුකින්ග්: {total_bookings}")
        
        # User type breakdown
        user_types = self.session.query(User.user_type, User.is_active).all()
        type_count = {}
        for user_type, active in user_types:
            if user_type not in type_count:
                type_count[user_type] = {'total': 0, 'active': 0}
            type_count[user_type]['total'] += 1
            if active:
                type_count[user_type]['active'] += 1
        
        print(f"\nපරිශීලක වර්ග:")
        for user_type, counts in type_count.items():
            print(f"  {user_type}: {counts['active']}/{counts['total']} active")
    
    def view_all_hotels(self):
        """සියලුම හොටෙල් බැලීම"""
        hotels = self.session.query(Hotel).all()
        
        print(f"\n🏨 සියලුම හොටෙල් ({len(hotels)})")
        print("="*50)
        
        for hotel in hotels:
            status = "✅ Approved" if hotel.is_approved else "⏳ Pending"
            print(f"ID: {hotel.id} | {hotel.name} | {hotel.location} | {status}")
    
    def view_all_bookings(self):
        """සියලුම බුකින්ග් බැලීම"""
        bookings = self.session.query(Booking).all()
        
        print(f"\n📅 සියලුම බුකින්ග් ({len(bookings)})")
        print("="*50)
        
        for booking in bookings:
            print(f"ID: {booking.id} | {booking.guest_name} | {booking.check_in_date} to {booking.check_out_date} | {booking.status}")
    
    def close(self):
        """Session close කිරීම"""
        self.session.close()