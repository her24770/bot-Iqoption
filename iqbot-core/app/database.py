"""Configuración de SQLAlchemy: engine, session y Base declarativa."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependencia de FastAPI para obtener una sesión de BD."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
