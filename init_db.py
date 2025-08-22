from database import engine, Base

# Import your models so SQLAlchemy knows about them
import models  # make sure models.py is in the same folder or adjust import

def init_db():
    try:
        # This will create all tables in Render PostgreSQL
        Base.metadata.create_all(bind=engine)
        print("✅ Database connected and tables created successfully!")
    except Exception as e:
        print("❌ Error connecting to database or creating tables:", e)

if __name__ == "__main__":
    init_db()
