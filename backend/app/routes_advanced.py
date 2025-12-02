"""
Routes Avancées - Brand Monitor
Routes pour rapports, influenceurs, analyse avancée
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta
import logging
import json
import asyncio

from app.database import get_db
from app.models import Keyword, Mention
from app.config import settings
from app.unified_ai_service import UnifiedAIService

# Import conditionnel des composants avancés
try:
    from app.hierarchical_summarizer import HierarchicalSummarizer
    HIERARCHICAL_AVAILABLE = True
except:
    HIERARCHICAL_AVAILABLE = False

try:
    from app.influencer_manager import AdvancedInfluencerAnalyzer
    INFLUENCER_AVAILABLE = True
except:
    INFLUENCER_AVAILABLE = False

try:
    from app.advanced_analyzer import AdvancedAnalyzer
    ADVANCED_ANALYZER_AVAILABLE = True
except:
    ADVANCED_ANALYZER_AVAILABLE = False

logger = logging.getLogger(__name__)

# Créer le router
router = APIRouter(prefix="/api/advanced", tags=["Advanced Features"])


# ============ SERVICE IA GLOBAL ============

def get_ai_service() -> UnifiedAIService:
    """Obtenir une instance du service IA unifié"""
    return UnifiedAIService(
        gemini_api_key=settings.GEMINI_API_KEY,
        groq_api_key=settings.GROQ_API_KEY,
        ollama_host=settings.OLLAMA_HOST,
        ollama_model=settings.OLLAMA_DEFAULT_MODEL
    )


# ============ ROUTES RÉSUMÉ HIÉRARCHIQUE ============

@router.post("/summarize")
async def generate_hierarchical_summary(
    keyword_ids: List[int],
    days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """
    Générer un résumé hiérarchique intelligent
    
    Traite des milliers de contenus en les regroupant par lots
    """
    
    if not HIERARCHICAL_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Résumé hiérarchique non disponible"
        )
    
    try:
        # Récupérer les contenus
        since_date = datetime.utcnow() - timedelta(days=days)
        
        mentions = db.query(Mention).filter(
            Mention.keyword_id.in_(keyword_ids),
            Mention.published_at >= since_date
        ).all()
        
        if not mentions:
            raise HTTPException(
                status_code=404,
                detail="Aucun contenu trouvé pour cette période"
            )
        
        # Convertir en format dict
        contents = [
            {
                'title': m.title,
                'content': m.content,
                'author': m.author,
                'source': m.source,
                'sentiment': m.sentiment,
                'engagement_score': m.engagement_score,
                'published_at': m.published_at
            }
            for m in mentions
        ]
        
        logger.info(f"📊 Résumé hiérarchique: {len(contents)} contenus")
        
        # Créer le résumeur
        ai_service = get_ai_service()
        summarizer = HierarchicalSummarizer(
            llm_service=ai_service,
            batch_size=settings.HIERARCHICAL_BATCH_SIZE
        )
        
        # Générer le résumé
        keywords = db.query(Keyword).filter(Keyword.id.in_(keyword_ids)).all()
        context = f"Surveillance: {', '.join([k.keyword for k in keywords])}"
        
        result = await summarizer.summarize_large_dataset(contents, context)
        
        return {
            'summary': result.final_summary,
            'key_insights': result.key_insights,
            'sentiment_analysis': result.sentiment_analysis,
            'themes': result.themes,
            'batch_summaries': result.batch_summaries,
            'total_contents': result.total_contents_analyzed,
            'processing_time': result.processing_time
        }
        
    except Exception as e:
        logger.error(f"Erreur résumé hiérarchique: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ ROUTES INFLUENCEURS ============

@router.get("/influencers")
async def get_influencers(
    days: int = Query(30, ge=1, le=90),
    keyword_ids: Optional[List[int]] = Query(None),
    min_engagement: float = Query(100.0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Analyser et classer les influenceurs par catégorie
    
    Retourne 3 catégories:
    - Activistes Surveillés
    - Influenceurs Émergents  
    - Médias Officiels
    """
    
    if not INFLUENCER_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Analyse des influenceurs non disponible"
        )
    
    try:
        analyzer = AdvancedInfluencerAnalyzer(db)
        
        influencers_by_category = analyzer.analyze_all_influencers(
            days=days,
            keyword_ids=keyword_ids,
            min_engagement=min_engagement
        )
        
        # Formater pour la réponse
        response = {
            'activists': [
                {
                    'name': inf.name,
                    'source': inf.source,
                    'total_mentions': inf.total_mentions,
                    'total_engagement': inf.total_engagement,
                    'sentiment_score': inf.sentiment_score,
                    'risk_level': inf.risk_level,
                    'trending': inf.trending,
                    'reach_estimate': inf.reach_estimate,
                    'recent_activity': inf.recent_activity[:3]
                }
                for inf in influencers_by_category['activists'][:20]
            ],
            'emerging': [
                {
                    'name': inf.name,
                    'source': inf.source,
                    'total_mentions': inf.total_mentions,
                    'total_engagement': inf.total_engagement,
                    'sentiment_score': inf.sentiment_score,
                    'risk_level': inf.risk_level,
                    'trending': inf.trending
                }
                for inf in influencers_by_category['emerging'][:20]
            ],
            'official_media': [
                {
                    'name': inf.name,
                    'source': inf.source,
                    'total_mentions': inf.total_mentions,
                    'total_engagement': inf.total_engagement,
                    'sentiment_score': inf.sentiment_score
                }
                for inf in influencers_by_category['official_media'][:10]
            ]
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Erreur analyse influenceurs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/influencers/{author_name}")
async def get_influencer_report(
    author_name: str,
    source: Optional[str] = None,
    days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """Rapport détaillé sur un influenceur spécifique"""
    
    if not INFLUENCER_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Analyse des influenceurs non disponible"
        )
    
    try:
        analyzer = AdvancedInfluencerAnalyzer(db)
        
        report = analyzer.get_influencer_detailed_report(
            author_name=author_name,
            source=source,
            days=days
        )
        
        if 'error' in report:
            raise HTTPException(status_code=404, detail=report['error'])
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur rapport influenceur: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ ROUTES ANALYSE AVANCÉE ============

@router.get("/anomalies")
async def detect_anomalies(
    keyword_id: int,
    days: int = Query(30, ge=7, le=90),
    sensitivity: float = Query(2.0, ge=1.0, le=5.0),
    db: Session = Depends(get_db)
):
    """
    Détecter les anomalies dans l'activité
    
    Types d'anomalies:
    - Pics de volume
    - Changements de sentiment
    - Nouveaux influenceurs
    - Patterns temporels inhabituels
    """
    
    if not ADVANCED_ANALYZER_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Analyse avancée non disponible"
        )
    
    try:
        analyzer = AdvancedAnalyzer(db)
        
        anomalies = analyzer.detect_anomalies(
            keyword_id=keyword_id,
            days=days,
            sensitivity=sensitivity
        )
        
        # Formater les anomalies
        formatted_anomalies = [
            {
                'type': a.type,
                'severity': a.severity,
                'timestamp': a.timestamp.isoformat(),
                'description': a.description,
                'metrics': a.metrics,
                'affected_entities': a.affected_entities
            }
            for a in anomalies
        ]
        
        return {
            'anomalies': formatted_anomalies,
            'total_found': len(anomalies),
            'critical_count': len([a for a in anomalies if a.severity == 'critical']),
            'high_count': len([a for a in anomalies if a.severity == 'high'])
        }
        
    except Exception as e:
        logger.error(f"Erreur détection anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/topics")
async def extract_topics(
    keyword_id: int,
    days: int = Query(30, ge=7, le=90),
    min_topic_size: int = Query(10, ge=5, le=50),
    db: Session = Depends(get_db)
):
    """
    Extraire automatiquement les topics principaux
    
    Utilise BERTopic pour identifier les thèmes dominants
    """
    
    if not ADVANCED_ANALYZER_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Topic modeling non disponible"
        )
    
    try:
        since_date = datetime.utcnow() - timedelta(days=days)
        
        mentions = db.query(Mention).filter(
            Mention.keyword_id == keyword_id,
            Mention.published_at >= since_date
        ).all()
        
        if not mentions:
            raise HTTPException(
                status_code=404,
                detail="Aucun contenu trouvé"
            )
        
        contents = [
            {
                'title': m.title,
                'content': m.content
            }
            for m in mentions
        ]
        
        analyzer = AdvancedAnalyzer(db)
        topics = analyzer.analyze_topics(
            contents=contents,
            min_topic_size=min_topic_size
        )
        
        # Formater les topics
        formatted_topics = [
            {
                'topic_id': t.topic_id,
                'keywords': t.keywords,
                'size': t.size,
                'coherence_score': t.coherence_score,
                'representative_docs': t.representative_docs[:2]
            }
            for t in topics
        ]
        
        return {
            'topics': formatted_topics,
            'total_topics': len(topics),
            'total_documents': len(contents)
        }
        
    except Exception as e:
        logger.error(f"Erreur extraction topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/network")
async def analyze_influence_network(
    keyword_id: int,
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db)
):
    """
    Analyser le réseau d'influence
    
    Identifie:
    - Qui influence qui
    - Communautés d'influenceurs
    - Nœuds centraux
    """
    
    if not ADVANCED_ANALYZER_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Analyse de réseau non disponible"
        )
    
    try:
        analyzer = AdvancedAnalyzer(db)
        
        network = analyzer.analyze_influence_network(
            keyword_id=keyword_id,
            days=days
        )
        
        return {
            'nodes': network.nodes[:50],  # Limiter pour performance
            'edges': network.edges[:100],
            'communities': network.communities,
            'central_nodes': network.central_nodes[:10],
            'metrics': network.metrics
        }
        
    except Exception as e:
        logger.error(f"Erreur analyse réseau: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ ROUTES HEALTH CHECK IA ============

@router.get("/ai/health")
async def check_ai_services():
    """Vérifier la santé de tous les services IA"""
    
    try:
        ai_service = get_ai_service()
        health = await ai_service.health_check()
        
        return {
            'services': health,
            'priority_order': [s['label'] for s in ai_service.get_available_services()]
        }
        
    except Exception as e:
        logger.error(f"Erreur health check IA: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/test")
async def test_ai_generation(
    prompt: str = Query(..., min_length=10),
    max_tokens: int = Query(200, ge=10, le=2000)
):
    """Tester la génération IA avec un prompt"""
    
    try:
        ai_service = get_ai_service()
        
        result = await ai_service.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=0.3
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=503,
                detail=f"Génération échouée: {result.get('error')}"
            )
        
        return {
            'text': result['text'],
            'service_used': result['service'],
            'model': result['model'],
            'tokens_used': result.get('tokens_used', 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur test IA: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ EXPORT DU ROUTER ============

def get_advanced_router() -> APIRouter:
    """Obtenir le router des routes avancées"""
    return router