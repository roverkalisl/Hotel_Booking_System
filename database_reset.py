from models import engine, Session, Base
from sqlalchemy import text

def update_database():
    """Database table එකට නව columns එකතු කිරීම"""
    try:
        # Session එක close කිරීම
        session = Session()
        session.close()
        
        # Database connection එක open කිරීම
        with engine.connect() as conn:
            # hotels table එකට නව columns එකතු කිරීම
            try:
                conn.execute(text("ALTER TABLE hotels ADD COLUMN image_data BLOB"))
                print("✅ image_data column එකතු කරන ලදී")
            except Exception as e:
                print(f"ℹ️ image_data column එක ඉහටම පවතී: {e}")
            
            try:
                conn.execute(text("ALTER TABLE hotels ADD COLUMN image_filename VARCHAR(255)"))
                print("✅ image_filename column එකතු කරන ලදී")
            except Exception as e:
                print(f"ℹ️ image_filename column එක ඉහටම පවතී: {e}")
            
            try:
                conn.execute(text("ALTER TABLE hotels ADD COLUMN image_content_type VARCHAR(100)"))
                print("✅ image_content_type column එකතු කරන ලදී")
            except Exception as e:
                print(f"ℹ️ image_content_type column එක ඉහටම පවතී: {e}")
            
            conn.commit()
        
        print("✅ Database update සාර්ථකයි!")
        
    except Exception as e:
        print(f"❌ Database update කිරීමේ දෝෂය: {e}")

if __name__ == "__main__":
    update_database()