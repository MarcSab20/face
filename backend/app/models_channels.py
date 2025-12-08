"""
Modèles pour le monitoring de channels (YouTube, Telegram, WhatsApp, Pages Web)
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.database import Base


class ChannelType(str, enum.Enum):
    """Types de channels supportés"""
    YOUTUBE_RSS = "youtube_rss"
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    WEB_RSS = "web_rss"
    NEWS_SITE = "news_site"


class AlertPriority(str, enum.Enum):
    """Priorités d'alerte"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MonitoredChannel(Base):
    """Channel surveillé (YouTube, Telegram, WhatsApp, site web)"""
    __tablename__ = "monitored_channels"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Informations de base
    name = Column(String(255), nullable=False)
    channel_type = Column(SQLEnum(ChannelType), nullable=False, index=True)
    channel_id = Column(String(500), nullable=False)  # URL, ID chaîne, etc.
    description = Column(Text, nullable=True)
    
    # Configuration
    active = Column(Boolean, default=True, nullable=False)
    check_interval_minutes = Column(Integer, default=60)  # Fréquence de vérification
    
    # Alertes
    enable_email_alerts = Column(Boolean, default=False)
    alert_keywords = Column(JSON, nullable=True)  # Mots-clés déclenchant des alertes
    alert_priority = Column(SQLEnum(AlertPriority), default=AlertPriority.MEDIUM)
    alert_emails = Column(JSON, nullable=True)  # Liste d'emails à notifier
    
    # Métadonnées de connexion (credentials pour Telegram/WhatsApp)
    connection_config = Column(JSON, nullable=True)
    
    # Statistiques
    total_items_collected = Column(Integer, default=0)
    last_check = Column(DateTime(timezone=True), nullable=True)
    last_item_date = Column(DateTime(timezone=True), nullable=True)
    
    # Dates
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relations
    items = relationship("ChannelItem", back_populates="channel", cascade="all, delete-orphan")
    logs = relationship("ChannelMonitorLog", back_populates="channel", cascade="all, delete-orphan")


class ChannelItem(Base):
    """Élément collecté depuis un channel"""
    __tablename__ = "channel_items"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, nullable=False, index=True)
    
    # Contenu
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=True)
    url = Column(Text, nullable=False, unique=True)
    author = Column(String(255), nullable=True)
    
    # Métadonnées
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)
    collected_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Analyse
    sentiment = Column(String(20), nullable=True, index=True)
    keywords_matched = Column(JSON, nullable=True)  # Mots-clés d'alerte trouvés
    alert_triggered = Column(Boolean, default=False)
    alert_sent = Column(Boolean, default=False)
    
    # Engagement (si disponible)
    engagement_score = Column(Integer, default=0)
    
    # Données brutes
    raw_data = Column(JSON, nullable=True)
    
    # Relation
    channel = relationship("MonitoredChannel", back_populates="items")


class ChannelMonitorLog(Base):
    """Logs de monitoring des channels"""
    __tablename__ = "channel_monitor_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, nullable=False, index=True)
    
    status = Column(String(20), nullable=False)  # success, error, warning
    items_found = Column(Integer, default=0)
    new_items = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    execution_time = Column(Integer, nullable=True)  # en secondes
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relation
    channel = relationship("MonitoredChannel", back_populates="logs")