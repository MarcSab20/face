from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.email_service import EmailService
from app.services.influencer_analyzer import InfluencerAnalyzer
from app.services.geo_analyzer import GeoAnalyzer

# Créer les routers
email_router = APIRouter(prefix="/api/reports", tags=["reports"])
influencer_router = APIRouter(prefix="/api/influencers", tags=["influencers"])
geo_router = APIRouter(prefix="/api/geography", tags=["geography"])


# ===== Routes Rapports Email =====

@email_router.post("/send-daily")
async def send_daily_report_now(
    to_email: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Envoyer immédiatement un rapport quotidien
    
    Args:
        to_email: Email du destinataire
    """
    def send_report():
        email_service = EmailService()
        email_service.send_daily_report(db, to_email)
    
    background_tasks.add_task(send_report)
    
    return {
        "message": "Envoi du rapport en cours",
        "recipient": to_email
    }


@email_router.post("/test")
async def test_email(
    to_email: str,
    db: Session = Depends(get_db)
):
    """
    Tester l'envoi d'email avec un rapport de test
    """
    email_service = EmailService()
    
    # Générer les données du rapport
    report_data = email_service.generate_daily_report(db)
    
    # Générer le HTML
    html_content = email_service.generate_daily_report_html(report_data)
    
    # Envoyer
    success = email_service.send_email(
        to_email,
        "Test - Rapport Quotidien Brand Monitor",
        html_content
    )
    
    return {
        "success": success,
        "message": "Email de test envoyé" if success else "Échec envoi email",
        "report_data": report_data
    }


@email_router.get("/preview")
async def preview_daily_report(db: Session = Depends(get_db)):
    """
    Prévisualiser le rapport quotidien (HTML)
    """
    email_service = EmailService()
    
    report_data = email_service.generate_daily_report(db)
    html_content = email_service.generate_daily_report_html(report_data)
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)


# ===== Routes Influenceurs =====

@influencer_router.get("/top")
async def get_top_influencers(
    days: int = 30,
    limit: int = 20,
    source: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Obtenir les top influenceurs
    
    Args:
        days: Période d'analyse en jours (défaut: 30)
        limit: Nombre d'influenceurs à retourner (défaut: 20)
        source: Filtrer par source (optionnel)
    """
    analyzer = InfluencerAnalyzer(db)
    influencers = analyzer.get_top_influencers(days=days, limit=limit, source=source)
    
    return {
        "period_days": days,
        "total_count": len(influencers),
        "influencers": influencers
    }


@influencer_router.get("/by-source")
async def get_influencers_by_source(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Obtenir les top influenceurs groupés par source
    
    Args:
        days: Période d'analyse en jours
    """
    analyzer = InfluencerAnalyzer(db)
    influencers_by_source = analyzer.get_influencers_by_source(days=days)
    
    return {
        "period_days": days,
        "sources": influencers_by_source
    }


@influencer_router.get("/growth/{author}")
async def get_influencer_growth(
    author: str,
    source: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Analyser la croissance d'un influenceur
    
    Args:
        author: Nom de l'auteur
        source: Source (youtube, tiktok, etc.)
        days: Période d'analyse en jours
    """
    analyzer = InfluencerAnalyzer(db)
    growth_data = analyzer.get_influencer_growth(author, source, days)
    
    return growth_data


@influencer_router.get("/stats")
async def get_influencer_stats(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Statistiques globales sur les influenceurs
    """
    analyzer = InfluencerAnalyzer(db)
    
    # Top influenceurs toutes sources
    all_influencers = analyzer.get_top_influencers(days=days, limit=100)
    
    # Par source
    by_source = analyzer.get_influencers_by_source(days=days)
    
    # Calculer stats
    total_influencers = len(all_influencers)
    total_engagement = sum(inf['total_engagement'] for inf in all_influencers)
    avg_engagement = total_engagement / total_influencers if total_influencers > 0 else 0
    
    # Top source
    source_counts = {}
    for source, influencers in by_source.items():
        source_counts[source] = len(influencers)
    
    return {
        "period_days": days,
        "total_influencers": total_influencers,
        "total_engagement": total_engagement,
        "avg_engagement_per_influencer": round(avg_engagement, 2),
        "influencers_by_source": source_counts,
        "top_source": max(source_counts.items(), key=lambda x: x[1])[0] if source_counts else None
    }


# ===== Routes Géographie =====

@geo_router.get("/distribution")
async def get_geographic_distribution(
    days: int = 30,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Obtenir la distribution géographique des mentions
    
    Args:
        days: Période d'analyse en jours
        keyword: Filtrer par mot-clé (optionnel)
    """
    analyzer = GeoAnalyzer(db)
    distribution = analyzer.get_geographic_distribution(days=days, keyword=keyword)
    
    return {
        "period_days": days,
        "keyword": keyword,
        "total_countries": len(distribution),
        "distribution": distribution
    }


@geo_router.get("/heatmap")
async def get_heatmap_data(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Obtenir les données pour la heatmap géographique
    
    Args:
        days: Période d'analyse en jours
        
    Returns:
        Données formatées pour Leaflet.js
    """
    analyzer = GeoAnalyzer(db)
    heatmap_data = analyzer.get_heatmap_data(days=days)
    
    return {
        "period_days": days,
        "points": heatmap_data,
        "total_points": len(heatmap_data)
    }


@geo_router.get("/top-countries")
async def get_top_countries(
    days: int = 30,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Obtenir les pays avec le plus de mentions
    
    Args:
        days: Période d'analyse en jours
        limit: Nombre de pays à retourner
    """
    analyzer = GeoAnalyzer(db)
    top_countries = analyzer.get_top_countries(days=days, limit=limit)
    
    return {
        "period_days": days,
        "countries": top_countries
    }


@geo_router.get("/country/{country_code}")
async def get_country_trends(
    country_code: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Obtenir les tendances pour un pays spécifique
    
    Args:
        country_code: Code ISO du pays (ex: FR, US, GB)
        days: Période d'analyse en jours
    """
    analyzer = GeoAnalyzer(db)
    trends = analyzer.get_country_trends(country_code.upper(), days=days)
    
    return trends