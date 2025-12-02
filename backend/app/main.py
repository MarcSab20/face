"""
Brand Monitor - Main Application
Système de surveillance et d'analyse d'opinion publique
Version 2.0 - Intégration complète avec routes avancées et IA unifié
"""

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
import logging
import json
import asyncio

# Configuration et base de données
from app.config import settings, validate_and_log_config
from app.database import get_db, init_db
from app.models import Keyword, Mention, CollectionLog

try:
    from app.collectors.youtube_collector import YouTubeCollectorEnhanced
    YOUTUBE_ENHANCED_AVAILABLE = True
except ImportError:
    YOUTUBE_ENHANCED_AVAILABLE = False
    logging.warning("YouTube Enhanced Collector non disponible")

try:
    from app.collectors.reddit_collector import RedditCollectorEnhanced
    REDDIT_ENHANCED_AVAILABLE = True
except ImportError:
    REDDIT_ENHANCED_AVAILABLE = False
    logging.warning("Reddit Enhanced Collector non disponible")

try:
    from app.collectors.google_news_collector import GoogleNewsCollectorEnhanced
    GNEWS_ENHANCED_AVAILABLE = True
except ImportError:
    GNEWS_ENHANCED_AVAILABLE = False
    logging.warning("Google News Enhanced Collector non disponible")

# Import du router des routes avancées
try:
    from app.routes_advanced import get_advanced_router
    ROUTES_ADVANCED_AVAILABLE = True
except ImportError:
    ROUTES_ADVANCED_AVAILABLE = False
    logging.warning("Routes avancées non disponibles")

# Import du service IA unifié
try:
    from app.unified_ai_service import UnifiedAIService
    UNIFIED_AI_AVAILABLE = True
except ImportError:
    UNIFIED_AI_AVAILABLE = False
    logging.warning("Service IA unifié non disponible")

# Modèles Pydantic
from pydantic import BaseModel
from app.scheduler import init_scheduler, start_scheduler, stop_scheduler
from app.sentiment_analyzer import SentimentAnalyzer
from app.collectors.rss_collector import RSSCollector
from app.collectors.collectors_stubs import GoogleSearchCollector
from app.collectors.collectors_stubs import MastodonCollector
from app.collectors.collectors_stubs import BlueskyCollector
from app.collectors.collectors_stubs import TelegramCollector
from app.collectors.collectors_stubs import YouTubeCollector
from app.collectors.collectors_stubs import RedditCollector

sentiment_analyzer = SentimentAnalyzer()

# Configuration du logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============ INITIALISATION FASTAPI ============

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Système professionnel de surveillance et d'analyse d'opinion publique",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============ CORS ============

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Type", "Content-Length"],
    max_age=3600,
)

# ============ ÉVÉNEMENTS STARTUP/SHUTDOWN ============

@app.on_event("startup")
async def startup_event():
    """Initialisation au démarrage"""
    try:
        # Valider la configuration
        validate_and_log_config()
        
        # Initialiser la base de données
        init_db()
        logger.info("✅ Base de données initialisée")
        
        # Initialiser le scheduler
        init_scheduler()
        start_scheduler()
        logger.info("✅ Scheduler initialisé")
        
        # Vérifier les services IA
        if UNIFIED_AI_AVAILABLE:
            ai_service = UnifiedAIService(
                gemini_api_key=settings.GEMINI_API_KEY,
                groq_api_key=settings.GROQ_API_KEY,
                ollama_host=settings.OLLAMA_HOST,
                ollama_model=settings.OLLAMA_DEFAULT_MODEL
            )
            available_services = ai_service.get_available_services()
            logger.info(f"✅ Services IA disponibles: {[s['label'] for s in available_services]}")
        else:
            logger.warning("⚠️ Service IA unifié non disponible")
        
        # Monter les routes avancées si disponibles
        if ROUTES_ADVANCED_AVAILABLE:
            advanced_router = get_advanced_router()
            app.include_router(advanced_router)
            logger.info("✅ Routes avancées montées")
        else:
            logger.warning("⚠️ Routes avancées non disponibles")
        
        logger.info("=" * 60)
        logger.info("🚀 APPLICATION DÉMARRÉE AVEC SUCCÈS")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Erreur au démarrage: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Nettoyage à l'arrêt"""
    logger.info("Arrêt de l'application...")
    try:
        stop_scheduler()
        logger.info("✅ Scheduler arrêté")
    except Exception as e:
        logger.error(f"Erreur arrêt: {e}")


# ============ GESTIONNAIRE D'ERREURS GLOBAL ============

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Gestionnaire d'erreurs global"""
    logger.error(f"Erreur non gérée: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Erreur interne du serveur",
            "detail": str(exc) if settings.DEBUG else "Une erreur est survenue"
        }
    )


# ============ MODÈLES PYDANTIC ============

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


class SystemStatusResponse(BaseModel):
    status: str
    version: str
    collectors_available: List[str]
    ai_services: dict
    features: dict


# ============ ROUTES API - RACINE ============

@app.get("/")
async def root():
    """Endpoint racine avec info système"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "documentation": "/docs",
        "health_check": "/health",
        "features": {
            "advanced_routes": ROUTES_ADVANCED_AVAILABLE,
            "unified_ai": UNIFIED_AI_AVAILABLE,
            "youtube_enhanced": YOUTUBE_ENHANCED_AVAILABLE,
            "reddit_enhanced": REDDIT_ENHANCED_AVAILABLE,
            "google_news": GNEWS_ENHANCED_AVAILABLE
        }
    }


@app.get("/health")
async def health_check():
    """Health check détaillé"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "database": "connected",
        "collectors": len(settings.get_available_collectors()),
        "features": {
            "advanced_routes": ROUTES_ADVANCED_AVAILABLE,
            "unified_ai": UNIFIED_AI_AVAILABLE,
            "youtube_enhanced": YOUTUBE_ENHANCED_AVAILABLE,
            "reddit_enhanced": REDDIT_ENHANCED_AVAILABLE,
            "google_news": GNEWS_ENHANCED_AVAILABLE
        }
    }
    
    # Tester le service IA unifié si disponible
    if UNIFIED_AI_AVAILABLE:
        try:
            ai_service = UnifiedAIService(
                gemini_api_key=settings.GEMINI_API_KEY,
                groq_api_key=settings.GROQ_API_KEY,
                ollama_host=settings.OLLAMA_HOST,
                ollama_model=settings.OLLAMA_DEFAULT_MODEL
            )
            ai_health = await ai_service.health_check()
            health_status["ai_services"] = ai_health
        except Exception as e:
            logger.error(f"Erreur health check IA: {e}")
            health_status["ai_services"] = {"error": str(e)}
    
    return health_status


@app.get("/system/status", response_model=SystemStatusResponse)
async def get_system_status():
    """Obtenir le statut complet du système"""
    
    # Services IA
    ai_services = {}
    if UNIFIED_AI_AVAILABLE:
        try:
            ai_service = UnifiedAIService(
                gemini_api_key=settings.GEMINI_API_KEY,
                groq_api_key=settings.GROQ_API_KEY,
                ollama_host=settings.OLLAMA_HOST,
                ollama_model=settings.OLLAMA_DEFAULT_MODEL
            )
            available = ai_service.get_available_services()
            ai_services = {
                "available": [s['label'] for s in available],
                "priority_order": [s['label'] for s in available],
                "unified_service": True
            }
        except Exception as e:
            ai_services = {"error": str(e), "unified_service": False}
    else:
        ai_services = settings.get_ai_services_status()
    
    return SystemStatusResponse(
        status="operational",
        version=settings.APP_VERSION,
        collectors_available=settings.get_available_collectors(),
        ai_services=ai_services,
        features={
            "email_alerts": settings.email_enabled,
            "network_analysis": settings.ENABLE_NETWORK_ANALYSIS,
            "anomaly_detection": settings.ENABLE_ANOMALY_DETECTION,
            "topic_modeling": settings.ENABLE_TOPIC_MODELING,
            "advanced_routes": ROUTES_ADVANCED_AVAILABLE,
            "unified_ai": UNIFIED_AI_AVAILABLE,
            "youtube_enhanced": YOUTUBE_ENHANCED_AVAILABLE,
            "reddit_enhanced": REDDIT_ENHANCED_AVAILABLE,
            "google_news": GNEWS_ENHANCED_AVAILABLE
        }
    )


@app.get("/system/config")
async def get_system_config():
    """Obtenir la configuration système (admin only - à sécuriser)"""
    if not settings.DEBUG:
        raise HTTPException(
            status_code=403,
            detail="Accès refusé en mode production"
        )
    return settings.get_config_summary()


# ============ ROUTES API - KEYWORDS ============

@app.post("/api/keywords", response_model=KeywordResponse)
async def create_keyword(keyword_data: KeywordCreate, db: Session = Depends(get_db)):
    """Créer un nouveau mot-clé à surveiller"""
    
    existing = db.query(Keyword).filter(Keyword.keyword == keyword_data.keyword).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce mot-clé existe déjà")
    
    # Valider les sources
    available_sources = settings.get_available_collectors()
    invalid_sources = [s for s in keyword_data.sources if s not in available_sources]
    
    if invalid_sources:
        raise HTTPException(
            status_code=400,
            detail=f"Sources invalides: {', '.join(invalid_sources)}"
        )
    
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


# ============ ROUTES API - ANALYSE SENTIMENT ============

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


# ============ ROUTES API - COLLECTE ============

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
    
    # Initialiser les collecteurs standards
    collectors = {
        'rss': RSSCollector()
    }
    
    # Ajouter collecteurs selon configuration
    if settings.reddit_enabled:
        if REDDIT_ENHANCED_AVAILABLE:
            collectors['reddit'] = RedditCollectorEnhanced(
                client_id=settings.REDDIT_CLIENT_ID,
                client_secret=settings.REDDIT_CLIENT_SECRET,
                user_agent=settings.REDDIT_USER_AGENT
            )
        else:
            collectors['reddit'] = RedditCollector()
    
    if settings.youtube_enabled:
        if YOUTUBE_ENHANCED_AVAILABLE:
            collectors['youtube'] = YouTubeCollectorEnhanced(api_key=settings.YOUTUBE_API_KEY)
        else:
            collectors['youtube'] = YouTubeCollector()
    
    if settings.gnews_enabled and GNEWS_ENHANCED_AVAILABLE:
        collectors['google_news'] = GoogleNewsCollectorEnhanced(api_key=settings.GNEWS_API_KEY)
    
    if settings.google_search_enabled:
        collectors['google_search'] = GoogleSearchCollector()
    
    if settings.mastodon_enabled:
        collectors['mastodon'] = MastodonCollector()
    
    if settings.bluesky_enabled:
        collectors['bluesky'] = BlueskyCollector()
    
    if settings.telegram_enabled:
        collectors['telegram'] = TelegramCollector()
    
    # Collecte pour chaque keyword
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


# ============ ROUTES API - MENTIONS ============

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


# ============ ROUTES API - STATISTIQUES ============

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


# ============ ROUTES API - SOURCES ============

@app.get("/api/sources")
async def get_available_sources():
    """Obtenir la liste des sources disponibles"""
    
    available_collectors = settings.get_available_collectors()
    
    sources_info = []
    
    # Définir les infos pour chaque source
    all_sources = {
        "rss": {
            "name": "RSS Feeds",
            "description": "Flux RSS d'actualités",
            "free": True,
            "limit": "Illimité",
            "enabled": True
        },
        "reddit": {
            "name": "Reddit",
            "description": "Posts et commentaires Reddit",
            "free": True,
            "limit": "100 requêtes/minute",
            "enabled": settings.reddit_enabled,
            "enhanced": REDDIT_ENHANCED_AVAILABLE
        },
        "youtube": {
            "name": "YouTube",
            "description": "Vidéos et commentaires YouTube",
            "free": True,
            "limit": "10,000 unités/jour",
            "enabled": settings.youtube_enabled,
            "enhanced": YOUTUBE_ENHANCED_AVAILABLE
        },
        "google_news": {
            "name": "Google News",
            "description": "Articles de presse",
            "free": True,
            "limit": "100 requêtes/jour",
            "enabled": settings.gnews_enabled,
            "enhanced": GNEWS_ENHANCED_AVAILABLE
        },
        "google_search": {
            "name": "Google Search",
            "description": "Recherche Google Custom",
            "free": True,
            "limit": "100 requêtes/jour",
            "enabled": settings.google_search_enabled
        },
        "telegram": {
            "name": "Telegram",
            "description": "Messages de canaux publics",
            "free": True,
            "limit": "Illimité",
            "enabled": settings.telegram_enabled
        },
        "mastodon": {
            "name": "Mastodon",
            "description": "Réseau social décentralisé",
            "free": True,
            "limit": "Illimité",
            "enabled": settings.mastodon_enabled
        },
        "bluesky": {
            "name": "Bluesky",
            "description": "Nouveau réseau social",
            "free": True,
            "limit": "Illimité",
            "enabled": settings.bluesky_enabled
        },
        "tiktok": {
            "name": "TikTok",
            "description": "Vidéos TikTok",
            "free": True,
            "limit": "Limité (scraping)",
            "enabled": settings.tiktok_enabled
        }
    }
    
    for source_id in available_collectors:
        if source_id in all_sources:
            sources_info.append({
                "id": source_id,
                **all_sources[source_id]
            })
    
    return {"sources": sources_info}


# ============ POINT D'ENTRÉE ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=settings.WORKERS if not settings.DEBUG else 1,
        log_level=settings.LOG_LEVEL.lower()
    )