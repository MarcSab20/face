"""
Modèles de Base de Données - SQLAlchemy ORM
"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.database import Base


class Keyword(Base):
    """Mot-clé à surveiller"""
    __tablename__ = "keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(255), unique=True, nullable=False, index=True)
    sources = Column(Text, nullable=False)  # JSON string: ["youtube", "reddit", ...]
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_collected = Column(DateTime(timezone=True), nullable=True)
    
    # Relations
    mentions = relationship("Mention", back_populates="keyword", cascade="all, delete-orphan")
    collection_logs = relationship("CollectionLog", back_populates="keyword", cascade="all, delete-orphan")


class Mention(Base):
    """Mention collectée"""
    __tablename__ = "mentions"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id"), nullable=False, index=True)
    
    # Source
    source = Column(String(50), nullable=False, index=True)
    source_url = Column(Text, nullable=False, unique=True)
    
    # Contenu
    title = Column(Text, nullable=False)
    content = Column(Text)
    author = Column(String(255), index=True)
    
    # Métriques
    engagement_score = Column(Float, default=0.0)
    sentiment = Column(String(20), index=True)
    
    # Dates
    published_at = Column(DateTime(timezone=True), index=True)
    collected_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Métadonnées (JSON)
    mention_metadata = Column(JSON, nullable=True)
    
    # Relations
    keyword = relationship("Keyword", back_populates="mentions")


class CollectionLog(Base):
    """Logs de collecte"""
    __tablename__ = "collection_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id"), nullable=False, index=True)
    source = Column(String(50), nullable=False)
    
    status = Column(String(20), nullable=False)
    mentions_found = Column(Integer, default=0)
    execution_time = Column(Float)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relations
    keyword = relationship("Keyword", back_populates="collection_logs")