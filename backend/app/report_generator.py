"""
Service de génération de rapports PDF professionnels
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import io
import base64

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Générateur de rapports PDF pour les mots-clés"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_keyword_report(
        self,
        keyword_id: int,
        days: int = 30,
        include_sections: List[str] = None
    ) -> Dict:
        """
        Générer un rapport complet pour un mot-clé
        
        Args:
            keyword_id: ID du mot-clé
            days: Période d'analyse en jours
            include_sections: Sections à inclure (stats, influencers, mentions, geography)
            
        Returns:
            Dict avec les données du rapport
        """
        from app.models import Keyword, Mention
        from app.influencer_analyzer import InfluencerAnalyzer
        from app.geo_analyzer import GeoAnalyzer
        
        # Sections par défaut
        if include_sections is None:
            include_sections = ['stats', 'influencers', 'mentions', 'geography']
        
        # Récupérer le mot-clé
        keyword = self.db.query(Keyword).filter(Keyword.id == keyword_id).first()
        if not keyword:
            raise ValueError(f"Keyword with id {keyword_id} not found")
        
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Récupérer toutes les mentions
        mentions = self.db.query(Mention).filter(
            Mention.keyword_id == keyword_id,
            Mention.published_at >= since_date
        ).all()
        
        report_data = {
            'keyword': keyword.keyword,
            'keyword_id': keyword_id,
            'period_days': days,
            'generated_at': datetime.utcnow(),
            'total_mentions': len(mentions),
        }
        
        # Section Statistiques
        if 'stats' in include_sections:
            report_data['stats'] = self._generate_stats_section(keyword_id, days, mentions)
        
        # Section Influenceurs
        if 'influencers' in include_sections:
            analyzer = InfluencerAnalyzer(self.db)
            influencers = analyzer.get_top_influencers(days=days, limit=10)
            # Filtrer par keyword
            influencers = [inf for inf in influencers if any(
                m.keyword_id == keyword_id 
                for m in self.db.query(Mention).filter(
                    Mention.author == inf['author'],
                    Mention.source == inf['source']
                ).all()
            )]
            report_data['influencers'] = influencers[:10]
        
        # Section Mentions
        if 'mentions' in include_sections:
            report_data['mentions'] = self._generate_mentions_section(mentions)
        
        # Section Géographie
        if 'geography' in include_sections:
            geo_analyzer = GeoAnalyzer(self.db)
            distribution = geo_analyzer.get_geographic_distribution(
                days=days,
                keyword=keyword.keyword
            )
            report_data['geography'] = distribution[:10]
        
        return report_data
    
    def _generate_stats_section(self, keyword_id: int, days: int, mentions: List) -> Dict:
        """Générer les statistiques"""
        from app.models import Mention
        
        # Distribution par source
        sources = {}
        for mention in mentions:
            sources[mention.source] = sources.get(mention.source, 0) + 1
        
        # Distribution sentiment
        sentiment_dist = {
            'positive': 0,
            'neutral': 0,
            'negative': 0
        }
        for mention in mentions:
            if mention.sentiment:
                sentiment_dist[mention.sentiment] = sentiment_dist.get(mention.sentiment, 0) + 1
        
        # Engagement total
        total_engagement = sum(m.engagement_score for m in mentions)
        avg_engagement = total_engagement / len(mentions) if mentions else 0
        
        # Timeline
        timeline = {}
        for mention in mentions:
            if mention.published_at:
                date_key = mention.published_at.date().isoformat()
                timeline[date_key] = timeline.get(date_key, 0) + 1
        
        timeline_data = [
            {'date': date, 'count': count}
            for date, count in sorted(timeline.items())
        ]
        
        # Top mentions engageantes
        top_engaged = sorted(mentions, key=lambda m: m.engagement_score, reverse=True)[:5]
        
        return {
            'sources': sources,
            'sentiment': sentiment_dist,
            'total_engagement': total_engagement,
            'avg_engagement': round(avg_engagement, 2),
            'timeline': timeline_data,
            'top_engaged': [
                {
                    'title': m.title,
                    'source': m.source,
                    'engagement': m.engagement_score,
                    'sentiment': m.sentiment,
                    'author': m.author,
                    'url': m.source_url
                }
                for m in top_engaged
            ]
        }
    
    def _generate_mentions_section(self, mentions: List) -> Dict:
        """Générer la section mentions"""
        # Top auteurs
        authors = {}
        for mention in mentions:
            authors[mention.author] = authors.get(mention.author, 0) + 1
        
        top_authors = sorted(authors.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Distribution horaire
        hourly = {}
        for mention in mentions:
            if mention.published_at:
                hour = mention.published_at.hour
                hourly[hour] = hourly.get(hour, 0) + 1
        
        return {
            'total': len(mentions),
            'top_authors': [{'author': a, 'count': c} for a, c in top_authors],
            'hourly_distribution': [
                {'hour': h, 'count': hourly.get(h, 0)}
                for h in range(24)
            ]
        }
    
    def generate_html_report(self, report_data: Dict) -> str:
        """
        Générer le HTML du rapport
        
        Args:
            report_data: Données du rapport
            
        Returns:
            HTML du rapport
        """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{
                    size: A4;
                    margin: 2cm;
                }}
                
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    color: #333;
                    line-height: 1.6;
                    max-width: 800px;
                    margin: 0 auto;
                }}
                
                .header {{
                    text-align: center;
                    padding: 30px 0;
                    border-bottom: 3px solid #667eea;
                    margin-bottom: 30px;
                }}
                
                .header h1 {{
                    color: #667eea;
                    font-size: 32px;
                    margin: 0 0 10px 0;
                }}
                
                .header .subtitle {{
                    color: #666;
                    font-size: 14px;
                }}
                
                .section {{
                    margin: 40px 0;
                    page-break-inside: avoid;
                }}
                
                .section-title {{
                    color: #667eea;
                    font-size: 24px;
                    border-bottom: 2px solid #e5e7eb;
                    padding-bottom: 10px;
                    margin-bottom: 20px;
                }}
                
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 20px;
                    margin: 20px 0;
                }}
                
                .stat-card {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                }}
                
                .stat-value {{
                    font-size: 36px;
                    font-weight: bold;
                    margin: 10px 0;
                }}
                
                .stat-label {{
                    font-size: 14px;
                    opacity: 0.9;
                }}
                
                .chart {{
                    margin: 20px 0;
                }}
                
                .bar {{
                    height: 30px;
                    background: #667eea;
                    margin: 10px 0;
                    border-radius: 5px;
                    position: relative;
                }}
                
                .bar-label {{
                    position: absolute;
                    left: 10px;
                    top: 50%;
                    transform: translateY(-50%);
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                }}
                
                .bar-value {{
                    position: absolute;
                    right: 10px;
                    top: 50%;
                    transform: translateY(-50%);
                    color: white;
                    font-size: 12px;
                }}
                
                .mention-item {{
                    background: #f9fafb;
                    padding: 15px;
                    border-left: 4px solid #667eea;
                    border-radius: 5px;
                    margin: 10px 0;
                }}
                
                .mention-title {{
                    font-weight: bold;
                    color: #1f2937;
                    margin-bottom: 8px;
                }}
                
                .mention-meta {{
                    font-size: 12px;
                    color: #6b7280;
                }}
                
                .sentiment-bar {{
                    display: flex;
                    height: 40px;
                    border-radius: 8px;
                    overflow: hidden;
                    margin: 20px 0;
                }}
                
                .sentiment-segment {{
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                }}
                
                .sentiment-positive {{ background: #10b981; }}
                .sentiment-neutral {{ background: #6b7280; }}
                .sentiment-negative {{ background: #ef4444; }}
                
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                
                th, td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #e5e7eb;
                }}
                
                th {{
                    background: #f9fafb;
                    font-weight: bold;
                    color: #667eea;
                }}
                
                .footer {{
                    margin-top: 50px;
                    padding-top: 20px;
                    border-top: 1px solid #e5e7eb;
                    text-align: center;
                    color: #6b7280;
                    font-size: 12px;
                }}
                
                .page-break {{
                    page-break-after: always;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Rapport d'Analyse</h1>
                <div class="subtitle">
                    Mot-clé: <strong>{report_data['keyword']}</strong><br>
                    Période: {report_data['period_days']} jours<br>
                    Généré le: {report_data['generated_at'].strftime('%d/%m/%Y à %H:%M')}
                </div>
            </div>
        """
        
        # Section Statistiques
        if 'stats' in report_data:
            stats = report_data['stats']
            
            # Calcul des pourcentages sentiment
            total_sentiment = sum(stats['sentiment'].values())
            sentiment_percentages = {}
            if total_sentiment > 0:
                for key, val in stats['sentiment'].items():
                    sentiment_percentages[key] = (val / total_sentiment) * 100
            else:
                sentiment_percentages = {'positive': 0, 'neutral': 0, 'negative': 0}
            
            html += f"""
            <div class="section">
                <h2 class="section-title">📈 Vue d'ensemble</h2>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">Total Mentions</div>
                        <div class="stat-value">{report_data['total_mentions']}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Engagement Total</div>
                        <div class="stat-value">{self._format_number(stats['total_engagement'])}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Engagement Moyen</div>
                        <div class="stat-value">{stats['avg_engagement']}</div>
                    </div>
                </div>
                
                <h3 style="margin-top: 30px;">Analyse de Sentiment</h3>
                <div class="sentiment-bar">
                    <div class="sentiment-segment sentiment-positive" style="width: {sentiment_percentages['positive']}%">
                        😊 {sentiment_percentages['positive']:.0f}%
                    </div>
                    <div class="sentiment-segment sentiment-neutral" style="width: {sentiment_percentages['neutral']}%">
                        😐 {sentiment_percentages['neutral']:.0f}%
                    </div>
                    <div class="sentiment-segment sentiment-negative" style="width: {sentiment_percentages['negative']}%">
                        😞 {sentiment_percentages['negative']:.0f}%
                    </div>
                </div>
                
                <h3 style="margin-top: 30px;">Mentions par Source</h3>
                <div class="chart">
            """
            
            # Sources chart
            max_source = max(stats['sources'].values()) if stats['sources'] else 1
            for source, count in sorted(stats['sources'].items(), key=lambda x: x[1], reverse=True):
                width_percent = (count / max_source) * 100
                html += f"""
                    <div class="bar" style="width: {width_percent}%">
                        <span class="bar-label">{source}</span>
                        <span class="bar-value">{count}</span>
                    </div>
                """
            
            html += """
                </div>
                
                <h3 style="margin-top: 30px;">🔥 Top Mentions Engageantes</h3>
            """
            
            for mention in stats['top_engaged']:
                sentiment_emoji = '😊' if mention['sentiment'] == 'positive' else '😐' if mention['sentiment'] == 'neutral' else '😞'
                html += f"""
                    <div class="mention-item">
                        <div class="mention-title">{mention['title'][:100]}</div>
                        <div class="mention-meta">
                            Source: {mention['source']} | 
                            Auteur: {mention['author']} | 
                            {sentiment_emoji} {mention['sentiment'] or 'N/A'} | 
                            ⭐ {self._format_number(mention['engagement'])}
                        </div>
                    </div>
                """
            
            html += """
            </div>
            <div class="page-break"></div>
            """
        
        # Section Influenceurs
        if 'influencers' in report_data and report_data['influencers']:
            html += """
            <div class="section">
                <h2 class="section-title">👑 Top Influenceurs</h2>
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Auteur</th>
                            <th>Source</th>
                            <th>Mentions</th>
                            <th>Engagement</th>
                            <th>Sentiment</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for i, influencer in enumerate(report_data['influencers'][:10], 1):
                sentiment_score = influencer.get('sentiment_score', 0)
                sentiment_emoji = '😊' if sentiment_score >= 70 else '😐' if sentiment_score >= 40 else '😞'
                
                html += f"""
                    <tr>
                        <td><strong>{i}</strong></td>
                        <td>{influencer['author']}</td>
                        <td>{influencer['source']}</td>
                        <td>{influencer['mention_count']}</td>
                        <td>{self._format_number(influencer['total_engagement'])}</td>
                        <td>{sentiment_emoji} {sentiment_score:.0f}%</td>
                    </tr>
                """
            
            html += """
                    </tbody>
                </table>
            </div>
            """
        
        # Section Géographie
        if 'geography' in report_data and report_data['geography']:
            html += """
            <div class="section">
                <h2 class="section-title">🌍 Distribution Géographique</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Rang</th>
                            <th>Pays</th>
                            <th>Mentions</th>
                            <th>Pourcentage</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for i, country in enumerate(report_data['geography'][:10], 1):
                html += f"""
                    <tr>
                        <td><strong>{i}</strong></td>
                        <td>{country['country_name']}</td>
                        <td>{country['mention_count']}</td>
                        <td>{country['percentage']:.1f}%</td>
                    </tr>
                """
            
            html += """
                    </tbody>
                </table>
            </div>
            """
        
        # Footer
        html += f"""
            <div class="footer">
                <p>Rapport généré par <strong>Superviseur MINDEF</strong></p>
                <p>Ce rapport est confidentiel et destiné à un usage interne uniquement.</p>
                <p>{report_data['generated_at'].strftime('%d/%m/%Y à %H:%M')}</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def generate_pdf(self, report_data: Dict) -> bytes:
        """
        Générer le PDF du rapport
        
        Args:
            report_data: Données du rapport
            
        Returns:
            PDF en bytes
        """
        try:
            from weasyprint import HTML, CSS
            
            html_content = self.generate_html_report(report_data)
            
            # Générer le PDF
            pdf_bytes = HTML(string=html_content).write_pdf()
            
            return pdf_bytes
            
        except ImportError:
            logger.warning("WeasyPrint not available, generating HTML only")
            # Fallback: retourner HTML
            html_content = self.generate_html_report(report_data)
            return html_content.encode('utf-8')
    
    def _format_number(self, num: float) -> str:
        """Formater un nombre pour affichage"""
        if num >= 1000000:
            return f"{num/1000000:.1f}M"
        elif num >= 1000:
            return f"{num/1000:.1f}K"
        return str(round(num))