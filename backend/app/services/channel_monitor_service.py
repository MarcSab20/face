"""
Service de monitoring automatique des channels
Vérifie périodiquement tous les channels actifs
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import SessionLocal
from app.models_channels import MonitoredChannel
from app.routers.channels import collect_channel_task

logger = logging.getLogger(__name__)


class ChannelMonitorService:
    """Service de monitoring automatique des channels"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        logger.info("✅ Channel Monitor Service initialisé")
    
    def start(self):
        """Démarrer le service de monitoring"""
        if self.is_running:
            logger.warning("Service déjà en cours")
            return
        
        # Ajouter le job de monitoring
        self.scheduler.add_job(
            func=self.check_all_channels,
            trigger=IntervalTrigger(minutes=5),  # Vérifier toutes les 5 minutes
            id='channel_monitor',
            name='Channel Monitoring',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        
        logger.info("✅ Channel Monitor Service démarré")
    
    def stop(self):
        """Arrêter le service"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("✅ Channel Monitor Service arrêté")
    
    async def check_all_channels(self):
        """Vérifier tous les channels qui nécessitent une collecte"""
        db = SessionLocal()
        
        try:
            # Récupérer tous les channels actifs
            channels = db.query(MonitoredChannel).filter(
                MonitoredChannel.active == True
            ).all()
            
            logger.info(f"🔍 Vérification de {len(channels)} channel(s)")
            
            for channel in channels:
                # Vérifier si le channel doit être collecté
                if self._should_collect(channel):
                    logger.info(f"⏰ Collecte planifiée: {channel.name}")
                    
                    try:
                        await collect_channel_task(channel.id, db)
                    except Exception as e:
                        logger.error(f"❌ Erreur collecte {channel.name}: {e}")
        
        except Exception as e:
            logger.error(f"❌ Erreur vérification channels: {e}")
        
        finally:
            db.close()
    
    def _should_collect(self, channel: MonitoredChannel) -> bool:
        """Déterminer si un channel doit être collecté maintenant"""
        
        # Si jamais collecté, oui
        if not channel.last_check:
            return True
        
        # Calculer le temps écoulé depuis la dernière collecte
        elapsed_minutes = (datetime.utcnow() - channel.last_check).total_seconds() / 60
        
        # Collecter si intervalle écoulé
        return elapsed_minutes >= channel.check_interval_minutes
    
    def get_next_checks(self) -> dict:
        """Obtenir les prochaines collectes planifiées"""
        db = SessionLocal()
        
        try:
            channels = db.query(MonitoredChannel).filter(
                MonitoredChannel.active == True
            ).all()
            
            next_checks = {}
            
            for channel in channels:
                if channel.last_check:
                    next_check = channel.last_check.timestamp() + (channel.check_interval_minutes * 60)
                    next_checks[channel.name] = {
                        'channel_id': channel.id,
                        'last_check': channel.last_check.isoformat(),
                        'next_check': datetime.fromtimestamp(next_check).isoformat(),
                        'interval_minutes': channel.check_interval_minutes
                    }
                else:
                    next_checks[channel.name] = {
                        'channel_id': channel.id,
                        'last_check': None,
                        'next_check': 'Immédiat',
                        'interval_minutes': channel.check_interval_minutes
                    }
            
            return next_checks
        
        finally:
            db.close()


# Instance globale
channel_monitor_service = ChannelMonitorService()