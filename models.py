import platform
from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Windows compatibility for fcntl
if platform.system() == 'Windows':
    class DummyFcntl:
        LOCK_EX = 0
        LOCK_SH = 1
        LOCK_NB = 4
        LOCK_UN = 8
        
        def flock(self, *args, **kwargs):
            pass
    fcntl = DummyFcntl()
else:
    import fcntl

# Database setup
database_url = os.environ.get('DATABASE_URL', 'sqlite:///hotels.db')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

engine = create_engine(database_url, connect_args={'check_same_thread': False} if 'sqlite' in database_url else {})
Base = declarative_base()
Session = sessionmaker(bind=engine)

class Hotel(Base):
    __tablename__ = 'hotels'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    location = Column(String(100), nullable=False)
    description = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship with rooms
    rooms = relationship("Room", back_populates="hotel", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Room(Base):
    __tablename__ = 'rooms'
    
    id = Column(Integer, primary_key=True)
    hotel_id = Column(Integer, ForeignKey('hotels.id'), nullable=False)
    room_number = Column(String(10), nullable=False)
    room_type = Column(String(50), nullable=False)
    price_per_night = Column(Float, nullable=False)
    is_available = Column(Integer, default=1)  # 1 for available, 0 for occupied
    max_guests = Column(Integer, default=2)
    
    # Relationships
    hotel = relationship("Hotel", back_populates="rooms")
    bookings = relationship("Booking", back_populates="room")
    
    def to_dict(self):
        return {
            'id': self.id,
            'hotel_id': self.hotel_id,
            'room_number': self.room_number,
            'room_type': self.room_type,
            'price_per_night': self.price_per_night,
            'is_available': bool(self.is_available),
            'max_guests': self.max_guests
        }

class Booking(Base):
    __tablename__ = 'bookings'
    
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)
    guest_name = Column(String(100), nullable=False)
    guest_email = Column(String(100))
    guest_phone = Column(String(20))
    check_in_date = Column(Date, nullable=False)
    check_out_date = Column(Date, nullable=False)
    total_price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default='confirmed')  # confirmed, cancelled, completed
    
    # Relationships
    room = relationship("Room", back_populates="bookings")
    
    def to_dict(self):
        return {
            'id': self.id,
            'room_id': self.room_id,
            'guest_name': self.guest_name,
            'guest_email': self.guest_email,
            'guest_phone': self.guest_phone,
            'check_in_date': self.check_in_date.isoformat() if self.check_in_date else None,
            'check_out_date': self.check_out_date.isoformat() if self.check_out_date else None,
            'total_price': self.total_price,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'status': self.status
        }

# Create tables
def create_tables():
    Base.metadata.create_all(engine)

if __name__ == '__main__':
    create_tables()
    print("Tables created successfully!")