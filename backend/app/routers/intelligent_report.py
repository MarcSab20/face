"""
Routes pour la génération de rapports intelligents narratifs
VERSION CORRIGÉE - SANS ERREUR F-STRING
Priorité absolue : Groq → Gemini → Ollama
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Keyword, Mention
from app.unified_ai_service import UnifiedAIService
import os
import json

router = APIRouter(prefix="/api/reports", tags=["Reports"])
logger = logging.getLogger(__name__)


def get_prioritized_ai_service() -> UnifiedAIService:
    """
    Initialise le service IA avec PRIORISATION ABSOLUE Groq → Gemini → Ollama
    """
    groq_key = os.getenv("GROQ_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    logger.info("🔍 Configuration des services IA:")
    logger.info(f"   - Groq: {'✅ Configuré' if groq_key else '❌ Manquant'}")
    logger.info(f"   - Gemini: {'✅ Configuré' if gemini_key else '❌ Manquant'}")
    
    if not groq_key and not gemini_key:
        logger.error("❌ CRITIQUE: Aucune API externe configurée!")
        raise HTTPException(
            status_code=503,
            detail="Aucune API IA externe configurée. Veuillez configurer GROQ_API_KEY ou GEMINI_API_KEY"
        )
    
    service = UnifiedAIService(
        groq_api_key=groq_key,
        gemini_api_key=gemini_key,
        ollama_host=os.getenv("OLLAMA_HOST", "http://ollama:11434"),
        ollama_model=os.getenv("OLLAMA_DEFAULT_MODEL", "gemma:2b")
    )
    
    return service


def filter_relevant_content(mentions: List[Mention], context_keywords: List[str]) -> List[Mention]:
    """
    Filtre intelligent des mentions pertinentes
    """
    relevant_mentions = []
    
    for mention in mentions:
        combined_text = " ".join(filter(None, [
            mention.title or "",
            mention.content or "",
            mention.author or ""
        ])).lower()
        
        # Vérifier pertinence
        is_relevant = any(kw.lower() in combined_text for kw in context_keywords)
        
        # Éliminer contenus trop courts (spam)
        if is_relevant and len(combined_text) > 50:
            relevant_mentions.append(mention)
    
    logger.info(f"📊 Filtrage: {len(mentions)} → {len(relevant_mentions)} contenus pertinents")
    return relevant_mentions


def build_content_list(contents: List[dict], max_items: int = 15) -> str:
    """
    Construire une liste de contenus pour les prompts
    """
    items = []
    for c in contents[:max_items]:
        title = c.get("title", "Sans titre")[:150]
        items.append(f"• {title}")
    
    return "\n".join(items)


def build_influencer_list(influencers: List[dict]) -> str:
    """
    Construire une liste d'influenceurs pour les prompts
    """
    items = []
    for i, inf in enumerate(influencers[:5], 1):
        author = inf.get("author", "Inconnu")
        content_samples = inf.get("content", [])
        sample_titles = [c.get("title", "")[:60] for c in content_samples[:2]]
        sample_text = ", ".join(sample_titles)
        items.append(f"{i}. {author} - Exemples d'interventions : {sample_text}")
    
    return "\n".join(items)


async def generate_narrative_pure(
    ai_service: UnifiedAIService,
    section_name: str,
    data: dict,
    context: str
) -> str:
    """
    Génère une section PUREMENT NARRATIVE sans aucune statistique
    Force l'utilisation de Groq ou Gemini
    """
    logger.info(f"🎨 Génération narrative: {section_name}")
    
    # Construire les contenus formatés AVANT les f-strings
    if section_name == "summary":
        content_list = build_content_list(data.get('content', []))
        prompt = f"""Contexte de surveillance : {context}

Vous analysez des discussions publiques collectées sur ce sujet.

CONTENUS COLLECTÉS (extraits représentatifs) :
{content_list}

INSTRUCTION ABSOLUE :
Rédigez un résumé narratif en 3-4 paragraphes fluides qui raconte ce qui se dit dans ces discussions.

RÈGLES STRICTES :
- Rédigez UNIQUEMENT en paragraphes narratifs fluides
- INTERDICTION ABSOLUE de listes à puces, numéros, bullet points
- INTERDICTION ABSOLUE de mentionner des chiffres, pourcentages, statistiques
- Décrivez qualitativement les tendances observées
- Racontez les thèmes principaux comme une histoire
- Ton professionnel, factuel, style briefing ministériel
- Ignorez les contenus non pertinents au contexte

Réponse (paragraphes narratifs uniquement) :"""

    elif section_name == "sentiment":
        positive_list = build_content_list(data.get('positive', []), 5)
        negative_list = build_content_list(data.get('negative', []), 5)
        neutral_list = build_content_list(data.get('neutral', []), 5)
        
        prompt = f"""Contexte : {context}

EXEMPLES DE CONTENUS POSITIFS :
{positive_list}

EXEMPLES DE CONTENUS CRITIQUES :
{negative_list}

EXEMPLES DE CONTENUS NEUTRES :
{neutral_list}

INSTRUCTION ABSOLUE :
Rédigez une analyse narrative en 3-4 paragraphes sur les tonalités et sentiments exprimés.

RÈGLES STRICTES :
- Paragraphes narratifs fluides UNIQUEMENT
- AUCUN chiffre, pourcentage, statistique
- Décrivez qualitativement : "majoritairement", "une partie", "certains", etc.
- Racontez les émotions et réactions observées
- Ton professionnel et analytique

Réponse :"""

    elif section_name == "influencers":
        influencer_list = build_influencer_list(data.get('influencers', []))
        
        prompt = f"""Contexte : {context}

PRINCIPAUX ACTEURS IDENTIFIÉS :
{influencer_list}

INSTRUCTION ABSOLUE :
Rédigez une analyse narrative en 3-4 paragraphes sur les acteurs influents et leur rôle.

RÈGLES STRICTES :
- Paragraphes narratifs fluides UNIQUEMENT
- AUCUN chiffre ou statistique
- Décrivez qualitativement leur influence et leur positionnement
- Racontez leur rôle dans les discussions
- Ton professionnel

Réponse :"""

    elif section_name == "themes":
        content_list = build_content_list(data.get('content', []), 20)
        
        prompt = f"""Contexte : {context}

CONTENUS À FORT ENGAGEMENT :
{content_list}

INSTRUCTION ABSOLUE :
Rédigez une analyse narrative en 3-4 paragraphes sur les thèmes principaux identifiés.

RÈGLES STRICTES :
- Paragraphes narratifs fluides UNIQUEMENT
- AUCUN chiffre ou statistique
- Identifiez et décrivez qualitativement les sujets récurrents
- Racontez les préoccupations principales
- Ton professionnel

Réponse :"""

    elif section_name == "recommendations":
        prompt = f"""Contexte : {context}

Observations générales sur les discussions analysées.

INSTRUCTION ABSOLUE :
Rédigez 3-4 paragraphes de recommandations stratégiques narratives.

RÈGLES STRICTES :
- Paragraphes narratifs fluides UNIQUEMENT
- AUCUN chiffre ou statistique
- Proposez des actions concrètes de manière narrative
- Ton professionnel, style briefing ministériel
- Recommandations actionnables

Réponse :"""

    else:
        return f"Section {section_name} non configurée."
    
    # FORCER Groq ou Gemini
    try:
        # Priorité 1 : GROQ
        if os.getenv("GROQ_API_KEY"):
            logger.info("🚀 Tentative avec Groq (priorité 1)")
            try:
                result = await ai_service.generate(
                    prompt=prompt,
                    max_tokens=1000,
                    temperature=0.2  # Factualité maximale
                )
                
                if result.get('success') and result.get('text'):
                    text = result['text'].strip()
                    if len(text) > 100:
                        logger.info(f"✅ Section '{section_name}' générée avec Groq")
                        return text
            except Exception as e:
                logger.warning(f"⚠️ Groq a échoué: {e}")
        
        # Priorité 2 : GEMINI
        if os.getenv("GEMINI_API_KEY"):
            logger.info("🌟 Tentative avec Gemini (priorité 2)")
            try:
                result = await ai_service.generate(
                    prompt=prompt,
                    max_tokens=1000,
                    temperature=0.2
                )
                
                if result.get('success') and result.get('text'):
                    text = result['text'].strip()
                    if len(text) > 100:
                        logger.info(f"✅ Section '{section_name}' générée avec Gemini")
                        return text
            except Exception as e:
                logger.warning(f"⚠️ Gemini a échoué: {e}")
        
        # Dernier recours : Ollama (mais on préfère éviter)
        logger.warning("⚠️ Fallback vers Ollama (moins optimal)")
        result = await ai_service.generate(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.2
        )
        
        if result.get('success') and result.get('text'):
            return result['text'].strip()
        
        raise Exception("Tous les services IA ont échoué")
        
    except Exception as e:
        logger.error(f"❌ Erreur génération section {section_name}: {str(e)}")
        return f"Impossible de générer cette section (erreur technique: {str(e)})"


@router.post("/generate-narrative")
async def generate_narrative_report(
    keyword_ids: List[int] = Query(..., description="Liste des IDs de mots-clés"),
    period: str = Query("30d", description="Période (7d, 14d, 30d, 90d)"),
    sections: List[str] = Query(
        ["summary", "sentiment", "influencers", "themes", "recommendations"],
        description="Sections à générer"
    ),
    db: Session = Depends(get_db)
):
    """
    Génère un rapport narratif pur sans statistiques
    Priorité : Groq → Gemini → Ollama
    """
    try:
        logger.info(f"📊 Génération rapport: keywords={keyword_ids}, period={period}")
        
        # === ÉTAPE 1: Récupérer contexte ===
        keywords = db.query(Keyword).filter(Keyword.id.in_(keyword_ids)).all()
        
        if not keywords:
            raise HTTPException(status_code=404, detail="Aucun mot-clé trouvé")
        
        keyword_texts = [kw.keyword for kw in keywords]
        context = f"Surveillance de l'opinion publique sur : {', '.join(keyword_texts)}"
        
        logger.info(f"🎯 Contexte: {context}")
        
        # === ÉTAPE 2: Récupérer mentions ===
        period_days = int(period.replace('d', ''))
        start_date = datetime.now() - timedelta(days=period_days)
        
        mentions = db.query(Mention).filter(
            Mention.keyword_id.in_(keyword_ids),
            Mention.collected_at >= start_date
        ).all()
        
        logger.info(f"📥 {len(mentions)} mentions brutes collectées")
        
        if len(mentions) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Aucune mention trouvée pour la période de {period_days} jours"
            )
        
        # === ÉTAPE 3: Filtrer contenus pertinents ===
        relevant_mentions = filter_relevant_content(mentions, keyword_texts)
        
        if len(relevant_mentions) == 0:
            raise HTTPException(
                status_code=404,
                detail="Aucun contenu pertinent après filtrage"
            )
        
        # === ÉTAPE 4: Initialiser service IA ===
        ai_service = get_prioritized_ai_service()
        
        # === ÉTAPE 5: Préparer données pour chaque section ===
        sample_mentions = relevant_mentions[:100]  # Limiter à 100 pour performance
        
        # Données résumé
        data_summary = {
            "content": [
                {
                    "title": m.title or "Sans titre",
                    "excerpt": (m.content or "")[:200]
                }
                for m in sample_mentions[:20]
            ]
        }
        
        # Données sentiment
        data_sentiment = {
            "positive": [
                {"title": m.title, "excerpt": (m.content or "")[:150]} 
                for m in sample_mentions if m.sentiment == "positive"
            ][:8],
            "negative": [
                {"title": m.title, "excerpt": (m.content or "")[:150]} 
                for m in sample_mentions if m.sentiment == "negative"
            ][:8],
            "neutral": [
                {"title": m.title, "excerpt": (m.content or "")[:150]} 
                for m in sample_mentions if m.sentiment == "neutral"
            ][:8]
        }
        
        # Données influenceurs
        from collections import Counter
        author_counts = Counter([m.author for m in sample_mentions if m.author and m.author != 'Unknown'])
        data_influencers = {
            "influencers": [
                {
                    "author": author,
                    "content": [
                        {"title": m.title}
                        for m in sample_mentions if m.author == author
                    ][:3]
                }
                for author, _ in author_counts.most_common(8)
            ]
        }
        
        # Données thèmes (contenus à fort engagement)
        sorted_mentions = sorted(
            sample_mentions,
            key=lambda m: getattr(m, 'engagement_score', 0) or 0,
            reverse=True
        )
        
        data_themes = {
            "content": [
                {
                    "title": m.title,
                    "excerpt": (m.content or "")[:200]
                }
                for m in sorted_mentions[:25]
            ]
        }
        
        # Données recommandations
        data_recommendations = {
            "context": context,
            "sample_concerns": [m.title for m in sorted_mentions[:10]]
        }
        
        # === ÉTAPE 6: Générer sections ===
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
                logger.info(f"📝 Génération section: {section}")
                content = await generate_narrative_pure(
                    ai_service,
                    section,
                    section_data_map[section],
                    context
                )
                report_sections[section] = content
        
        # === ÉTAPE 7: Compiler rapport final ===
        # Obtenir info sur service utilisé (STRING pas OBJECT)
        available_services = ai_service.get_available_services()
        primary_service_label = available_services[0].get("label", "Inconnu") if available_services else "Inconnu"
        
        report = {
            "metadata": {
                "title": f"Rapport d'Analyse - {', '.join(keyword_texts)}",
                "generated_at": datetime.now().isoformat(),
                "period": f"{period_days} jours",
                "keywords": keyword_texts,
                "total_mentions_collected": len(mentions),
                "relevant_mentions_analyzed": len(relevant_mentions),
                "classification": "DOCUMENT DE TRAVAIL - DIFFUSION RESTREINTE",
                "ai_service_used": primary_service_label  # STRING pas OBJECT
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
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-ai-services")
async def test_ai_services():
    """
    Tester la disponibilité des services IA
    """
    try:
        ai_service = get_prioritized_ai_service()
        
        available = ai_service.get_available_services()
        
        # Test rapide
        test_result = await ai_service.generate(
            prompt="Réponds simplement 'Service fonctionnel' en un paragraphe.",
            max_tokens=50,
            temperature=0.1
        )
        
        return {
            "services_disponibles": [
                {
                    "nom": svc.get("label"),
                    "priorite": svc.get("priority")
                }
                for svc in available
            ],
            "service_primaire": available[0].get("label") if available else "Aucun",
            "test_generation": {
                "succes": test_result.get('success'),
                "service_utilise": test_result.get('service'),
                "reponse": test_result.get('text', '')[:100]
            }
        }
    except Exception as e:
        logger.error(f"Erreur test services IA: {e}")
        raise HTTPException(status_code=500, detail=str(e))