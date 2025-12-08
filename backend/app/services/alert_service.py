"""
Service d'alertes Email intelligent
Notifications pour contenus critiques
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from datetime import datetime
import asyncio

from app.config import settings

logger = logging.getLogger(__name__)


class AlertService:
    """
    Service d'alertes par email
    
    Envoie des notifications pour:
    - Nouveaux contenus avec mots-clés critiques
    - Pics d'activité inhabituelle
    - Sentiment négatif élevé
    """
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_from = settings.SMTP_FROM
        self.smtp_use_tls = settings.SMTP_USE_TLS
        
        self.enabled = bool(
            self.smtp_host and 
            self.smtp_user and 
            self.smtp_password
        )
        
        if self.enabled:
            logger.info("✅ Alert Service initialisé")
        else:
            logger.warning("⚠️ Alert Service désactivé (SMTP non configuré)")
    
    def send_alert(
        self,
        to_emails: List[str],
        subject: str,
        content: str,
        priority: str = "normal",
        html: bool = False
    ) -> bool:
        """
        Envoyer une alerte par email
        
        Args:
            to_emails: Liste d'emails destinataires
            subject: Sujet de l'email
            content: Contenu de l'email
            priority: Priorité (low, normal, high, critical)
            html: Si True, content est du HTML
            
        Returns:
            True si envoyé avec succès
        """
        if not self.enabled:
            logger.warning("Alertes email désactivées")
            return False
        
        try:
            # Créer le message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_from
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = self._format_subject(subject, priority)
            
            # Ajouter le contenu
            if html:
                msg.attach(MIMEText(content, 'html'))
            else:
                msg.attach(MIMEText(content, 'plain'))
            
            # Envoyer l'email
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                if self.smtp_use_tls:
                    server.starttls()
                
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"✅ Alerte envoyée à {len(to_emails)} destinataire(s)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur envoi alerte: {e}")
            return False
    
    def send_channel_alert(
        self,
        channel_name: str,
        channel_type: str,
        items: List[Dict],
        keywords_matched: List[str],
        to_emails: List[str],
        priority: str = "high"
    ) -> bool:
        """
        Envoyer une alerte pour un channel surveillé
        
        Args:
            channel_name: Nom du channel
            channel_type: Type de channel
            items: Liste d'items déclenchant l'alerte
            keywords_matched: Mots-clés trouvés
            to_emails: Destinataires
            priority: Priorité de l'alerte
        """
        subject = f"🚨 Alerte {channel_name} - {len(items)} nouveau(x) contenu(s)"
        
        # Construire le contenu HTML
        html_content = self._build_channel_alert_html(
            channel_name,
            channel_type,
            items,
            keywords_matched
        )
        
        return self.send_alert(
            to_emails=to_emails,
            subject=subject,
            content=html_content,
            priority=priority,
            html=True
        )
    
    def _format_subject(self, subject: str, priority: str) -> str:
        """Formater le sujet avec indicateur de priorité"""
        priority_prefix = {
            'low': '',
            'normal': '',
            'high': '⚠️ ',
            'critical': '🚨 [URGENT] '
        }
        
        prefix = priority_prefix.get(priority, '')
        return f"{prefix}{subject}"
    
    def _build_channel_alert_html(
        self,
        channel_name: str,
        channel_type: str,
        items: List[Dict],
        keywords_matched: List[str]
    ) -> str:
        """Construire le HTML de l'alerte"""
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .header {{
                    background-color: #d32f2f;
                    color: white;
                    padding: 20px;
                    text-align: center;
                }}
                .content {{
                    padding: 20px;
                }}
                .info-box {{
                    background-color: #f5f5f5;
                    padding: 15px;
                    margin: 10px 0;
                    border-left: 4px solid #2196F3;
                }}
                .item {{
                    border: 1px solid #ddd;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 5px;
                }}
                .item-title {{
                    font-weight: bold;
                    color: #1976D2;
                    margin-bottom: 5px;
                }}
                .keywords {{
                    background-color: #fff3cd;
                    padding: 10px;
                    margin: 10px 0;
                    border-radius: 5px;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px;
                    color: #666;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚨 Nouvelle Alerte - {channel_name}</h1>
            </div>
            
            <div class="content">
                <div class="info-box">
                    <p><strong>Source:</strong> {channel_type.upper()}</p>
                    <p><strong>Channel:</strong> {channel_name}</p>
                    <p><strong>Nombre de contenus:</strong> {len(items)}</p>
                    <p><strong>Date:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                </div>
                
                <div class="keywords">
                    <strong>🔍 Mots-clés détectés:</strong> {', '.join(keywords_matched)}
                </div>
                
                <h2>📋 Contenus détectés:</h2>
        """
        
        # Ajouter chaque item
        for i, item in enumerate(items[:10], 1):  # Max 10 items
            title = item.get('title', 'Sans titre')
            url = item.get('url', '#')
            content_preview = item.get('content', '')[:200]
            date = item.get('published_at', item.get('date', ''))
            
            html += f"""
                <div class="item">
                    <div class="item-title">{i}. {title}</div>
                    <p>{content_preview}...</p>
                    <p><small>📅 {date}</small></p>
                    <p><a href="{url}" target="_blank">Voir le contenu complet →</a></p>
                </div>
            """
        
        if len(items) > 10:
            html += f"<p><em>... et {len(items) - 10} autre(s) contenu(s)</em></p>"
        
        html += """
            </div>
            
            <div class="footer">
                <p>Cet email a été généré automatiquement par BrandMonitor</p>
                <p>Pour modifier vos préférences d'alertes, connectez-vous au tableau de bord</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    async def send_alert_async(self, *args, **kwargs) -> bool:
        """Version asynchrone de send_alert"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.send_alert, *args, **kwargs)


# Instance globale
alert_service = AlertService()


# Test
if __name__ == '__main__':
    # Test d'envoi
    alert_service.send_channel_alert(
        channel_name="France 24 Afrique",
        channel_type="youtube_rss",
        items=[
            {
                'title': "Actualité importante",
                'url': "https://example.com",
                'content': "Contenu de test...",
                'published_at': datetime.now()
            }
        ],
        keywords_matched=["politique", "économie"],
        to_emails=[settings.ALERT_EMAIL],
        priority="high"
    )