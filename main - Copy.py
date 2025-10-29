from hotel_manager import HotelManager, RoomManager
from datetime import datetime, timedelta

def main():
    manager = HotelManager()
    
    while True:
        print("\n=== Hotel Booking System ===")
        print("1. හොටෙල් එකතු කරන්න (ජයාරුපය සමග)")
        print("2. සියලුම හොටෙල් බලන්න")
        print("3. හොටෙල් සෙවීම")
        print("4. බුකින්ග් කරන්න")
        print("5. ජයාරුපය සමග හොටෙල් බලන්න")
        print("6. පිටවීම")
        
        choice = input("ඔබගේ තේරීම ඇතුළත් කරන්න: ")
        
        if choice == '1':
            manager.add_hotel_with_image_interactive()
        elif choice == '2':
            view_all_hotels(manager)
        elif choice == '3':
            search_hotels_interactive(manager)
        elif choice == '4':
            make_booking_interactive()
        elif choice == '5':
            view_hotel_with_image(manager)
        elif choice == '6':
            print("පද්ධතියෙන් පිටවෙමින්...")
            manager.close()
            break
        else:
            print("කරුණාකර වලංගු තේරීමක් ඇතුළත් කරන්න!")

def view_all_hotels(manager):
    """සියලුම හොටෙල් පෙන්වීම"""
    hotels = manager.get_all_hotels()
    
    if not hotels:
        print("කිසිදු හොටෙලයක් නොමැත!")
        return
    
    print(f"\n--- සියලුම හොටෙල් ({len(hotels)}) ---")
    for hotel in hotels:
        manager.display_hotel_with_image(hotel)

def view_hotel_with_image(manager):
    """ජයාරුපය සමග specific හොටෙල් එකක් බලා ගැනීම"""
    hotel_id = input("හොටෙල් ID එක ඇතුළත් කරන්න: ")
    
    try:
        hotel_id = int(hotel_id)
        hotel = manager.get_hotel_by_id(hotel_id)
        
        if hotel:
            print("\n--- හොටෙල් විස්තර ---")
            manager.display_hotel_with_image(hotel)
            
            # ජයාරුපය save කිරීමට option එක
            if hotel.image_data:
                save_choice = input("ජයාරුපය file එකකට save කිරීමට අවශ්‍යද? (y/n): ")
                if save_choice.lower() == 'y':
                    try:
                        filename = f"hotel_{hotel.id}_{hotel.name}.jpg"
                        with open(filename, 'wb') as f:
                            f.write(hotel.image_data)
                        print(f"✅ ජයාරුපය {filename} ලෙස save කරන ලදී!")
                    except Exception as e:
                        print(f"❌ ජයාරුපය save කිරීම අසාර්ථක විය: {e}")
        else:
            print("❌ හොටෙලය හමු නොවීය!")
    except ValueError:
        print("❌ කරුණාකර වලංගු ID එකක් ඇතුළත් කරන්න!")

def search_hotels_interactive(manager):
    """Interactive hotel search"""
    print("\n--- හොටෙල් සෙවීම ---")
    
    location = input("ස්ථානය (හිස්ව තැබිය හැක): ")
    max_price_input = input("උපරිම මිල (හිස්ව තැබිය හැක): ")
    
    max_price = float(max_price_input) if max_price_input else None
    
    hotels = manager.search_hotels(location, max_price)
    
    if not hotels:
        print("සෙවුමට ගැලපෙන හොටෙල් නොමැත!")
        return
    
    print(f"\n--- සෙවුම් ප්‍රතිඵල ({len(hotels)}) ---")
    for hotel in hotels:
        manager.display_hotel_with_image(hotel)

def make_booking_interactive():
    """Interactive booking system"""
    print("\n--- බුකින්ග් කිරීම ---")
    print("මෙම feature එක ඊළග පියවරේදී implement කරනු ලැබේ!")

if __name__ == "__main__":
    main()