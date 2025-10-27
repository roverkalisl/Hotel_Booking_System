import os

class Config:
    SECRET_KEY = 'your-secret-key-12345-change-this-in-production'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///hotel_booking.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False