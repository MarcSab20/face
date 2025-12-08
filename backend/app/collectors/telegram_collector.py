"""
Collecteur Telegram Avancé avec Telethon
Surveillance de chaînes/groupes Telegram
"""

import logging
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from telethon import TelegramClient
from telethon.tl.types import Channel, User
from telethon.errors import SessionPasswordNeededError

logger = logging.getLogger(__name__)


class TelegramCollectorAdvanced:
    """
    Collecteur Telegram professionnel
    
    Utilise Telethon pour:
    - Surveiller des chaînes publiques
    - Surveiller des groupes (si membre)
    - Récupérer l'historique des messages
    """
    
    def __init__(
        self,
        api_id: str,
        api_hash: str,
        phone: str,
        session_name: str = "brand_monitor"
    ):
        """
        Initialiser le client Telegram
        
        Args:
            api_id: ID de l'application Telegram
            api_hash: Hash de l'application
            phone: Numéro de téléphone
            session_name: Nom de la session
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        
        self.client = TelegramClient(session_name, api_id, api_hash)
        self.is_connected = False
        
        logger.info("✅ Telegram Collector initialisé")
    
    async def connect(self):
        """Se connecter à Telegram"""
        if self.is_connected:
            return
        
        try:
            await self.client.start(phone=self.phone)
            self.is_connected = True
            logger.info("✅ Connecté à Telegram")
        except Exception as e:
            logger.error(f"❌ Erreur connexion Telegram: {e}")
            raise
    
    async def collect_channel_messages(
        self,
        channel_username: str,
        limit: int = 50,
        since_hours: int = 24
    ) -> List[Dict]:
        """
        Collecter les messages récents d'une chaîne
        
        Args:
            channel_username: Nom d'utilisateur de la chaîne (ex: @france24_fr)
            limit: Nombre maximum de messages
            since_hours: Collecter les messages des X dernières heures
            
        Returns:
            Liste de messages
        """
        if not self.is_connected:
            await self.connect()
        
        # Nettoyer le nom d'utilisateur
        if not channel_username.startswith('@'):
            channel_username = f'@{channel_username}'
        
        logger.info(f"🔍 Collecte Telegram: {channel_username}")
        
        try:
            # Obtenir l'entité de la chaîne
            channel = await self.client.get_entity(channel_username)
            
            # Calculer la date limite
            since_date = datetime.now() - timedelta(hours=since_hours)
            
            messages = []
            
            # Itérer sur les messages
            async for message in self.client.iter_messages(
                channel,
                limit=limit,
                offset_date=since_date
            ):
                try:
                    # Extraire les données du message
                    msg_data = {
                        'id': message.id,
                        'text': message.text or '',
                        'date': message.date,
                        'views': message.views or 0,
                        'forwards': message.forwards or 0,
                        'replies': message.replies.replies if message.replies else 0,
                        'url': f"https://t.me/{channel_username.lstrip('@')}/{message.id}",
                        'channel': channel_username,
                        'channel_title': channel.title if hasattr(channel, 'title') else channel_username,
                        'has_media': message.media is not None,
                        'media_type': type(message.media).__name__ if message.media else None,
                        'source': 'telegram'
                    }
                    
                    # Ajouter infos de l'expéditeur si disponible
                    if message.sender:
                        msg_data['sender_name'] = getattr(message.sender, 'first_name', 'Inconnu')
                        if hasattr(message.sender, 'username'):
                            msg_data['sender_username'] = message.sender.username
                    
                    messages.append(msg_data)
                    
                except Exception as e:
                    logger.error(f"Erreur parsing message: {e}")
                    continue
            
            logger.info(f"✅ {len(messages)} messages collectés")
            return messages
            
        except Exception as e:
            logger.error(f"❌ Erreur collecte Telegram: {e}")
            return []
    
    async def get_channel_info(self, channel_username: str) -> Optional[Dict]:
        """
        Obtenir les informations d'une chaîne
        
        Returns:
            Informations de la chaîne ou None
        """
        if not self.is_connected:
            await self.connect()
        
        if not channel_username.startswith('@'):
            channel_username = f'@{channel_username}'
        
        try:
            channel = await self.client.get_entity(channel_username)
            
            if isinstance(channel, Channel):
                return {
                    'id': channel.id,
                    'title': channel.title,
                    'username': channel.username,
                    'description': channel.about if hasattr(channel, 'about') else '',
                    'participants_count': channel.participants_count if hasattr(channel, 'participants_count') else None,
                    'verified': channel.verified if hasattr(channel, 'verified') else False,
                    'restricted': channel.restricted if hasattr(channel, 'restricted') else False
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur récupération info chaîne: {e}")
            return None
    
    async def search_channels(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Rechercher des chaînes Telegram
        
        Returns:
            Liste de chaînes trouvées
        """
        if not self.is_connected:
            await self.connect()
        
        try:
            results = await self.client.get_dialogs(limit=limit)
            
            channels = []
            for dialog in results:
                if isinstance(dialog.entity, Channel):
                    if query.lower() in dialog.title.lower():
                        channels.append({
                            'title': dialog.title,
                            'username': dialog.entity.username if dialog.entity.username else None,
                            'id': dialog.entity.id
                        })
            
            return channels
            
        except Exception as e:
            logger.error(f"Erreur recherche: {e}")
            return []
    
    async def disconnect(self):
        """Se déconnecter"""
        if self.is_connected:
            await self.client.disconnect()
            self.is_connected = False
            logger.info("✅ Déconnecté de Telegram")


# Fonction utilitaire async
async def test_telegram_collector():
    """Tester le collecteur"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    
    if not all([api_id, api_hash, phone]):
        print("❌ Configuration Telegram manquante")
        return
    
    collector = TelegramCollectorAdvanced(api_id, api_hash, phone)
    
    try:
        await collector.connect()
        
        # Test: France 24 Telegram
        messages = await collector.collect_channel_messages('@france24_fr', limit=5)
        
        for msg in messages:
            print(f"\n📱 {msg['date']}")
            print(f"   {msg['text'][:100]}...")
            print(f"   Vues: {msg['views']}, Forwards: {msg['forwards']}")
        
    finally:
        await collector.disconnect()


if __name__ == '__main__':
    asyncio.run(test_telegram_collector())