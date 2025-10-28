from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
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

from pydantic import BaseModel

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialisation FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Système de surveillance des mentions en ligne"
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

# ============ Routes API ============

@app.get("/")
async def root():
    """Endpoint racine"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# ===== Gestion des mots-clés =====

@app.post("/api/keywords", response_model=KeywordResponse)
async def create_keyword(keyword_data: KeywordCreate, db: Session = Depends(get_db)):
    """Créer un nouveau mot-clé à surveiller"""
    
    # Vérifier si le mot-clé existe déjà
    existing = db.query(Keyword).filter(Keyword.keyword == keyword_data.keyword).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce mot-clé existe déjà")
    
    # Créer le mot-clé
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

# ===== Collecte de données =====

@app.post("/api/collect")
async def collect_mentions(
    request: CollectionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Lancer une collecte de mentions"""
    
    # Déterminer les mots-clés à collecter
    if request.keyword_id:
        keywords = [db.query(Keyword).filter(Keyword.id == request.keyword_id).first()]
        if not keywords[0]:
            raise HTTPException(status_code=404, detail="Mot-clé non trouvé")
    else:
        keywords = db.query(Keyword).filter(Keyword.active == True).all()
    
    if not keywords:
        raise HTTPException(status_code=400, detail="Aucun mot-clé actif à collecter")
    
    # Lancer la collecte en arrière-plan
    background_tasks.add_task(run_collection, keywords, request.sources, db)
    
    return {
        "message": "Collecte lancée",
        "keywords_count": len(keywords),
        "status": "processing"
    }

async def run_collection(keywords: List[Keyword], sources: Optional[List[str]], db: Session):
    """Exécuter la collecte pour les mots-clés donnés"""
    
    # Initialiser les collecteurs
    collectors = {
        'rss': RSSCollector(),
        'reddit': RedditCollector(),
        'youtube': YouTubeCollector(),
        'tiktok': TikTokCollector(),
        'google_search': GoogleSearchCollector(),
        'google_alerts': GoogleAlertsCollector()
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
                # Collecter les mentions
                mentions_data = collector.collect(
                    keyword.keyword,
                    max_results=settings.MAX_RESULTS_PER_SOURCE
                )
                
                # Sauvegarder les mentions
                saved_count = 0
                for mention_data in mentions_data:
                    try:
                        # Vérifier si la mention existe déjà
                        existing = db.query(Mention).filter(
                            Mention.source_url == mention_data['source_url']
                        ).first()
                        
                        if existing:
                            continue
                        
                        # Créer la mention - CORRECTION ICI: metadata -> mention_metadata
                        mention = Mention(
                            keyword_id=keyword.id,
                            source=mention_data['source'],
                            source_url=mention_data['source_url'],
                            title=mention_data['title'],
                            content=mention_data['content'],
                            author=mention_data['author'],
                            engagement_score=mention_data['engagement_score'],
                            published_at=mention_data['published_at'],
                            mention_metadata=json.dumps(mention_data.get('metadata', {}))
                        )
                        
                        db.add(mention)
                        saved_count += 1
                        
                    except Exception as e:
                        logger.error(f"Erreur sauvegarde mention: {str(e)}")
                        continue
                
                db.commit()
                
                # Log de la collecte
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
        
        # Mettre à jour la date de dernière collecte
        keyword.last_collected = datetime.utcnow()
        db.commit()

# ===== Mentions =====

@app.get("/api/mentions", response_model=List[MentionResponse])
async def get_mentions(
    keyword: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Obtenir les mentions"""
    query = db.query(Mention)
    
    if keyword:
        keyword_obj = db.query(Keyword).filter(Keyword.keyword == keyword).first()
        if keyword_obj:
            query = query.filter(Mention.keyword_id == keyword_obj.id)
    
    if source:
        query = query.filter(Mention.source == source)
    
    mentions = query.order_by(Mention.published_at.desc()).offset(offset).limit(limit).all()
    
    return mentions

@app.get("/api/mentions/{mention_id}", response_model=MentionResponse)
async def get_mention(mention_id: int, db: Session = Depends(get_db)):
    """Obtenir une mention spécifique"""
    mention = db.query(Mention).filter(Mention.id == mention_id).first()
    
    if not mention:
        raise HTTPException(status_code=404, detail="Mention non trouvée")
    
    return mention

# ===== Statistiques =====

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
    from sqlalchemy import func
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
    
    return StatsResponse(
        total_keywords=total_keywords,
        total_mentions=total_mentions,
        mentions_today=mentions_today,
        mentions_by_source=mentions_by_source,
        top_keywords=top_keywords
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
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)