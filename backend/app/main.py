from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
import logging
import json

from app.config import settings
from app.database import get_db, init_db
from app.models import Keyword, Mention, CollectionLog
from app.collectors.rss_collector import RSSCollector
from app.collectors.reddit_collector import RedditCollector
from app.collectors.youtube_collector import YouTubeCollector
from app.collectors.tiktok_collector import TikTokCollector
from app.collectors.google_search_collector import GoogleSearchCollector
from app.collectors.google_alerts_collector import GoogleAlertsCollector
from app.sentiment_analyzer import SentimentAnalyzer
from app.collectors.mastodon_collector import MastodonCollector
from app.collectors.bluesky_collector import BlueskyCollector
from app.collectors.telegram_collector import TelegramCollector
from pydantic import BaseModel
from app.api import email_router, influencer_router, geo_router
from app.report_api import intelligent_reports_router
from app.scheduler import init_scheduler, start_scheduler
from app.scheduler import stop_scheduler

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialiser l'analyseur de sentiment
sentiment_analyzer = SentimentAnalyzer()

# Initialisation FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Système de surveillance des mentions en ligne avec analyse de sentiment"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialiser la base de données au démarrage
@app.on_event("startup")
async def startup_event():
    init_db()
    init_scheduler()
    start_scheduler()
    logger.info("Application démarrée et base de données initialisée")

# ============ Modèles Pydantic ============

class KeywordCreate(BaseModel):
    keyword: str
    sources: List[str] = ["rss", "reddit", "youtube", "google_search"]

class KeywordResponse(BaseModel):
    id: int
    keyword: str
    active: bool
    sources: str
    created_at: datetime
    last_collected: Optional[datetime]
    
    class Config:
        from_attributes = True

class MentionResponse(BaseModel):
    id: int
    keyword_id: int
    source: str
    source_url: str
    title: str
    content: str
    author: str
    engagement_score: float
    sentiment: Optional[str]
    published_at: Optional[datetime]
    collected_at: datetime
    
    class Config:
        from_attributes = True

class CollectionRequest(BaseModel):
    keyword_id: Optional[int] = None
    sources: Optional[List[str]] = None

class StatsResponse(BaseModel):
    total_keywords: int
    total_mentions: int
    mentions_today: int
    mentions_by_source: dict
    top_keywords: List[dict]
    sentiment_distribution: Optional[dict] = None

class AdvancedStatsResponse(BaseModel):
    timeline: List[dict]
    sentiment_by_source: dict
    top_engaged: List[dict]
    hourly_distribution: List[dict]
    daily_distribution: List[dict]

# ============ Routes API ============

app.include_router(email_router)
app.include_router(influencer_router)
app.include_router(geo_router)
app.include_router(intelligent_reports_router)

@app.get("/")
async def root():
    """Endpoint racine"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "features": ["sentiment_analysis", "advanced_stats", "filters"]
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# ===== Gestion des mots-clés =====

@app.post("/api/keywords", response_model=KeywordResponse)
async def create_keyword(keyword_data: KeywordCreate, db: Session = Depends(get_db)):
    """Créer un nouveau mot-clé à surveiller"""
    
    existing = db.query(Keyword).filter(Keyword.keyword == keyword_data.keyword).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce mot-clé existe déjà")
    
    keyword = Keyword(
        keyword=keyword_data.keyword,
        sources=json.dumps(keyword_data.sources),
        active=True
    )
    
    db.add(keyword)
    db.commit()
    db.refresh(keyword)
    
    logger.info(f"Mot-clé créé: {keyword_data.keyword}")
    return keyword

@app.get("/api/keywords", response_model=List[KeywordResponse])
async def get_keywords(active_only: bool = True, db: Session = Depends(get_db)):
    """Obtenir la liste des mots-clés"""
    query = db.query(Keyword)
    
    if active_only:
        query = query.filter(Keyword.active == True)
    
    keywords = query.all()
    return keywords

@app.get("/api/keywords/{keyword_id}", response_model=KeywordResponse)
async def get_keyword(keyword_id: int, db: Session = Depends(get_db)):
    """Obtenir un mot-clé spécifique"""
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    
    if not keyword:
        raise HTTPException(status_code=404, detail="Mot-clé non trouvé")
    
    return keyword

@app.delete("/api/keywords/{keyword_id}")
async def delete_keyword(keyword_id: int, db: Session = Depends(get_db)):
    """Supprimer un mot-clé"""
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    
    if not keyword:
        raise HTTPException(status_code=404, detail="Mot-clé non trouvé")
    
    db.delete(keyword)
    db.commit()
    
    logger.info(f"Mot-clé supprimé: {keyword.keyword}")
    return {"message": "Mot-clé supprimé avec succès"}

# ===== Analyse de sentiment =====

@app.post("/api/analyze-sentiment/{mention_id}")
async def analyze_mention_sentiment(mention_id: int, db: Session = Depends(get_db)):
    """Analyser le sentiment d'une mention spécifique"""
    mention = db.query(Mention).filter(Mention.id == mention_id).first()
    
    if not mention:
        raise HTTPException(status_code=404, detail="Mention non trouvée")
    
    # Analyser le sentiment
    text = f"{mention.title} {mention.content}"
    analysis = sentiment_analyzer.analyze(text)
    
    # Mettre à jour la mention
    mention.sentiment = analysis['sentiment']
    db.commit()
    
    return {
        "mention_id": mention_id,
        "sentiment": analysis['sentiment'],
        "score": analysis['score'],
        "details": analysis
    }

@app.post("/api/analyze-all-sentiments")
async def analyze_all_sentiments(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Analyser le sentiment de toutes les mentions sans sentiment"""
    mentions_without_sentiment = db.query(Mention).filter(
        or_(Mention.sentiment == None, Mention.sentiment == '')
    ).all()
    
    if not mentions_without_sentiment:
        return {"message": "Toutes les mentions ont déjà un sentiment", "count": 0}
    
    background_tasks.add_task(process_sentiment_analysis, mentions_without_sentiment, db)
    
    return {
        "message": "Analyse de sentiment lancée en arrière-plan",
        "count": len(mentions_without_sentiment)
    }

def process_sentiment_analysis(mentions: List[Mention], db: Session):
    """Traiter l'analyse de sentiment en arrière-plan"""
    for mention in mentions:
        try:
            text = f"{mention.title} {mention.content}"
            analysis = sentiment_analyzer.analyze(text)
            mention.sentiment = analysis['sentiment']
            db.commit()
        except Exception as e:
            logger.error(f"Erreur analyse sentiment mention {mention.id}: {e}")
    
    logger.info(f"Analyse de sentiment terminée pour {len(mentions)} mentions")

# ===== Collecte de données =====

@app.post("/api/collect")
async def collect_mentions(
    request: CollectionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Lancer une collecte de mentions"""
    
    if request.keyword_id:
        keywords = [db.query(Keyword).filter(Keyword.id == request.keyword_id).first()]
        if not keywords[0]:
            raise HTTPException(status_code=404, detail="Mot-clé non trouvé")
    else:
        keywords = db.query(Keyword).filter(Keyword.active == True).all()
    
    if not keywords:
        raise HTTPException(status_code=400, detail="Aucun mot-clé actif à collecter")
    
    background_tasks.add_task(run_collection, keywords, request.sources, db)
    
    return {
        "message": "Collecte lancée",
        "keywords_count": len(keywords),
        "status": "processing"
    }

async def run_collection(keywords: List[Keyword], sources: Optional[List[str]], db: Session):
    """Exécuter la collecte pour les mots-clés donnés"""
    
    collectors = {
        'rss': RSSCollector(),
        'reddit': RedditCollector(),
        'youtube': YouTubeCollector(),
        'tiktok': TikTokCollector(),
        'google_search': GoogleSearchCollector(),
        'google_alerts': GoogleAlertsCollector(),
        'mastodon': MastodonCollector(),
        'bluesky': BlueskyCollector(),
        'telegram': TelegramCollector()
    }
    
    for keyword in keywords:
        keyword_sources = sources or json.loads(keyword.sources)
        
        logger.info(f"Collecte pour '{keyword.keyword}' sur {len(keyword_sources)} sources")
        
        for source_name in keyword_sources:
            if source_name not in collectors:
                logger.warning(f"Collecteur inconnu: {source_name}")
                continue
            
            start_time = datetime.utcnow()
            collector = collectors[source_name]
            
            try:
                mentions_data = collector.collect(
                    keyword.keyword,
                    max_results=settings.MAX_RESULTS_PER_SOURCE
                )
                
                saved_count = 0
                for mention_data in mentions_data:
                    try:
                        existing = db.query(Mention).filter(
                            Mention.source_url == mention_data['source_url']
                        ).first()
                        
                        if existing:
                            continue
                        
                        # Analyser le sentiment immédiatement
                        text = f"{mention_data['title']} {mention_data['content']}"
                        sentiment_analysis = sentiment_analyzer.analyze(text)
                        
                        mention = Mention(
                            keyword_id=keyword.id,
                            source=mention_data['source'],
                            source_url=mention_data['source_url'],
                            title=mention_data['title'],
                            content=mention_data['content'],
                            author=mention_data['author'],
                            engagement_score=mention_data['engagement_score'],
                            published_at=mention_data['published_at'],
                            sentiment=sentiment_analysis['sentiment'],
                            mention_metadata=json.dumps(mention_data.get('metadata', {}))
                        )
                        
                        db.add(mention)
                        saved_count += 1
                        
                    except Exception as e:
                        logger.error(f"Erreur sauvegarde mention: {str(e)}")
                        continue
                
                db.commit()
                
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                
                log_entry = CollectionLog(
                    keyword_id=keyword.id,
                    source=source_name,
                    status='success',
                    mentions_found=saved_count,
                    execution_time=execution_time
                )
                
                db.add(log_entry)
                db.commit()
                
                logger.info(f"✓ {source_name}: {saved_count} nouvelles mentions pour '{keyword.keyword}'")
                
            except Exception as e:
                logger.error(f"✗ Erreur collecte {source_name} pour '{keyword.keyword}': {str(e)}")
                
                log_entry = CollectionLog(
                    keyword_id=keyword.id,
                    source=source_name,
                    status='error',
                    mentions_found=0,
                    error_message=str(e),
                    execution_time=(datetime.utcnow() - start_time).total_seconds()
                )
                
                db.add(log_entry)
                db.commit()
        
        keyword.last_collected = datetime.utcnow()
        db.commit()

# ===== Mentions avec filtres avancés =====

@app.get("/api/mentions", response_model=List[MentionResponse])
async def get_mentions(
    keyword: Optional[str] = None,
    source: Optional[str] = None,
    sentiment: Optional[str] = Query(None, pattern="^(positive|negative|neutral)$"),
    min_engagement: Optional[float] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Obtenir les mentions avec filtres avancés"""
    query = db.query(Mention)
    
    # Filtre par mot-clé
    if keyword:
        keyword_obj = db.query(Keyword).filter(Keyword.keyword == keyword).first()
        if keyword_obj:
            query = query.filter(Mention.keyword_id == keyword_obj.id)
    
    # Filtre par source
    if source:
        query = query.filter(Mention.source == source)
    
    # Filtre par sentiment
    if sentiment:
        query = query.filter(Mention.sentiment == sentiment)
    
    # Filtre par engagement minimum
    if min_engagement is not None:
        query = query.filter(Mention.engagement_score >= min_engagement)
    
    # Filtre par date
    if date_from:
        query = query.filter(Mention.published_at >= date_from)
    if date_to:
        query = query.filter(Mention.published_at <= date_to)
    
    # Recherche textuelle
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Mention.title.ilike(search_pattern),
                Mention.content.ilike(search_pattern)
            )
        )
    
    mentions = query.order_by(Mention.published_at.desc()).offset(offset).limit(limit).all()
    
    return mentions

@app.get("/api/mentions/{mention_id}", response_model=MentionResponse)
async def get_mention(mention_id: int, db: Session = Depends(get_db)):
    """Obtenir une mention spécifique"""
    mention = db.query(Mention).filter(Mention.id == mention_id).first()
    
    if not mention:
        raise HTTPException(status_code=404, detail="Mention non trouvée")
    
    return mention

# ===== Statistiques de base =====

@app.get("/api/stats", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    """Obtenir les statistiques globales"""
    
    total_keywords = db.query(Keyword).filter(Keyword.active == True).count()
    total_mentions = db.query(Mention).count()
    
    # Mentions aujourd'hui
    today = datetime.utcnow().date()
    mentions_today = db.query(Mention).filter(
        Mention.collected_at >= today
    ).count()
    
    # Mentions par source
    mentions_by_source = dict(
        db.query(Mention.source, func.count(Mention.id))
        .group_by(Mention.source)
        .all()
    )
    
    # Top keywords
    top_keywords_query = db.query(
        Keyword.keyword,
        func.count(Mention.id).label('mention_count')
    ).join(Mention).group_by(Keyword.keyword).order_by(
        func.count(Mention.id).desc()
    ).limit(10).all()
    
    top_keywords = [
        {"keyword": kw, "mentions": count}
        for kw, count in top_keywords_query
    ]
    
    # Distribution des sentiments
    sentiment_dist = dict(
        db.query(Mention.sentiment, func.count(Mention.id))
        .filter(Mention.sentiment != None)
        .group_by(Mention.sentiment)
        .all()
    )
    
    return StatsResponse(
        total_keywords=total_keywords,
        total_mentions=total_mentions,
        mentions_today=mentions_today,
        mentions_by_source=mentions_by_source,
        top_keywords=top_keywords,
        sentiment_distribution=sentiment_dist
    )

# ===== Statistiques avancées =====

@app.get("/api/stats/advanced", response_model=AdvancedStatsResponse)
async def get_advanced_stats(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """Obtenir des statistiques avancées"""
    
    # Date de début
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Timeline (évolution temporelle)
    timeline_query = db.query(
        func.date(Mention.published_at).label('date'),
        func.count(Mention.id).label('count')
    ).filter(
        Mention.published_at >= start_date
    ).group_by(
        func.date(Mention.published_at)
    ).order_by('date').all()
    
    timeline = [
        {"date": str(date), "count": count}
        for date, count in timeline_query
    ]
    
    # Sentiment par source
    sentiment_by_source_query = db.query(
        Mention.source,
        Mention.sentiment,
        func.count(Mention.id).label('count')
    ).filter(
        Mention.published_at >= start_date,
        Mention.sentiment != None
    ).group_by(
        Mention.source,
        Mention.sentiment
    ).all()
    
    sentiment_by_source = {}
    for source, sentiment, count in sentiment_by_source_query:
        if source not in sentiment_by_source:
            sentiment_by_source[source] = {}
        sentiment_by_source[source][sentiment] = count
    
    # Top mentions engageantes
    top_engaged_query = db.query(Mention).filter(
        Mention.published_at >= start_date
    ).order_by(
        Mention.engagement_score.desc()
    ).limit(10).all()
    
    top_engaged = [
        {
            "id": m.id,
            "title": m.title,
            "source": m.source,
            "engagement": m.engagement_score,
            "sentiment": m.sentiment,
            "url": m.source_url
        }
        for m in top_engaged_query
    ]
    
    # Distribution horaire
    hourly_query = db.query(
        func.extract('hour', Mention.published_at).label('hour'),
        func.count(Mention.id).label('count')
    ).filter(
        Mention.published_at >= start_date
    ).group_by('hour').order_by('hour').all()
    
    hourly_distribution = [
        {"hour": int(hour), "count": count}
        for hour, count in hourly_query
    ]
    
    # Distribution par jour de la semaine
    daily_query = db.query(
        func.extract('dow', Mention.published_at).label('dow'),
        func.count(Mention.id).label('count')
    ).filter(
        Mention.published_at >= start_date
    ).group_by('dow').order_by('dow').all()
    
    days_names = ['Dimanche', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']
    daily_distribution = [
        {"day": days_names[int(dow)], "count": count}
        for dow, count in daily_query
    ]
    
    return AdvancedStatsResponse(
        timeline=timeline,
        sentiment_by_source=sentiment_by_source,
        top_engaged=top_engaged,
        hourly_distribution=hourly_distribution,
        daily_distribution=daily_distribution
    )

# ===== Configuration =====

@app.get("/api/sources")
async def get_available_sources():
    """Obtenir la liste des sources disponibles"""
    return {
        "sources": [
            {
                "id": "rss",
                "name": "RSS Feeds",
                "description": "Flux RSS d'actualités",
                "free": True,
                "limit": "Illimité"
            },
            {
                "id": "reddit",
                "name": "Reddit",
                "description": "Posts et commentaires Reddit",
                "free": True,
                "limit": "100 requêtes/minute"
            },
            {
                "id": "youtube",
                "name": "YouTube",
                "description": "Vidéos YouTube",
                "free": True,
                "limit": "10,000 requêtes/jour"
            },
            {
                "id": "tiktok",
                "name": "TikTok",
                "description": "Vidéos TikTok",
                "free": True,
                "limit": "Limité (scraping)"
            },
            {
                "id": "google_search",
                "name": "Google Search",
                "description": "Recherche Google Custom",
                "free": True,
                "limit": "100 requêtes/jour"
            },
            {
                "id": "google_alerts",
                "name": "Google Alerts",
                "description": "Alertes Google par email",
                "free": True,
                "limit": "Illimité"
            },
            {
                "id": "mastodon",
                "name": "Mastodon",
                "description": "Réseau social décentralisé",
                "free": True,
                "limit": "Illimité"
            },
            {
                "id": "bluesky",
                "name": "Bluesky",
                "description": "Nouveau réseau social",
                "free": True,
                "limit": "Illimité"
            },
            {
                "id": "telegram",
                "name": "Telegram",
                "description": "Messages de canaux publics",
                "free": True,
                "limit": "Illimité"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)