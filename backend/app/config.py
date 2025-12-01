"""
Configuration Centralisée - Brand Monitor
Gère toutes les variables d'environnement et configuration
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Configuration centralisée de l'application"""
    
    # ===== APPLICATION =====
    APP_NAME: str = "BrandMonitor"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # ===== DATABASE =====
    DATABASE_URL: str = Field(
        default="postgresql://brandmonitor:brandmonitor_password@localhost:5432/brandmonitor",
        env="DATABASE_URL"
    )
    
    # ===== REDIS =====
    REDIS_URL: str = Field(
        default="redis://localhost:6379",
        env="REDIS_URL"
    )
    
    # ===== OLLAMA (IA Local) =====
    OLLAMA_HOST: str = Field(
        default="http://localhost:11434",
        env="OLLAMA_HOST"
    )
    OLLAMA_DEFAULT_MODEL: str = Field(
        default="gemma:2b",
        env="OLLAMA_DEFAULT_MODEL"
    )
    OLLAMA_AVAILABLE_MODELS: str = Field(
        default="gemma:2b,tinyllama,mistral:7b",
        env="OLLAMA_AVAILABLE_MODELS"
    )
    
    @property
    def ollama_models_list(self) -> List[str]:
        """Liste des modèles Ollama disponibles"""
        return [m.strip() for m in self.OLLAMA_AVAILABLE_MODELS.split(',')]
    
    # ===== GOOGLE GEMINI API =====
    GEMINI_API_KEY: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    
    @property
    def gemini_enabled(self) -> bool:
        """Vérifier si Gemini est configuré"""
        return bool(self.GEMINI_API_KEY)
    
    # ===== GROQ API =====
    GROQ_API_KEY: Optional[str] = Field(default=None, env="GROQ_API_KEY")
    
    @property
    def groq_enabled(self) -> bool:
        """Vérifier si Groq est configuré"""
        return bool(self.GROQ_API_KEY)
    
    # ===== YOUTUBE API =====
    YOUTUBE_API_KEY: Optional[str] = Field(default=None, env="YOUTUBE_API_KEY")
    
    @property
    def youtube_enabled(self) -> bool:
        """Vérifier si YouTube est configuré"""
        return bool(self.YOUTUBE_API_KEY)
    
    # ===== REDDIT API =====
    REDDIT_CLIENT_ID: Optional[str] = Field(default=None, env="REDDIT_CLIENT_ID")
    REDDIT_CLIENT_SECRET: Optional[str] = Field(default=None, env="REDDIT_CLIENT_SECRET")
    REDDIT_USER_AGENT: str = Field(
        default="BrandMonitor/2.0",
        env="REDDIT_USER_AGENT"
    )
    
    @property
    def reddit_enabled(self) -> bool:
        """Vérifier si Reddit est configuré"""
        return bool(self.REDDIT_CLIENT_ID and self.REDDIT_CLIENT_SECRET)
    
    # ===== GOOGLE NEWS (GNews) =====
    GNEWS_API_KEY: Optional[str] = Field(default=None, env="GNEWS_API_KEY")
    
    @property
    def gnews_enabled(self) -> bool:
        """Vérifier si GNews est configuré"""
        return bool(self.GNEWS_API_KEY)
    
    # ===== GOOGLE CUSTOM SEARCH =====
    GOOGLE_API_KEY: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    GOOGLE_SEARCH_ENGINE_ID: Optional[str] = Field(default=None, env="GOOGLE_SEARCH_ENGINE_ID")
    
    @property
    def google_search_enabled(self) -> bool:
        """Vérifier si Google Custom Search est configuré"""
        return bool(self.GOOGLE_API_KEY and self.GOOGLE_SEARCH_ENGINE_ID)
    
    # ===== EMAIL / SMTP =====
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USER: Optional[str] = Field(default=None, env="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    SMTP_FROM: Optional[str] = Field(default=None, env="SMTP_FROM")
    SMTP_USE_TLS: bool = Field(default=True, env="SMTP_USE_TLS")
    ALERT_EMAIL: Optional[str] = Field(default=None, env="ALERT_EMAIL")
    
    @property
    def email_enabled(self) -> bool:
        """Vérifier si l'email est configuré"""
        return bool(
            self.SMTP_HOST and 
            self.SMTP_USER and 
            self.SMTP_PASSWORD and 
            self.SMTP_FROM
        )
    
    # ===== TELEGRAM (Optionnel) =====
    TELEGRAM_API_ID: Optional[str] = Field(default=None, env="TELEGRAM_API_ID")
    TELEGRAM_API_HASH: Optional[str] = Field(default=None, env="TELEGRAM_API_HASH")
    TELEGRAM_PHONE: Optional[str] = Field(default=None, env="TELEGRAM_PHONE")
    
    @property
    def telegram_enabled(self) -> bool:
        """Vérifier si Telegram est configuré"""
        return bool(
            self.TELEGRAM_API_ID and 
            self.TELEGRAM_API_HASH and 
            self.TELEGRAM_PHONE
        )
    
    # ===== MASTODON (Optionnel) =====
    MASTODON_INSTANCE_URL: str = Field(
        default="https://mastodon.social",
        env="MASTODON_INSTANCE_URL"
    )
    MASTODON_ACCESS_TOKEN: Optional[str] = Field(default=None, env="MASTODON_ACCESS_TOKEN")
    
    @property
    def mastodon_enabled(self) -> bool:
        """Vérifier si Mastodon est configuré"""
        return bool(self.MASTODON_ACCESS_TOKEN)
    
    # ===== BLUESKY (Optionnel) =====
    BLUESKY_HANDLE: Optional[str] = Field(default=None, env="BLUESKY_HANDLE")
    BLUESKY_PASSWORD: Optional[str] = Field(default=None, env="BLUESKY_PASSWORD")
    
    @property
    def bluesky_enabled(self) -> bool:
        """Vérifier si Bluesky est configuré"""
        return bool(self.BLUESKY_HANDLE and self.BLUESKY_PASSWORD)
    
    # ===== TIKTOK (Optionnel) =====
    TIKTOK_SESSION_ID: Optional[str] = Field(default=None, env="TIKTOK_SESSION_ID")
    
    @property
    def tiktok_enabled(self) -> bool:
        """Vérifier si TikTok est configuré"""
        # TikTok peut fonctionner sans session ID (mode limité)
        return True
    
    # ===== COLLECTE =====
    MAX_RESULTS_PER_SOURCE: int = Field(default=50, env="MAX_RESULTS_PER_SOURCE")
    COLLECTION_INTERVAL_MINUTES: int = Field(default=60, env="COLLECTION_INTERVAL_MINUTES")
    AUTO_COLLECT_ON_START: bool = Field(default=False, env="AUTO_COLLECT_ON_START")
    
    # ===== ANALYSE =====
    HIERARCHICAL_BATCH_SIZE: int = Field(default=20, env="HIERARCHICAL_BATCH_SIZE")
    USE_EXTERNAL_AI_PRIORITY: bool = Field(default=True, env="USE_EXTERNAL_AI_PRIORITY")
    INFLUENCER_MIN_ENGAGEMENT: float = Field(default=100.0, env="INFLUENCER_MIN_ENGAGEMENT")
    
    # ===== SÉCURITÉ =====
    SECRET_KEY: str = Field(
        default="changez_cette_cle_par_une_valeur_aleatoire_tres_longue_et_securisee",
        env="SECRET_KEY"
    )
    CORS_ORIGINS: str = Field(
        default="http://localhost:8080,http://localhost:3000",
        env="CORS_ORIGINS"
    )
    ALLOWED_HOSTS: str = Field(
        default="localhost,127.0.0.1,0.0.0.0",
        env="ALLOWED_HOSTS"
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Liste des origines CORS autorisées"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(',')]
    
    @property
    def allowed_hosts_list(self) -> List[str]:
        """Liste des hosts autorisés"""
        return [host.strip() for host in self.ALLOWED_HOSTS.split(',')]
    
    # ===== RATE LIMITING =====
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    # ===== MONITORING =====
    ENABLE_PROMETHEUS: bool = Field(default=True, env="ENABLE_PROMETHEUS")
    
    # ===== PDF GENERATION =====
    REPORT_DEFAULT_LANGUAGE: str = Field(default="fr", env="REPORT_DEFAULT_LANGUAGE")
    REPORT_DATE_FORMAT: str = Field(default="%d/%m/%Y", env="REPORT_DATE_FORMAT")
    
    # ===== GÉOLOCALISATION =====
    ENABLE_GEOLOCATION: bool = Field(default=True, env="ENABLE_GEOLOCATION")
    GEOLOCATION_API_KEY: Optional[str] = Field(default=None, env="GEOLOCATION_API_KEY")
    
    # ===== STORAGE =====
    REPORTS_STORAGE_PATH: str = Field(default="/app/reports", env="REPORTS_STORAGE_PATH")
    REPORTS_RETENTION_DAYS: int = Field(default=90, env="REPORTS_RETENTION_DAYS")
    
    # ===== ADVANCED FEATURES =====
    ENABLE_NETWORK_ANALYSIS: bool = Field(default=True, env="ENABLE_NETWORK_ANALYSIS")
    ENABLE_ANOMALY_DETECTION: bool = Field(default=True, env="ENABLE_ANOMALY_DETECTION")
    ENABLE_TOPIC_MODELING: bool = Field(default=True, env="ENABLE_TOPIC_MODELING")
    
    # ===== PERFORMANCE =====
    WORKERS: int = Field(default=4, env="WORKERS")
    REQUEST_TIMEOUT: int = Field(default=30, env="REQUEST_TIMEOUT")
    
    # ===== BACKUP =====
    ENABLE_AUTO_BACKUP: bool = Field(default=False, env="ENABLE_AUTO_BACKUP")
    BACKUP_INTERVAL_HOURS: int = Field(default=24, env="BACKUP_INTERVAL_HOURS")
    
    # ===== NOTIFICATIONS =====
    NOTIFICATION_CHANNELS: str = Field(default="email", env="NOTIFICATION_CHANNELS")
    WEBHOOK_URL: Optional[str] = Field(default=None, env="WEBHOOK_URL")
    SLACK_WEBHOOK_URL: Optional[str] = Field(default=None, env="SLACK_WEBHOOK_URL")
    
    @property
    def notification_channels_list(self) -> List[str]:
        """Liste des canaux de notification activés"""
        return [ch.strip() for ch in self.NOTIFICATION_CHANNELS.split(',')]
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True
    
    # ===== MÉTHODES UTILITAIRES =====
    
    def get_available_collectors(self) -> List[str]:
        """Obtenir la liste des collecteurs disponibles"""
        collectors = []
        
        if self.youtube_enabled:
            collectors.append('youtube')
        if self.reddit_enabled:
            collectors.append('reddit')
        if self.gnews_enabled:
            collectors.append('google_news')
        if self.google_search_enabled:
            collectors.append('google_search')
        if self.telegram_enabled:
            collectors.append('telegram')
        if self.mastodon_enabled:
            collectors.append('mastodon')
        if self.bluesky_enabled:
            collectors.append('bluesky')
        if self.tiktok_enabled:
            collectors.append('tiktok')
        
        # Collecteurs sans API (toujours disponibles)
        collectors.extend(['rss'])
        
        return collectors
    
    def get_ai_services_status(self) -> dict:
        """Obtenir le statut des services IA"""
        return {
            'external': {
                'gemini': {
                    'enabled': self.gemini_enabled,
                    'priority': 1 if self.USE_EXTERNAL_AI_PRIORITY else 2
                },
                'groq': {
                    'enabled': self.groq_enabled,
                    'priority': 1 if self.USE_EXTERNAL_AI_PRIORITY else 2
                }
            },
            'local': {
                'ollama': {
                    'enabled': True,
                    'host': self.OLLAMA_HOST,
                    'default_model': self.OLLAMA_DEFAULT_MODEL,
                    'available_models': self.ollama_models_list,
                    'priority': 2 if self.USE_EXTERNAL_AI_PRIORITY else 1
                }
            }
        }
    
    def validate_critical_config(self) -> tuple[bool, List[str]]:
        """
        Valider que la configuration minimale est présente
        
        Returns:
            (is_valid, missing_items)
        """
        missing = []
        
        # Base de données (critique)
        if not self.DATABASE_URL:
            missing.append("DATABASE_URL")
        
        # Au moins un service IA (critique pour analyse)
        has_ai = (
            self.gemini_enabled or 
            self.groq_enabled or 
            self.OLLAMA_HOST
        )
        if not has_ai:
            missing.append("AI_SERVICE (Gemini, Groq ou Ollama)")
        
        # Au moins un collecteur (warning seulement)
        has_collector = len(self.get_available_collectors()) > 1  # >1 car RSS toujours dispo
        if not has_collector:
            # Ne pas bloquer, juste avertir
            pass
        
        is_valid = len(missing) == 0
        return is_valid, missing
    
    def get_config_summary(self) -> dict:
        """Obtenir un résumé de la configuration"""
        return {
            'app': {
                'name': self.APP_NAME,
                'version': self.APP_VERSION,
                'debug': self.DEBUG
            },
            'collectors_enabled': self.get_available_collectors(),
            'ai_services': self.get_ai_services_status(),
            'features': {
                'email_alerts': self.email_enabled,
                'network_analysis': self.ENABLE_NETWORK_ANALYSIS,
                'anomaly_detection': self.ENABLE_ANOMALY_DETECTION,
                'topic_modeling': self.ENABLE_TOPIC_MODELING,
                'geolocation': self.ENABLE_GEOLOCATION
            }
        }


# Instance globale des settings
settings = Settings()


# Fonction de validation au démarrage
def validate_and_log_config():
    """Valider et logger la configuration au démarrage"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("=" * 60)
    
    # Validation critique
    is_valid, missing = settings.validate_critical_config()
    
    if not is_valid:
        logger.error("❌ CONFIGURATION INVALIDE !")
        logger.error("   Éléments manquants:")
        for item in missing:
            logger.error(f"   - {item}")
        logger.error("   Consultez .env.example et API_KEYS_SETUP_GUIDE.md")
        raise ValueError(f"Configuration invalide: {', '.join(missing)}")
    
    # Log des services activés
    logger.info("\n📊 Services activés:")
    
    # Collecteurs
    collectors = settings.get_available_collectors()
    logger.info(f"   📡 Collecteurs ({len(collectors)}): {', '.join(collectors)}")
    
    # IA
    ai_status = settings.get_ai_services_status()
    external_enabled = [
        name for name, info in ai_status['external'].items() 
        if info['enabled']
    ]
    if external_enabled:
        logger.info(f"   🤖 IA Externe: {', '.join(external_enabled)}")
    else:
        logger.info("   🤖 IA Externe: Aucune (utilisation Ollama local uniquement)")
    
    logger.info(f"   🏠 IA Locale: Ollama ({settings.OLLAMA_DEFAULT_MODEL})")
    
    # Features
    if settings.email_enabled:
        logger.info(f"   📧 Email: Activé ({settings.SMTP_HOST})")
    
    if settings.ENABLE_NETWORK_ANALYSIS:
        logger.info("   🕸️  Analyse de réseau: Activée")
    
    if settings.ENABLE_TOPIC_MODELING:
        logger.info("   📚 Topic modeling: Activé")
    
    logger.info("\n✅ Configuration validée avec succès")
    logger.info("=" * 60 + "\n")


# Export pour usage dans l'app
__all__ = ['settings', 'validate_and_log_config', 'Settings']