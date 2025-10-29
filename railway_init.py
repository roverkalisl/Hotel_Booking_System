#!/usr/bin/env python3
"""
Railway-specific initialization script
Run this on Railway to set up the database
"""

import os
import sys

# Add current directory to Python path
sys.path.append(os.path.dirname(__file__))

from app import app, db, init_db

def main():
    print("🚀 Starting Railway initialization...")
    
    with app.app_context():
        try:
            # Create all tables
            print("📦 Creating database tables...")
            db.create_all()
            print("✅ Tables created successfully!")
            
            # Initialize with sample data
            print("📝 Initializing sample data...")
            init_db()
            print("✅ Sample data initialized successfully!")
            
            print("🎉 Railway setup completed!")
            print("🌐 Your app is ready!")
            
        except Exception as e:
            print(f"❌ Error during initialization: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()