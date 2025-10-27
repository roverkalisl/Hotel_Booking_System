from models import Session, Hotel, Room, Booking
from datetime import date, timedelta

class CustomerSystem:
    def __init__(self, auth_system):
        self.session = Session()
        self.auth = auth_system
    
    def dashboard(self):
        """Customer dashboard"""
        while True:
            print("\n" + "="*60)
            print("👤 CUSTOMER DASHBOARD")
            print("="*60)
            print("1. 🔍 හොටෙල් සෙවීම")
            print("2. 🏨 හොටෙල් බැලීම")
            print("3. 📅 මගේ බුකින්ග්")
            print("4. 🔙 ප්‍රධාන මෙනුව")
            
            choice = input("\nතේරීම (1-4): ")
            
            if choice == '1':
                self.search_hotels()
            elif choice == '2':
                self.view_hotels()
            elif choice == '3':
                self.my_bookings()
            elif choice == '4':
                break
            else:
                print("❌ වලංගු නොවන තේරීම!")
    
    def search_hotels(self):
        """හොටෙල් සෙවීම"""
        print("\n🔍 හොටෙල් සෙවීම")
        print("="*50)
        
        location = input("ස්ථානය: ")
        check_in = input("Check-in දිනය (YYYY-MM-DD): ")
        check_out = input("Check-out දිනය (YYYY-MM-DD): ")
        guests = int(input("පුද්ගලයන් ගණන: "))
        
        try:
            check_in_date = date.fromisoformat(check_in)
            check_out_date = date.fromisoformat(check_out)
        except ValueError:
            print("❌ වලංගු නොවන දින ආකෘතිය!")
            return
        
        # Approved hotels only
        hotels = self.session.query(Hotel).filter(
            Hotel.location.ilike(f"%{location}%"),
            Hotel.is_approved == True,
            Hotel.available_rooms >= 1
        ).all()
        
        if not hotels:
            print(f"\n❌ '{location}' සඳහා හොටෙල් හමු නොවීය!")
            return
        
        print(f"\n🔍 සෙවුම් ප්‍රතිඵල ({len(hotels)})")
        print("="*50)
        
        for hotel in hotels:
            print(f"\n🏨 {hotel.name} (ID: {hotel.id})")
            print(f"📍 {hotel.location}")
            print(f"💰 රු. {hotel.price_per_night:,.2f} per night")
            print(f"🛏️ {hotel.available_rooms} කාමර available")
            print(f"⭐ {hotel.amenities}")
            print("-" * 40)
    
    def view_hotels(self):
        """හොටෙල් බැලීම"""
        hotels = self.session.query(Hotel).filter(Hotel.is_approved == True).all()
        
        if not hotels:
            print("\n❌ කිසිදු හොටෙලයක් නොමැත!")
            return
        
        print(f"\n🏨 අනුමත හොටෙල් ({len(hotels)})")
        print("="*50)
        
        for hotel in hotels:
            print(f"\n🏨 {hotel.name} (ID: {hotel.id})")
            print(f"📍 {hotel.location}")
            print(f"💰 රු. {hotel.price_per_night:,.2f} per night")
            print(f"🛏️ {hotel.available_rooms} කාමර available")
            print(f"📞 {hotel.contact_number}")
            print("-" * 40)
    
    def my_bookings(self):
        """ගනුදෙනුකරුගේ බුකින්ග් බැලීම"""
        if not self.auth.current_user:
            print("❌ කරුණාකර පළමුව පිවිසෙන්න!")
            return
        
        bookings = self.session.query(Booking).filter(
            Booking.customer_id == self.auth.current_user.id
        ).all()
        
        if not bookings:
            print("\n❔ ඔබට තවමත් බුකින්ග් නොමැත!")
            return
        
        print(f"\n📅 මගේ බුකින්ග් ({len(bookings)})")
        print("="*50)
        
        for booking in bookings:
            hotel = self.session.query(Hotel).filter(Hotel.id == booking.hotel_id).first()
            hotel_name = hotel.name if hotel else "Unknown Hotel"
            print(f"බුකින්ග් ID: {booking.id} | {hotel_name} | {booking.check_in_date} to {booking.check_out_date} | {booking.status} | රු. {booking.total_price:,.2f}")
    
    def close(self):
        """Session close කිරීම"""
        self.session.close()