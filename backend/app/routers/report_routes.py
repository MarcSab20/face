"""
Routes pour la génération de rapports avancés - VERSION CORRIGÉE
Brand Monitor v2.0

Cette version gère l'absence potentielle de l'attribut sentiment_score
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from collections import Counter
import statistics

from app.database import get_db
from app.models import Keyword, Mention
from app.unified_ai_service import UnifiedAIService

router = APIRouter(prefix="/api/reports", tags=["reports"])


# ============================================================
# FONCTIONS UTILITAIRES AVEC GESTION DES ATTRIBUTS MANQUANTS
# ============================================================

def get_sentiment_score(mention: Mention) -> float:
    """
    Récupérer le score de sentiment avec fallback
    Gère les cas où l'attribut n'existe pas
    """
    # Essayer sentiment_score
    if hasattr(mention, 'sentiment_score') and mention.sentiment_score is not None:
        return float(mention.sentiment_score)
    
    # Essayer score (nom alternatif)
    if hasattr(mention, 'score') and mention.score is not None:
        return float(mention.score)
    
    # Fallback : convertir sentiment en score
    sentiment = getattr(mention, 'sentiment', None)
    if sentiment:
        if sentiment.lower() == 'positive':
            return 0.7
        elif sentiment.lower() == 'negative':
            return -0.7
        else:
            return 0.0
    
    return 0.0


def get_sentiment_label(score: float) -> str:
    """Convertir un score en label"""
    if score > 0.3:
        return "positive"
    elif score < -0.3:
        return "negative"
    return "neutral"


def get_date_range(period: str) -> Optional[datetime]:
    """Calculer la date de début selon la période"""
    if period == "all":
        return None
    
    days_map = {
        "24h": 1,
        "7d": 7,
        "30d": 30,
        "90d": 90
    }
    
    days = days_map.get(period, 7)
    return datetime.utcnow() - timedelta(days=days)


def calculate_sentiment_distribution(mentions: List[Mention]) -> Dict[str, Any]:
    """Calculer la distribution des sentiments"""
    sentiments = []
    
    for m in mentions:
        sentiment = getattr(m, 'sentiment', None)
        if sentiment:
            sentiments.append(sentiment)
        else:
            # Fallback basé sur le score
            score = get_sentiment_score(m)
            sentiments.append(get_sentiment_label(score))
    
    total = len(sentiments)
    
    if total == 0:
        return {
            "positive": 0,
            "neutral": 0,
            "negative": 0,
            "positive_percent": 0,
            "neutral_percent": 0,
            "negative_percent": 0
        }
    
    counter = Counter(sentiments)
    
    return {
        "positive": counter.get('positive', 0),
        "neutral": counter.get('neutral', 0),
        "negative": counter.get('negative', 0),
        "positive_percent": round((counter.get('positive', 0) / total) * 100, 1),
        "neutral_percent": round((counter.get('neutral', 0) / total) * 100, 1),
        "negative_percent": round((counter.get('negative', 0) / total) * 100, 1)
    }


def calculate_source_distribution(mentions: List[Mention]) -> Dict[str, int]:
    """Calculer la distribution par source"""
    sources = [m.source for m in mentions]
    return dict(Counter(sources))


def identify_top_influencers(mentions: List[Mention], limit: int = 10) -> List[Dict[str, Any]]:
    """Identifier les principaux influenceurs"""
    author_mentions = {}
    
    for mention in mentions:
        author = getattr(mention, 'author', None)
        if not author:
            continue
        
        if author not in author_mentions:
            author_mentions[author] = {
                "name": author,
                "mentions_count": 0,
                "sources": set(),
                "sentiment_scores": [],
                "urls": []
            }
        
        author_mentions[author]["mentions_count"] += 1
        author_mentions[author]["sources"].add(mention.source)
        
        # Récupérer le score avec fallback
        score = get_sentiment_score(mention)
        author_mentions[author]["sentiment_scores"].append(score)
        
        url = getattr(mention, 'url', None)
        if url and len(author_mentions[author]["urls"]) < 3:
            author_mentions[author]["urls"].append(url)
    
    # Calculer les moyennes et trier
    influencers = []
    for author, data in author_mentions.items():
        avg_sentiment = statistics.mean(data["sentiment_scores"]) if data["sentiment_scores"] else 0.0
        
        influencers.append({
            "name": author,
            "mentions_count": data["mentions_count"],
            "sources": list(data["sources"]),
            "avg_sentiment": round(avg_sentiment, 2),
            "sentiment_label": get_sentiment_label(avg_sentiment),
            "sample_urls": data["urls"]
        })
    
    # Trier par nombre de mentions
    influencers.sort(key=lambda x: x["mentions_count"], reverse=True)
    
    return influencers[:limit]


def calculate_daily_trends(mentions: List[Mention], days: int = 7) -> List[Dict[str, Any]]:
    """Calculer les tendances quotidiennes"""
    daily_data = {}
    
    for mention in mentions:
        collected_at = getattr(mention, 'collected_at', None)
        if not collected_at:
            continue
        
        date_key = collected_at.date().isoformat()
        
        if date_key not in daily_data:
            daily_data[date_key] = {
                "date": date_key,
                "count": 0,
                "sentiment_scores": []
            }
        
        daily_data[date_key]["count"] += 1
        
        score = get_sentiment_score(mention)
        daily_data[date_key]["sentiment_scores"].append(score)
    
    # Calculer les moyennes
    trends = []
    for date_key, data in sorted(daily_data.items()):
        avg_sentiment = statistics.mean(data["sentiment_scores"]) if data["sentiment_scores"] else 0.0
        
        trends.append({
            "date": data["date"],
            "mentions_count": data["count"],
            "avg_sentiment": round(avg_sentiment, 2)
        })
    
    return trends


def extract_key_topics(mentions: List[Mention], limit: int = 10) -> List[Dict[str, Any]]:
    """Extraire les sujets clés (mots fréquents dans les titres)"""
    import re
    
    # Mots à ignorer
    stop_words = {
        'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'et', 'ou', 'mais',
        'pour', 'dans', 'sur', 'avec', 'sans', 'the', 'a', 'an', 'and', 'or',
        'but', 'for', 'in', 'on', 'at', 'to', 'of', 'is', 'are', 'was', 'were'
    }
    
    words = []
    for mention in mentions:
        title = getattr(mention, 'title', None)
        if title:
            # Extraire les mots
            title_words = re.findall(r'\b\w+\b', title.lower())
            # Filtrer
            title_words = [w for w in title_words if len(w) > 3 and w not in stop_words]
            words.extend(title_words)
    
    # Compter les occurrences
    word_counts = Counter(words)
    
    topics = []
    for word, count in word_counts.most_common(limit):
        topics.append({
            "topic": word,
            "count": count
        })
    
    return topics


# ============================================================
# ROUTE PRINCIPALE : GÉNÉRATION DE RAPPORT
# ============================================================

@router.post("/generate")
async def generate_report(
    keyword_ids: List[int] = Query(..., description="IDs des mots-clés à analyser"),
    period: str = Query("7d", description="Période d'analyse: 24h, 7d, 30d, 90d, all"),
    include_ai_analysis: bool = Query(True, description="Inclure l'analyse IA"),
    include_influencers: bool = Query(True, description="Inclure les influenceurs"),
    include_trends: bool = Query(True, description="Inclure les tendances"),
    db: Session = Depends(get_db)
):
    """
    Générer un rapport complet d'analyse
    """
    
    try:
        # Vérifier les mots-clés
        keywords = db.query(Keyword).filter(Keyword.id.in_(keyword_ids)).all()
        if not keywords:
            raise HTTPException(status_code=404, detail="Aucun mot-clé trouvé")
        
        # Calculer la période
        start_date = get_date_range(period)
        
        # Récupérer les mentions
        query = db.query(Mention).filter(Mention.keyword_id.in_(keyword_ids))
        
        if start_date:
            query = query.filter(Mention.collected_at >= start_date)
        
        mentions = query.all()
        
        if not mentions:
            raise HTTPException(
                status_code=404,
                detail="Aucune mention trouvée pour cette période"
            )
        
        # ============================================================
        # STATISTIQUES GLOBALES
        # ============================================================
        
        total_mentions = len(mentions)
        sentiment_dist = calculate_sentiment_distribution(mentions)
        source_dist = calculate_source_distribution(mentions)
        
        # Sentiment moyen avec gestion des attributs manquants
        sentiment_scores = [get_sentiment_score(m) for m in mentions]
        avg_sentiment = round(statistics.mean(sentiment_scores), 2) if sentiment_scores else 0.0
        
        # ============================================================
        # INFLUENCEURS
        # ============================================================
        
        influencers = []
        if include_influencers:
            influencers = identify_top_influencers(mentions, limit=10)
        
        # ============================================================
        # TENDANCES TEMPORELLES
        # ============================================================
        
        trends = []
        if include_trends:
            days_map = {"24h": 1, "7d": 7, "30d": 30, "90d": 90}
            days = days_map.get(period, 7)
            trends = calculate_daily_trends(mentions, days=days)
        
        # ============================================================
        # SUJETS CLÉS
        # ============================================================
        
        key_topics = extract_key_topics(mentions, limit=10)
        
        # ============================================================
        # ANALYSE IA (OPTIONNEL)
        # ============================================================
        
        ai_analysis = None
        strategic_recommendations = []
        
        if include_ai_analysis:
            try:
                ai_service = UnifiedAIService()
                
                # Préparer le contexte pour l'IA
                context = f"""
Analyse de surveillance de marque pour les mots-clés : {', '.join([k.keyword for k in keywords])}
Période d'analyse : {period}

STATISTIQUES GLOBALES :
- Total de mentions : {total_mentions}
- Sentiment moyen : {avg_sentiment} ({get_sentiment_label(avg_sentiment)})
- Distribution des sentiments :
  * Positif : {sentiment_dist['positive']} ({sentiment_dist['positive_percent']}%)
  * Neutre : {sentiment_dist['neutral']} ({sentiment_dist['neutral_percent']}%)
  * Négatif : {sentiment_dist['negative']} ({sentiment_dist['negative_percent']}%)

SOURCES PRINCIPALES :
{chr(10).join([f'- {source}: {count} mentions' for source, count in sorted(source_dist.items(), key=lambda x: x[1], reverse=True)])}

TOP 5 INFLUENCEURS :
{chr(10).join([f'- {inf["name"]}: {inf["mentions_count"]} mentions, sentiment {inf["sentiment_label"]}' for inf in influencers[:5]])}

En tant qu'analyste expert en intelligence stratégique, fournis :

1. RÉSUMÉ EXÉCUTIF (2-3 phrases)
2. ANALYSE DÉTAILLÉE (points positifs, préoccupations, évolution)
3. RECOMMANDATIONS STRATÉGIQUES (3-5 actions concrètes)

Format JSON attendu :
{{
    "executive_summary": "...",
    "detailed_analysis": {{
        "positive_points": ["...", "..."],
        "concerns": ["...", "..."],
        "sentiment_evolution": "..."
    }},
    "strategic_recommendations": [
        {{"priority": "haute", "action": "...", "rationale": "..."}}
    ]
}}
"""
                
                ai_response = await ai_service.generate_text(
                    prompt=context,
                    max_tokens=2000,
                    temperature=0.3
                )
                
                # Parser la réponse IA
                import json
                import re
                
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    ai_analysis = json.loads(json_match.group())
                    strategic_recommendations = ai_analysis.get("strategic_recommendations", [])
                else:
                    ai_analysis = {
                        "executive_summary": ai_response[:500],
                        "detailed_analysis": {
                            "positive_points": ["Analyse IA disponible dans le résumé"],
                            "concerns": [],
                            "sentiment_evolution": "Voir résumé exécutif"
                        },
                        "strategic_recommendations": []
                    }
            
            except Exception as e:
                print(f"Erreur analyse IA: {e}")
                ai_analysis = {
                    "executive_summary": "Analyse IA non disponible",
                    "detailed_analysis": {
                        "positive_points": [],
                        "concerns": [],
                        "sentiment_evolution": "N/A"
                    },
                    "strategic_recommendations": []
                }
        
        # ============================================================
        # CONSTRUIRE LE RAPPORT FINAL
        # ============================================================
        
        report = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "period": period,
                "keywords": [{"id": k.id, "keyword": k.keyword} for k in keywords],
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": datetime.utcnow().isoformat()
                }
            },
            
            "executive_summary": ai_analysis.get("executive_summary") if ai_analysis else None,
            
            "statistics": {
                "total_mentions": total_mentions,
                "avg_sentiment_score": avg_sentiment,
                "sentiment_label": get_sentiment_label(avg_sentiment),
                "sentiment_distribution": sentiment_dist,
                "source_distribution": source_dist,
                "unique_authors": len(set(getattr(m, 'author', None) for m in mentions if getattr(m, 'author', None)))
            },
            
            "influencers": influencers if include_influencers else [],
            
            "trends": trends if include_trends else [],
            
            "key_topics": key_topics,
            
            "ai_analysis": ai_analysis.get("detailed_analysis") if ai_analysis else None,
            
            "strategic_recommendations": strategic_recommendations,
            
            "sample_mentions": [
                {
                    "id": m.id,
                    "source": m.source,
                    "title": getattr(m, 'title', None),
                    "url": getattr(m, 'url', None),
                    "author": getattr(m, 'author', None),
                    "sentiment": getattr(m, 'sentiment', None),
                    "sentiment_score": get_sentiment_score(m),
                    "collected_at": getattr(m, 'collected_at', datetime.utcnow()).isoformat()
                }
                for m in mentions[:10]
            ]
        }
        
        return report
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erreur lors de la génération du rapport: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération du rapport: {str(e)}"
        )


# ============================================================
# AUTRES ROUTES
# ============================================================

@router.post("/export/pdf")
async def export_report_pdf(
    keyword_ids: List[int] = Query(...),
    period: str = Query("7d"),
    db: Session = Depends(get_db)
):
    """Générer un rapport PDF (à implémenter)"""
    report_data = await generate_report(
        keyword_ids=keyword_ids,
        period=period,
        include_ai_analysis=True,
        include_influencers=True,
        include_trends=True,
        db=db
    )
    
    return {
        "message": "Export PDF en cours d'implémentation",
        "report_data": report_data
    }


@router.get("/history")
async def get_report_history(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Récupérer l'historique des rapports (à implémenter)"""
    return {
        "message": "Historique des rapports",
        "reports": []
    }