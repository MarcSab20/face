"""
Collecteur TikTok Professionnel avec Commentaires
Utilise TikTokApi (unofficial) pour collecter vidéos + commentaires
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class TikTokComment:
    """Représente un commentaire TikTok"""
    author: str
    text: str
    likes: int
    created_at: datetime
    reply_count: int


@dataclass
class TikTokVideo:
    """Représente une vidéo TikTok avec métadonnées complètes"""
    video_id: str
    description: str
    author: str
    author_id: str
    created_at: datetime
    view_count: int
    like_count: int
    comment_count: int
    share_count: int
    video_url: str
    comments: List[TikTokComment]
    engagement_score: float


class TikTokCollectorEnhanced:
    """
    Collecteur TikTok professionnel avec commentaires
    
    Note: TikTok n'a pas d'API officielle gratuite.
    On utilise TikTokApi (unofficial) avec précautions.
    """
    
    def __init__(self):
        try:
            from TikTokApi import TikTokApi
            self.api = TikTokApi()
            self.enabled = True
            logger.info("TikTok Enhanced Collector initialisé")
        except ImportError:
            logger.warning("TikTokApi non installé. Installer avec: pip install TikTokApi")
            self.enabled = False
        except Exception as e:
            logger.error(f"Erreur initialisation TikTok: {e}")
            self.enabled = False
    
    async def search_videos(
        self,
        keyword: str,
        max_results: int = 30
    ) -> List[TikTokVideo]:
        """
        Rechercher des vidéos TikTok avec leurs commentaires
        
        Args:
            keyword: Mot-clé de recherche
            max_results: Nombre max de résultats
            
        Returns:
            Liste de vidéos avec commentaires
        """
        if not self.enabled:
            logger.warning("TikTok collector non activé")
            return []
        
        try:
            logger.info(f"🔍 Recherche TikTok: '{keyword}' (max {max_results})")
            
            videos = []
            
            # Contexte async pour TikTokApi
            async with self.api:
                # Recherche de vidéos
                search_results = self.api.search.videos(keyword, count=max_results)
                
                async for video_data in search_results:
                    video = await self._parse_video_with_comments(video_data)
                    if video:
                        videos.append(video)
                        logger.info(f"  ✓ @{video.author}: {video.description[:50]}... - {len(video.comments)} commentaires")
            
            logger.info(f"✅ {len(videos)} vidéos TikTok collectées")
            return videos
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche TikTok: {e}")
            return []
    
    async def get_user_videos(
        self,
        username: str,
        max_results: int = 30
    ) -> List[TikTokVideo]:
        """Récupérer les vidéos d'un utilisateur TikTok"""
        
        if not self.enabled:
            return []
        
        try:
            videos = []
            
            async with self.api:
                user = self.api.user(username)
                user_videos = user.videos(count=max_results)
                
                async for video_data in user_videos:
                    video = await self._parse_video_with_comments(video_data)
                    if video:
                        videos.append(video)
            
            return videos
            
        except Exception as e:
            logger.error(f"Erreur récupération vidéos @{username}: {e}")
            return []
    
    async def _parse_video_with_comments(
        self,
        video_data
    ) -> Optional[TikTokVideo]:
        """
        Parser une vidéo TikTok et récupérer ses commentaires
        
        Args:
            video_data: Objet vidéo TikTokApi
            
        Returns:
            TikTokVideo avec commentaires
        """
        try:
            video_info = video_data.as_dict
            stats = video_info.get('stats', {})
            author_info = video_info.get('author', {})
            
            # Récupérer les commentaires
            comments = await self._get_video_comments(video_data, max_comments=100)
            
            # Calculer score d'engagement
            engagement_score = (
                stats.get('playCount', 0) * 1.0 +
                stats.get('diggCount', 0) * 10.0 +
                stats.get('commentCount', 0) * 50.0 +
                stats.get('shareCount', 0) * 100.0
            )
            
            return TikTokVideo(
                video_id=video_info.get('id'),
                description=video_info.get('desc', ''),
                author=author_info.get('uniqueId', 'Unknown'),
                author_id=author_info.get('id', ''),
                created_at=datetime.fromtimestamp(video_info.get('createTime', 0)),
                view_count=stats.get('playCount', 0),
                like_count=stats.get('diggCount', 0),
                comment_count=stats.get('commentCount', 0),
                share_count=stats.get('shareCount', 0),
                video_url=f"https://www.tiktok.com/@{author_info.get('uniqueId')}/video/{video_info.get('id')}",
                comments=comments,
                engagement_score=engagement_score
            )
            
        except Exception as e:
            logger.error(f"Erreur parsing vidéo TikTok: {e}")
            return None
    
    async def _get_video_comments(
        self,
        video,
        max_comments: int = 100
    ) -> List[TikTokComment]:
        """Récupérer les commentaires d'une vidéo"""
        
        comments = []
        
        try:
            comment_iterator = video.comments(count=max_comments)
            
            async for comment_data in comment_iterator:
                comment_dict = comment_data.as_dict
                
                parsed_comment = TikTokComment(
                    author=comment_dict.get('user', {}).get('uniqueId', 'Unknown'),
                    text=comment_dict.get('text', ''),
                    likes=comment_dict.get('digg_count', 0),
                    created_at=datetime.fromtimestamp(comment_dict.get('create_time', 0)),
                    reply_count=comment_dict.get('reply_comment_total', 0)
                )
                
                comments.append(parsed_comment)
                
                if len(comments) >= max_comments:
                    break
            
        except Exception as e:
            logger.debug(f"Erreur récupération commentaires: {e}")
        
        return comments
    
    def convert_to_mentions(
        self,
        videos: List[TikTokVideo],
        keyword_id: int
    ) -> List[Dict]:
        """
        Convertir les vidéos TikTok en format mentions pour la base de données
        
        Args:
            videos: Liste de vidéos TikTok
            keyword_id: ID du mot-clé associé
            
        Returns:
            Liste de mentions formatées
        """
        mentions = []
        
        for video in videos:
            # Mention principale (la vidéo)
            video_mention = {
                'keyword_id': keyword_id,
                'source': 'tiktok',
                'source_url': video.video_url,
                'title': f"@{video.author} - {video.description[:100]}",
                'content': video.description,
                'author': video.author,
                'engagement_score': float(video.engagement_score),
                'published_at': video.created_at,
                'metadata': {
                    'video_id': video.video_id,
                    'author_id': video.author_id,
                    'view_count': video.view_count,
                    'like_count': video.like_count,
                    'comment_count': video.comment_count,
                    'share_count': video.share_count,
                    'comments_collected': len(video.comments)
                }
            }
            mentions.append(video_mention)
            
            # Ajouter les commentaires significatifs
            for comment in video.comments[:50]:  # Top 50 commentaires
                comment_mention = {
                    'keyword_id': keyword_id,
                    'source': 'tiktok_comment',
                    'source_url': video.video_url,
                    'title': f"Commentaire sur vidéo de @{video.author}",
                    'content': comment.text,
                    'author': comment.author,
                    'engagement_score': float(comment.likes * 2),
                    'published_at': comment.created_at,
                    'metadata': {
                        'parent_video_id': video.video_id,
                        'parent_author': video.author,
                        'likes': comment.likes,
                        'reply_count': comment.reply_count
                    }
                }
                mentions.append(comment_mention)
        
        logger.info(f"✅ Converti {len(videos)} vidéos en {len(mentions)} mentions")
        return mentions


# Installation et configuration
def get_tiktok_setup_instructions() -> str:
    """Instructions pour configurer TikTok collector"""
    return """
    📱 Configuration TikTok Collector:
    
    1. Installer TikTokApi:
       pip install TikTokApi
       playwright install
    
    2. IMPORTANT - Limites et Risques:
       - API non officielle (peut casser)
       - Rate limiting strict
       - Besoin de Playwright (navigateur headless)
       - Peut nécessiter proxy pour éviter blocage IP
    
    3. Utilisation responsable:
       - Limiter les requêtes (max 10-20/heure)
       - Ajouter delays entre requêtes
       - Utiliser rotation de proxies si volume élevé
    
    4. Alternative: TikTok Official API
       - Requiert approbation TikTok
       - Accès limité aux données publiques
       - Plus stable mais plus restrictif
    """


if __name__ == '__main__':
    # Test du collecteur
    async def test():
        collector = TikTokCollectorEnhanced()
        
        if not collector.enabled:
            print("❌ TikTok collector non disponible")
            print(get_tiktok_setup_instructions())
            return
        
        print("\n🔍 Test recherche TikTok...")
        videos = await collector.search_videos('Cameroun politique', max_results=3)
        
        for video in videos:
            print(f"\n📹 @{video.author}: {video.description[:50]}...")
            print(f"   Vues: {video.view_count:,} | Likes: {video.like_count:,}")
            print(f"   Commentaires collectés: {len(video.comments)}")
    
    asyncio.run(test())