"""
Configuration Base de Données - SQLAlchemy
"""

import logging
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

logger = logging.getLogger(__name__)

# Créer l'engine SQLAlchemy
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles
Base = declarative_base()


def get_db():
    """
    Dependency pour obtenir une session DB
    Utilisé avec FastAPI Depends()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialiser la base de données
    Créer toutes les tables
    """
    try:
        # Import des modèles pour que SQLAlchemy les connaisse
        from app import models  # noqa: F401
        
        # Créer toutes les tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ Base de données initialisée")
        
    except Exception as e:
        logger.error(f"❌ Erreur initialisation DB: {e}")
        raise


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Activer foreign keys pour SQLite uniquement"""
    # Ne s'exécute que pour SQLite, pas pour PostgreSQL
    if 'sqlite' in str(engine.url).lower():
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()