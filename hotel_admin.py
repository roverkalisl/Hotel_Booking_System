from models import Session, Hotel, Room, Booking, User
from datetime import date, timedelta
import os

class HotelAdminSystem:
    def __init__(self, auth_system):
        self.session = Session()
        self.auth = auth_system
        self.current_hotel = None
    
    def get_my_hotel(self):
        """Hotel admin ගේ හොටෙල් ලබා ගැනීම"""
        if self.auth.current_user.user_type == 'super_admin':
            return None  # Super admin සඳහා specific hotel එකක් නොමැත
        
        # Hotel admin සඳහා ඔවුන්ගේ හොටෙල් ලබා ගැනීම
        hotel = self.session.query(Hotel).filter(
            Hotel.owner_email == self.auth.current_user.email
        ).first()
        
        return hotel
    
    def dashboard(self):
        """Hotel admin dashboard"""
        self.current_hotel = self.get_my_hotel()
        
        if not self.current_hotel:
            print("\n❌ ඔබට අනුමත හොටෙලයක් නොමැත!")
            return
        
        while True:
            print("\n" + "="*60)
            print(f"🏨 HOTEL ADMIN DASHBOARD - {self.current_hotel.name}")
            print("="*60)
            print("1. 📊 හොටෙල් විස්තර")
            print("2. 🛏️ කාමර පාලනය")
            print("3. 📅 බුකින්ග් පාලනය")
            print("4. ✏️ හොටෙල් යාවත්කාලීන කිරීම")
            print("5. 🔙 ප්‍රධාන මෙනුව")
            
            choice = input("\nතේරීම (1-5): ")
            
            if choice == '1':
                self.view_hotel_details()
            elif choice == '2':
                self.manage_rooms()
            elif choice == '3':
                self.manage_bookings()
            elif choice == '4':
                self.update_hotel()
            elif choice == '5':
                break
            else:
                print("❌ වලංගු නොවන තේරීම!")
    
    def view_hotel_details(self):
        """හොටෙල් විස්තර බැලීම"""
        hotel = self.current_hotel
        print(f"\n🏨 {hotel.name} - විස්තර")
        print("="*50)
        print(f"📍 ස්ථානය: {hotel.location}")
        print(f"📝 විස්තරය: {hotel.description}")
        print(f"💰 මිල: රු. {hotel.price_per_night:,.2f} per night")
        print(f"🛏️ කාමර: {hotel.available_rooms}/{hotel.total_rooms} available")
        print(f"👤 හිමිකරු: {hotel.owner_name}")
        print(f"📞 දුරකථන: {hotel.contact_number}")
        print(f"✉️ ඊමේල්: {hotel.owner_email}")
        print(f"⭐ සේවා: {hotel.amenities}")
        
        status = "✅ Approved" if hotel.is_approved else "⏳ Pending Approval"
        print(f"📊 Status: {status}")
    
    def manage_rooms(self):
        """කාමර පාලනය"""
        rooms = self.session.query(Room).filter(Room.hotel_id == self.current_hotel.id).all()
        
        print(f"\n🛏️ {self.current_hotel.name} - කාමර")
        print("="*50)
        
        for room in rooms:
            status = "✅ Available" if room.is_available else "❌ Booked"
            print(f"කාමර {room.room_number} | {room.room_type} | {room.capacity} පුද්ගලයන් | රු. {room.price_per_night:,.2f} | {status}")
    
    def manage_bookings(self):
        """බුකින්ග් පාලනය"""
        bookings = self.session.query(Booking).filter(Booking.hotel_id == self.current_hotel.id).all()
        
        print(f"\n📅 {self.current_hotel.name} - බුකින්ග්")
        print("="*50)
        
        for booking in bookings:
            room = self.session.query(Room).filter(Room.id == booking.room_id).first()
            room_info = f"කාමර {room.room_number}" if room else "Unknown Room"
            print(f"බුකින්ග් ID: {booking.id} | {booking.guest_name} | {room_info} | {booking.check_in_date} to {booking.check_out_date} | {booking.status}")
    
    def update_hotel(self):
        """හොටෙල් යාවත්කාලීන කිරීම"""
        hotel = self.current_hotel
        
        print(f"\n✏️ {hotel.name} - යාවත්කාලීන කිරීම")
        print("="*50)
        
        print("යාවත්කාලීන කිරීමට අවශ්‍ය ක්ෂේත්‍රය තෝරන්න:")
        print("1. හොටෙල් නම")
        print("2. ස්ථානය")
        print("3. විස්තරය")
        print("4. දුරකථන අංකය")
        print("5. මිල")
        print("6. සේවා")
        
        field_choice = input("තේරීම (1-6): ")
        
        if field_choice == '1':
            hotel.name = input("නව හොටෙල් නම: ")
        elif field_choice == '2':
            hotel.location = input("නව ස්ථානය: ")
        elif field_choice == '3':
            hotel.description = input("නව විස්තරය: ")
        elif field_choice == '4':
            hotel.contact_number = input("නව දුරකථන අංකය: ")
        elif field_choice == '5':
            hotel.price_per_night = float(input("නව මිල: "))
        elif field_choice == '6':
            hotel.amenities = input("නව සේවා: ")
        else:
            print("❌ වලංගු නොවන තේරීම!")
            return
        
        self.session.commit()
        print("✅ හොටෙල් තොරතුරු සාර්ථකව යාවත්කාලීන කරන ලදී!")
    
    def close(self):
        """Session close කිරීම"""
        self.session.close()