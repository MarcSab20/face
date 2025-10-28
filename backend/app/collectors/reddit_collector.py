import praw
import logging
from typing import List, Dict
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)

class RedditCollector:
    """Collecteur pour Reddit via l'API PRAW"""
    
    def __init__(self):
        if not settings.REDDIT_CLIENT_ID or not settings.REDDIT_CLIENT_SECRET:
            logger.warning("Reddit API credentials not configured")
            self.reddit = None
            return
            
        try:
            self.reddit = praw.Reddit(
                client_id=settings.REDDIT_CLIENT_ID,
                client_secret=settings.REDDIT_CLIENT_SECRET,
                user_agent=settings.REDDIT_USER_AGENT
            )
            logger.info("Reddit API initialisée avec succès")
        except Exception as e:
            logger.error(f"Erreur d'initialisation Reddit: {str(e)}")
            self.reddit = None
    
    def collect(self, keyword: str, max_results: int = 50) -> List[Dict]:
        """
        Collecter les mentions d'un mot-clé sur Reddit
        
        Args:
            keyword: Mot-clé à rechercher
            max_results: Nombre maximum de résultats
            
        Returns:
            Liste de mentions trouvées
        """
        if not self.reddit:
            logger.warning("Reddit collector not initialized")
            return []
        
        mentions = []
        
        try:
            logger.info(f"Recherche Reddit pour '{keyword}'")
            
            # Recherche sur tous les subreddits
            for submission in self.reddit.subreddit('all').search(
                keyword, 
                limit=max_results,
                sort='new',
                time_filter='week'
            ):
                mention = {
                    'source': 'reddit',
                    'source_url': f"https://reddit.com{submission.permalink}",
                    'title': submission.title,
                    'content': submission.selftext[:1000] if submission.selftext else '',
                    'author': str(submission.author) if submission.author else '[deleted]',
                    'published_at': datetime.fromtimestamp(submission.created_utc),
                    'engagement_score': float(submission.score + submission.num_comments),
                    'metadata': {
                        'subreddit': submission.subreddit.display_name,
                        'upvote_ratio': submission.upvote_ratio,
                        'num_comments': submission.num_comments,
                        'score': submission.score,
                        'is_self': submission.is_self,
                        'post_hint': getattr(submission, 'post_hint', None)
                    }
                }
                mentions.append(mention)
            
            # Rechercher aussi dans les commentaires des posts populaires
            if len(mentions) < max_results:
                for submission in self.reddit.subreddit('all').search(
                    keyword, 
                    limit=10,
                    sort='hot',
                    time_filter='week'
                ):
                    submission.comments.replace_more(limit=0)
                    for comment in submission.comments.list()[:20]:
                        if keyword.lower() in comment.body.lower():
                            mention = {
                                'source': 'reddit',
                                'source_url': f"https://reddit.com{comment.permalink}",
                                'title': f"Comment on: {submission.title}",
                                'content': comment.body[:1000],
                                'author': str(comment.author) if comment.author else '[deleted]',
                                'published_at': datetime.fromtimestamp(comment.created_utc),
                                'engagement_score': float(comment.score),
                                'metadata': {
                                    'subreddit': submission.subreddit.display_name,
                                    'parent_title': submission.title,
                                    'score': comment.score,
                                    'is_comment': True
                                }
                            }
                            mentions.append(mention)
                            
                            if len(mentions) >= max_results:
                                break
                    
                    if len(mentions) >= max_results:
                        break
            
            logger.info(f"Reddit: {len(mentions)} mentions trouvées pour '{keyword}'")
            return mentions[:max_results]
            
        except Exception as e:
            logger.error(f"Erreur lors de la collecte Reddit: {str(e)}")
            return mentions
    
    def get_trending_subreddits(self) -> List[str]:
        """Obtenir les subreddits tendances"""
        if not self.reddit:
            return []
        
        try:
            return [sr.display_name for sr in self.reddit.subreddits.popular(limit=50)]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des subreddits: {str(e)}")
            return []