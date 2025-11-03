"""
Routes API pour la génération de rapports - Version 2
Support de multi-mots-clés et objet de rapport
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import logging
import sys

from app.database import get_db
from app.models import Keyword
from app.report_generator import ReportGenerator

logger = logging.getLogger(__name__)

# Router
reports_router = APIRouter(prefix="/api/reports", tags=["reports"])


# ===== Modèles Pydantic =====

class ReportRequest(BaseModel):
    keyword_ids: List[int]  # Maintenant accepte plusieurs IDs
    days: int = 30
    report_object: str = ""  # Objet du rapport
    include_sections: Optional[List[str]] = None
    format: str = "pdf"  # pdf ou html


class ReportPreview(BaseModel):
    keywords: List[str]
    period_days: int
    total_mentions: int
    has_analysis: bool
    has_influencers: bool


# ===== Routes =====

@reports_router.post("/generate")
async def generate_report(
    request: ReportRequest,
    db: Session = Depends(get_db)
):
    """
    Générer un rapport pour un ou plusieurs mots-clés
    
    Args:
        request: Configuration du rapport
        
    Returns:
        PDF ou HTML du rapport
    """
    try:
        # Vérifier que les mots-clés existent
        keywords = db.query(Keyword).filter(Keyword.id.in_(request.keyword_ids)).all()
        if not keywords:
            raise HTTPException(status_code=404, detail="Aucun mot-clé trouvé")
        
        # Générer le rapport avec le nouveau générateur
        generator = ReportGenerator(db)
        report_data = generator.generate_keyword_report(
            keyword_ids=request.keyword_ids,
            days=request.days,
            report_object=request.report_object,
            include_sections=request.include_sections or ['analysis', 'influencers']
        )
        
        if request.format == "pdf":
            # Générer PDF
            pdf_bytes = generator.generate_pdf(report_data)
            
            keywords_str = '_'.join([kw.keyword for kw in keywords])
            filename = f"rapport_{keywords_str}_{report_data['generated_at'].strftime('%Y%m%d_%H%M%S')}.pdf"
            
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )
        else:
            # Retourner HTML
            html_content = generator.generate_html_report(report_data)
            
            return Response(
                content=html_content,
                media_type="text/html"
            )
            
    except Exception as e:
        logger.error(f"Erreur génération rapport: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération du rapport: {str(e)}"
        )


@reports_router.post("/preview")
async def preview_report(
    keyword_ids: List[int],
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Prévisualiser les informations d'un rapport sans le générer
    
    Args:
        keyword_ids: IDs des mots-clés
        days: Période d'analyse
        
    Returns:
        Informations de prévisualisation
    """
    from app.models import Mention
    from datetime import datetime, timedelta
    
    # Vérifier que les mots-clés existent
    keywords = db.query(Keyword).filter(Keyword.id.in_(keyword_ids)).all()
    if not keywords:
        raise HTTPException(status_code=404, detail="Aucun mot-clé trouvé")
    
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Compter les mentions
    mentions_count = db.query(Mention).filter(
        Mention.keyword_id.in_(keyword_ids),
        Mention.published_at >= since_date
    ).count()
    
    return {
        "keywords": [kw.keyword for kw in keywords],
        "keyword_ids": keyword_ids,
        "period_days": days,
        "total_mentions": mentions_count,
        "has_analysis": mentions_count > 0,
        "has_influencers": mentions_count > 0,
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