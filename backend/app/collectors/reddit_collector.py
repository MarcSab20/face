"""
Collecteur Reddit Professionnel - Avec commentaires complets
Récupère posts + tous les commentaires (arbre complet)
"""

import praw
import logging
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RedditComment:
    """Représente un commentaire Reddit"""
    author: str
    text: str
    score: int
    created_at: datetime
    is_submitter: bool
    depth: int  # Niveau de profondeur dans l'arbre
    parent_id: Optional[str]
    awards_count: int


@dataclass
class RedditPost:
    """Représente un post Reddit avec métadonnées complètes"""
    post_id: str
    title: str
    selftext: str
    author: str
    subreddit: str
    score: int
    upvote_ratio: float
    num_comments: int
    created_at: datetime
    url: str
    is_self: bool
    post_hint: Optional[str]
    comments: List[RedditComment]
    engagement_score: float


class RedditCollectorEnhanced:
    """Collecteur Reddit professionnel avec gestion complète des commentaires"""
    
    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        
        if not client_id or not client_secret:
            logger.warning("Reddit API credentials manquantes")
            self.reddit = None
            self.enabled = False
        else:
            try:
                self.reddit = praw.Reddit(
                    client_id=client_id,
                    client_secret=client_secret,
                    user_agent=user_agent
                )
                # Test de connexion
                _ = self.reddit.user.me()
                self.enabled = True
                logger.info("Reddit Enhanced Collector initialisé")
            except Exception as e:
                logger.error(f"Erreur initialisation Reddit: {e}")
                self.reddit = None
                self.enabled = False
    
    def search_posts(
        self,
        keyword: str,
        max_results: int = 50,
        time_filter: str = 'week',  # hour, day, week, month, year, all
        sort: str = 'relevance',  # relevance, hot, top, new, comments
        subreddits: Optional[List[str]] = None
    ) -> List[RedditPost]:
        """
        Rechercher des posts Reddit avec tous leurs commentaires
        
        Args:
            keyword: Mot-clé de recherche
            max_results: Nombre max de résultats
            time_filter: Filtre temporel
            sort: Ordre de tri
            subreddits: Liste de subreddits (None = all)
            
        Returns:
            Liste de posts avec commentaires complets
        """
        if not self.enabled:
            logger.warning("Reddit collector non activé")
            return []
        
        try:
            logger.info(f"🔍 Recherche Reddit: '{keyword}' (max {max_results})")
            
            # Définir la cible de recherche
            if subreddits and len(subreddits) > 0:
                target = self.reddit.subreddit('+'.join(subreddits))
                logger.info(f"   Subreddits: {', '.join(subreddits)}")
            else:
                target = self.reddit.subreddit('all')
                logger.info(f"   Recherche globale (r/all)")
            
            posts = []
            
            # Recherche des submissions
            submissions = target.search(
                keyword,
                limit=max_results,
                sort=sort,
                time_filter=time_filter
            )
            
            for submission in submissions:
                post = self._parse_submission_with_comments(submission)
                if post:
                    posts.append(post)
                    logger.info(f"  ✓ r/{post.subreddit}: {post.title[:50]}... - {len(post.comments)} commentaires")
            
            logger.info(f"✅ {len(posts)} posts collectés avec commentaires")
            return posts
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche Reddit: {e}")
            return []
    
    def get_subreddit_posts(
        self,
        subreddit_name: str,
        sort: str = 'hot',  # hot, new, top, rising
        limit: int = 25,
        time_filter: str = 'day'
    ) -> List[RedditPost]:
        """Récupérer les posts d'un subreddit spécifique"""
        
        if not self.enabled:
            return []
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Sélectionner la méthode selon le tri
            if sort == 'hot':
                submissions = subreddit.hot(limit=limit)
            elif sort == 'new':
                submissions = subreddit.new(limit=limit)
            elif sort == 'top':
                submissions = subreddit.top(time_filter=time_filter, limit=limit)
            elif sort == 'rising':
                submissions = subreddit.rising(limit=limit)
            else:
                submissions = subreddit.hot(limit=limit)
            
            posts = []
            for submission in submissions:
                post = self._parse_submission_with_comments(submission)
                if post:
                    posts.append(post)
            
            return posts
            
        except Exception as e:
            logger.error(f"Erreur récupération posts r/{subreddit_name}: {e}")
            return []
    
    def _parse_submission_with_comments(self, submission) -> Optional[RedditPost]:
        """
        Parser un submission Reddit et récupérer tous ses commentaires
        
        Args:
            submission: Objet praw.Submission
            
        Returns:
            RedditPost avec commentaires complets
        """
        try:
            # Expand all comments (récupère l'arbre complet)
            submission.comments.replace_more(limit=None)
            
            # Parser les commentaires récursivement
            comments = self._parse_comment_forest(submission.comments)
            
            # Calculer score d'engagement
            engagement_score = (
                submission.score * 1.0 +
                submission.num_comments * 5.0 +
                len([c for c in comments if c.score > 10]) * 2.0  # Commentaires populaires
            )
            
            return RedditPost(
                post_id=submission.id,
                title=submission.title,
                selftext=submission.selftext,
                author=str(submission.author) if submission.author else '[deleted]',
                subreddit=submission.subreddit.display_name,
                score=submission.score,
                upvote_ratio=submission.upvote_ratio,
                num_comments=submission.num_comments,
                created_at=datetime.fromtimestamp(submission.created_utc),
                url=f"https://reddit.com{submission.permalink}",
                is_self=submission.is_self,
                post_hint=getattr(submission, 'post_hint', None),
                comments=comments,
                engagement_score=engagement_score
            )
            
        except Exception as e:
            logger.error(f"Erreur parsing submission {submission.id}: {e}")
            return None
    
    def _parse_comment_forest(
        self, 
        comment_forest,
        depth: int = 0,
        max_depth: int = 10
    ) -> List[RedditComment]:
        """
        Parser récursivement l'arbre des commentaires
        
        Args:
            comment_forest: Forest de commentaires PRAW
            depth: Profondeur actuelle
            max_depth: Profondeur maximale à parser
            
        Returns:
            Liste plate de tous les commentaires
        """
        comments = []
        
        if depth > max_depth:
            return comments
        
        for comment in comment_forest:
            # Ignorer les MoreComments objects
            if isinstance(comment, praw.models.MoreComments):
                continue
            
            try:
                # Parser le commentaire
                parsed_comment = RedditComment(
                    author=str(comment.author) if comment.author else '[deleted]',
                    text=comment.body,
                    score=comment.score,
                    created_at=datetime.fromtimestamp(comment.created_utc),
                    is_submitter=comment.is_submitter,
                    depth=depth,
                    parent_id=comment.parent_id,
                    awards_count=len(comment.all_awardings) if hasattr(comment, 'all_awardings') else 0
                )
                comments.append(parsed_comment)
                
                # Parser récursivement les réponses
                if hasattr(comment, 'replies') and comment.replies:
                    replies = self._parse_comment_forest(
                        comment.replies,
                        depth=depth + 1,
                        max_depth=max_depth
                    )
                    comments.extend(replies)
                    
            except Exception as e:
                logger.debug(f"Erreur parsing commentaire: {e}")
                continue
        
        return comments
    
    def search_with_keyword_in_comments(
        self,
        keyword: str,
        subreddit_names: List[str],
        max_posts: int = 10,
        max_comments_per_post: int = 100
    ) -> List[RedditPost]:
        """
        Rechercher des posts et filtrer ceux ayant le mot-clé dans les commentaires
        
        Utile pour trouver des discussions pertinentes même si le titre ne contient pas le mot-clé
        """
        if not self.enabled:
            return []
        
        keyword_lower = keyword.lower()
        relevant_posts = []
        
        for subreddit_name in subreddit_names:
            try:
                # Récupérer les posts récents du subreddit
                posts = self.get_subreddit_posts(
                    subreddit_name,
                    sort='new',
                    limit=max_posts * 2  # On en récupère plus car on va filtrer
                )
                
                # Filtrer les posts ayant le mot-clé dans les commentaires
                for post in posts:
                    # Vérifier si le mot-clé est dans les commentaires
                    relevant_comments = [
                        c for c in post.comments
                        if keyword_lower in c.text.lower()
                    ]
                    
                    if relevant_comments:
                        # Ne garder que les commentaires pertinents
                        post.comments = relevant_comments[:max_comments_per_post]
                        relevant_posts.append(post)
                        logger.info(f"  ✓ Post pertinent trouvé: {post.title[:50]}...")
                        
                        if len(relevant_posts) >= max_posts:
                            break
                
            except Exception as e:
                logger.error(f"Erreur recherche dans r/{subreddit_name}: {e}")
                continue
        
        return relevant_posts[:max_posts]
    
    def get_user_posts_and_comments(
        self,
        username: str,
        limit: int = 100
    ) -> Dict:
        """
        Récupérer tous les posts et commentaires d'un utilisateur spécifique
        
        Utile pour suivre l'activité d'influenceurs ou activistes
        """
        if not self.enabled:
            return {'posts': [], 'comments': []}
        
        try:
            user = self.reddit.redditor(username)
            
            # Récupérer les submissions
            user_posts = []
            for submission in user.submissions.new(limit=limit):
                post = self._parse_submission_with_comments(submission)
                if post:
                    user_posts.append(post)
            
            # Récupérer les commentaires
            user_comments = []
            for comment in user.comments.new(limit=limit):
                try:
                    parsed_comment = RedditComment(
                        author=username,
                        text=comment.body,
                        score=comment.score,
                        created_at=datetime.fromtimestamp(comment.created_utc),
                        is_submitter=False,
                        depth=0,
                        parent_id=comment.parent_id,
                        awards_count=len(comment.all_awardings) if hasattr(comment, 'all_awardings') else 0
                    )
                    user_comments.append(parsed_comment)
                except Exception as e:
                    logger.debug(f"Erreur parsing commentaire utilisateur: {e}")
                    continue
            
            logger.info(f"✅ Récupéré activité u/{username}: {len(user_posts)} posts, {len(user_comments)} commentaires")
            
            return {
                'posts': user_posts,
                'comments': user_comments,
                'username': username,
                'collected_at': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Erreur récupération activité u/{username}: {e}")
            return {'posts': [], 'comments': []}
    
    def convert_to_mentions(self, posts: List[RedditPost], keyword_id: int) -> List[Dict]:
        """
        Convertir les posts Reddit en format mentions pour la base de données
        
        Args:
            posts: Liste de posts Reddit
            keyword_id: ID du mot-clé associé
            
        Returns:
            Liste de mentions formatées
        """
        mentions = []
        
        for post in posts:
            # Mention principale (le post lui-même)
            post_mention = {
                'keyword_id': keyword_id,
                'source': 'reddit',
                'source_url': post.url,
                'title': post.title,
                'content': post.selftext[:2000] if post.selftext else '[Lien externe]',
                'author': post.author,
                'engagement_score': float(post.engagement_score),
                'published_at': post.created_at,
                'metadata': {
                    'post_id': post.post_id,
                    'subreddit': post.subreddit,
                    'score': post.score,
                    'upvote_ratio': post.upvote_ratio,
                    'num_comments': post.num_comments,
                    'is_self': post.is_self,
                    'post_hint': post.post_hint,
                    'comments_collected': len(post.comments)
                }
            }
            mentions.append(post_mention)
            
            # Ajouter les commentaires significatifs comme mentions séparées
            # On garde seulement les commentaires avec un certain engagement
            significant_comments = [
                c for c in post.comments
                if c.score >= 2 or c.depth == 0  # Comments populaires ou de premier niveau
            ]
            
            for comment in significant_comments[:50]:  # Top 50 commentaires
                comment_mention = {
                    'keyword_id': keyword_id,
                    'source': 'reddit_comment',
                    'source_url': f"{post.url}/{comment.parent_id}",
                    'title': f"Commentaire sur: {post.title[:100]}",
                    'content': comment.text[:1000],
                    'author': comment.author,
                    'engagement_score': float(comment.score * 2),
                    'published_at': comment.created_at,
                    'metadata': {
                        'parent_post_id': post.post_id,
                        'parent_post_title': post.title,
                        'subreddit': post.subreddit,
                        'score': comment.score,
                        'depth': comment.depth,
                        'is_submitter': comment.is_submitter,
                        'awards_count': comment.awards_count
                    }
                }
                mentions.append(comment_mention)
        
        logger.info(f"✅ Converti {len(posts)} posts en {len(mentions)} mentions (avec commentaires)")
        return mentions
    
    def get_trending_subreddits(self, limit: int = 50) -> List[str]:
        """Obtenir les subreddits tendance"""
        if not self.enabled:
            return []
        
        try:
            return [sr.display_name for sr in self.reddit.subreddits.popular(limit=limit)]
        except Exception as e:
            logger.error(f"Erreur récupération subreddits tendance: {e}")
            return []


# Suggestions de subreddits pertinents selon les thématiques
SUGGESTED_SUBREDDITS = {
    'politique_fr': [
        'france', 'europe', 'geopolitics', 'worldnews',
        'PolitiqueFrancaise', 'Quebec', 'belgium'
    ],
    'politique_afrique': [
        'Africa', 'africanews', 'Cameroon', 'Nigeria',
        'Morocco', 'SouthAfrica'
    ],
    'technologie': [
        'technology', 'programming', 'artificial', 'MachineLearning',
        'startups', 'Entrepreneur'
    ],
    'actualites': [
        'news', 'worldnews', 'UpliftingNews', 'nottheonion'
    ],
    'societe': [
        'TrueOffMyChest', 'ChangeMyView', 'unpopularopinion',
        'NoStupidQuestions', 'OutOfTheLoop'
    ]
}


if __name__ == '__main__':
    # Test du collecteur
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    user_agent = os.getenv('REDDIT_USER_AGENT', 'BrandMonitor/1.0')
    
    if not client_id or not client_secret:
        print("❌ Reddit API credentials non configurées")
        exit(1)
    
    collector = RedditCollectorEnhanced(client_id, client_secret, user_agent)
    
    # Test de recherche
    print("\n🔍 Test de recherche Reddit avec commentaires complets...")
    posts = collector.search_posts(
        'Cameroun',
        max_results=3,
        time_filter='week',
        subreddits=['africa', 'worldnews']
    )
    
    for post in posts:
        print(f"\n📝 r/{post.subreddit}: {post.title}")
        print(f"   Auteur: u/{post.author}")
        print(f"   Score: {post.score} | Ratio: {post.upvote_ratio:.0%}")
        print(f"   Commentaires collectés: {len(post.comments)}")
        
        if post.comments:
            print(f"\n   💬 Exemples de commentaires:")
            for comment in post.comments[:3]:
                indent = "  " * comment.depth
                print(f"      {indent}- u/{comment.author} (score: {comment.score}):")
                print(f"      {indent}  {comment.text[:100]}...")