
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import SearchGlobalRequest
from telethon.tl.types import InputMessagesFilterEmpty
import logging
from typing import List, Dict
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)

class TelegramCollector:
    """Collecteur pour Telegram (canaux publics)"""
    
    def __init__(self):
        self.api_id = settings.TELEGRAM_API_ID
        self.api_hash = settings.TELEGRAM_API_HASH
        
        if not self.api_id or not self.api_hash:
            logger.warning("Telegram API not configured")
            self.enabled = False
            return
        
        try:
            self.client = TelegramClient('brand_monitor_session', int(self.api_id), self.api_hash)
            logger.info("Telegram client initialized")
            self.enabled = True
        except Exception as e:
            logger.error(f"Telegram error: {str(e)}")
            self.enabled = False
    
    def collect(self, keyword: str, max_results: int = 50) -> List[Dict]:
        """Collecter les messages Telegram mentionnant un mot-clé"""
        if not self.enabled:
            return []
        
        mentions = []
        
        try:
            with self.client:
                logger.info(f"Recherche Telegram pour '{keyword}'")
                
                # Note: Recherche limitée aux canaux publics
                # Pour une recherche complète, il faudrait implémenter une logique plus complexe
                
                logger.info(f"Telegram: Recherche simplifiée (canaux publics limités)")
                
                # Exemple de recherche dans un canal spécifique
                # Vous pouvez ajouter vos propres canaux ici
                channels = ['@news', '@technology']  # Exemples
                
                for channel_username in channels:
                    try:
                        channel = self.client.get_entity(channel_username)
                        messages = self.client.get_messages(channel, limit=50, search=keyword)
                        
                        for message in messages:
                            if not message.message:
                                continue
                            
                            mention = {
                                'source': 'telegram',
                                'source_url': f"https://t.me/{channel_username.replace('@', '')}/{message.id}",
                                'title': f"Message dans {channel_username}",
                                'content': message.message[:1000],
                                'author': channel_username,
                                'published_at': message.date,
                                'engagement_score': float(getattr(message, 'views', 0) or 0),
                                'metadata': {
                                    'message_id': message.id,
                                    'views': getattr(message, 'views', 0),
                                    'channel': channel_username,
                                }
                            }
                            mentions.append(mention)
                            
                            if len(mentions) >= max_results:
                                break
                    except Exception as e:
                        logger.debug(f"Erreur canal {channel_username}: {str(e)}")
                        continue
                    
                    if len(mentions) >= max_results:
                        break
            
            logger.info(f"Telegram: {len(mentions)} messages trouvés")
            return mentions
            
        except Exception as e:
            logger.error(f"Erreur Telegram: {str(e)}")
            return mentions