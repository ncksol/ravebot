from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from settings import DatabaseConfiguration

SQLALCHEMY_DATABASE_URL = DatabaseConfiguration.connection_string

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_size=1, max_overflow=0, pool_pre_ping=True, pool_recycle=300, pool_use_lifo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    db = SessionLocal()    
    try:
        yield db
    finally:
        db.close()