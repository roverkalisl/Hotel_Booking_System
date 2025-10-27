from models import Session, Hotel, Room, Booking
from datetime import datetime, date, timedelta
import os

# Simple image handling for console app (PIL නොමැතිව)
class ConsoleImageManager:
    @staticmethod
    def handle_image_upload(hotel, session):
        """Console application සඳහා ජයාරුප upload කිරීම"""
        print("\n--- ජයාරුපය එකතු කිරීම ---")
        print("වර්තමානයේදී ඔබට image path එක enter කිරීමට හැකිය.")
        print("1. ජයාරුපය නොමැතිව ඉදිරියට යන්න")
        print("2. පසුව ජයාරුපය එකතු කිරීම")
        
        choice = input("ඔබගේ තේරීම (1/2): ")
        
        if choice == '1':
            image_path = input("ජයාරුපයේ path එක ඇතුළත් කරන්න: ")
            
            if os.path.exists(image_path):
                try:
                    with open(image_path, 'rb') as f:
                        image_data = f.read()
                    
                    hotel.image_data = image_data
                    hotel.image_filename = os.path.basename(image_path)
                    hotel.image_content_type = 'image/jpeg'
                    session.commit()
                    print("✅ ජයාරුපය සාර්ථකව එකතු කරන ලදී!")
                except Exception as e:
                    print(f"❌ ජයාරුපය එකතු කිරීම අසාර්ථක විය: {e}")
            else:
                print("❌ ජයාරුපය හමු නොවීය!")
        else:
            print("ජයාරුපය එකතු නොකර ඉදිරියට යනවා...")

class HotelManager:
    def __init__(self):
        self.session = Session()
    
    def add_hotel_with_image_interactive(self):
        """Interactive hotel addition with image"""
        print("\n--- නව හොටෙල් එකතු කිරීම (ජයාරුපය සමග) ---")
        
        name = input("හොටෙල් නම: ")
        location = input("ස්ථානය: ")
        description = input("විස්තරය: ")
        owner_name = input("හිමිකරුගේ නම: ")
        owner_email = input("ඊමේල්: ")
        contact_number = input("දුරකථන අංකය: ")
        price_per_night = float(input("රාත්‍රියක මිල: "))
        total_rooms = int(input("කාමර ගණන: "))
        amenities = input("සුවිශේෂී සේවා (comma separated): ")
        
        hotel = Hotel(
            name=name,
            location=location,
            description=description,
            owner_name=owner_name,
            owner_email=owner_email,
            contact_number=contact_number,
            price_per_night=price_per_night,
            total_rooms=total_rooms,
            available_rooms=total_rooms,
            amenities=amenities
        )
        
        self.session.add(hotel)
        self.session.commit()
        
        # ජයාරුපය එකතු කිරීම
        ConsoleImageManager.handle_image_upload(hotel, self.session)
        
        # Rooms create කිරීම
        self._create_rooms_for_hotel(hotel.id, total_rooms)
        
        print(f"✅ {name} හොටෙල් සාර්ථකව එකතු කරන ලදී!")
        return hotel
    
    def _create_rooms_for_hotel(self, hotel_id, total_rooms):
        """හො𝑇ෙල් එකට rooms create කිරීම"""
        room_types = ['Single', 'Double', 'Suite']
        
        for i in range(1, total_rooms + 1):
            room_type = room_types[i % len(room_types)]
            capacity = 1 if room_type == 'Single' else 2 if room_type == 'Double' else 4
            
            room = Room(
                hotel_id=hotel_id,
                room_number=f"{i:03d}",
                room_type=room_type,
                capacity=capacity,
                price_per_night=5000 + (i % 3) * 2000,
                is_available=True,
                features="WiFi, AC, TV"
            )
            self.session.add(room)
        
        self.session.commit()
    
    def get_all_hotels(self):
        """සියලුම හොටෙල් ලබා ගැනීම"""
        return self.session.query(Hotel).all()
    
    def get_hotel_by_id(self, hotel_id):
        """ID එකෙන් හොටෙල් එකක් ලබා ගැනීම"""
        return self.session.query(Hotel).filter(Hotel.id == hotel_id).first()
    
    def search_hotels(self, location=None, max_price=None):
        """හොටෙල් search කිරීම"""
        query = self.session.query(Hotel)
        
        if location:
            query = query.filter(Hotel.location.ilike(f"%{location}%"))
        if max_price:
            query = query.filter(Hotel.price_per_night <= max_price)
        
        return query.all()
    
    def display_hotel_with_image(self, hotel):
        """ජයාරුපය සමග හොටෙල් display කිරීම"""
        print(f"\n🏨 {hotel.name}")
        print(f"📍 {hotel.location}")
        print(f"💰 රු. {hotel.price_per_night:.2f} per night")
        print(f"🛏️ {hotel.available_rooms}/{hotel.total_rooms} කාමර available")
        print(f"📞 {hotel.contact_number}")
        print(f"✉️ {hotel.owner_email}")
        
        if hotel.image_data:
            print("🖼️ ජයාරුපය: [Available]")
        else:
            print("🖼️ ජයාරුපය: [Not Available]")
        
        print("-" * 50)
    
    def close(self):
        """Session close කිරීම"""
        self.session.close()

class RoomManager:
    def __init__(self):
        self.session = Session()
    
    def get_available_rooms(self, hotel_id, check_in_date, check_out_date, guests=1):
        """Available rooms බලා ගැනීම"""
        # Simple implementation for now
        available_rooms = self.session.query(Room).filter(
            Room.hotel_id == hotel_id,
            Room.is_available == True,
            Room.capacity >= guests
        ).all()
        
        return available_rooms
    
    def close(self):
        self.session.close()