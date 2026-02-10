from sqlalchemy import text
from app.db.database import engine

def migrate():
    with engine.connect() as conn:
        try:
            print("Adding 'chunks' column to 'videotranscribe' table...")
            conn.execute(text("ALTER TABLE videotranscribe ADD COLUMN IF NOT EXISTS chunks JSON;"))
            conn.commit()
            print("Migration successful! Column 'chunks' added.")
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
