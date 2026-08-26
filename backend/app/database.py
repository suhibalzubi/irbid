from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from app.models import Base

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+psycopg2://irbid:irbidpass@db:5432/irbid_db')

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
