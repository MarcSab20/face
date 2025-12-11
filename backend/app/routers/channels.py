"""
Routes API pour la gestion des channels surveillés
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.database import get_db
from app.models_channels import (
    MonitoredChannel, ChannelItem, ChannelMonitorLog,
    ChannelType, AlertPriority
)
from app.collectors.invidious_youtube_collector import InvidiousYouTubeCollector
from app.collectors.telegram_collector import TelegramCollectorAdvanced
from app.collectors.whatsapp_collector import WhatsAppCollector
from app.collectors.web_rss_collector import WebRSSCollector
from app.services.alert_service import alert_service
from app.sentiment_analyzer import SentimentAnalyzer
from app.config import settings
import json
import logging
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/channels", tags=["Channels"])

sentiment_analyzer = SentimentAnalyzer()


# ============ MODÈLES PYDANTIC ============

class ChannelCreate(BaseModel):
    name: str
    channel_type: ChannelType
    channel_id: str
    description: Optional[str] = None
    check_interval_minutes: int = 60
    enable_email_alerts: bool = False
    alert_keywords: Optional[List[str]] = None
    alert_priority: AlertPriority = AlertPriority.MEDIUM
    alert_emails: Optional[List[str]] = None
    connection_config: Optional[dict] = None


class ChannelUpdate(BaseModel):
    name: Optional[str] = None
    active: Optional[bool] = None
    check_interval_minutes: Optional[int] = None
    enable_email_alerts: Optional[bool] = None
    alert_keywords: Optional[List[str]] = None
    alert_priority: Optional[AlertPriority] = None
    alert_emails: Optional[List[str]] = None


class ChannelResponse(BaseModel):
    id: int
    name: str
    channel_type: ChannelType
    channel_id: str
    active: bool
    total_items_collected: int
    last_check: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============ ROUTES CRUD ============

@router.post("/", response_model=ChannelResponse)
async def create_channel(
    channel: ChannelCreate,
    db: Session = Depends(get_db)
):
    """Créer un nouveau channel à surveiller"""
    
    # Vérifier si existe déjà
    existing = db.query(MonitoredChannel).filter(
        MonitoredChannel.channel_id == channel.channel_id,
        MonitoredChannel.channel_type == channel.channel_type
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Ce channel existe déjà")
    
    # Créer le channel
    new_channel = MonitoredChannel(
        name=channel.name,
        channel_type=channel.channel_type,
        channel_id=channel.channel_id,
        description=channel.description,
        check_interval_minutes=channel.check_interval_minutes,
        enable_email_alerts=channel.enable_email_alerts,
        alert_keywords=channel.alert_keywords,
        alert_priority=channel.alert_priority,
        alert_emails=channel.alert_emails or [settings.ALERT_EMAIL],
        connection_config=channel.connection_config
    )
    
    db.add(new_channel)
    db.commit()
    db.refresh(new_channel)
    
    logger.info(f"✅ Channel créé: {channel.name} ({channel.channel_type})")
    
    return new_channel


@router.get("/", response_model=List[ChannelResponse])
async def list_channels(
    active_only: bool = True,
    channel_type: Optional[ChannelType] = None,
    db: Session = Depends(get_db)
):
    """Lister tous les channels"""
    query = db.query(MonitoredChannel)
    
    if active_only:
        query = query.filter(MonitoredChannel.active == True)
    
    if channel_type:
        query = query.filter(MonitoredChannel.channel_type == channel_type)
    
    return query.all()


@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(channel_id: int, db: Session = Depends(get_db)):
    """Obtenir un channel spécifique"""
    channel = db.query(MonitoredChannel).filter(MonitoredChannel.id == channel_id).first()
    
    if not channel:
        raise HTTPException(status_code=404, detail="Channel non trouvé")
    
    return channel


@router.put("/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    channel_id: int,
    updates: ChannelUpdate,
    db: Session = Depends(get_db)
):
    """Mettre à jour un channel"""
    channel = db.query(MonitoredChannel).filter(MonitoredChannel.id == channel_id).first()
    
    if not channel:
        raise HTTPException(status_code=404, detail="Channel non trouvé")
    
    # Appliquer les mises à jour
    for field, value in updates.dict(exclude_unset=True).items():
        setattr(channel, field, value)
    
    channel.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(channel)
    
    return channel


@router.delete("/{channel_id}")
async def delete_channel(channel_id: int, db: Session = Depends(get_db)):
    """Supprimer un channel"""
    channel = db.query(MonitoredChannel).filter(MonitoredChannel.id == channel_id).first()
    
    if not channel:
        raise HTTPException(status_code=404, detail="Channel non trouvé")
    
    db.delete(channel)
    db.commit()
    
    return {"message": "Channel supprimé avec succès"}


# ============ ROUTES COLLECTE ============

@router.post("/{channel_id}/collect")
async def collect_channel(
    channel_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Lancer une collecte manuelle pour un channel"""
    channel = db.query(MonitoredChannel).filter(MonitoredChannel.id == channel_id).first()
    
    if not channel:
        raise HTTPException(status_code=404, detail="Channel non trouvé")
    
    if not channel.active:
        raise HTTPException(status_code=400, detail="Channel désactivé")
    
    # Lancer la collecte en arrière-plan
    background_tasks.add_task(collect_channel_task, channel.id, db)
    
    return {
        "message": "Collecte lancée",
        "channel": channel.name,
        "status": "processing"
    }


@router.post("/collect-all")
async def collect_all_channels(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Lancer la collecte pour tous les channels actifs"""
    channels = db.query(MonitoredChannel).filter(MonitoredChannel.active == True).all()
    
    if not channels:
        raise HTTPException(status_code=404, detail="Aucun channel actif")
    
    for channel in channels:
        background_tasks.add_task(collect_channel_task, channel.id, db)
    
    return {
        "message": f"Collecte lancée pour {len(channels)} channel(s)",
        "channels": [c.name for c in channels]
    }


# ============ FONCTION DE COLLECTE ============

async def collect_channel_task(channel_id: int, db: Session):
    """
    Tâche de collecte pour un channel
    """
    start_time = datetime.utcnow()
    
    channel = db.query(MonitoredChannel).filter(MonitoredChannel.id == channel_id).first()
    if not channel:
        return
    
    logger.info(f"🔍 Collecte: {channel.name} ({channel.channel_type})")
    
    try:
        items_collected = []
        
        # Sélectionner le collecteur approprié
        if channel.channel_type == ChannelType.YOUTUBE_RSS:
            collector = InvidiousYouTubeCollector()
            raw_items = collector.collect_channel_videos(channel.channel_id, max_results=50)
            items_collected = [format_youtube_item(item) for item in raw_items]
        
        elif channel.channel_type == ChannelType.TELEGRAM:
            config = channel.connection_config or {}
            collector = TelegramCollectorAdvanced(
                api_id=config.get('api_id', settings.TELEGRAM_API_ID),
                api_hash=config.get('api_hash', settings.TELEGRAM_API_HASH),
                phone=config.get('phone', settings.TELEGRAM_PHONE)
            )
            raw_items = await collector.collect_channel_messages(channel.channel_id, limit=50)
            items_collected = [format_telegram_item(item) for item in raw_items]
            await collector.disconnect()
        
        elif channel.channel_type == ChannelType.WHATSAPP:
            collector = WhatsAppCollector()
            raw_items = collector.collect_group_messages(channel.channel_id, limit=50)
            items_collected = [format_whatsapp_item(item) for item in raw_items]
        
        elif channel.channel_type == ChannelType.WEB_RSS:
            collector = WebRSSCollector()
            raw_items = collector.collect_feed(channel.channel_id, max_results=50)
            items_collected = [format_rss_item(item) for item in raw_items]
        
        else:
            raise ValueError(f"Type de channel non supporté: {channel.channel_type}")
        
        # Sauvegarder les nouveaux items
        new_items = []
        alert_items = []
        
        for item_data in items_collected:
            # Vérifier si existe déjà
            existing = db.query(ChannelItem).filter(
                ChannelItem.url == item_data['url']
            ).first()
            
            if existing:
                continue
            
            # Analyser le sentiment
            text = f"{item_data['title']} {item_data['content']}"
            sentiment_result = sentiment_analyzer.analyze(text)
            
            # Vérifier les mots-clés d'alerte
            keywords_matched = []
            if channel.alert_keywords:
                text_lower = text.lower()
                keywords_matched = [
                    kw for kw in channel.alert_keywords
                    if kw.lower() in text_lower
                ]
            
            # Créer l'item
            new_item = ChannelItem(
                channel_id=channel.id,
                title=item_data['title'],
                content=item_data['content'],
                url=item_data['url'],
                author=item_data.get('author'),
                published_at=item_data.get('published_at'),
                sentiment=sentiment_result['sentiment'],
                keywords_matched=keywords_matched,
                alert_triggered=bool(keywords_matched),
                engagement_score=item_data.get('engagement_score', 0),
                raw_data=item_data
            )
            
            db.add(new_item)
            new_items.append(new_item)
            
            if keywords_matched:
                alert_items.append(item_data)
        
        db.commit()
        
        # Envoyer une alerte si nécessaire
        if alert_items and channel.enable_email_alerts:
            alert_service.send_channel_alert(
                channel_name=channel.name,
                channel_type=channel.channel_type.value,
                items=alert_items,
                keywords_matched=list(set(sum([item.keywords_matched for item in new_items if item.keywords_matched], []))),
                to_emails=channel.alert_emails,
                priority=channel.alert_priority.value
            )
        
        # Mettre à jour les statistiques du channel
        channel.total_items_collected += len(new_items)
        channel.last_check = datetime.utcnow()
        
        if new_items:
            channel.last_item_date = max(item.published_at for item in new_items if item.published_at)
        
        # Logger le succès
        execution_time = int((datetime.utcnow() - start_time).total_seconds())
        
        log = ChannelMonitorLog(
            channel_id=channel.id,
            status='success',
            items_found=len(items_collected),
            new_items=len(new_items),
            execution_time=execution_time
        )
        
        db.add(log)
        db.commit()
        
        logger.info(f"✅ {channel.name}: {len(new_items)} nouveaux items")
        
    except Exception as e:
        logger.error(f"❌ Erreur collecte {channel.name}: {e}")
        
        # Logger l'erreur
        execution_time = int((datetime.utcnow() - start_time).total_seconds())
        
        log = ChannelMonitorLog(
            channel_id=channel.id,
            status='error',
            items_found=0,
            new_items=0,
            error_message=str(e),
            execution_time=execution_time
        )
        
        db.add(log)
        db.commit()


# ============ FONCTIONS DE FORMATAGE ============

def format_youtube_item(item: dict) -> dict:
    """Formater un item YouTube"""
    return {
        'title': item['title'],
        'content': item['description'],
        'url': item['url'],
        'author': item['author'],
        'published_at': item['published_at'],
        'engagement_score': 0
    }


def format_telegram_item(item: dict) -> dict:
    """Formater un item Telegram"""
    return {
        'title': f"Message Telegram - {item['channel']}",
        'content': item['text'],
        'url': item['url'],
        'author': item.get('sender_name', 'Inconnu'),
        'published_at': item['date'],
        'engagement_score': item['views'] + item['forwards'] * 2
    }


def format_whatsapp_item(item: dict) -> dict:
    """Formater un item WhatsApp"""
    return {
        'title': f"Message WhatsApp - {item['group_name']}",
        'content': item['text'],
        'url': f"whatsapp://group/{item['group_id']}",
        'author': item['sender_name'],
        'published_at': item['timestamp'],
        'engagement_score': 0
    }


def format_rss_item(item: dict) -> dict:
    """Formater un item RSS"""
    return {
        'title': item['title'],
        'content': item['content'] or item['summary'],
        'url': item['url'],
        'author': item['author'],
        'published_at': item['published_at'],
        'engagement_score': 0
    }


# ============ ROUTES STATISTIQUES ============

@router.get("/{channel_id}/stats")
async def get_channel_stats(
    channel_id: int,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """Obtenir les statistiques d'un channel"""
    channel = db.query(MonitoredChannel).filter(MonitoredChannel.id == channel_id).first()
    
    if not channel:
        raise HTTPException(status_code=404, detail="Channel non trouvé")
    
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Items collectés
    items = db.query(ChannelItem).filter(
        ChannelItem.channel_id == channel_id,
        ChannelItem.collected_at >= since_date
    ).all()
    
    # Statistiques
    total_items = len(items)
    alert_items = len([i for i in items if i.alert_triggered])
    
    sentiment_dist = {
        'positive': len([i for i in items if i.sentiment == 'positive']),
        'neutral': len([i for i in items if i.sentiment == 'neutral']),
        'negative': len([i for i in items if i.sentiment == 'negative'])
    }
    
    return {
        'channel': {
            'id': channel.id,
            'name': channel.name,
            'type': channel.channel_type,
            'active': channel.active
        },
        'period_days': days,
        'stats': {
            'total_items': total_items,
            'alert_items': alert_items,
            'sentiment_distribution': sentiment_dist,
            'last_check': channel.last_check,
            'last_item_date': channel.last_item_date
        }
    }


@router.get("/{channel_id}/items")
async def get_channel_items(
    channel_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    alert_only: bool = False,
    db: Session = Depends(get_db)
):
    """Obtenir les items d'un channel"""
    query = db.query(ChannelItem).filter(ChannelItem.channel_id == channel_id)
    
    if alert_only:
        query = query.filter(ChannelItem.alert_triggered == True)
    
    items = query.order_by(ChannelItem.published_at.desc()).offset(offset).limit(limit).all()
    
    return {
        'channel_id': channel_id,
        'total': query.count(),
        'items': items
    }

# ============ ROUTES UTILITAIRES ============

@router.get("/discover/youtube")
async def discover_youtube_channel(search: str = Query(..., min_length=3)):
    """Rechercher une chaîne YouTube par nom"""
    from app.collectors.invidious_youtube_collector import find_youtube_channel_id
    
    channel_id = find_youtube_channel_id(search)
    
    if channel_id:
        collector = InvidiousYouTubeCollector()
        info = collector.get_channel_info(channel_id)
        
        return {
            'found': True,
            'channel_id': channel_id,
            'info': info
        }
    else:
        return {
            'found': False,
            'message': 'Chaîne non trouvée'
        }


@router.get("/discover/rss")
async def discover_rss_feed(website_url: str = Query(...)):
    """Découvrir le flux RSS d'un site web"""
    collector = WebRSSCollector()
    feed_url = collector.discover_feed_url(website_url)
    
    if feed_url:
        return {
            'found': True,
            'feed_url': feed_url,
            'message': 'Flux RSS découvert'
        }
    else:
        return {
            'found': False,
            'message': 'Aucun flux RSS trouvé'
        }


@router.get("/presets/popular")
async def get_popular_channels():
    """Obtenir les channels populaires pré-configurés"""
    return {
        'youtube_news': [
            {
                'name': 'France 24 English',
                'channel_id': 'UCQfwfsi5VrQ8yKZ-UWmAEFg',
                'type': 'youtube_rss'
            },
            {
                'name': 'BBC News',
                'channel_id': 'UC16niRr50-MSBwiO3YDb3RA',
                'type': 'youtube_rss'
            },
            {
                'name': 'RFI Afrique',
                'channel_id': 'UCjdlPdaD4nYjW8qFvEy3FKg',
                'type': 'youtube_rss'
            }
        ],
        'rss_feeds': WebRSSCollector().get_popular_feeds(),
        'telegram_channels': [
            {
                'name': 'France 24 Français',
                'channel_id': '@france24_fr',
                'type': 'telegram'
            }
        ]
    }


@router.get("/monitoring/schedule")
async def get_monitoring_schedule():
    """Obtenir le planning de monitoring"""
    next_checks = channel_monitor_service.get_next_checks()
    
    return {
        'service_running': channel_monitor_service.is_running,
        'channels': next_checks,
        'total_channels': len(next_checks)
    }


@router.post("/test-alert")
async def test_alert_email(
    channel_id: int,
    db: Session = Depends(get_db)
):
    """Tester l'envoi d'une alerte email"""
    channel = db.query(MonitoredChannel).filter(MonitoredChannel.id == channel_id).first()
    
    if not channel:
        raise HTTPException(status_code=404, detail="Channel non trouvé")
    
    success = alert_service.send_channel_alert(
        channel_name=channel.name,
        channel_type=channel.channel_type.value,
        items=[{
            'title': 'Test d\'alerte',
            'url': 'https://example.com',
            'content': 'Ceci est un test d\'alerte email',
            'published_at': datetime.utcnow()
        }],
        keywords_matched=['test'],
        to_emails=channel.alert_emails,
        priority='medium'
    )
    
    return {
        'success': success,
        'message': 'Email de test envoyé' if success else 'Échec envoi email'
    }