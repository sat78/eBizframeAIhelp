from app.db.database import SessionLocal, engine
from sqlalchemy import text
from app.models.user import User

def test_connection():
    try:
        # Test connection
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        print("✅ Database connection successful!")
        
        # Test table existence
        try:
            db.query(User).first()
            print("✅ Users table exists and is accessible.")
        except Exception as e:
            print(f"❌ Error accessing Users table: {e}")
            # Try to create tables
            from app.db.database import Base
            Base.metadata.create_all(bind=engine)
            print("⚠️ Attempted to create tables. Please check if they exist now.")

        db.close()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    test_connection()
