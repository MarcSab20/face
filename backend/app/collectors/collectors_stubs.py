"""
Collecteurs Simplifiés
Pour démarrage de l'application
"""

import logging
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class GoogleSearchCollector:
    """Collecteur Google Custom Search"""
    
    def __init__(self):
        self.enabled = False
        logger.info("Google Search Collector initialisé (mode stub)")
    
    def collect(self, keyword: str, max_results: int = 50) -> List[Dict]:
        """Collecter (stub)"""
        logger.info(f"🔍 Google Search: {keyword} (non configuré)")
        return []


class MastodonCollector:
    """Collecteur Mastodon"""
    
    def __init__(self):
        self.enabled = False
        logger.info("Mastodon Collector initialisé (mode stub)")
    
    def collect(self, keyword: str, max_results: int = 50) -> List[Dict]:
        """Collecter (stub)"""
        logger.info(f"🔍 Mastodon: {keyword} (non configuré)")
        return []


class BlueskyCollector:
    """Collecteur Bluesky"""
    
    def __init__(self):
        self.enabled = False
        logger.info("Bluesky Collector initialisé (mode stub)")
    
    def collect(self, keyword: str, max_results: int = 50) -> List[Dict]:
        """Collecter (stub)"""
        logger.info(f"🔍 Bluesky: {keyword} (non configuré)")
        return []


class TelegramCollector:
    """Collecteur Telegram"""
    
    def __init__(self):
        self.enabled = False
        logger.info("Telegram Collector initialisé (mode stub)")
    
    def collect(self, keyword: str, max_results: int = 50) -> List[Dict]:
        """Collecter (stub)"""
        logger.info(f"🔍 Telegram: {keyword} (non configuré)")
        return []


class YouTubeCollector:
    """Collecteur YouTube simple (fallback)"""
    
    def __init__(self):
        self.enabled = False
        logger.info("YouTube Collector initialisé (fallback)")
    
    def collect(self, keyword: str, max_results: int = 50) -> List[Dict]:
        """Collecter (stub)"""
        logger.info(f"🔍 YouTube: {keyword} (utiliser YouTubeCollectorEnhanced)")
        return []


class RedditCollector:
    """Collecteur Reddit simple (fallback)"""
    
    def __init__(self):
        self.enabled = False
        logger.info("Reddit Collector initialisé (fallback)")
    
    def collect(self, keyword: str, max_results: int = 50) -> List[Dict]:
        """Collecter (stub)"""
        logger.info(f"🔍 Reddit: {keyword} (utiliser RedditCollectorEnhanced)")
        return []