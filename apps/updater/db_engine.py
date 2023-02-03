from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from settings import DatabaseConfiguration

SQLALCHEMY_DATABASE_URL = DatabaseConfiguration.connection_string

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    db = SessionLocal()    
    try:
        yield db
    finally:
        db.close()