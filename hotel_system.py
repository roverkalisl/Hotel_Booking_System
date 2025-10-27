from models import Session, Hotel, Room, Booking
from datetime import datetime, date, timedelta
import os

class HotelManagement:
    def __init__(self):
        self.session = Session()
    
    def add_hotel(self):
        """නව හොටෙල් එකතු කිරීම"""
        print("\n" + "="*50)
        print("නව හොටෙල් ලියාපදිංචි කිරීම")
        print("="*50)
        
        name = input("හොටෙල් නම: ")
        location = input("ස්ථානය: ")
        description = input("විස්තරය: ")
        owner_name = input("හිමිකරුගේ නම: ")
        owner_email = input("ඊමේල්: ")
        contact_number = input("දුරකථන අංකය: ")
        price_per_night = float(input("රාත්‍රියක මිල (රුපියල්): "))
        total_rooms = int(input("මුළු කාමර ගණන: "))
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
        
        # කාමර create කිරීම
        self._create_rooms_for_hotel(hotel.id, total_rooms)
        
        # ජයාරුපය එකතු කිරීම
        self._add_hotel_image(hotel)
        
        print(f"\n✅ '{name}' හොටෙල් සාර්ථකව ලියාපදිංචි කරන ලදී!")
        print(f"🆔 හොටෙල් ID: {hotel.id}")
        return hotel
    
    def _create_rooms_for_hotel(self, hotel_id, total_rooms):
        """හොටෙල් එකට කාමර create කිරීම"""
        room_types = [
            {'type': 'Single', 'capacity': 1, 'base_price': 4000},
            {'type': 'Double', 'capacity': 2, 'base_price': 6000},
            {'type': 'Suite', 'capacity': 4, 'base_price': 10000},
            {'type': 'Deluxe', 'capacity': 3, 'base_price': 8000}
        ]
        
        for i in range(1, total_rooms + 1):
            room_type = room_types[i % len(room_types)]
            
            room = Room(
                hotel_id=hotel_id,
                room_number=f"{i:03d}",
                room_type=room_type['type'],
                capacity=room_type['capacity'],
                price_per_night=room_type['base_price'] + (i % 4) * 500,
                is_available=True,
                features=f"WiFi, AC, TV, {room_type['type']} Room"
            )
            self.session.add(room)
        
        self.session.commit()
    
    def _add_hotel_image(self, hotel):
        """හොටෙල් එකට ජයාරුපය එකතු කිරීම"""
        print("\n--- ජයාරුපය එකතු කිරීම ---")
        choice = input("ජයාරුපය එකතු කිරීමට අවශ්‍යද? (y/n): ")
        
        if choice.lower() == 'y':
            image_path = input("ජයාරුපයේ path එක ඇතුළත් කරන්න: ")
            
            if os.path.exists(image_path):
                try:
                    with open(image_path, 'rb') as f:
                        image_data = f.read()
                    
                    hotel.image_data = image_data
                    hotel.image_filename = os.path.basename(image_path)
                    hotel.image_content_type = 'image/jpeg'
                    self.session.commit()
                    print("✅ ජයාරුපය සාර්ථකව එකතු කරන ලදී!")
                except Exception as e:
                    print(f"❌ ජයාරුපය එකතු කිරීම අසාර්ථක විය: {e}")
            else:
                print("❌ ජයාරුපය හමු නොවීය!")
    
    def view_all_hotels(self):
        """සියලුම හොටෙල් බැලීම"""
        hotels = self.session.query(Hotel).all()
        
        if not hotels:
            print("\n❌ කිසිදු හොටෙලයක් ලියාපදිංචි වී නොමැත!")
            return
        
        print(f"\n" + "="*60)
        print(f"ලියාපදිංචි හොටෙල් ({len(hotels)})")
        print("="*60)
        
        for hotel in hotels:
            self._display_hotel_details(hotel)
    
    def _display_hotel_details(self, hotel):
        """හොටෙල් විස්තර පෙන්වීම"""
        print(f"\n🏨 {hotel.name} (ID: {hotel.id})")
        print(f"📍 ස්ථානය: {hotel.location}")
        print(f"📝 විස්තරය: {hotel.description}")
        print(f"💰 මිල: රු. {hotel.price_per_night:,.2f} per night")
        print(f"🛏️ කාමර: {hotel.available_rooms}/{hotel.total_rooms} available")
        print(f"👤 හිමිකරු: {hotel.owner_name}")
        print(f"📞 දුරකථන: {hotel.contact_number}")
        print(f"✉️ ඊමේල්: {hotel.owner_email}")
        print(f"⭐ සේවා: {hotel.amenities}")
        
        if hotel.image_data:
            print("🖼️ ජයාරුපය: ✅ Available")
        else:
            print("🖼️ ජයාරුපය: ❌ Not Available")
        
        print(f"📅 ලියාපදිංචි දිනය: {hotel.created_at}")
        print("-" * 60)
    
    def search_hotels(self):
        """හොටෙල් සෙවීම"""
        print("\n" + "="*50)
        print("හොටෙල් සෙවීම")
        print("="*50)
        
        print("සෙවුම් විකල්ප:")
        print("1. ස්ථානය අනුව")
        print("2. මිල අනුව")
        print("3. ස්ථානය සහ මිල අනුව")
        
        choice = input("තේරීම (1/2/3): ")
        
        location = None
        max_price = None
        
        if choice in ['1', '3']:
            location = input("සෙවිය යුතු ස්ථානය: ")
        
        if choice in ['2', '3']:
            try:
                max_price = float(input("උපරිම මිල (රුපියල්): "))
            except ValueError:
                print("❌ කරුණාකර වලංගු මිලක් ඇතුළත් කරන්න!")
                return
        
        hotels = self.session.query(Hotel)
        
        if location:
            hotels = hotels.filter(Hotel.location.ilike(f"%{location}%"))
        if max_price:
            hotels = hotels.filter(Hotel.price_per_night <= max_price)
        
        results = hotels.all()
        
        if not results:
            print(f"\n❌ '{location if location else ''}' සඳහා හොටෙල් හමු නොවීය!")
            return
        
        print(f"\n🔍 සෙවුම් ප්‍රතිඵල ({len(results)})")
        print("="*50)
        
        for hotel in results:
            self._display_hotel_details(hotel)
    
    def update_hotel(self):
        """හොටෙල් තොරතුරු යාවත්කාලීන කිරීම"""
        print("\n" + "="*50)
        print("හොටෙල් යාවත්කාලීන කිරීම")
        print("="*50)
        
        hotel_id = input("යාවත්කාලීන කිරීමට අවශ්‍ය හොටෙල් ID: ")
        
        try:
            hotel_id = int(hotel_id)
            hotel = self.session.query(Hotel).filter(Hotel.id == hotel_id).first()
            
            if not hotel:
                print("❌ හොටෙල් හමු නොවීය!")
                return
            
            print(f"\n🏨 වත්මන් විස්තර: {hotel.name}")
            self._display_hotel_details(hotel)
            
            print("\nයාවත්කාලීන කිරීමට අවශ්‍ය ක්ෂේත්‍රය තෝරන්න:")
            print("1. හොටෙල් නම")
            print("2. ස්ථානය")
            print("3. විස්තරය")
            print("4. දුරකථන අංකය")
            print("5. මිල")
            print("6. සේවා")
            print("7. ජයාරුපය")
            
            field_choice = input("තේරීම (1-7): ")
            
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
            elif field_choice == '7':
                self._add_hotel_image(hotel)
            else:
                print("❌ වලංගු නොවන තේරීම!")
                return
            
            self.session.commit()
            print("✅ හොටෙල් තොරතුරු සාර්ථකව යාවත්කාලීන කරන ලදී!")
            
        except ValueError:
            print("❌ කරුණාකර වලංගු ID එකක් ඇතුළත් කරන්න!")
        except Exception as e:
            print(f"❌ යාවත්කාලීන කිරීම අසාර්ථක විය: {e}")
    
    def delete_hotel(self):
        """හොටෙල් ඉවත් කිරීම"""
        print("\n" + "="*50)
        print("හොටෙල් ඉවත් කිරීම")
        print("="*50)
        
        hotel_id = input("ඉවත් කිරීමට අවශ්‍ය හොටෙල් ID: ")
        
        try:
            hotel_id = int(hotel_id)
            hotel = self.session.query(Hotel).filter(Hotel.id == hotel_id).first()
            
            if not hotel:
                print("❌ හොටෙල් හමු නොවීය!")
                return
            
            print(f"\n⚠️ ඔබට '{hotel.name}' හොටෙල් ඉවත් කිරීමට අවශ්‍යද?")
            confirmation = input("තහවුරු කිරීමට 'YES' ඇතුළත් කරන්න: ")
            
            if confirmation.upper() == 'YES':
                # සම්බන්ධ කාමර ඉවත් කිරීම
                self.session.query(Room).filter(Room.hotel_id == hotel_id).delete()
                # සම්බන්ධ බුකින්ග් ඉවත් කිරීම
                self.session.query(Booking).filter(Booking.hotel_id == hotel_id).delete()
                # හොටෙල් ඉවත් කිරීම
                self.session.delete(hotel)
                self.session.commit()
                print("✅ හොටෙල් සහ සම්බන්ධ තොරතුරු සාර්ථකව ඉවත් කරන ලදී!")
            else:
                print("❌ ඉවත් කිරීම අවලංගු කරන ලදී!")
                
        except ValueError:
            print("❌ කරුණාකර වලංගු ID එකක් ඇතුළත් කරන්න!")
        except Exception as e:
            print(f"❌ ඉවත් කිරීම අසාර්ථක විය: {e}")
    
    def view_hotel_stats(self):
        """හොටෙල් සංඛ්‍යාලේඛන"""
        hotels = self.session.query(Hotel).all()
        
        if not hotels:
            print("\n❌ කිසිදු හොටෙලයක් නොමැත!")
            return
        
        total_hotels = len(hotels)
        total_rooms = sum(hotel.total_rooms for hotel in hotels)
        available_rooms = sum(hotel.available_rooms for hotel in hotels)
        total_capacity = sum(hotel.total_rooms * hotel.price_per_night for hotel in hotels) / len(hotels) if hotels else 0
        
        print("\n" + "="*50)
        print("හොටෙල් සංඛ්‍යාලේඛන")
        print("="*50)
        print(f"🏨 මුළු හොටෙල්: {total_hotels}")
        print(f"🛏️ මුළු කාමර: {total_rooms}")
        print(f"✅ තිබෙන කාමර: {available_rooms}")
        print(f"📊 සාමාන්‍ය මිල: රු. {total_capacity:,.2f}")
        
        # Location-wise statistics
        locations = {}
        for hotel in hotels:
            if hotel.location in locations:
                locations[hotel.location] += 1
            else:
                locations[hotel.location] = 1
        
        print(f"\n📍 ස්ථානය අනුව හොටෙල්:")
        for location, count in locations.items():
            print(f"   {location}: {count} හොටෙල්")
    
    def close(self):
        """Session close කිරීම"""
        self.session.close()

def main():
    manager = HotelManagement()
    
    while True:
        print("\n" + "="*60)
        print("🏨 හොටෙල් මැනේජ්මන්ට් සිස්ටම්")
        print("="*60)
        print("1. 🆕 නව හොටෙල් ලියාපදිංචි කිරීම")
        print("2. 📋 සියලුම හොටෙල් බැලීම")
        print("3. 🔍 හොටෙල් සෙවීම")
        print("4. ✏️ හොටෙල් යාවත්කාලීන කිරීම")
        print("5. 🗑️ හොටෙල් ඉවත් කිරීම")
        print("6. 📊 සංඛ්‍යාලේඛන බැලීම")
        print("7. 🚪 පිටවීම")
        
        choice = input("\nඔබගේ තේරීම ඇතුළත් කරන්න (1-7): ")
        
        if choice == '1':
            manager.add_hotel()
        elif choice == '2':
            manager.view_all_hotels()
        elif choice == '3':
            manager.search_hotels()
        elif choice == '4':
            manager.update_hotel()
        elif choice == '5':
            manager.delete_hotel()
        elif choice == '6':
            manager.view_hotel_stats()
        elif choice == '7':
            print("\n✅ හොටෙල් මැනේජ්මන්ට් සිස්ටම් වසා දමමින්...")
            manager.close()
            break
        else:
            print("❌ කරුණාකර වලංගු තේරීමක් ඇතුළත් කරන්න (1-7)!")
        
        # Continue prompt
        if choice != '7':
            input("\nEnter බොත්තම ඔබන්න ඉදිරියට යාමට...")

if __name__ == "__main__":
    main()