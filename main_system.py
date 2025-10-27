from auth_system import AuthSystem
from super_admin import SuperAdminSystem
from hotel_admin import HotelAdminSystem
from customer_system import CustomerSystem
from models import Session, Hotel
import os

class MainSystem:
    def __init__(self):
        self.auth = AuthSystem()
        self.super_admin = SuperAdminSystem(self.auth)
        self.hotel_admin = HotelAdminSystem(self.auth)
        self.customer = CustomerSystem(self.auth)
    
    def main_menu(self):
        """ප්‍රධාන මෙනුව"""
        while True:
            print("\n" + "="*60)
            print("🏨 HOTEL BOOKING MANAGEMENT SYSTEM")
            print("="*60)
            
            if not self.auth.get_current_user():
                # Not logged in
                print("1. 🔐 පිවිසීම")
                print("2. 📝 ලියාපදිංචි වීම")
                print("3. 🚪 පිටවීම")
                
                choice = input("\nතේරීම (1-3): ")
                
                if choice == '1':
                    user = self.auth.login()
                    if user:
                        self.user_dashboard()
                elif choice == '2':
                    self.auth.register_user()
                elif choice == '3':
                    print("\n✅ පද්ධතිය වසා දමමින්...")
                    break
                else:
                    print("❌ වලංගු නොවන තේරීම!")
            else:
                # Already logged in
                self.user_dashboard()
    
    def user_dashboard(self):
        """User type අනුව dashboard display කිරීම"""
        user = self.auth.get_current_user()
        
        while user:
            print(f"\n👋 පිළිගනිමු {user.full_name}!")
            
            if user.user_type == 'super_admin':
                self.super_admin.dashboard()
            elif user.user_type == 'hotel_admin':
                self.hotel_admin.dashboard()
            elif user.user_type == 'customer':
                self.customer.dashboard()
            
            # Sub-menu for logged-in users
            print("\n1. 🔄 ප්‍රධාන මෙනුව")
            print("2. 🔐 පිටවීම")
            print("3. 🚪 පද්ධතියෙන් පිටවීම")
            
            choice = input("\nතේරීම (1-3): ")
            
            if choice == '1':
                break
            elif choice == '2':
                self.auth.logout()
                break
            elif choice == '3':
                self.auth.logout()
                print("\n✅ පද්ධතිය වසා දමමින්...")
                exit()
            else:
                print("❌ වලංගු නොවන තේරීම!")
    
    def initialize_system(self):
        """පද්ධතිය initialize කිරීම"""
        print("🚀 Hotel Booking System Starting...")
        self.auth.create_super_admin()
        print("✅ System initialized successfully!")

def main():
    system = MainSystem()
    system.initialize_system()
    system.main_menu()

if __name__ == "__main__":
    main()