"""
API pour la génération de rapports intelligents avec IA souveraine
Endpoints pour créer, prévisualiser et télécharger des rapports IA
"""

from fastapi import APIRouter, Depends, HTTPException, Response, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging
import asyncio
import json
import uuid
from pathlib import Path
import asyncio
from datetime import datetime, timedelta

from app.database import get_db
from app.models import Keyword, Mention
from app.report_generator import StrategicReportGeneratorV3

logger = logging.getLogger(__name__)

# Router
intelligent_reports_router = APIRouter(prefix="/api/intelligent-reports", tags=["intelligent-reports"])

# Dictionnaire de cache des rapports
report_cache = {}

# ===== Modèles Pydantic =====

class IntelligentReportRequest(BaseModel):
    """Requête de génération de rapport intelligent"""
    keyword_ids: List[int] = Field(..., description="IDs des mots-clés à analyser")
    days: int = Field(30, ge=1, le=365, description="Période d'analyse en jours")
    report_title: str = Field("", description="Titre personnalisé du rapport")
    include_web_analysis: bool = Field(True, description="Inclure l'analyse web approfondie")
    format: str = Field("pdf", pattern="^(pdf|html)$", description="Format de sortie")

    class Config:
        schema_extra = {
            "example": {
                "keyword_ids": [1, 2, 3],
                "days": 30,
                "report_title": "Analyse IA - Opinion publique Q4",
                "include_web_analysis": True,
                "format": "pdf"
            }
        }


class ReportPreviewRequest(BaseModel):
    """Requête de prévisualisation de rapport"""
    keyword_ids: List[int]
    days: int = 30


class IntelligentReportPreview(BaseModel):
    """Prévisualisation d'un rapport intelligent"""
    keywords: List[str]
    period_days: int
    total_mentions: int
    estimated_web_sources: int
    sources_distribution: dict
    sentiment_preview: dict
    processing_time_estimate: str
    confidence_score: float
    risk_indicators: List[str]


class AIServiceStatus(BaseModel):
    """Statut du service IA"""
    ai_available: bool
    ollama_status: str
    transformers_status: str
    models_available: List[str]
    recommendation: str


class ReportGenerationResponse(BaseModel):
    """Réponse de génération de rapport"""
    success: bool
    message: str
    report_id: Optional[str] = None
    download_url: Optional[str] = None
    processing_time: Optional[float] = None


# ===== Routes =====


@intelligent_reports_router.post("/preview", response_model=IntelligentReportPreview)
async def preview_intelligent_report(
    request: ReportPreviewRequest,
    db: Session = Depends(get_db)
):
    """
    Prévisualiser un rapport intelligent avant génération
    
    Fournit des métriques et estimations sans lancer l'analyse IA complète
    """
    try:
        # Vérifier les mots-clés
        keywords = db.query(Keyword).filter(Keyword.id.in_(request.keyword_ids)).all()
        if not keywords:
            raise HTTPException(status_code=404, detail="Aucun mot-clé trouvé")
        
        since_date = datetime.utcnow() - timedelta(days=request.days)
        
        # Collecter les données de base
        mentions = db.query(Mention).filter(
            Mention.keyword_id.in_(request.keyword_ids),
            Mention.published_at >= since_date
        ).all()
        
        if not mentions:
            raise HTTPException(
                status_code=400,
                detail="Aucune mention trouvée pour cette période"
            )
        
        # Analyser les données pour la prévisualisation
        sources_dist = {}
        sentiment_dist = {'positive': 0, 'neutral': 0, 'negative': 0, 'unknown': 0}
        web_sources = set()
        risk_indicators = []
        
        for mention in mentions:
            # Distribution des sources
            sources_dist[mention.source] = sources_dist.get(mention.source, 0) + 1
            
            # Distribution des sentiments
            sentiment = mention.sentiment or 'unknown'
            if sentiment in sentiment_dist:
                sentiment_dist[sentiment] += 1
            
            # Sources web uniques
            if mention.source_url and mention.source_url.startswith('http'):
                web_sources.add(mention.source_url)
            
            # Indicateurs de risque simples
            content_lower = f"{mention.title} {mention.content}".lower()
            if any(word in content_lower for word in ['crise', 'scandale', 'problème', 'urgent']):
                risk_indicators.append(f"Contenu sensible détecté dans {mention.source}")
        
        # Calculer les métriques de prévisualisation
        total_mentions = len(mentions)
        estimated_web_sources = min(len(web_sources), 10)  # Limité à 10 pour la performance
        
        # Estimer le temps de traitement
        base_time = 20  # 20 secondes de base
        ai_time = 30  # 30 secondes pour l'IA
        web_time = estimated_web_sources * 3  # 3 secondes par source web
        
        total_time = base_time + ai_time + web_time
        if total_time < 60:
            time_estimate = f"{total_time} secondes"
        else:
            time_estimate = f"{total_time // 60} min {total_time % 60} sec"
        
        # Calculer un score de confiance préliminaire
        confidence_factors = []
        
        # Volume de données
        if total_mentions >= 50:
            confidence_factors.append(0.8)
        elif total_mentions >= 20:
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(0.4)
        
        # Diversité des sources
        if len(sources_dist) >= 3:
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.5)
        
        # Données de sentiment
        sentiment_coverage = (total_mentions - sentiment_dist['unknown']) / total_mentions
        confidence_factors.append(sentiment_coverage)
        
        confidence_score = sum(confidence_factors) / len(confidence_factors)
        
        # Détecter des indicateurs de risque
        risk_indicators_unique = list(set(risk_indicators))[:5]
        
        negative_ratio = sentiment_dist['negative'] / total_mentions if total_mentions > 0 else 0
        if negative_ratio > 0.5:
            risk_indicators_unique.insert(0, f"Sentiment négatif dominant ({negative_ratio:.1%})")
        
        return IntelligentReportPreview(
            keywords=[kw.keyword for kw in keywords],
            period_days=request.days,
            total_mentions=total_mentions,
            estimated_web_sources=estimated_web_sources,
            sources_distribution=dict(sorted(sources_dist.items(), key=lambda x: x[1], reverse=True)[:5]),
            sentiment_preview={
                'distribution': sentiment_dist,
                'negative_ratio': negative_ratio,
                'dominant': max(sentiment_dist, key=sentiment_dist.get)
            },
            processing_time_estimate=time_estimate,
            confidence_score=round(confidence_score, 2),
            risk_indicators=risk_indicators_unique
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur prévisualisation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la prévisualisation: {str(e)}"
        )

@intelligent_reports_router.post("/generate-ministerial-async")
async def generate_ministerial_report_async(
    request: IntelligentReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Générer le rapport ministériel de manière asynchrone
    Évite les problèmes CORS en utilisant GET pour le téléchargement
    """
    report_id = str(uuid.uuid4())
    
    # Mettre en file d'attente
    report_cache[report_id] = {
        'status': 'generating',
        'progress': 0,
        'created_at': datetime.utcnow()
    }


@intelligent_reports_router.get("/status/{report_id}")
async def check_report_status(report_id: str):
    """Vérifier le statut d'un rapport"""
    if report_id not in report_cache:
        raise HTTPException(status_code=404, detail="Rapport non trouvé")
    
    info = report_cache[report_id]
    
    return {
        "report_id": report_id,
        "status": info['status'],
        "progress": info.get('progress', 0),
        "error": info.get('error'),
        "filename": info.get('filename'),
        "size": info.get('size'),
        "download_url": f"/api/intelligent-reports/download/{report_id}" if info['status'] == 'ready' else None
    }


@intelligent_reports_router.get("/download/{report_id}")
async def download_report(report_id: str):
    """Télécharger un rapport généré (GET simple, pas de CORS)"""
    if report_id not in report_cache:
        raise HTTPException(status_code=404, detail="Rapport non trouvé")
    
    info = report_cache[report_id]
    
    if info['status'] != 'ready':
        if info['status'] == 'error':
            raise HTTPException(status_code=500, detail=info.get('error', 'Erreur de génération'))
        else:
            raise HTTPException(status_code=425, detail="Rapport en cours de génération")
    
    filepath = Path(info['filepath'])
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Fichier non trouvé sur le serveur")
    
    # Lire le fichier
    with open(filepath, 'rb') as f:
        content = f.read()
    
    headers = {
        "Content-Disposition": f'attachment; filename="{info["filename"]}"',
    }
    
    return Response(
        content=content,
        media_type=info['content_type'],
        headers=headers
    )
    
@intelligent_reports_router.get("/ai-status", response_model=AIServiceStatus)
async def get_ai_service_status():
    """
    Obtenir le statut du service IA souverain
    
    Vérifie la disponibilité des modèles LLM locaux (Ollama, Transformers)
    """
    try:
        from app.ai_service import SovereignLLMService
        
        # Initialiser le service IA
        llm_service = SovereignLLMService()
        
        # Vérifier Ollama
        if llm_service.ollama_available:
            ollama_status = f"✅ Actif ({len(llm_service.available_models)} modèles)"
            models_available = llm_service.available_models
        else:
            ollama_status = "❌ Non disponible"
            models_available = []
        
        # Vérifier Transformers
        if llm_service.transformers_available:
            transformers_status = "✅ Actif"
            if not models_available:  # Si Ollama indisponible
                models_available = ["HuggingFace Transformers"]
        else:
            transformers_status = "❌ Non disponible"
        
        # Déterminer la disponibilité globale
        ai_available = llm_service.is_available()
        
        # Recommandation
        if not ai_available:
            recommendation = "Installer Ollama (https://ollama.ai) ou configurer HuggingFace Transformers"
        elif llm_service.ollama_available:
            recommendation = "Service IA optimal - Ollama disponible"
        else:
            recommendation = "Service IA de base - Envisager l'installation d'Ollama pour de meilleures performances"
        
        return AIServiceStatus(
            ai_available=ai_available,
            ollama_status=ollama_status,
            transformers_status=transformers_status,
            models_available=models_available,
            recommendation=recommendation
        )
        
    except Exception as e:
        logger.error(f"Erreur vérification statut IA: {e}")
        return AIServiceStatus(
            ai_available=False,
            ollama_status="❌ Erreur de vérification",
            transformers_status="❌ Erreur de vérification", 
            models_available=[],
            recommendation="Vérifier l'installation des dépendances IA"
        )

@intelligent_reports_router.get("/capabilities")
async def get_ai_capabilities():
    """
    Obtenir les capacités détaillées du système IA
    
    Liste les fonctionnalités d'analyse disponibles avec l'IA souveraine
    """
    return {
        "ai_agents": [
            {
                "name": "Analyseur de Sentiment Avancé",
                "description": "Détection nuancée des émotions et polarisation",
                "capabilities": [
                    "Analyse multilingue (français/anglais)",
                    "Détection d'émotions complexes",
                    "Évaluation de la polarisation",
                    "Comparaison sentiment officiel vs public"
                ]
            },
            {
                "name": "Analyseur de Tendances",
                "description": "Détection de patterns temporels et signaux faibles",
                "capabilities": [
                    "Détection automatique de pics d'activité",
                    "Prédictions basées sur les patterns",
                    "Signaux d'alerte précoce",
                    "Analyse de volatilité"
                ]
            },
            {
                "name": "Analyseur d'Influenceurs",
                "description": "Évaluation intelligente de l'impact et des risques",
                "capabilities": [
                    "Scoring automatique de risque",
                    "Estimation de la portée",
                    "Recommandations d'engagement",
                    "Détection de comptes suspects"
                ]
            },
            {
                "name": "Extracteur de Contenu Web",
                "description": "Lecture et analyse intelligente du contenu web",
                "capabilities": [
                    "Extraction automatique d'articles",
                    "Analyse des commentaires",
                    "Score d'authenticité des interactions",
                    "Détection de contenu généré artificiellement"
                ]
            }
        ],
        "ai_technologies": {
            "local_llm": {
                "name": "Modèles LLM Locaux (Ollama)",
                "description": "Modèles de langage hébergés localement",
                "models": ["Mistral 7B", "Llama 2 7B", "CodeLlama 7B", "Neural Chat 7B"],
                "advantages": ["Confidentialité totale", "Pas de limites d'usage", "Latence faible"]
            },
            "transformers": {
                "name": "HuggingFace Transformers",
                "description": "Modèles spécialisés open source",
                "models": ["Sentiment Analysis", "Zero-shot Classification", "Summarization"],
                "advantages": ["Modèles spécialisés", "Performance optimisée", "Multilingue"]
            },
            "rule_based": {
                "name": "Analyse par Règles",
                "description": "Système de fallback intelligent",
                "capabilities": ["Détection de patterns", "Indicateurs de risque", "Classification automatique"],
                "advantages": ["Rapide", "Explicable", "Toujours disponible"]
            }
        },
        "web_analysis": {
            "description": "Analyse approfondie du contenu web",
            "features": [
                "Extraction automatique du contenu principal",
                "Récupération et analyse des commentaires",
                "Évaluation de l'authenticité des interactions",
                "Comparaison sentiment articles vs réactions",
                "Détection de manipulation ou de bots"
            ],
            "supported_sites": [
                "Sites d'actualités standards",
                "Blogs et médiums",
                "Forums de discussion",
                "Plateformes avec commentaires",
                "Réseaux sociaux (selon disponibilité)"
            ],
            "limitations": [
                "Maximum 10 sources par rapport",
                "Respect des robots.txt",
                "Sites publics uniquement",
                "Pas de contenu protégé par authentification"
            ]
        },
        "output_formats": [
            {
                "format": "PDF",
                "description": "Rapport professionnel imprimable",
                "features": ["Mise en page optimisée", "Graphiques intégrés", "Export facilité"]
            },
            {
                "format": "HTML",
                "description": "Rapport interactif navigable",
                "features": ["Navigation fluide", "Responsive design", "Liens cliquables"]
            }
        ],
        "intelligence_features": [
            "Synthèse exécutive automatique",
            "Recommandations actionnables personnalisées",
            "Détection automatique de niveaux de priorité",
            "Évaluation de confiance des analyses",
            "Signaux d'alerte intelligents",
            "Comparaisons temporelles automatiques"
        ]
    }

# Ajouter AVANT l'endpoint POST generate-ministerial
@intelligent_reports_router.options("/generate-ministerial")
async def options_ministerial_report():
    """Handle preflight CORS request"""
    return Response(
        content="",
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, X-Requested-With",
            "Access-Control-Max-Age": "3600",
        }
    )


@intelligent_reports_router.post("/generate-ministerial")
async def generate_ministerial_report(
    request: IntelligentReportRequest,
    db: Session = Depends(get_db)
):
    """
    Rapport V3 - Style Ministériel Narratif
    """
    try:
        # AJOUT: Logs de débogage
        logger.info(f"Type de keyword_ids: {type(request.keyword_ids)}")
        logger.info(f"Contenu keyword_ids: {request.keyword_ids}")
        
        # Vérifications
        keywords = db.query(Keyword).filter(Keyword.id.in_(request.keyword_ids)).all()
        if not keywords:
            raise HTTPException(status_code=404, detail="Aucun mot-clé trouvé")
        
        # Initialiser générateur V3
        from app.report_generator import StrategicReportGeneratorV3
        generator = StrategicReportGeneratorV3(db)
        
        # Générer rapport ministériel
        logger.info("📝 Génération rapport ministériel V3...")
        report_data = await generator.generate_ministerial_report(
            keyword_ids=request.keyword_ids,
            days=request.days,
            report_title=request.report_title or "Rapport Stratégique Ministériel"
        )
        
        # Générer HTML
        from app.report_template import generate_ministerial_report_html
        html_content = generate_ministerial_report_html(report_data)
        
        # ✅ CORRECTION CRITIQUE : Utiliser StreamingResponse au lieu de Response
        from fastapi.responses import StreamingResponse
        import io
        
        if request.format == 'pdf':
            from weasyprint import HTML
            pdf_bytes = HTML(string=html_content).write_pdf()
            
            # Créer un stream depuis les bytes
            pdf_stream = io.BytesIO(pdf_bytes)
            
            filename = f"rapport_ministeriel_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            return StreamingResponse(
                pdf_stream,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"'
                }
            )
        else:
            # HTML
            html_stream = io.BytesIO(html_content.encode('utf-8'))
            
            filename = f"rapport_ministeriel_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.html"
            
            return StreamingResponse(
                html_stream,
                media_type="text/html",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"'
                }
            )
            
    except Exception as e:
        logger.error(f"Erreur génération rapport ministériel: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@intelligent_reports_router.get("/examples")
async def get_ai_analysis_examples():
    """
    Obtenir des exemples d'analyses IA
    
    Montre des exemples concrets d'insights générés par l'IA
    """
    return {
        "sentiment_analysis_examples": [
            {
                "input": "50 mentions avec 60% négatives, 30% neutres, 10% positives",
                "ai_output": "Sentiment critique dominant (60% négatif) indiquant une opinion publique défavorable. La faible proportion de mentions positives (10%) suggère un déficit de soutien actif. Recommandation: stratégie de gestion de crise avec communication proactive pour inverser la tendance.",
                "actions": ["Cellule de crise", "Communication corrective", "Engagement influenceurs"]
            },
            {
                "input": "100 mentions très polarisées: 45% positives, 5% neutres, 50% négatives",
                "ai_output": "Opinion publique extrêmement polarisée avec quasi-absence de neutralité (5%). Cette bipolarisation indique un sujet clivant nécessitant une communication nuancée pour éviter l'escalade.",
                "actions": ["Communication équilibrée", "Dialogue avec les deux camps", "Médiation"]
            }
        ],
        "trend_analysis_examples": [
            {
                "input": "Pic de 300% d'activité le 15/01, retour normal le 17/01",
                "ai_output": "Pic d'activité majeur détecté (+300% vs moyenne) avec retour rapide à la normale. Pattern typique d'une réaction à un événement ponctuel. L'IA recommande d'identifier le déclencheur pour anticipation future.",
                "triggers_detected": ["Annonce produit", "Déclaration officielle", "Article viral"]
            },
            {
                "input": "Croissance graduelle de 20% par semaine sur 4 semaines",
                "ai_output": "Tendance croissante soutenue (+20%/semaine) suggérant un intérêt grandissant organique. Pattern positif indiquant une montée d'influence naturelle à capitaliser.",
                "actions": ["Amplifier la communication", "Surfer sur la tendance", "Préparer la suite"]
            }
        ],
        "influencer_analysis_examples": [
            {
                "input": "Compte @TechExpert: 50k engagement, 20% sentiment négatif",
                "ai_output": "Influenceur à risque modéré identifié. Fort engagement (50k) mais tonalité critique (20% négatif). L'IA recommande un engagement proactif pour convertir cette influence en opportunité.",
                "risk_level": "MODÉRÉ",
                "recommended_action": "Engagement direct et constructif"
            },
            {
                "input": "Compte @NewsSource: 200k engagement, 80% sentiment négatif",
                "ai_output": "ALERTE: Influenceur critique majeur détecté. Combinaison dangereuse de forte portée (200k) et sentiment très négatif (80%). Intervention urgente requise.",
                "risk_level": "CRITIQUE",
                "recommended_action": "Gestion de crise immédiate"
            }
        ],
        "web_content_examples": [
            {
                "scenario": "Article neutre mais commentaires très négatifs",
                "ai_analysis": "Divergence détectée entre le ton de l'article (neutre) et les réactions du public (85% négatives). L'IA identifie un décalage entre la communication officielle et la perception réelle.",
                "insight": "Le message ne passe pas auprès du public malgré un traitement médiatique équilibré",
                "action": "Revoir la stratégie de communication pour mieux résonner avec les préoccupations du public"
            },
            {
                "scenario": "Commentaires suspects (même formulation, comptes récents)",
                "ai_analysis": "Score d'authenticité faible (0.3/1.0) détecté. L'IA identifie des patterns suspects: formulations similaires, comptes créés récemment, timing coordonné.",
                "insight": "Possible campagne artificielle ou manipulation de l'opinion",
                "action": "Enquête approfondie et surveillance renforcée des interactions"
            }
        ],
        "synthesis_examples": [
            {
                "scenario": "Crise modérée multi-sources",
                "ai_synthesis": "NIVEAU PRIORITÉ: ÉLEVÉ. L'IA détecte une convergence critique: sentiment négatif croissant (65%), 3 influenceurs à risque actifs, et 2 pics d'activité en 48h. Bien que modérée, la situation montre des signaux d'escalade potentielle.",
                "recommendations": [
                    "Activation surveillance H24",
                    "Préparation éléments de communication",
                    "Contact préventif avec influenceurs clés"
                ]
            }
        ]
    }


@intelligent_reports_router.post("/test-analysis")
async def test_ai_analysis(
    text: str,
    analysis_type: str = "sentiment",
    db: Session = Depends(get_db)
):
    """
    Tester l'analyse IA sur un texte donné
    
    Permet de tester les capacités d'analyse sans générer un rapport complet
    """
    if len(text) < 10:
        raise HTTPException(status_code=400, detail="Texte trop court (minimum 10 caractères)")
    
    try:
        from app.ia_service import SovereignLLMService
        
        # Initialiser le service IA
        llm_service = SovereignLLMService()
        
        if not llm_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="Service IA non disponible. Vérifiez l'installation d'Ollama ou HuggingFace."
            )
        
        # Préparer un contexte de test
        test_context = {
            'mentions': [
                {
                    'title': 'Test',
                    'content': text,
                    'author': 'Test User',
                    'source': 'test',
                    'sentiment': None,
                    'engagement_score': 1
                }
            ],
            'keywords': ['test'],
            'period_days': 1
        }
        
        # Construire le prompt selon le type d'analyse
        if analysis_type == "sentiment":
            prompt = f"Analyse le sentiment de ce texte et explique ton raisonnement: '{text}'"
        elif analysis_type == "risk":
            prompt = f"Évalue le niveau de risque de ce contenu: '{text}'"
        elif analysis_type == "category":
            prompt = f"Catégorise ce contenu et identifie ses thèmes principaux: '{text}'"
        else:
            prompt = f"Analyse ce texte de manière générale: '{text}'"
        
        # Lancer l'analyse
        start_time = datetime.utcnow()
        result = await llm_service.analyze_with_local_llm(prompt, test_context)
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Déterminer la méthode utilisée
        if llm_service.ollama_available:
            method_used = "Ollama LLM"
        elif llm_service.transformers_available:
            method_used = "HuggingFace Transformers"
        else:
            method_used = "Analyse par règles"
        
        return {
            "input_text": text,
            "analysis_type": analysis_type,
            "ai_result": result,
            "method_used": method_used,
            "processing_time_seconds": round(processing_time, 2),
            "ai_confidence": "high" if method_used != "Analyse par règles" else "medium"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur test IA: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du test IA: {str(e)}"
        )


@intelligent_reports_router.get("/keywords-available")
async def get_available_keywords(db: Session = Depends(get_db)):
    """
    Obtenir la liste des mots-clés disponibles avec statistiques
    
    Aide à la sélection des mots-clés pour les rapports
    """
    try:
        # Récupérer tous les mots-clés actifs
        keywords = db.query(Keyword).filter(Keyword.active == True).all()
        
        if not keywords:
            return {"keywords": []}
        
        # Calculer les statistiques pour chaque mot-clé
        keyword_stats = []
        
        # Période de référence (30 derniers jours)
        since_date = datetime.utcnow() - timedelta(days=30)
        
        for keyword in keywords:
            # Compter les mentions
            mentions_count = db.query(Mention).filter(
                Mention.keyword_id == keyword.id,
                Mention.published_at >= since_date
            ).count()
            
            # Analyser le sentiment
            mentions = db.query(Mention).filter(
                Mention.keyword_id == keyword.id,
                Mention.published_at >= since_date
            ).all()
            
            sentiment_dist = {'positive': 0, 'neutral': 0, 'negative': 0}
            total_engagement = 0
            
            for mention in mentions:
                if mention.sentiment and mention.sentiment in sentiment_dist:
                    sentiment_dist[mention.sentiment] += 1
                total_engagement += mention.engagement_score
            
            # Déterminer le niveau de priorité suggéré
            if mentions_count == 0:
                priority = "low"
            elif mentions_count >= 100:
                priority = "high"
            elif mentions_count >= 50:
                priority = "medium"
            else:
                priority = "low"
            
            # Sentiment dominant
            if sum(sentiment_dist.values()) > 0:
                dominant_sentiment = max(sentiment_dist, key=sentiment_dist.get)
            else:
                dominant_sentiment = "unknown"
            
            keyword_stats.append({
                "id": keyword.id,
                "keyword": keyword.keyword,
                "mentions_30d": mentions_count,
                "sentiment_distribution": sentiment_dist,
                "dominant_sentiment": dominant_sentiment,
                "total_engagement": total_engagement,
                "avg_engagement": total_engagement / max(mentions_count, 1),
                "last_collected": keyword.last_collected.isoformat() if keyword.last_collected else None,
                "priority_suggested": priority,
                "sources": json.loads(keyword.sources) if keyword.sources else []
            })
        
        # Trier par nombre de mentions (plus pertinent en premier)
        keyword_stats.sort(key=lambda x: x['mentions_30d'], reverse=True)
        
        return {
            "keywords": keyword_stats,
            "total_keywords": len(keyword_stats),
            "period": "30 derniers jours",
            "recommendations": {
                "min_keywords": 1,
                "max_keywords": 10,
                "suggested_period": "30 jours pour une analyse complète"
            }
        }
        
    except Exception as e:
        logger.error(f"Erreur récupération mots-clés: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la récupération des mots-clés"
        )


# ===== Fonctions utilitaires =====

def generate_report_async(
    keyword_ids: List[int],
    days: int,
    report_title: str,
    include_web_analysis: bool,
    format_type: str,
    db: Session,
    user_email: Optional[str] = None
):
    """
    Générer un rapport en arrière-plan (pour les gros rapports)
    """
    async def _generate():
        try:
            generator = IntelligentReportGenerator(db)
            
            report_data = await generator.generate_complete_report(
                keyword_ids=keyword_ids,
                days=days,
                report_title=report_title,
                include_web_analysis=include_web_analysis,
                format_type=format_type
            )
            
            logger.info(f"Rapport IA généré en arrière-plan pour {len(keyword_ids)} mots-clés")
            
            # TODO: Sauvegarder le rapport et envoyer un email si user_email fourni
            
        except Exception as e:
            logger.error(f"Erreur génération rapport arrière-plan: {e}")
    
    # Lancer la tâche asynchrone
    asyncio.create_task(_generate())


def generate_simple_executive_html(report_data: Dict) -> str:
    """Générer un HTML simple pour le rapport exécutif"""
    
    metadata = report_data.get('metadata', {})
    synthesis = report_data.get('executive_synthesis', {})
    summaries = report_data.get('content_summaries', {})
    recommendations = report_data.get('strategic_recommendations', [])
    
    html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{metadata.get('title', 'Rapport Exécutif')}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        .metadata {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}
        .synthesis {{
            background: #e8f5e9;
            padding: 20px;
            border-left: 4px solid #4caf50;
            margin: 20px 0;
        }}
        .summary-section {{
            margin: 20px 0;
            padding: 15px;
            background: #f9f9f9;
            border-radius: 5px;
        }}
        .recommendation {{
            background: #fff3cd;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #ffc107;
        }}
        .priority {{
            font-weight: bold;
            color: #d32f2f;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 {metadata.get('title', 'Rapport Exécutif')}</h1>
        
        <div class="metadata">
            <strong>Mots-clés analysés:</strong> {', '.join(metadata.get('keywords', []))}<br>
            <strong>Période:</strong> {metadata.get('period_days', 0)} jours<br>
            <strong>Contenus analysés:</strong> {metadata.get('total_contents_analyzed', 0)}<br>
            <strong>Généré le:</strong> {datetime.utcnow().strftime('%d/%m/%Y à %H:%M')}
        </div>
        
        <div class="synthesis">
            <h2>📊 Synthèse Exécutive</h2>
            <p><strong>Tonalité générale:</strong> {synthesis.get('overall_tone', 'N/A')} {synthesis.get('sentiment_emoji', '')}</p>
            <p>{synthesis.get('synthesis_text', 'Synthèse en cours de génération...')}</p>
        </div>
        
        <h2>💡 Points Critiques</h2>
        <ul>
            {''.join(f'<li>{point}</li>' for point in synthesis.get('critical_points', []))}
        </ul>
        
        <h2>✨ Opportunités</h2>
        <ul>
            {''.join(f'<li>{opp}</li>' for opp in synthesis.get('opportunities', []))}
        </ul>
        
        <h2>🎯 Recommandations Stratégiques</h2>
        {''.join(f'''
        <div class="recommendation">
            <div class="priority">Priorité: {rec.get('priority', 'N/A')}</div>
            <strong>{rec.get('category', 'N/A')}:</strong> {rec.get('action', 'N/A')}<br>
            <em>Rationale:</em> {rec.get('rationale', 'N/A')}<br>
            <em>Timeline:</em> {rec.get('timeline', 'N/A')}
        </div>
        ''' for rec in recommendations)}
        
        <h2>📝 Résumés par Catégorie</h2>
        {''.join(f'''
        <div class="summary-section">
            <h3>{category.replace('_', ' ').title()}: {data.get('count', 0)} contenus</h3>
            <p>{data.get('summary', 'N/A')}</p>
        </div>
        ''' for category, data in summaries.items() if data.get('count', 0) > 0)}
    </div>
</body>
</html>
    """
    
    return html

@intelligent_reports_router.post("/generate-async")
async def generate_intelligent_report_async(
    request: IntelligentReportRequest,
    background_tasks: BackgroundTasks,
    user_email: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Lancer la génération d'un rapport intelligent en arrière-plan
    
    Utile pour les rapports complexes qui prennent du temps
    """
    # Vérifications de base
    keywords = db.query(Keyword).filter(Keyword.id.in_(request.keyword_ids)).all()
    if not keywords:
        raise HTTPException(status_code=404, detail="Aucun mot-clé trouvé")
    
    # Lancer en arrière-plan
    background_tasks.add_task(
        generate_report_async,
        request.keyword_ids,
        request.days,
        request.report_title,
        request.include_web_analysis,
        request.format,
        db,
        user_email
    )
    
    return {
        "message": "Génération de rapport IA lancée en arrière-plan",
        "keywords": [kw.keyword for kw in keywords],
        "estimated_time": "2-5 minutes selon la complexité",
        "status": "processing",
        "notification": "Email envoyé une fois terminé" if user_email else "Consultez les logs pour le statut"
    }