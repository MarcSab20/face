"""
Routes pour la génération de rapports intelligents narratifs
VERSION CORRIGÉE - Priorisation Groq/Gemini
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi import Depends
from typing import List, Optional
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Keyword, Mention
from app.unified_ai_service import UnifiedAIService
import os

router = APIRouter(prefix="/api/reports", tags=["Reports"])
logger = logging.getLogger(__name__)


def get_prioritized_ai_service() -> UnifiedAIService:
    """
    Initialise le service IA avec PRIORISATION ABSOLUE de Groq et Gemini
    """
    # Récupérer les clés API depuis l'environnement
    groq_key = os.getenv("GROQ_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    logger.info("🔍 Vérification des clés API disponibles:")
    logger.info(f"   - Groq API Key: {'✅ Présente' if groq_key else '❌ Manquante'}")
    logger.info(f"   - Gemini API Key: {'✅ Présente' if gemini_key else '❌ Manquante'}")
    
    # Créer le service avec priorisation explicite
    service = UnifiedAIService(
        groq_api_key=groq_key,
        gemini_api_key=gemini_key,
        ollama_host=os.getenv("OLLAMA_HOST", "http://ollama:11434")
    )
    
    # Vérifier les services disponibles
    available = service.get_available_services()
    logger.info(f"🤖 Services IA disponibles: {available}")
    
    if not groq_key and not gemini_key:
        logger.warning("⚠️ ATTENTION: Aucune clé API externe - utilisation d'Ollama uniquement")
    
    return service


def filter_relevant_content(mentions: List[Mention], context_keywords: List[str]) -> List[Mention]:
    """
    Filtre les mentions pour ne garder que celles qui sont réellement pertinentes au contexte
    
    Args:
        mentions: Liste de toutes les mentions
        context_keywords: Mots-clés du contexte de surveillance
    
    Returns:
        Liste filtrée de mentions pertinentes
    """
    relevant_mentions = []
    
    for mention in mentions:
        # Combiner tous les textes disponibles
        combined_text = " ".join(filter(None, [
            mention.title or "",
            mention.content or "",
            mention.author or ""
        ])).lower()
        
        # Vérifier si au moins un mot-clé du contexte est présent
        is_relevant = any(kw.lower() in combined_text for kw in context_keywords)
        
        # Éliminer les contenus trop courts (probablement spam)
        if is_relevant and len(combined_text) > 50:
            relevant_mentions.append(mention)
    
    logger.info(f"📊 Filtrage: {len(mentions)} mentions → {len(relevant_mentions)} pertinentes")
    
    return relevant_mentions


async def generate_narrative_section(
    ai_service: UnifiedAIService,
    section_name: str,
    data: dict,
    context: str
) -> str:
    """
    Génère une section narrative en utilisant l'IA avec PRIORISATION GROQ/GEMINI
    
    Args:
        ai_service: Service IA unifié
        section_name: Nom de la section
        data: Données à analyser
        context: Contexte de surveillance
    
    Returns:
        Texte narratif généré
    """
    logger.info(f"🎨 Génération section: {section_name}")
    
    # Construire le prompt spécifique à chaque section
    prompts = {
        "summary": f"""Contexte: {context}

Données: {len(data.get('content', []))} contenus les plus représentatifs collectés.

INSTRUCTION CRITIQUE:
Rédigez un résumé exécutif professionnel de 2-4 paragraphes qui présente les tendances principales observées dans les discussions.

RÈGLES STRICTES:
- Rédigez UNIQUEMENT en paragraphes fluides et cohérents
- N'utilisez JAMAIS de listes à puces, numéros ou bullet points
- N'incluez AUCUN chiffre, statistique ou pourcentage
- Ton professionnel, factuel, neutre (style briefing ministériel)
- Ignorez complètement les données non pertinentes au contexte
- Concentrez-vous sur les grandes tendances, pas les détails

Exemples de contenus analysés (titres):
{chr(10).join([f'- {c.get("title", "Sans titre")[:100]}' for c in data.get('content', [])[:10]])}

Réponse:""",

        "sentiment": f"""Contexte: {context}

Données analysées:
- Contenus positifs: {len(data.get('positive', []))} exemples
- Contenus négatifs: {len(data.get('negative', []))} exemples  
- Contenus neutres: {len(data.get('neutral', []))} exemples

INSTRUCTION CRITIQUE:
Rédigez une analyse narrative de 2-4 paragraphes sur les sentiments exprimés dans les discussions.

RÈGLES STRICTES:
- Rédigez UNIQUEMENT en paragraphes fluides et cohérents
- N'utilisez JAMAIS de listes à puces, numéros ou bullet points
- N'incluez AUCUN chiffre, statistique ou pourcentage
- Décrivez les tonalités observées de manière qualitative
- Ignorez complètement les données non pertinentes au contexte

Exemples de contenus positifs:
{chr(10).join([f'- {c.get("title", "")}' for c in data.get('positive', [])[:5]])}

Exemples de contenus négatifs:
{chr(10).join([f'- {c.get("title", "")}' for c in data.get('negative', [])[:5]])}

Réponse:""",

        "influencers": f"""Contexte: {context}

Top 5 des auteurs les plus actifs:
{chr(10).join([f'{i+1}. {inf.get("author")} - Exemples: {", ".join([c.get("title", "")[:50] for c in inf.get("content", [])[:2]])}' 
              for i, inf in enumerate(data.get('influencers', [])[:5])])}

INSTRUCTION CRITIQUE:
Rédigez une analyse narrative de 2-4 paragraphes sur les acteurs clés et leur influence dans les discussions.

RÈGLES STRICTES:
- Rédigez UNIQUEMENT en paragraphes fluides et cohérents
- N'utilisez JAMAIS de listes à puces, numéros ou bullet points
- N'incluez AUCUN chiffre, statistique ou pourcentage
- Décrivez les rôles et l'impact des acteurs de manière qualitative
- Ignorez complètement les données non pertinentes au contexte

Réponse:""",

        "themes": f"""Contexte: {context}

Principaux contenus à fort engagement:
{chr(10).join([f'- {c.get("title", "Sans titre")[:100]}' for c in data.get('content', [])[:15]])}

INSTRUCTION CRITIQUE:
Rédigez une analyse narrative de 2-4 paragraphes sur les thèmes principaux et les préoccupations identifiées.

RÈGLES STRICTES:
- Rédigez UNIQUEMENT en paragraphes fluides et cohérents
- N'utilisez JAMAIS de listes à puces, numéros ou bullet points
- N'incluez AUCUN chiffre, statistique ou pourcentage
- Identifiez les sujets récurrents et leur importance
- Ignorez complètement les données non pertinentes au contexte

Réponse:""",

        "recommendations": f"""Contexte: {context}

Observations:
- Ratio contenus critiques/positifs dans les discussions
- Préoccupations principales identifiées

INSTRUCTION CRITIQUE:
Rédigez 2-4 paragraphes de recommandations stratégiques basées sur l'analyse.

RÈGLES STRICTES:
- Rédigez UNIQUEMENT en paragraphes fluides et cohérents
- N'utilisez JAMAIS de listes à puces, numéros ou bullet points
- N'incluez AUCUN chiffre, statistique ou pourcentage
- Proposez des actions concrètes de manière narrative
- Ton professionnel adapté à un briefing ministériel

Réponse:"""
    }
    
    prompt = prompts.get(section_name, "")
    
    if not prompt:
        return f"[Section {section_name} non configurée]"
    
    try:
        # FORCER l'utilisation de Groq/Gemini en priorité
        services_to_try = []
        
        # 1. GROQ en premier (si disponible)
        if os.getenv("GROQ_API_KEY"):
            services_to_try.append(("groq", "llama-3.1-70b-versatile"))
            logger.info("🚀 Tentative avec Groq (priorité 1)")
        
        # 2. GEMINI en second (si disponible)
        if os.getenv("GEMINI_API_KEY"):
            services_to_try.append(("gemini", "gemini-1.5-flash"))
            logger.info("🌟 Gemini disponible en fallback (priorité 2)")
        
        # 3. OLLAMA en dernier recours uniquement
        services_to_try.append(("ollama", "gemma:2b"))
        
        # Essayer les services dans l'ordre de priorité
        last_error = None
        for service_name, model in services_to_try:
            try:
                logger.info(f"🤖 Tentative avec {service_name} ({model})...")
                
                response = await ai_service.generate_completion(
                    prompt=prompt,
                    max_tokens=800,
                    temperature=0.3,  # Factualité maximale
                    service=service_name,
                    model=model
                )
                
                if response and len(response.strip()) > 50:
                    logger.info(f"✅ Section '{section_name}' générée avec {service_name}")
                    return response.strip()
                else:
                    logger.warning(f"⚠️ Réponse vide de {service_name}, passage au suivant")
                    
            except Exception as e:
                last_error = e
                logger.warning(f"⚠️ Échec avec {service_name}: {str(e)}, passage au suivant")
                continue
        
        # Si tous les services ont échoué
        raise Exception(f"Tous les services IA ont échoué. Dernière erreur: {last_error}")
        
    except Exception as e:
        logger.error(f"❌ Erreur génération section {section_name}: {str(e)}")
        return f"[Impossible de générer la section {section_name}]"


@router.post("/generate-narrative")
async def generate_narrative_report(
    keyword_ids: List[int] = Query(..., description="Liste des IDs de mots-clés à analyser"),
    period: str = Query("7d", description="Période d'analyse (7d, 14d, 30d, 90d)"),
    sections: List[str] = Query(..., description="Sections à inclure dans le rapport"),
    db: Session = Depends(get_db)
):
    """
    Génère un rapport intelligent narratif avec priorisation Groq/Gemini
    
    Sections disponibles:
    - summary: Résumé exécutif
    - sentiment: Analyse de sentiment
    - influencers: Influenceurs et acteurs clés
    - themes: Thèmes et préoccupations
    - recommendations: Recommandations stratégiques
    """
    try:
        logger.info(f"📊 Génération rapport narratif: keywords={keyword_ids}, period={period}")
        
        # === ÉTAPE 1: Récupérer le contexte (mots-clés) ===
        keywords = db.query(Keyword).filter(Keyword.id.in_(keyword_ids)).all()
        
        if not keywords:
            raise HTTPException(status_code=404, detail="Aucun mot-clé trouvé")
        
        keyword_texts = [kw.keyword for kw in keywords]
        context = f"Surveillance de l'opinion publique sur : {', '.join(keyword_texts)}"
        
        logger.info(f"🎯 Contexte: {context}")
        
        # === ÉTAPE 2: Récupérer les mentions de la période ===
        period_days = int(period.replace('d', ''))
        start_date = datetime.now() - timedelta(days=period_days)
        
        mentions = db.query(Mention).filter(
            Mention.keyword_id.in_(keyword_ids),
            Mention.collected_at >= start_date
        ).all()
        
        logger.info(f"📥 {len(mentions)} mentions collectées pour la période")
        
        if len(mentions) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Aucune mention trouvée pour la période de {period_days} jours"
            )
        
        # === ÉTAPE 3: Filtrer les mentions pertinentes ===
        relevant_mentions = filter_relevant_content(mentions, keyword_texts)
        
        if len(relevant_mentions) == 0:
            raise HTTPException(
                status_code=404,
                detail="Aucun contenu pertinent trouvé après filtrage"
            )
        
        # === ÉTAPE 4: Initialiser le service IA (GROQ/GEMINI prioritaire) ===
        ai_service = get_prioritized_ai_service()
        available_services = ai_service.get_available_services()
        
        if not available_services:
            raise HTTPException(
                status_code=503,
                detail="Aucun service IA disponible"
            )
        
        # === ÉTAPE 5: Préparer les données pour chaque section ===
        # Limiter à 50 mentions max pour éviter surcharge
        sample_mentions = relevant_mentions[:50]
        
        data_summary = {
            "content": [
                {
                    "title": m.title or "Sans titre",
                    "source": m.source,
                    "author": m.author,
                    "excerpt": (m.content or "")[:300],
                    "sentiment": m.sentiment,
                    "collected_at": m.collected_at.isoformat() if m.collected_at else None
                }
                for m in sample_mentions[:10]  # 10 plus représentatives
            ]
        }
        
        data_sentiment = {
            "positive": [{"title": m.title, "excerpt": (m.content or "")[:200]} 
                        for m in sample_mentions if m.sentiment == "positive"][:5],
            "negative": [{"title": m.title, "excerpt": (m.content or "")[:200]} 
                        for m in sample_mentions if m.sentiment == "negative"][:5],
            "neutral": [{"title": m.title, "excerpt": (m.content or "")[:200]} 
                       for m in sample_mentions if m.sentiment == "neutral"][:5]
        }
        
        # Top auteurs par nombre de contenus
        from collections import Counter
        author_counts = Counter([m.author for m in sample_mentions if m.author])
        data_influencers = {
            "influencers": [
                {
                    "author": author,
                    "count": count,
                    "content": [
                        {"title": m.title, "source": m.source}
                        for m in sample_mentions if m.author == author
                    ][:3]
                }
                for author, count in author_counts.most_common(5)
            ]
        }
        
        # Trier par engagement pour identifier les thèmes
        sorted_by_engagement = sorted(
            sample_mentions,
            key=lambda m: getattr(m, 'engagement_score', 0) or 0,
            reverse=True
        )
        
        data_themes = {
            "content": [
                {
                    "title": m.title,
                    "excerpt": (m.content or "")[:200],
                    "engagement": getattr(m, 'engagement_score', 0)
                }
                for m in sorted_by_engagement[:15]
            ]
        }
        
        # Données pour recommandations
        critical_ratio = len([m for m in sample_mentions if m.sentiment == "negative"]) / max(len(sample_mentions), 1)
        data_recommendations = {
            "critical_ratio": critical_ratio,
            "total_analyzed": len(sample_mentions),
            "main_concerns": [m.title for m in sorted_by_engagement[:5]]
        }
        
        # === ÉTAPE 6: Générer les sections demandées ===
        report_sections = {}
        
        section_data_map = {
            "summary": data_summary,
            "sentiment": data_sentiment,
            "influencers": data_influencers,
            "themes": data_themes,
            "recommendations": data_recommendations
        }
        
        for section in sections:
            if section in section_data_map:
                content = await generate_narrative_section(
                    ai_service,
                    section,
                    section_data_map[section],
                    context
                )
                report_sections[section] = content
        
        # === ÉTAPE 7: Compiler le rapport final ===
        report = {
            "metadata": {
                "title": f"Rapport d'Analyse - {', '.join(keyword_texts)}",
                "generated_at": datetime.now().isoformat(),
                "period": f"{period_days} jours",
                "keywords": keyword_texts,
                "total_mentions_collected": len(mentions),
                "relevant_mentions_analyzed": len(relevant_mentions),
                "ai_services_used": available_services,
                "classification": "DOCUMENT DE TRAVAIL - DIFFUSION RESTREINTE"
            },
            "sections": report_sections,
            "context": context
        }
        
        logger.info(f"✅ Rapport généré avec succès ({len(report_sections)} sections)")
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur génération rapport: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))