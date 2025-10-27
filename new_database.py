import os
from models import Base, engine

def create_new_database():
    """නව database එකක් create කිරීම"""
    try:
        # පැරණි database එක rename කිරීම (backup ලෙස)
        if os.path.exists('hotel_booking.db'):
            os.rename('hotel_booking.db', 'hotel_booking_old.db')
            print("✅ පැරණි database එක backup ලෙස rename කරන ලදී")
        
        # නව tables create කිරීම
        Base.metadata.create_all(engine)
        print("✅ නව database tables create කරන ලදී")
        print("✅ සියලුම නව columns එකතු කරන ලදී")
        
    except Exception as e:
        print(f"❌ Database create කිරීමේ දෝෂය: {e}")

if __name__ == "__main__":
    create_new_database()