"""
Routes API pour la génération de rapports - Version Cameroun
Support des analyses structurées en 5 sections
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import logging

from app.database import get_db
from app.models import Keyword
from app.report_generator import CameroonReportGenerator

logger = logging.getLogger(__name__)

# Router
reports_router = APIRouter(prefix="/api/reports", tags=["reports"])


# ===== Modèles Pydantic =====

class EnhancedReportRequest(BaseModel):
    keyword_ids: List[int]  # Plusieurs mots-clés
    days: int = 30
    report_object: str = ""  # Objet du rapport
    include_sections: Optional[List[str]] = None  # Sections à inclure (legacy)
    format: str = "pdf"  # pdf ou html


class ReportPreview(BaseModel):
    keywords: List[str]
    period_days: int
    total_mentions: int
    has_analysis: bool
    has_risk_assessment: bool
    has_trends: bool
    has_influencers: bool
    has_geography: bool
    risk_level: Optional[str] = None


# ===== Routes =====

@reports_router.post("/generate_enhanced_report")
async def generate_enhanced_report(
    request: EnhancedReportRequest,
    db: Session = Depends(get_db)
):
    """
    Générer un rapport enrichi avec analyse de risque et recommandations
    Structure en 5 sections : Positif, Négatif, Neutre, Synthèse, Influenceurs
    
    Args:
        request: Configuration du rapport enrichi
        
    Returns:
        PDF ou HTML du rapport enrichi
    """
    try:
        # Vérifier que les mots-clés existent
        keywords = db.query(Keyword).filter(Keyword.id.in_(request.keyword_ids)).all()
        if not keywords:
            raise HTTPException(status_code=404, detail="Aucun mot-clé trouvé")
        
        # Générer le rapport avec le nouveau générateur camerounais
        generator = CameroonReportGenerator(db)
        report_data = generator.generate_cameroon_report(
            keyword_ids=request.keyword_ids,
            days=request.days,
            report_object=request.report_object
        )
        
        if request.format == "pdf":
            # Générer PDF enrichi
            pdf_bytes = generator.generate_cameroon_pdf(report_data)
            
            keywords_str = '_'.join([kw.keyword for kw in keywords])[:30]
            filename = f"rapport_enrichi_{keywords_str}_{report_data['generated_at'].strftime('%Y%m%d_%H%M%S')}.pdf"
            
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )
        else:
            # Retourner HTML enrichi
            html_content = generator.generate_cameroon_html_report(report_data)
            
            return Response(
                content=html_content,
                media_type="text/html"
            )
            
    except Exception as e:
        logger.error(f"Erreur génération rapport enrichi: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération du rapport enrichi: {str(e)}"
        )


@reports_router.post("/preview-enhanced")
async def preview_enhanced_report(
    keyword_ids: List[int],
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Prévisualiser un rapport enrichi sans le générer
    
    Args:
        keyword_ids: IDs des mots-clés
        days: Période d'analyse
        
    Returns:
        Informations de prévisualisation enrichies
    """
    from app.models import Mention
    from datetime import datetime, timedelta
    
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
    
    # Évaluation rapide du risque
    risk_level = None
    if mentions:
        negative_mentions = [m for m in mentions if m.sentiment == 'negative']
        negative_ratio = len(negative_mentions) / mentions_count
        total_engagement = sum(m.engagement_score for m in mentions)
        
        # Score de risque simplifié
        risk_score = (negative_ratio * 0.5) + (min(mentions_count / (days * 5), 1) * 0.3) + (min(total_engagement / 10000, 1) * 0.2)
        
        if risk_score > 0.6:
            risk_level = "ÉLEVÉ"
        elif risk_score > 0.3:
            risk_level = "MODÉRÉ"
        else:
            risk_level = "FAIBLE"
    
    # Détection de pics
    timeline = {}
    for mention in mentions:
        if mention.published_at:
            date_key = mention.published_at.date()
            timeline[date_key] = timeline.get(date_key, 0) + 1
    
    has_trends = len(timeline) > 1
    
    # Diversité géographique (simulation)
    countries = set()
    for mention in mentions:
        # Simulation de détection de pays dans le contenu
        content_lower = (mention.title + ' ' + mention.content).lower()
        if 'france' in content_lower:
            countries.add('FR')
        if 'usa' in content_lower or 'united states' in content_lower:
            countries.add('US')
        if 'uk' in content_lower or 'royaume-uni' in content_lower:
            countries.add('GB')
    
    has_geography = len(countries) > 0
    
    return {
        "keywords": [kw.keyword for kw in keywords],
        "keyword_ids": keyword_ids,
        "period_days": days,
        "total_mentions": mentions_count,
        "has_analysis": mentions_count > 0,
        "has_risk_assessment": mentions_count > 0,
        "has_trends": has_trends,
        "has_influencers": mentions_count > 0,
        "has_geography": has_geography,
        "risk_level": risk_level
    }


@reports_router.get("/sections-available")
async def get_available_sections():
    """
    Obtenir la liste des sections disponibles pour les rapports enrichis
    (Maintenu pour compatibilité, mais la structure est maintenant fixe)
    
    Returns:
        Liste des sections avec descriptions
    """
    return {
        "sections": [
            {
                "id": "risk_assessment",
                "name": "Évaluation de Gravité",
                "description": "Note de risque (faible/modéré/élevé) avec facteurs détaillés",
                "icon": "🚨",
                "required": True
            },
            {
                "id": "positive_sentiment",
                "name": "Jugements Positifs",
                "description": "Analyse des réactions favorables des internautes",
                "icon": "😊",
                "required": True
            },
            {
                "id": "negative_sentiment",
                "name": "Jugements Négatifs",
                "description": "Analyse des réactions critiques des internautes",
                "icon": "😞",
                "required": True
            },
            {
                "id": "neutral_sentiment",
                "name": "Jugements Neutres",
                "description": "Analyse des réactions neutres et leur potentiel",
                "icon": "😐",
                "required": True
            },
            {
                "id": "synthesis",
                "name": "Synthèse des Jugements",
                "description": "Vue d'ensemble et tendance dominante",
                "icon": "📊",
                "required": True
            },
            {
                "id": "engaged_influencers",
                "name": "Influenceurs Engagés",
                "description": "France 24 et personnalités camerounaises actives",
                "icon": "👑",
                "required": True
            }
        ],
        "note": "Structure fixe en 6 sections pour cohérence analytique"
    }


@reports_router.get("/risk-methodology")
async def get_risk_methodology():
    """
    Obtenir la méthodologie d'évaluation du risque
    
    Returns:
        Explication de la grille de risque
    """
    return {
        "methodology": {
            "title": "Méthodologie d'Évaluation du Risque",
            "description": "Le niveau de risque est calculé selon 5 facteurs pondérés",
            "factors": [
                {
                    "name": "Volume",
                    "weight": "25%",
                    "description": "Nombre de mentions par jour (seuil: 10/jour = score max)",
                    "calculation": "Volume normalisé sur base 10 mentions/jour"
                },
                {
                    "name": "Sentiment",
                    "weight": "30%",
                    "description": "Proportion de mentions négatives",
                    "calculation": "Ratio mentions négatives / total mentions"
                },
                {
                    "name": "Engagement",
                    "weight": "20%",
                    "description": "Niveau d'interaction (likes, partages, vues)",
                    "calculation": "Engagement moyen normalisé sur 2000"
                },
                {
                    "name": "Pics d'Activité",
                    "weight": "15%",
                    "description": "Détection de pics inhabituels",
                    "calculation": "Ratio pic maximum / moyenne mobile"
                },
                {
                    "name": "Diversité Sources",
                    "weight": "10%",
                    "description": "Propagation sur différentes plateformes",
                    "calculation": "Nombre de sources distinctes (max 5)"
                }
            ],
            "scale": [
                {
                    "level": "FAIBLE",
                    "range": "0-39",
                    "color": "#10b981",
                    "description": "Situation normale, surveillance standard"
                },
                {
                    "level": "MODÉRÉ",
                    "range": "40-69",
                    "color": "#f59e0b",
                    "description": "Attention requise, surveillance renforcée"
                },
                {
                    "level": "ÉLEVÉ",
                    "range": "70-100",
                    "color": "#ef4444",
                    "description": "Situation critique, action immédiate requise"
                }
            ]
        }
    }


@reports_router.get("/templates")
async def get_report_templates():
    """
    Obtenir des modèles de rapport prédéfinis
    
    Returns:
        Liste des templates disponibles
    """
    return {
        "templates": [
            {
                "id": "standard_cameroon",
                "name": "Rapport Standard Cameroun",
                "description": "Structure complète en 6 sections pour analyse approfondie",
                "sections": ["risk_assessment", "positive_sentiment", "negative_sentiment", "neutral_sentiment", "synthesis", "engaged_influencers"],
                "duration": "14-30 jours",
                "audience": "Direction, analystes"
            },
            {
                "id": "crisis_management",
                "name": "Gestion de Crise",
                "description": "Focus sur les jugements négatifs et influenceurs à risque",
                "sections": ["risk_assessment", "negative_sentiment", "engaged_influencers", "synthesis"],
                "duration": "7 jours",
                "audience": "Cellule de crise"
            },
            {
                "id": "influence_mapping",
                "name": "Cartographie d'Influence",
                "description": "Analyse détaillée des influenceurs France 24 et personnalités",
                "sections": ["engaged_influencers", "synthesis"],
                "duration": "30 jours",
                "audience": "Service influence"
            }
        ]
    }

@reports_router.get("/keywords-available")
async def get_available_keywords(db: Session = Depends(get_db)):
    """
    Obtenir la liste des mots-clés disponibles pour les rapports
    
    Returns:
        Liste des mots-clés avec nombre de mentions
    """
    from app.models import Mention
    from datetime import datetime, timedelta
    
    keywords = db.query(Keyword).filter(Keyword.active == True).all()
    
    result = []
    since_date = datetime.utcnow() - timedelta(days=30)
    
    for keyword in keywords:
        mentions_count = db.query(Mention).filter(
            Mention.keyword_id == keyword.id,
            Mention.published_at >= since_date
        ).count()
        
        result.append({
            "id": keyword.id,
            "keyword": keyword.keyword,
            "mentions_30d": mentions_count,
            "last_collected": keyword.last_collected.isoformat() if keyword.last_collected else None
        })
    
    return {"keywords": result}

# Route de compatibilité avec l'ancienne API
@reports_router.post("/generate")
async def generate_legacy_report(
    request: EnhancedReportRequest,
    db: Session = Depends(get_db)
):
    """
    Route de compatibilité - redirige vers le générateur enrichi
    """
    return await generate_enhanced_report(request, db)