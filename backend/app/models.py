from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Keyword(Base):
    """Mots-clés à surveiller"""
    __tablename__ = "keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(255), unique=True, nullable=False, index=True)
    active = Column(Boolean, default=True)
    sources = Column(String(500))  # JSON stringifié des sources actives
    created_at = Column(DateTime, default=datetime.utcnow)
    last_collected = Column(DateTime, nullable=True)
    
    mentions = relationship("Mention", back_populates="keyword_obj", cascade="all, delete-orphan")

class Mention(Base):
    """Mentions trouvées en ligne"""
    __tablename__ = "mentions"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id"), nullable=False)
    
    # Source
    source = Column(String(50), nullable=False, index=True)  # reddit, youtube, tiktok, etc.
    source_url = Column(String(1000), unique=True)
    
    # Contenu
    title = Column(String(500))
    content = Column(Text)
    author = Column(String(255))
    
    # Métriques
    engagement_score = Column(Float, default=0.0)  # likes, upvotes, views, etc.
    sentiment = Column(String(20))  # positive, negative, neutral
    
    # Dates
    published_at = Column(DateTime, nullable=True)
    collected_at = Column(DateTime, default=datetime.utcnow)
    
    # Metadata (renamed to avoid SQLAlchemy reserved word)
    mention_metadata = Column(Text)  # JSON pour infos spécifiques à la source
    
    keyword_obj = relationship("Keyword", back_populates="mentions")
    
    __table_args__ = (
        Index('idx_keyword_source', 'keyword_id', 'source'),
        Index('idx_published_at', 'published_at'),
    )

class CollectionLog(Base):
    """Log des collectes pour monitoring"""
    __tablename__ = "collection_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id"))
    source = Column(String(50), nullable=False)
    status = Column(String(20))  # success, error, partial
    mentions_found = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    execution_time = Column(Float)  # secondes
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class Alert(Base):
    """Alertes configurées"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id"))
    
    # Conditions
    trigger_type = Column(String(50))  # new_mention, volume_spike, sentiment_change
    threshold = Column(Float)
    
    # Notification
    notification_method = Column(String(50))  # email, webhook
    notification_target = Column(String(500))
    active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_triggered = Column(DateTime, nullable=True)