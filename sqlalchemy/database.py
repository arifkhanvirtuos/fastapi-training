from sqlalchemy import create_engine 
from sqlalchemy import text

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import QueuePool
import os 


DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost/fastapi-learning"


engine = create_engine(DATABASE_URL, echo=True)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



Base = declarative_base()


def init_db() -> None:
    """Create database tables based on the SQLAlchemy models."""
    from .models import User, Product, RawMaterial  # Import models here to register them with Base
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    # Test the database connection
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("Database connection successful:", result.fetchone())
    except Exception as e:
        print("Database connection failed:", e)

    # Sync models with the database
    try:
        init_db()
        print("Database schema synchronized with models.")
    except Exception as e:
        print("Database schema sync failed:", e)

