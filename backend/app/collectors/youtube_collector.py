"""
Collecteur YouTube Professionnel - Avec commentaires complets
Récupère vidéos + métadonnées + tous les commentaires
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
import requests
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class YouTubeComment:
    """Représente un commentaire YouTube"""
    author: str
    text: str
    likes: int
    published_at: datetime
    reply_count: int
    is_reply: bool = False
    parent_id: Optional[str] = None


@dataclass
class YouTubeVideo:
    """Représente une vidéo YouTube avec métadonnées complètes"""
    video_id: str
    title: str
    description: str
    channel_title: str
    channel_id: str
    published_at: datetime
    view_count: int
    like_count: int
    comment_count: int
    duration: str
    thumbnail_url: str
    comments: List[YouTubeComment]
    engagement_score: float


class YouTubeCollectorEnhanced:
    """Collecteur YouTube professionnel avec gestion complète des commentaires"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
        
        if not api_key:
            logger.warning("YouTube API key manquante")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("YouTube Enhanced Collector initialisé")
    
    def search_videos(
        self, 
        keyword: str, 
        max_results: int = 50,
        order: str = 'relevance',  # relevance, date, viewCount, rating
        published_after: Optional[datetime] = None
    ) -> List[YouTubeVideo]:
        """
        Rechercher des vidéos avec métadonnées complètes
        
        Args:
            keyword: Mot-clé de recherche
            max_results: Nombre max de résultats
            order: Ordre de tri (relevance, date, viewCount, rating)
            published_after: Date minimale de publication
            
        Returns:
            Liste de vidéos avec commentaires
        """
        if not self.enabled:
            logger.warning("YouTube collector non activé")
            return []
        
        try:
            logger.info(f"🔍 Recherche YouTube: '{keyword}' (max {max_results})")
            
            # Étape 1: Recherche des vidéos
            video_ids = self._search_video_ids(keyword, max_results, order, published_after)
            
            if not video_ids:
                logger.info("Aucune vidéo trouvée")
                return []
            
            # Étape 2: Récupérer détails + statistiques
            videos = self._get_video_details(video_ids)
            
            # Étape 3: Récupérer les commentaires pour chaque vidéo
            for video in videos:
                video.comments = self._get_video_comments(video.video_id)
                logger.info(f"  ✓ {video.title[:50]}... - {len(video.comments)} commentaires")
            
            logger.info(f"✅ {len(videos)} vidéos collectées avec commentaires")
            return videos
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche YouTube: {e}")
            return []
    
    def _search_video_ids(
        self,
        keyword: str,
        max_results: int,
        order: str,
        published_after: Optional[datetime]
    ) -> List[str]:
        """Rechercher les IDs des vidéos"""
        
        params = {
            'part': 'id',
            'q': keyword,
            'key': self.api_key,
            'type': 'video',
            'maxResults': min(max_results, 50),  # API limit
            'order': order,
            'relevanceLanguage': 'fr',
            'videoDuration': 'any',
            'videoEmbeddable': 'true'
        }
        
        # Ajouter filtre de date si spécifié
        if published_after:
            params['publishedAfter'] = published_after.isoformat() + 'Z'
        
        try:
            response = requests.get(
                f"{self.base_url}/search",
                params=params,
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            
            video_ids = [
                item['id']['videoId'] 
                for item in data.get('items', [])
                if item.get('id', {}).get('kind') == 'youtube#video'
            ]
            
            return video_ids
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur recherche vidéos: {e}")
            return []
    
    def _get_video_details(self, video_ids: List[str]) -> List[YouTubeVideo]:
        """Récupérer les détails complets des vidéos"""
        
        if not video_ids:
            return []
        
        # YouTube API accepte jusqu'à 50 IDs par requête
        videos = []
        
        for i in range(0, len(video_ids), 50):
            batch_ids = video_ids[i:i+50]
            
            params = {
                'part': 'snippet,statistics,contentDetails',
                'id': ','.join(batch_ids),
                'key': self.api_key
            }
            
            try:
                response = requests.get(
                    f"{self.base_url}/videos",
                    params=params,
                    timeout=15
                )
                response.raise_for_status()
                data = response.json()
                
                for item in data.get('items', []):
                    video = self._parse_video_item(item)
                    if video:
                        videos.append(video)
                        
            except requests.exceptions.RequestException as e:
                logger.error(f"Erreur récupération détails: {e}")
                continue
        
        return videos
    
    def _parse_video_item(self, item: dict) -> Optional[YouTubeVideo]:
        """Parser un item vidéo de l'API YouTube"""
        
        try:
            video_id = item['id']
            snippet = item.get('snippet', {})
            statistics = item.get('statistics', {})
            content_details = item.get('contentDetails', {})
            
            # Calculer score d'engagement
            views = int(statistics.get('viewCount', 0))
            likes = int(statistics.get('likeCount', 0))
            comments_count = int(statistics.get('commentCount', 0))
            
            engagement_score = views + (likes * 10) + (comments_count * 50)
            
            # Parser la date de publication
            published_at = datetime.fromisoformat(
                snippet.get('publishedAt', '').replace('Z', '+00:00')
            )
            
            return YouTubeVideo(
                video_id=video_id,
                title=snippet.get('title', ''),
                description=snippet.get('description', ''),
                channel_title=snippet.get('channelTitle', ''),
                channel_id=snippet.get('channelId', ''),
                published_at=published_at,
                view_count=views,
                like_count=likes,
                comment_count=comments_count,
                duration=content_details.get('duration', ''),
                thumbnail_url=snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                comments=[],  # Sera rempli plus tard
                engagement_score=engagement_score
            )
            
        except Exception as e:
            logger.error(f"Erreur parsing vidéo: {e}")
            return None
    
    def _get_video_comments(
        self, 
        video_id: str, 
        max_comments: int = 100
    ) -> List[YouTubeComment]:
        """
        Récupérer tous les commentaires d'une vidéo (top-level + réponses)
        
        Args:
            video_id: ID de la vidéo
            max_comments: Nombre maximum de commentaires à récupérer
            
        Returns:
            Liste de commentaires
        """
        comments = []
        
        params = {
            'part': 'snippet,replies',
            'videoId': video_id,
            'key': self.api_key,
            'maxResults': min(max_comments, 100),  # API limit
            'order': 'relevance',  # Les plus pertinents d'abord
            'textFormat': 'plainText'
        }
        
        try:
            # Récupérer les commentaires principaux
            next_page_token = None
            collected = 0
            
            while collected < max_comments:
                if next_page_token:
                    params['pageToken'] = next_page_token
                
                response = requests.get(
                    f"{self.base_url}/commentThreads",
                    params=params,
                    timeout=15
                )
                
                # Si les commentaires sont désactivés, retourner liste vide
                if response.status_code == 403:
                    logger.debug(f"Commentaires désactivés pour vidéo {video_id}")
                    break
                
                response.raise_for_status()
                data = response.json()
                
                # Parser les commentaires
                for item in data.get('items', []):
                    # Commentaire principal
                    top_comment = self._parse_comment(item['snippet']['topLevelComment'])
                    if top_comment:
                        comments.append(top_comment)
                        collected += 1
                    
                    # Réponses au commentaire (si présentes)
                    if 'replies' in item:
                        for reply_item in item['replies']['comments']:
                            reply = self._parse_comment(reply_item, is_reply=True)
                            if reply:
                                comments.append(reply)
                                collected += 1
                                
                                if collected >= max_comments:
                                    break
                    
                    if collected >= max_comments:
                        break
                
                # Pagination
                next_page_token = data.get('nextPageToken')
                if not next_page_token or collected >= max_comments:
                    break
            
            logger.debug(f"Collecté {len(comments)} commentaires pour vidéo {video_id}")
            return comments
            
        except requests.exceptions.RequestException as e:
            logger.debug(f"Impossible de récupérer commentaires vidéo {video_id}: {e}")
            return []
    
    def _parse_comment(
        self, 
        comment_data: dict, 
        is_reply: bool = False
    ) -> Optional[YouTubeComment]:
        """Parser un commentaire YouTube"""
        
        try:
            snippet = comment_data.get('snippet', {})
            
            return YouTubeComment(
                author=snippet.get('authorDisplayName', 'Anonyme'),
                text=snippet.get('textDisplay', ''),
                likes=int(snippet.get('likeCount', 0)),
                published_at=datetime.fromisoformat(
                    snippet.get('publishedAt', '').replace('Z', '+00:00')
                ),
                reply_count=0,  # Les réponses n'ont pas de reply_count
                is_reply=is_reply,
                parent_id=snippet.get('parentId') if is_reply else None
            )
            
        except Exception as e:
            logger.error(f"Erreur parsing commentaire: {e}")
            return None
    
    def get_channel_videos(
        self,
        channel_id: str,
        max_results: int = 20
    ) -> List[YouTubeVideo]:
        """Récupérer les vidéos d'une chaîne spécifique"""
        
        if not self.enabled:
            return []
        
        try:
            # Rechercher les vidéos de la chaîne
            params = {
                'part': 'id',
                'channelId': channel_id,
                'key': self.api_key,
                'type': 'video',
                'maxResults': min(max_results, 50),
                'order': 'date'
            }
            
            response = requests.get(
                f"{self.base_url}/search",
                params=params,
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            
            video_ids = [
                item['id']['videoId'] 
                for item in data.get('items', [])
            ]
            
            # Récupérer les détails
            videos = self._get_video_details(video_ids)
            
            # Récupérer les commentaires
            for video in videos:
                video.comments = self._get_video_comments(video.video_id)
            
            return videos
            
        except Exception as e:
            logger.error(f"Erreur récupération vidéos chaîne: {e}")
            return []
    
    def convert_to_mentions(self, videos: List[YouTubeVideo], keyword_id: int) -> List[Dict]:
        """
        Convertir les vidéos YouTube en format mentions pour la base de données
        
        Args:
            videos: Liste de vidéos YouTube
            keyword_id: ID du mot-clé associé
            
        Returns:
            Liste de mentions formatées
        """
        mentions = []
        
        for video in videos:
            # Mention principale (la vidéo elle-même)
            video_mention = {
                'keyword_id': keyword_id,
                'source': 'youtube',
                'source_url': f"https://www.youtube.com/watch?v={video.video_id}",
                'title': video.title,
                'content': video.description[:2000],  # Limiter taille
                'author': video.channel_title,
                'engagement_score': float(video.engagement_score),
                'published_at': video.published_at,
                'metadata': {
                    'video_id': video.video_id,
                    'channel_id': video.channel_id,
                    'thumbnail': video.thumbnail_url,
                    'view_count': video.view_count,
                    'like_count': video.like_count,
                    'comment_count': video.comment_count,
                    'duration': video.duration,
                    'comments_collected': len(video.comments)
                }
            }
            mentions.append(video_mention)
            
            # Ajouter les commentaires comme mentions séparées (optionnel)
            # Cela permet de les analyser individuellement pour le sentiment
            for comment in video.comments[:50]:  # Top 50 commentaires
                comment_mention = {
                    'keyword_id': keyword_id,
                    'source': 'youtube_comment',
                    'source_url': f"https://www.youtube.com/watch?v={video.video_id}&lc={comment.parent_id or 'top'}",
                    'title': f"Commentaire sur: {video.title[:100]}",
                    'content': comment.text[:1000],
                    'author': comment.author,
                    'engagement_score': float(comment.likes * 2),  # Likes = engagement
                    'published_at': comment.published_at,
                    'metadata': {
                        'parent_video_id': video.video_id,
                        'parent_video_title': video.title,
                        'likes': comment.likes,
                        'is_reply': comment.is_reply
                    }
                }
                mentions.append(comment_mention)
        
        logger.info(f"✅ Converti {len(videos)} vidéos en {len(mentions)} mentions (avec commentaires)")
        return mentions


# Fonction utilitaire pour obtenir les statistiques d'utilisation de l'API
def check_youtube_quota_usage(api_key: str) -> Dict:
    """
    Vérifier l'utilisation du quota YouTube API
    
    Note: YouTube Data API v3 a une limite de 10,000 unités/jour
    - search: 100 unités
    - videos.list: 1 unité
    - commentThreads.list: 1 unité
    """
    return {
        'daily_quota': 10000,
        'cost_per_search': 100,
        'cost_per_video_details': 1,
        'cost_per_comments_page': 1,
        'note': 'Vérifier https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas'
    }


if __name__ == '__main__':
    # Test du collecteur
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        print("❌ YOUTUBE_API_KEY non configurée")
        exit(1)
    
    collector = YouTubeCollectorEnhanced(api_key)
    
    # Test de recherche
    print("\n🔍 Test de recherche YouTube avec commentaires...")
    videos = collector.search_videos('Cameroun politique', max_results=3)
    
    for video in videos:
        print(f"\n📹 {video.title}")
        print(f"   Chaîne: {video.channel_title}")
        print(f"   Vues: {video.view_count:,} | Likes: {video.like_count:,}")
        print(f"   Commentaires collectés: {len(video.comments)}")
        
        if video.comments:
            print(f"\n   💬 Exemple de commentaires:")
            for comment in video.comments[:3]:
                print(f"      - {comment.author}: {comment.text[:100]}...")
                print(f"        👍 {comment.likes} likes")