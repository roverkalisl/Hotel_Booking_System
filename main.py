from flask import Flask, request, jsonify
from hotel_manager import HotelManager, RoomManager, BookingManager
from models import create_tables
from datetime import datetime
import os

app = Flask(__name__)

# Initialize database tables
@app.before_first_request
def initialize_database():
    create_tables()

# Hotel routes
@app.route('/hotels', methods=['GET'])
def get_hotels():
    try:
        manager = HotelManager()
        hotels = manager.get_all_hotels()
        return jsonify({'success': True, 'data': hotels})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/hotels', methods=['POST'])
def create_hotel():
    try:
        data = request.get_json()
        manager = HotelManager()
        hotel = manager.create_hotel(
            name=data['name'],
            location=data['location'],
            description=data.get('description')
        )
        return jsonify({'success': True, 'data': hotel})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/hotels/<int:hotel_id>', methods=['GET'])
def get_hotel(hotel_id):
    try:
        manager = HotelManager()
        hotel = manager.get_hotel_by_id(hotel_id)
        if hotel:
            return jsonify({'success': True, 'data': hotel})
        else:
            return jsonify({'success': False, 'error': 'Hotel not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Room routes
@app.route('/hotels/<int:hotel_id>/rooms', methods=['GET'])
def get_hotel_rooms(hotel_id):
    try:
        manager = RoomManager()
        rooms = manager.get_rooms_by_hotel(hotel_id)
        return jsonify({'success': True, 'data': rooms})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/rooms/available', methods=['GET'])
def get_available_rooms():
    try:
        hotel_id = request.args.get('hotel_id', type=int)
        manager = RoomManager()
        rooms = manager.get_available_rooms(hotel_id)
        return jsonify({'success': True, 'data': rooms})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/rooms', methods=['POST'])
def create_room():
    try:
        data = request.get_json()
        manager = RoomManager()
        room = manager.create_room(
            hotel_id=data['hotel_id'],
            room_number=data['room_number'],
            room_type=data['room_type'],
            price_per_night=data['price_per_night'],
            max_guests=data.get('max_guests', 2)
        )
        return jsonify({'success': True, 'data': room})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Booking routes
@app.route('/bookings', methods=['POST'])
def create_booking():
    try:
        data = request.get_json()
        manager = BookingManager()
        
        # Convert string dates to date objects
        check_in = datetime.strptime(data['check_in_date'], '%Y-%m-%d').date()
        check_out = datetime.strptime(data['check_out_date'], '%Y-%m-%d').date()
        
        booking = manager.create_booking(
            room_id=data['room_id'],
            guest_name=data['guest_name'],
            guest_email=data.get('guest_email'),
            guest_phone=data.get('guest_phone'),
            check_in_date=check_in,
            check_out_date=check_out
        )
        return jsonify({'success': True, 'data': booking})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/bookings', methods=['GET'])
def get_bookings():
    try:
        manager = BookingManager()
        bookings = manager.get_all_bookings()
        return jsonify({'success': True, 'data': bookings})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
def cancel_booking(booking_id):
    try:
        manager = BookingManager()
        success = manager.cancel_booking(booking_id)
        if success:
            return jsonify({'success': True, 'message': 'Booking cancelled'})
        else:
            return jsonify({'success': False, 'error': 'Booking not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Health check
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'Hotel Management API'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)