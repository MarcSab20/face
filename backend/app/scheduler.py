"""
Système de Planification - APScheduler
Gère les collectes automatiques périodiques
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

logger = logging.getLogger(__name__)

# Instance globale du scheduler
scheduler = AsyncIOScheduler()


def init_scheduler():
    """Initialiser le scheduler"""
    try:
        logger.info("📅 Initialisation du scheduler...")
        
        # Le scheduler sera démarré manuellement avec start_scheduler()
        logger.info("✅ Scheduler initialisé")
        
    except Exception as e:
        logger.error(f"❌ Erreur initialisation scheduler: {e}")
        raise


def start_scheduler():
    """Démarrer le scheduler"""
    try:
        if not scheduler.running:
            scheduler.start()
            logger.info("✅ Scheduler démarré")
        else:
            logger.info("ℹ️ Scheduler déjà en cours d'exécution")
            
    except Exception as e:
        logger.error(f"❌ Erreur démarrage scheduler: {e}")


def stop_scheduler():
    """Arrêter le scheduler"""
    try:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("✅ Scheduler arrêté")
        else:
            logger.info("ℹ️ Scheduler déjà arrêté")
            
    except Exception as e:
        logger.error(f"❌ Erreur arrêt scheduler: {e}")


def add_collection_job(keyword_id: int, interval_minutes: int = 60):
    """
    Ajouter une tâche de collecte périodique
    
    Args:
        keyword_id: ID du mot-clé à collecter
        interval_minutes: Intervalle en minutes
    """
    try:
        job_id = f"collect_keyword_{keyword_id}"
        
        # Vérifier si le job existe déjà
        if scheduler.get_job(job_id):
            logger.info(f"Job {job_id} existe déjà")
            return
        
        # Ajouter le job
        scheduler.add_job(
            func=lambda: logger.info(f"Collecte pour keyword {keyword_id}"),
            trigger=IntervalTrigger(minutes=interval_minutes),
            id=job_id,
            name=f"Collecte automatique - Keyword {keyword_id}",
            replace_existing=True
        )
        
        logger.info(f"✅ Job ajouté: {job_id} (intervalle: {interval_minutes}min)")
        
    except Exception as e:
        logger.error(f"❌ Erreur ajout job: {e}")


def remove_collection_job(keyword_id: int):
    """Supprimer une tâche de collecte"""
    try:
        job_id = f"collect_keyword_{keyword_id}"
        scheduler.remove_job(job_id)
        logger.info(f"✅ Job supprimé: {job_id}")
        
    except Exception as e:
        logger.error(f"❌ Erreur suppression job: {e}")


def get_scheduled_jobs():
    """Obtenir la liste des jobs planifiés"""
    try:
        jobs = scheduler.get_jobs()
        
        return [
            {
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None
            }
            for job in jobs
        ]
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération jobs: {e}")
        return []