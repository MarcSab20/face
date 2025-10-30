"""
Planificateur de tâches pour les rapports automatiques
"""

import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

from app.database import SessionLocal
from app.services.email_service import EmailService
from app.config import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def send_daily_reports():
    """Envoyer les rapports quotidiens à tous les utilisateurs configurés"""
    logger.info("Début envoi rapports quotidiens")
    
    db = SessionLocal()
    try:
        email_service = EmailService()
        
        # Liste des emails à notifier (à adapter selon votre système d'utilisateurs)
        recipients = []
        
        # Si configuré dans settings
        if settings.ALERT_EMAIL:
            recipients.append(settings.ALERT_EMAIL)
        
        # Envoyer à chaque destinataire
        for recipient in recipients:
            try:
                success = email_service.send_daily_report(db, recipient)
                if success:
                    logger.info(f"Rapport envoyé à {recipient}")
                else:
                    logger.warning(f"Échec envoi rapport à {recipient}")
            except Exception as e:
                logger.error(f"Erreur envoi à {recipient}: {str(e)}")
        
    except Exception as e:
        logger.error(f"Erreur envoi rapports quotidiens: {str(e)}")
    finally:
        db.close()


def init_scheduler():
    """Initialiser le planificateur de tâches"""
    
    # Rapport quotidien tous les jours à 8h00
    scheduler.add_job(
        send_daily_reports,
        trigger=CronTrigger(hour=8, minute=0),
        id='daily_report',
        name='Envoi rapport quotidien',
        replace_existing=True
    )
    
    logger.info("Planificateur de tâches initialisé")
    logger.info("- Rapport quotidien: tous les jours à 8h00")


def start_scheduler():
    """Démarrer le planificateur"""
    try:
        scheduler.start()
        logger.info("Planificateur démarré")
    except Exception as e:
        logger.error(f"Erreur démarrage planificateur: {str(e)}")


def stop_scheduler():
    """Arrêter le planificateur"""
    try:
        scheduler.shutdown()
        logger.info("Planificateur arrêté")
    except Exception as e:
        logger.error(f"Erreur arrêt planificateur: {str(e)}")