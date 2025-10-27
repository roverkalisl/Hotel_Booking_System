from hotel_manager import HotelManager

def add_sample_data():
    manager = HotelManager()
    
    # Sample hotels without images first
    sample_hotels = [
        {
            'name': 'කොළඹ ජයවර්ධන හොටෙල්',
            'location': 'කොළඹ 07',
            'description': 'විලාසිතා සහිත 5-තාරකා හොටෙලය',
            'owner_name': 'කුමාර පෙරේරා',
            'owner_email': 'kumara@jaywardene.lk',
            'contact_number': '0112345678',
            'price_per_night': 12000.00,
            'total_rooms': 50,
            'amenities': 'WiFi, Pool, Spa, Gym, Restaurant'
        },
        {
            'name': 'ගාල්ල ඇන්කර් හොටෙල්',
            'location': 'ගාල්ල',
            'description': 'සමුද්‍ර තීරයේ අලංකාර හොටෙලය',
            'owner_name': 'නිශාන් සිල්වා',
            'owner_email': 'nishan@anchor.lk',
            'contact_number': '0912345678',
            'price_per_night': 8000.00,
            'total_rooms': 30,
            'amenities': 'WiFi, Beach Access, Restaurant, Bar'
        }
    ]
    
    for hotel_data in sample_hotels:
        # Create hotel without image first
        hotel = manager.add_hotel_with_image_interactive()
    
    manager.close()
    print("✅ Sample data added successfully!")

if __name__ == "__main__":
    add_sample_data()