"""
Service d'envoi d'emails pour les rapports quotidiens
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.config import settings
from app.models import Keyword, Mention

logger = logging.getLogger(__name__)


class EmailService:
    """Service pour l'envoi d'emails de rapports"""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_USER
        
    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """
        Envoyer un email
        
        Args:
            to_email: Adresse du destinataire
            subject: Sujet de l'email
            html_content: Contenu HTML
            
        Returns:
            True si succès, False sinon
        """
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email envoyé à {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur envoi email à {to_email}: {str(e)}")
            return False
    
    def generate_daily_report(self, db: Session) -> Dict:
        """
        Générer les données du rapport quotidien
        
        Args:
            db: Session de base de données
            
        Returns:
            Dictionnaire avec les statistiques du jour
        """
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        
        # Mentions d'hier
        yesterday_mentions = db.query(Mention).filter(
            func.date(Mention.collected_at) == yesterday
        ).all()
        
        # Total mentions
        total_mentions = len(yesterday_mentions)
        
        # Mentions par source
        mentions_by_source = {}
        for mention in yesterday_mentions:
            mentions_by_source[mention.source] = mentions_by_source.get(mention.source, 0) + 1
        
        # Distribution sentiment
        sentiment_dist = {
            'positive': 0,
            'neutral': 0,
            'negative': 0
        }
        for mention in yesterday_mentions:
            if mention.sentiment:
                sentiment_dist[mention.sentiment] = sentiment_dist.get(mention.sentiment, 0) + 1
        
        # Top mots-clés
        top_keywords_query = db.query(
            Keyword.keyword,
            func.count(Mention.id).label('count')
        ).join(
            Mention, Mention.keyword_id == Keyword.id
        ).filter(
            func.date(Mention.collected_at) == yesterday
        ).group_by(
            Keyword.keyword
        ).order_by(
            func.count(Mention.id).desc()
        ).limit(5).all()
        
        top_keywords = [
            {'keyword': kw, 'count': count}
            for kw, count in top_keywords_query
        ]
        
        # Top mentions engageantes
        top_engaged = db.query(Mention).filter(
            func.date(Mention.collected_at) == yesterday
        ).order_by(
            Mention.engagement_score.desc()
        ).limit(5).all()
        
        # Calcul pourcentage sentiment
        total_with_sentiment = sum(sentiment_dist.values())
        sentiment_percentages = {}
        if total_with_sentiment > 0:
            for sentiment, count in sentiment_dist.items():
                sentiment_percentages[sentiment] = (count / total_with_sentiment) * 100
        else:
            sentiment_percentages = {'positive': 0, 'neutral': 0, 'negative': 0}
        
        # Comparaison avec avant-hier
        day_before_yesterday = yesterday - timedelta(days=1)
        previous_mentions_count = db.query(Mention).filter(
            func.date(Mention.collected_at) == day_before_yesterday
        ).count()
        
        change_percentage = 0
        if previous_mentions_count > 0:
            change_percentage = ((total_mentions - previous_mentions_count) / previous_mentions_count) * 100
        
        return {
            'date': yesterday.strftime('%d/%m/%Y'),
            'total_mentions': total_mentions,
            'change_percentage': round(change_percentage, 1),
            'mentions_by_source': mentions_by_source,
            'sentiment_distribution': sentiment_dist,
            'sentiment_percentages': sentiment_percentages,
            'top_keywords': top_keywords,
            'top_engaged': [
                {
                    'title': m.title,
                    'source': m.source,
                    'engagement': m.engagement_score,
                    'sentiment': m.sentiment,
                    'url': m.source_url
                }
                for m in top_engaged
            ]
        }
    
    def generate_daily_report_html(self, report_data: Dict) -> str:
        """
        Générer le HTML du rapport quotidien
        
        Args:
            report_data: Données du rapport
            
        Returns:
            HTML du rapport
        """
        # Icônes sentiment
        sentiment_icons = {
            'positive': '😊',
            'neutral': '😐',
            'negative': '😞'
        }
        
        # Couleurs sentiment
        sentiment_colors = {
            'positive': '#10b981',
            'neutral': '#6b7280',
            'negative': '#ef4444'
        }
        
        # Flèche tendance
        arrow = '📈' if report_data['change_percentage'] >= 0 else '📉'
        arrow_color = '#10b981' if report_data['change_percentage'] >= 0 else '#ef4444'
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    background-color: white;
                    border-radius: 12px;
                    padding: 30px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    padding-bottom: 20px;
                    border-bottom: 3px solid #667eea;
                }}
                .header h1 {{
                    color: #667eea;
                    margin: 0 0 10px 0;
                    font-size: 28px;
                }}
                .date {{
                    color: #6b7280;
                    font-size: 14px;
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 15px;
                    margin: 25px 0;
                }}
                .stat-card {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                }}
                .stat-value {{
                    font-size: 32px;
                    font-weight: bold;
                    margin: 10px 0;
                }}
                .stat-label {{
                    font-size: 14px;
                    opacity: 0.9;
                }}
                .section {{
                    margin: 25px 0;
                }}
                .section-title {{
                    font-size: 18px;
                    font-weight: 600;
                    color: #1f2937;
                    margin-bottom: 15px;
                    padding-bottom: 8px;
                    border-bottom: 2px solid #e5e7eb;
                }}
                .sentiment-bar {{
                    display: flex;
                    height: 30px;
                    border-radius: 8px;
                    overflow: hidden;
                    margin: 10px 0;
                }}
                .sentiment-segment {{
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 12px;
                    font-weight: 600;
                }}
                .keyword-item {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 12px;
                    background-color: #f9fafb;
                    border-radius: 6px;
                    margin: 8px 0;
                }}
                .keyword-name {{
                    font-weight: 600;
                    color: #1f2937;
                }}
                .keyword-count {{
                    background-color: #667eea;
                    color: white;
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-size: 14px;
                }}
                .mention-item {{
                    padding: 15px;
                    background-color: #f9fafb;
                    border-left: 4px solid #667eea;
                    border-radius: 6px;
                    margin: 10px 0;
                }}
                .mention-title {{
                    font-weight: 600;
                    color: #1f2937;
                    margin-bottom: 8px;
                }}
                .mention-meta {{
                    display: flex;
                    gap: 12px;
                    font-size: 13px;
                    color: #6b7280;
                }}
                .badge {{
                    display: inline-block;
                    padding: 4px 10px;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: 600;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #e5e7eb;
                    text-align: center;
                    color: #6b7280;
                    font-size: 13px;
                }}
                .cta-button {{
                    display: inline-block;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 12px 30px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: 600;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Rapport Quotidien Brand Monitor</h1>
                    <p class="date">{report_data['date']}</p>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">Total Mentions</div>
                        <div class="stat-value">{report_data['total_mentions']}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Tendance</div>
                        <div class="stat-value" style="color: {arrow_color}">
                            {arrow} {abs(report_data['change_percentage'])}%
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <h2 class="section-title">📈 Analyse de Sentiment</h2>
                    <div class="sentiment-bar">
                        <div class="sentiment-segment" style="width: {report_data['sentiment_percentages']['positive']}%; background-color: {sentiment_colors['positive']}">
                            {sentiment_icons['positive']} {report_data['sentiment_percentages']['positive']:.0f}%
                        </div>
                        <div class="sentiment-segment" style="width: {report_data['sentiment_percentages']['neutral']}%; background-color: {sentiment_colors['neutral']}">
                            {sentiment_icons['neutral']} {report_data['sentiment_percentages']['neutral']:.0f}%
                        </div>
                        <div class="sentiment-segment" style="width: {report_data['sentiment_percentages']['negative']}%; background-color: {sentiment_colors['negative']}">
                            {sentiment_icons['negative']} {report_data['sentiment_percentages']['negative']:.0f}%
                        </div>
                    </div>
                    <p style="text-align: center; color: #6b7280; font-size: 14px; margin-top: 10px;">
                        {report_data['sentiment_distribution']['positive']} positives • 
                        {report_data['sentiment_distribution']['neutral']} neutres • 
                        {report_data['sentiment_distribution']['negative']} négatives
                    </p>
                </div>
                
                <div class="section">
                    <h2 class="section-title">🔥 Top Mots-Clés</h2>
        """
        
        for kw in report_data['top_keywords']:
            html += f"""
                    <div class="keyword-item">
                        <span class="keyword-name">{kw['keyword']}</span>
                        <span class="keyword-count">{kw['count']} mentions</span>
                    </div>
            """
        
        html += """
                </div>
                
                <div class="section">
                    <h2 class="section-title">⭐ Mentions les Plus Engageantes</h2>
        """
        
        for mention in report_data['top_engaged'][:3]:
            sentiment_emoji = sentiment_icons.get(mention['sentiment'], '😐')
            html += f"""
                    <div class="mention-item">
                        <div class="mention-title">{mention['title'][:100]}...</div>
                        <div class="mention-meta">
                            <span class="badge" style="background-color: #667eea;">{mention['source']}</span>
                            <span>{sentiment_emoji} {mention['sentiment'] or 'N/A'}</span>
                            <span>⭐ {mention['engagement']:.0f}</span>
                        </div>
                    </div>
            """
        
        html += f"""
                </div>
                
                <div style="text-align: center;">
                    <a href="http://localhost:3000" class="cta-button">
                        Voir le Dashboard Complet →
                    </a>
                </div>
                
                <div class="footer">
                    <p>Brand Monitor Pro • Surveillance de marque intelligente</p>
                    <p style="font-size: 11px; margin-top: 10px;">
                        Vous recevez ce rapport car vous êtes abonné aux notifications.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def send_daily_report(self, db: Session, to_email: str) -> bool:
        """
        Envoyer le rapport quotidien
        
        Args:
            db: Session de base de données
            to_email: Email du destinataire
            
        Returns:
            True si succès, False sinon
        """
        try:
            report_data = self.generate_daily_report(db)
            
            if report_data['total_mentions'] == 0:
                logger.info("Aucune mention hier, pas d'email envoyé")
                return False
            
            html_content = self.generate_daily_report_html(report_data)
            
            subject = f"📊 Rapport Quotidien Brand Monitor - {report_data['date']}"
            
            return self.send_email(to_email, subject, html_content)
            
        except Exception as e:
            logger.error(f"Erreur génération rapport quotidien: {str(e)}")
            return False