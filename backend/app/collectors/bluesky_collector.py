from atproto import Client
import logging
from typing import List, Dict
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)

class BlueskyCollector:
    """Collecteur pour Bluesky (nouveau réseau social décentralisé)"""
    
    def __init__(self):
        try:
            self.client = Client()
            logger.info("Bluesky client initialized")
            self.enabled = True
        except Exception as e:
            logger.error(f"Bluesky error: {str(e)}")
            self.client = None
            self.enabled = False
    
    def collect(self, keyword: str, max_results: int = 50) -> List[Dict]:
        """Collecter les posts Bluesky mentionnant un mot-clé"""
        if not self.client:
            return []
        
        mentions = []
        
        try:
            logger.info(f"Recherche Bluesky pour '{keyword}'")
            
            results = self.client.app.bsky.feed.search_posts({
                'q': keyword,
                'limit': min(max_results, 100)
            })
            
            for post in results.posts:
                author = post.author
                
                engagement_score = (
                    post.repost_count * 10 +
                    post.reply_count * 5 +
                    post.like_count * 2
                )
                
                post_id = post.uri.split('/')[-1]
                
                mention = {
                    'source': 'bluesky',
                    'source_url': f"https://bsky.app/profile/{author.handle}/post/{post_id}",
                    'title': f"Post de @{author.handle}",
                    'content': post.record.text[:1000],
                    'author': f"@{author.handle}",
                    'published_at': datetime.fromisoformat(post.record.created_at.replace('Z', '+00:00')),
                    'engagement_score': float(engagement_score),
                    'metadata': {
                        'post_uri': post.uri,
                        'reposts': post.repost_count,
                        'replies': post.reply_count,
                        'likes': post.like_count,
                    }
                }
                mentions.append(mention)
            
            logger.info(f"Bluesky: {len(mentions)} posts trouvés")
            return mentions
            
        except Exception as e:
            logger.error(f"Erreur Bluesky: {str(e)}")
            return mentions