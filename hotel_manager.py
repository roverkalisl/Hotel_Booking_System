from models import Session, Hotel, Room, Booking
from sqlalchemy import and_, or_, func
from datetime import datetime, date

class HotelManager:
    def __init__(self):
        self.session = Session()
    
    def __del__(self):
        self.session.close()
    
    def create_hotel(self, name, location, description=None):
        """Create a new hotel"""
        try:
            hotel = Hotel(
                name=name,
                location=location,
                description=description
            )
            self.session.add(hotel)
            self.session.commit()
            return hotel.to_dict()
        except Exception as e:
            self.session.rollback()
            raise e
    
    def get_all_hotels(self):
        """Get all hotels"""
        try:
            hotels = self.session.query(Hotel).all()
            return [hotel.to_dict() for hotel in hotels]
        except Exception as e:
            raise e
        finally:
            self.session.close()
    
    def get_hotel_by_id(self, hotel_id):
        """Get hotel by ID"""
        try:
            hotel = self.session.query(Hotel).filter(Hotel.id == hotel_id).first()
            return hotel.to_dict() if hotel else None
        except Exception as e:
            raise e
        finally:
            self.session.close()
    
    def update_hotel(self, hotel_id, **kwargs):
        """Update hotel details"""
        try:
            hotel = self.session.query(Hotel).filter(Hotel.id == hotel_id).first()
            if not hotel:
                return None
            
            for key, value in kwargs.items():
                if hasattr(hotel, key):
                    setattr(hotel, key, value)
            
            self.session.commit()
            return hotel.to_dict()
        except Exception as e:
            self.session.rollback()
            raise e
    
    def delete_hotel(self, hotel_id):
        """Delete a hotel"""
        try:
            hotel = self.session.query(Hotel).filter(Hotel.id == hotel_id).first()
            if not hotel:
                return False
            
            self.session.delete(hotel)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise e

class RoomManager:
    def __init__(self):
        self.session = Session()
    
    def __del__(self):
        self.session.close()
    
    def create_room(self, hotel_id, room_number, room_type, price_per_night, max_guests=2):
        """Create a new room"""
        try:
            room = Room(
                hotel_id=hotel_id,
                room_number=room_number,
                room_type=room_type,
                price_per_night=price_per_night,
                max_guests=max_guests,
                is_available=1
            )
            self.session.add(room)
            self.session.commit()
            return room.to_dict()
        except Exception as e:
            self.session.rollback()
            raise e
    
    def get_rooms_by_hotel(self, hotel_id):
        """Get all rooms in a hotel"""
        try:
            rooms = self.session.query(Room).filter(Room.hotel_id == hotel_id).all()
            return [room.to_dict() for room in rooms]
        except Exception as e:
            raise e
        finally:
            self.session.close()
    
    def get_available_rooms(self, hotel_id=None):
        """Get available rooms, optionally filtered by hotel"""
        try:
            query = self.session.query(Room).filter(Room.is_available == 1)
            
            if hotel_id:
                query = query.filter(Room.hotel_id == hotel_id)
            
            rooms = query.all()
            return [room.to_dict() for room in rooms]
        except Exception as e:
            raise e
        finally:
            self.session.close()
    
    def update_room(self, room_id, **kwargs):
        """Update room details"""
        try:
            room = self.session.query(Room).filter(Room.id == room_id).first()
            if not room:
                return None
            
            for key, value in kwargs.items():
                if hasattr(room, key):
                    setattr(room, key, value)
            
            self.session.commit()
            return room.to_dict()
        except Exception as e:
            self.session.rollback()
            raise e
    
    def delete_room(self, room_id):
        """Delete a room"""
        try:
            room = self.session.query(Room).filter(Room.id == room_id).first()
            if not room:
                return False
            
            self.session.delete(room)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise e

class BookingManager:
    def __init__(self):
        self.session = Session()
    
    def __del__(self):
        self.session.close()
    
    def create_booking(self, room_id, guest_name, guest_email, guest_phone, 
                      check_in_date, check_out_date):
        """Create a new booking"""
        try:
            # Check if room is available
            room = self.session.query(Room).filter(Room.id == room_id).first()
            if not room or not room.is_available:
                raise Exception("Room is not available")
            
            # Calculate total price
            nights = (check_out_date - check_in_date).days
            if nights <= 0:
                raise Exception("Invalid date range")
            
            total_price = nights * room.price_per_night
            
            # Create booking
            booking = Booking(
                room_id=room_id,
                guest_name=guest_name,
                guest_email=guest_email,
                guest_phone=guest_phone,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                total_price=total_price,
                status='confirmed'
            )
            
            # Mark room as occupied
            room.is_available = 0
            
            self.session.add(booking)
            self.session.commit()
            return booking.to_dict()
        except Exception as e:
            self.session.rollback()
            raise e
    
    def get_all_bookings(self):
        """Get all bookings"""
        try:
            bookings = self.session.query(Booking).all()
            return [booking.to_dict() for booking in bookings]
        except Exception as e:
            raise e
        finally:
            self.session.close()
    
    def get_booking_by_id(self, booking_id):
        """Get booking by ID"""
        try:
            booking = self.session.query(Booking).filter(Booking.id == booking_id).first()
            return booking.to_dict() if booking else None
        except Exception as e:
            raise e
        finally:
            self.session.close()
    
    def cancel_booking(self, booking_id):
        """Cancel a booking"""
        try:
            booking = self.session.query(Booking).filter(Booking.id == booking_id).first()
            if not booking:
                return False
            
            # Mark room as available again
            room = self.session.query(Room).filter(Room.id == booking.room_id).first()
            if room:
                room.is_available = 1
            
            booking.status = 'cancelled'
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise e
    
    def complete_booking(self, booking_id):
        """Mark booking as completed and free the room"""
        try:
            booking = self.session.query(Booking).filter(Booking.id == booking_id).first()
            if not booking:
                return False
            
            # Mark room as available
            room = self.session.query(Room).filter(Room.id == booking.room_id).first()
            if room:
                room.is_available = 1
            
            booking.status = 'completed'
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise e