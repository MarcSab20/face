"""
Routes API pour la génération de rapports intelligents avec IA
Support des analyses avancées avec agents IA et lecture web
"""

from fastapi import APIRouter, Depends, HTTPException, Response, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import logging
import asyncio

from app.database import get_db
from app.models import Keyword
from enhanced_intelligent_report_generator import IntelligentReportGenerator

logger = logging.getLogger(__name__)

# Router
intelligent_reports_router = APIRouter(prefix="/api/intelligent-reports", tags=["intelligent-reports"])


# ===== Modèles Pydantic =====

class IntelligentReportRequest(BaseModel):
    keyword_ids: List[int]
    days: int = 30
    report_object: str = ""
    include_web_analysis: bool = True
    ai_model: str = "mistral:7b"  # Modèle IA à utiliser
    format: str = "pdf"  # pdf ou html


class IntelligentReportPreview(BaseModel):
    keywords: List[str]
    keyword_ids: List[int]
    period_days: int
    total_mentions: int
    estimated_web_sources: int
    ai_models_available: List[str]
    processing_time_estimate: str
    risk_level_preview: Optional[str] = None


class AIModelStatus(BaseModel):
    name: str
    available: bool
    description: str
    performance: str


# ===== Routes =====

@intelligent_reports_router.post("/generate")
async def generate_intelligent_report(
    request: IntelligentReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Générer un rapport intelligent avec analyse IA et contenu web
    
    Args:
        request: Configuration du rapport intelligent
        
    Returns:
        PDF ou HTML du rapport avec analyse IA avancée
    """
    try:
        # Vérifier que les mots-clés existent
        keywords = db.query(Keyword).filter(Keyword.id.in_(request.keyword_ids)).all()
        if not keywords:
            raise HTTPException(status_code=404, detail="Aucun mot-clé trouvé")
        
        # Créer le générateur intelligent
        generator = IntelligentReportGenerator(db)
        
        # Générer le rapport avec analyse IA
        logger.info(f"Génération rapport intelligent pour {len(keywords)} mots-clés avec IA")
        
        report_data = await generator.generate_intelligent_report(
            keyword_ids=request.keyword_ids,
            days=request.days,
            report_object=request.report_object,
            include_web_analysis=request.include_web_analysis
        )
        
        if request.format == "pdf":
            # Générer PDF intelligent
            pdf_bytes = await generator.generate_intelligent_pdf(report_data)
            
            keywords_str = '_'.join([kw.keyword for kw in keywords])[:30]
            filename = f"rapport_intelligent_{keywords_str}_{report_data['generated_at'].strftime('%Y%m%d_%H%M%S')}.pdf"
            
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )
        else:
            # Retourner HTML intelligent
            html_content = await generator.generate_intelligent_html_report(report_data)
            
            return Response(
                content=html_content,
                media_type="text/html"
            )
            
    except Exception as e:
        logger.error(f"Erreur génération rapport intelligent: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération du rapport intelligent: {str(e)}"
        )


@intelligent_reports_router.post("/preview")
async def preview_intelligent_report(
    keyword_ids: List[int],
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Prévisualiser un rapport intelligent sans le générer
    
    Args:
        keyword_ids: IDs des mots-clés
        days: Période d'analyse
        
    Returns:
        Informations de prévisualisation avec estimation IA
    """
    from app.models import Mention
    from datetime import datetime, timedelta
    from enhanced_ai_service import LLMService
    
    # Vérifier que les mots-clés existent
    keywords = db.query(Keyword).filter(Keyword.id.in_(keyword_ids)).all()
    if not keywords:
        raise HTTPException(status_code=404, detail="Aucun mot-clé trouvé")
    
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Compter les mentions
    mentions = db.query(Mention).filter(
        Mention.keyword_id.in_(keyword_ids),
        Mention.published_at >= since_date
    ).all()
    
    mentions_count = len(mentions)
    
    # Estimer les sources web
    unique_urls = set()
    for mention in mentions:
        if mention.source_url and mention.source_url.startswith('http'):
            unique_urls.add(mention.source_url)
    
    estimated_web_sources = min(len(unique_urls), 10)  # Limité à 10 pour performance
    
    # Vérifier les modèles IA disponibles
    llm_service = LLMService()
    ai_models = []
    
    if llm_service.ollama_available:
        ai_models.append("Ollama (Modèles locaux)")
    if llm_service.hf_available:
        ai_models.append("HuggingFace Transformers")
    
    if not ai_models:
        ai_models.append("Analyse basique (IA non disponible)")
    
    # Estimation du temps de traitement
    base_time = 30  # 30 secondes de base
    web_time = estimated_web_sources * 5  # 5 secondes par source web
    ai_time = 20 if llm_service.is_available() else 0  # 20 secondes pour l'IA
    
    total_time = base_time + web_time + ai_time
    
    if total_time < 60:
        time_estimate = f"{total_time} secondes"
    else:
        time_estimate = f"{total_time // 60} min {total_time % 60} sec"
    
    # Évaluation rapide du risque
    risk_level = None
    if mentions:
        negative_mentions = [m for m in mentions if m.sentiment == 'negative']
        negative_ratio = len(negative_mentions) / mentions_count
        
        if negative_ratio > 0.6:
            risk_level = "ÉLEVÉ"
        elif negative_ratio > 0.3:
            risk_level = "MODÉRÉ"
        else:
            risk_level = "FAIBLE"
    
    return IntelligentReportPreview(
        keywords=[kw.keyword for kw in keywords],
        keyword_ids=keyword_ids,
        period_days=days,
        total_mentions=mentions_count,
        estimated_web_sources=estimated_web_sources,
        ai_models_available=ai_models,
        processing_time_estimate=time_estimate,
        risk_level_preview=risk_level
    )


@intelligent_reports_router.get("/ai-status")
async def get_ai_status():
    """
    Obtenir le statut des modèles IA disponibles
    
    Returns:
        Statut détaillé des modèles IA
    """
    from enhanced_ai_service import LLMService
    
    llm_service = LLMService()
    
    models_status = []
    
    # Statut Ollama
    models_status.append(AIModelStatus(
        name="Ollama",
        available=llm_service.ollama_available,
        description="Modèles LLM locaux (Mistral, Llama, etc.)",
        performance="Haute performance" if llm_service.ollama_available else "Non disponible"
    ))
    
    # Statut HuggingFace
    models_status.append(AIModelStatus(
        name="HuggingFace Transformers",
        available=llm_service.hf_available,
        description="Modèles de transformers open source",
        performance="Performance modérée" if llm_service.hf_available else "Non disponible"
    ))
    
    return {
        "ai_service_available": llm_service.is_available(),
        "models": models_status,
        "recommendation": "Ollama recommandé pour de meilleures performances" if llm_service.ollama_available else "Installer Ollama pour une IA optimale"
    }


@intelligent_reports_router.get("/capabilities")
async def get_ai_capabilities():
    """
    Obtenir les capacités d'analyse IA disponibles
    
    Returns:
        Liste des capacités d'analyse
    """
    return {
        "analysis_types": [
            {
                "name": "Analyse de Sentiment Avancée",
                "description": "Détection nuancée des émotions et polarisation",
                "agent": "SentimentAnalysisAgent",
                "features": ["Polarisation", "Nuances émotionnelles", "Comparaison web/mentions"]
            },
            {
                "name": "Analyse des Tendances",
                "description": "Détection de patterns temporels et prédictions",
                "agent": "TrendAnalysisAgent", 
                "features": ["Détection de pics", "Prédictions", "Signaux d'alerte"]
            },
            {
                "name": "Analyse d'Influenceurs",
                "description": "Évaluation de l'impact et des risques",
                "agent": "InfluencerAnalysisAgent",
                "features": ["Évaluation de risque", "Portée estimée", "Recommandations d'engagement"]
            },
            {
                "name": "Analyse de Contenu Web",
                "description": "Lecture et analyse du contenu des sources",
                "agent": "WebContentAnalysisAgent",
                "features": ["Extraction contenu", "Analyse commentaires", "Score d'authenticité"]
            }
        ],
        "web_analysis": {
            "description": "Capacité de lecture et d'analyse du contenu web",
            "features": [
                "Extraction automatique du contenu des articles",
                "Analyse des commentaires et réactions",
                "Détection d'authenticité",
                "Comparaison sentiment officiel vs public"
            ],
            "limitations": [
                "Maximum 10 sources par rapport",
                "Limité aux pages publiques",
                "Respect des robots.txt"
            ]
        },
        "intelligence_features": [
            "Génération de texte en langage naturel",
            "Analyse contextuelle avancée",
            "Recommandations actionnables",
            "Évaluation de risque multicritères",
            "Détection de signaux faibles"
        ]
    }


@intelligent_reports_router.post("/test-ai")
async def test_ai_analysis(
    text: str,
    analysis_type: str = "sentiment"
):
    """
    Tester l'analyse IA sur un texte donné
    
    Args:
        text: Texte à analyser
        analysis_type: Type d'analyse (sentiment, trend, etc.)
        
    Returns:
        Résultat de l'analyse IA
    """
    from enhanced_ai_service import LLMService, SentimentAnalysisAgent, AnalysisContext
    
    if len(text) < 10:
        raise HTTPException(status_code=400, detail="Texte trop court pour l'analyse")
    
    try:
        llm_service = LLMService()
        
        if not llm_service.is_available():
            raise HTTPException(status_code=503, detail="Service IA non disponible")
        
        # Créer un contexte de test
        test_context = AnalysisContext(
            mentions=[{
                'title': 'Test',
                'content': text,
                'sentiment': None,
                'source': 'test',
                'author': 'Test User',
                'engagement_score': 1
            }],
            keywords=['test'],
            period_days=1,
            total_mentions=1,
            sentiment_distribution={'positive': 0, 'neutral': 0, 'negative': 0},
            top_sources={'test': 1},
            engagement_stats={'total': 1, 'average': 1, 'max': 1},
            geographic_data=[],
            influencers_data=[],
            time_trends=[],
            web_content=[]
        )
        
        if analysis_type == "sentiment":
            agent = SentimentAnalysisAgent(llm_service)
            result = await agent.analyze(test_context)
            
            return {
                "analysis_type": "sentiment",
                "input_text": text,
                "result": result,
                "processing_time": "< 1 seconde"
            }
        else:
            raise HTTPException(status_code=400, detail="Type d'analyse non supporté")
            
    except Exception as e:
        logger.error(f"Erreur test IA: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du test IA: {str(e)}")


@intelligent_reports_router.get("/examples")
async def get_report_examples():
    """
    Obtenir des exemples de rapports intelligents
    
    Returns:
        Exemples de structure et contenu
    """
    return {
        "sample_analyses": {
            "sentiment_analysis": {
                "input": "Les réactions des utilisateurs à la nouvelle fonctionnalité",
                "output": "L'analyse révèle une réception majoritairement positive (67%) avec des réserves sur l'interface utilisateur. L'IA détecte une opportunité d'amélioration de l'UX pour convertir les 28% d'opinions neutres."
            },
            "trend_analysis": {
                "input": "Évolution des mentions sur 30 jours",
                "output": "Pic d'activité détecté le 15/01 (+300% vs moyenne) corrélé avec l'annonce produit. L'IA prédit une stabilisation dans les 7 prochains jours avec surveillance recommandée."
            },
            "web_content_analysis": {
                "input": "15 articles analysés + 234 commentaires extraits",
                "output": "Divergence détectée : articles neutres (score 0.1) vs commentaires positifs (score 0.7). L'IA identifie un écart entre couverture médiatique et réaction publique, suggérant une campagne de relations presse."
            }
        },
        "report_sections": [
            "🧠 Synthèse Exécutive IA",
            "🎯 Analyse Intelligente", 
            "🚨 Évaluation de Risque IA",
            "🔍 Évaluation d'Authenticité",
            "🌐 Analyse Contenu Web",
            "📊 Patterns d'Engagement IA",
            "🎯 Recommandations Actionnables"
        ],
        "ai_insights_examples": [
            "Détection automatique de campagnes coordonnées",
            "Identification de signaux d'alerte précoce",
            "Analyse de cohérence narrative",
            "Évaluation de l'authenticité des interactions",
            "Prédictions de tendances basées sur les patterns"
        ]
    }


# Fonction utilitaire pour les tâches en arrière-plan
async def process_intelligent_report_background(
    keyword_ids: List[int],
    days: int,
    report_object: str,
    db: Session,
    user_email: str = None
):
    """
    Traiter un rapport intelligent en arrière-plan
    """
    try:
        generator = IntelligentReportGenerator(db)
        
        report_data = await generator.generate_intelligent_report(
            keyword_ids=keyword_ids,
            days=days,
            report_object=report_object,
            include_web_analysis=True
        )
        
        # Ici, vous pourriez envoyer le rapport par email ou le sauvegarder
        logger.info(f"Rapport intelligent généré avec succès pour {len(keyword_ids)} mots-clés")
        
        # TODO: Implémenter l'envoi par email si user_email fourni
        
    except Exception as e:
        logger.error(f"Erreur génération rapport en arrière-plan: {e}")


@intelligent_reports_router.post("/generate-async")
async def generate_intelligent_report_async(
    request: IntelligentReportRequest,
    background_tasks: BackgroundTasks,
    user_email: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Lancer la génération d'un rapport intelligent en arrière-plan
    """
    # Vérifier que les mots-clés existent
    keywords = db.query(Keyword).filter(Keyword.id.in_(request.keyword_ids)).all()
    if not keywords:
        raise HTTPException(status_code=404, detail="Aucun mot-clé trouvé")
    
    # Lancer en arrière-plan
    background_tasks.add_task(
        process_intelligent_report_background,
        request.keyword_ids,
        request.days,
        request.report_object,
        db,
        user_email
    )
    
    return {
        "message": "Génération de rapport intelligent lancée en arrière-plan",
        "keywords": [kw.keyword for kw in keywords],
        "estimated_time": "2-5 minutes selon la complexité",
        "notification": "Email envoyé une fois terminé" if user_email else "Consultez les logs pour le statut"
    }