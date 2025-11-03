"""
Générateur de rapports enrichi spécialisé pour le contexte camerounais
Structuré en 5 sections : Positif, Négatif, Neutre, Synthèse, Influenceurs Engagés
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc
from collections import Counter
import statistics

logger = logging.getLogger(__name__)


class CameroonReportGenerator:
    """Générateur de rapports enrichi pour le contexte camerounais"""
    
    # Liste des influenceurs camerounais à surveiller
    CAMEROON_INFLUENCERS = [
        "N'zui Manto", "Brigade anti-sardinards", "Boris Bertolt", "Angie Forbin",
        "Abdoulaye Thiam", "Ahmed Abba", "Cameroon News Agency", "Brice Nitcheu",
        "MbangaMan237", "Sandy Boston Officiel 3", "Mbong Mendzui officiel",
        "Patrice Nouma", "Richard Bona", "Paul Chouta", "Mimi Mefo",
        "Général Valsero", "Jaques Bertrand mang", "Michelle ngatchou",
        "AfroBrains Cameroon-ABC", "Infolage", "Mc-Kenzo-officiel",
        "Lepierro Lemonstre", "James Bardock Bardock", "Fernandtech TV",
        "Maurice Kamto", "Kah Walla", "Valsero", "Brenda Biya",
        "Calibri Calibro", "Patrice Nganang", "Wilfried Ekanga",
        "Abdouraman Hamadou", "Ernest Obama", "Christian Penda Ekoka",
        "Fabrice Lena", "Michel Biem Tong", "Armand Okol",
        "Claude Wilfried Ekanga", "Paul Éric Kingué", "Célestin Djamen",
        "C'est le hoohaaa"
    ]
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_cameroon_report(
        self,
        keyword_ids: List[int],
        days: int = 30,
        report_object: str = ""
    ) -> Dict:
        """
        Générer un rapport enrichi avec structure en 5 sections
        
        Structure:
        1. Évaluation de gravité
        2. Jugements positifs des internautes
        3. Jugements négatifs des internautes
        4. Jugements neutres des internautes
        5. Synthèse des jugements
        6. Influenceurs engagés (France 24 + Liste spécifique)
        """
        from app.models import Keyword, Mention
        
        # Récupérer les mots-clés
        keywords = self.db.query(Keyword).filter(
            Keyword.id.in_(keyword_ids)
        ).all()
        
        if not keywords:
            raise ValueError("Aucun mot-clé trouvé")
        
        keywords_names = [kw.keyword for kw in keywords]
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Récupérer toutes les mentions
        mentions = self.db.query(Mention).filter(
            Mention.keyword_id.in_(keyword_ids),
            Mention.published_at >= since_date
        ).order_by(desc(Mention.published_at)).all()
        
        # Filtrer les mentions France 24 et influenceurs spécifiques pour la section influenceurs
        france24_mentions = [m for m in mentions if 'france' in m.source.lower() and '24' in m.source.lower()]
        influencer_mentions = [
            m for m in mentions 
            if any(inf.lower() in m.author.lower() for inf in self.CAMEROON_INFLUENCERS)
        ]
        targeted_mentions = france24_mentions + influencer_mentions
        
        report_data = {
            'keywords': keywords_names,
            'keyword_ids': keyword_ids,
            'period_days': days,
            'report_object': report_object or ', '.join(keywords_names),
            'generated_at': datetime.utcnow(),
            'total_mentions': len(mentions),
        }
        
        # 1. Évaluation de gravité (maintenue)
        report_data['risk_assessment'] = self._generate_risk_assessment(mentions, days)
        
        # 2-4. Sections par sentiment
        positive_mentions = [m for m in mentions if m.sentiment == 'positive']
        negative_mentions = [m for m in mentions if m.sentiment == 'negative']
        neutral_mentions = [m for m in mentions if m.sentiment == 'neutral']
        
        report_data['positive_analysis'] = self._analyze_positive_sentiment(positive_mentions)
        report_data['negative_analysis'] = self._analyze_negative_sentiment(negative_mentions)
        report_data['neutral_analysis'] = self._analyze_neutral_sentiment(neutral_mentions)
        
        # 5. Synthèse des jugements
        report_data['judgment_synthesis'] = self._generate_judgment_synthesis(
            positive_mentions, negative_mentions, neutral_mentions
        )
        
        # 6. Influenceurs engagés (France 24 + liste spécifique)
        report_data['engaged_influencers'] = self._analyze_engaged_influencers(targeted_mentions)
        
        return report_data
    
    def _generate_risk_assessment(self, mentions: List, days: int) -> Dict:
        """Évaluation de la gravité (identique à l'original)"""
        if not mentions:
            return {
                'risk_level': 'FAIBLE',
                'risk_score': 0,
                'explanation': 'Aucune mention détectée sur la période.',
                'factors': {}
            }
        
        total_mentions = len(mentions)
        
        # Facteurs de risque
        volume_score = min(total_mentions / (days * 10), 1.0)
        
        negative_mentions = [m for m in mentions if m.sentiment == 'negative']
        negative_ratio = len(negative_mentions) / total_mentions if total_mentions > 0 else 0
        sentiment_score = negative_ratio
        
        if mentions:
            avg_engagement = sum(m.engagement_score for m in mentions) / len(mentions)
            max_engagement = max(m.engagement_score for m in mentions)
            engagement_score = min((avg_engagement + max_engagement) / 2000, 1.0)
        else:
            engagement_score = 0
        
        # Pics d'activité
        timeline = {}
        for mention in mentions:
            if mention.published_at:
                date_key = mention.published_at.date()
                timeline[date_key] = timeline.get(date_key, 0) + 1
        
        if timeline:
            daily_counts = list(timeline.values())
            avg_daily = statistics.mean(daily_counts)
            max_daily = max(daily_counts)
            spike_score = min((max_daily / (avg_daily + 1)) / 5, 1.0)
        else:
            spike_score = 0
        
        # Diversité sources
        sources = set(m.source for m in mentions)
        source_diversity_score = min(len(sources) / 5, 1.0)
        
        # Score global
        risk_score = (
            volume_score * 25 +
            sentiment_score * 30 +
            engagement_score * 20 +
            spike_score * 15 +
            source_diversity_score * 10
        )
        
        if risk_score >= 70:
            risk_level = 'ÉLEVÉ'
            color = '#ef4444'
        elif risk_score >= 40:
            risk_level = 'MODÉRÉ'
            color = '#f59e0b'
        else:
            risk_level = 'FAIBLE'
            color = '#10b981'
        
        return {
            'risk_level': risk_level,
            'risk_score': round(risk_score, 1),
            'color': color,
            'explanation': f"Niveau de risque {risk_level} déterminé par l'analyse de {total_mentions} mentions sur {days} jours.",
            'factors': {
                'volume': {'score': round(volume_score * 100, 1), 'weight': '25%'},
                'sentiment': {'score': round(sentiment_score * 100, 1), 'weight': '30%'},
                'engagement': {'score': round(engagement_score * 100, 1), 'weight': '20%'},
                'spike': {'score': round(spike_score * 100, 1), 'weight': '15%'},
                'diversity': {'score': round(source_diversity_score * 100, 1), 'weight': '10%'}
            }
        }
    
    def _analyze_positive_sentiment(self, mentions: List) -> Dict:
        """Analyse des jugements positifs avec contexte camerounais"""
        if not mentions:
            return {
                'count': 0,
                'percentage': 0,
                'analysis': "Aucun commentaire positif identifié sur la période analysée.",
                'key_themes': [],
                'top_mentions': [],
                'strategic_context': "L'absence de réactions positives mérite une attention particulière dans le contexte des relations publiques institutionnelles."
            }
        
        # Analyse des thèmes
        all_content = ' '.join([m.title + ' ' + m.content for m in mentions])
        positive_themes = self._extract_positive_themes(all_content)
        
        # Top mentions engageantes
        top_mentions = sorted(mentions, key=lambda x: x.engagement_score, reverse=True)[:5]
        
        return {
            'count': len(mentions),
            'percentage': 0,  # Sera calculé dans la synthèse
            'analysis': f"L'analyse révèle {len(mentions)} mentions à connotation positive, témoignant d'une réception favorable sur certains aspects. Ces réactions positives constituent un capital de confiance précieux qu'il convient de consolider et d'amplifier dans la stratégie de communication.",
            'key_themes': positive_themes,
            'top_mentions': [
                {
                    'title': m.title[:100] + '...' if len(m.title) > 100 else m.title,
                    'author': m.author,
                    'source': m.source,
                    'engagement': m.engagement_score,
                    'content_extract': m.content[:200] + '...' if len(m.content) > 200 else m.content
                }
                for m in top_mentions
            ],
            'strategic_context': "Ces réactions positives reflètent l'efficacité de certains messages institutionnels et constituent des leviers d'influence à exploiter pour renforcer l'adhésion populaire aux politiques publiques."
        }
    
    def _analyze_negative_sentiment(self, mentions: List) -> Dict:
        """Analyse des jugements négatifs avec enjeux stratégiques"""
        if not mentions:
            return {
                'count': 0,
                'percentage': 0,
                'analysis': "Aucun commentaire négatif significatif détecté sur la période.",
                'key_concerns': [],
                'top_mentions': [],
                'strategic_context': "Cette absence de critiques majeures indique une période de relative stabilité dans l'opinion publique."
            }
        
        # Analyse des préoccupations
        all_content = ' '.join([m.title + ' ' + m.content for m in mentions])
        negative_themes = self._extract_negative_themes(all_content)
        
        top_mentions = sorted(mentions, key=lambda x: x.engagement_score, reverse=True)[:5]
        
        return {
            'count': len(mentions),
            'percentage': 0,
            'analysis': f"L'analyse identifie {len(mentions)} mentions à caractère critique, révélant des points de tension dans l'opinion publique. Ces signaux d'alarme nécessitent une attention immédiate et une réponse stratégique adaptée pour prévenir toute escalade de la contestation.",
            'key_concerns': negative_themes,
            'top_mentions': [
                {
                    'title': m.title[:100] + '...' if len(m.title) > 100 else m.title,
                    'author': m.author,
                    'source': m.source,
                    'engagement': m.engagement_score,
                    'content_extract': m.content[:200] + '...' if len(m.content) > 200 else m.content
                }
                for m in top_mentions
            ],
            'strategic_context': "Ces critiques peuvent constituer le terreau d'une mobilisation plus large si elles ne sont pas traitées avec célérité. Une réponse coordonnée s'impose pour restaurer la confiance et neutraliser les narratifs défavorables."
        }
    
    def _analyze_neutral_sentiment(self, mentions: List) -> Dict:
        """Analyse des jugements neutres et leur potentiel d'influence"""
        if not mentions:
            return {
                'count': 0,
                'percentage': 0,
                'analysis': "Aucune mention neutre significative identifiée.",
                'observation_themes': [],
                'strategic_context': "L'absence de réactions neutres peut indiquer une polarisation forte de l'opinion publique."
            }
        
        all_content = ' '.join([m.title + ' ' + m.content for m in mentions])
        neutral_themes = self._extract_neutral_themes(all_content)
        
        return {
            'count': len(mentions),
            'percentage': 0,
            'analysis': f"Les {len(mentions)} mentions neutres reflètent une approche observatrice et factuelle de la part d'une frange de l'opinion publique. Cette neutralité représente un terreau fertile pour l'influence, ces audiences étant potentiellement réceptives à des arguments bien construits.",
            'observation_themes': neutral_themes,
            'strategic_context': "Ces voix neutres constituent un segment stratégique de l'opinion publique, susceptible de basculer vers le soutien avec une communication ciblée et persuasive. Leur conversion représente un enjeu majeur pour élargir la base de soutien institutionnel."
        }
    
    def _generate_judgment_synthesis(self, positive: List, negative: List, neutral: List) -> Dict:
        """Synthèse stratégique des jugements publics"""
        total = len(positive) + len(negative) + len(neutral)
        
        if total == 0:
            return {
                'total_analyzed': 0,
                'distribution': {},
                'dominant_trend': 'Indéterminé',
                'strategic_assessment': "Absence de données suffisantes pour établir une analyse de tendance.",
                'recommendation': "Intensifier la collecte d'informations pour obtenir une vision claire de l'opinion publique."
            }
        
        pos_pct = (len(positive) / total) * 100
        neg_pct = (len(negative) / total) * 100
        neu_pct = (len(neutral) / total) * 100
        
        # Déterminer la tendance dominante
        if pos_pct > neg_pct and pos_pct > neu_pct:
            dominant_trend = "Favorable"
            trend_analysis = "Les réactions positives dominent le paysage médiatique, traduisant une adhésion majoritaire aux messages institutionnels."
        elif neg_pct > pos_pct and neg_pct > neu_pct:
            dominant_trend = "Critique"
            trend_analysis = "Les réactions négatives prédominent, signalant une crise de confiance qui nécessite une réponse immédiate et coordonnée."
        else:
            dominant_trend = "Mitigé"
            trend_analysis = "L'opinion publique apparaît divisée, révélant une opportunité de conquête des indécis par une communication stratégique ciblée."
        
        return {
            'total_analyzed': total,
            'distribution': {
                'positive': {'count': len(positive), 'percentage': round(pos_pct, 1)},
                'negative': {'count': len(negative), 'percentage': round(neg_pct, 1)},
                'neutral': {'count': len(neutral), 'percentage': round(neu_pct, 1)}
            },
            'dominant_trend': dominant_trend,
            'strategic_assessment': trend_analysis,
            'recommendation': self._generate_strategic_recommendation(pos_pct, neg_pct, neu_pct)
        }
    
    def _analyze_engaged_influencers(self, mentions: List) -> Dict:
        """Analyse des influenceurs engagés (France 24 + liste camerounaise)"""
        if not mentions:
            return {
                'total_identified': 0,
                'analysis': "Aucun influenceur significatif identifié sur la période.",
                'influencers_table': [],
                'strategic_context': "L'absence d'engagement des influenceurs peut indiquer soit un désintérêt, soit une stratégie d'attentisme."
            }
        
        # Regrouper par auteur
        influencer_data = {}
        for mention in mentions:
            author = mention.author
            if author not in influencer_data:
                influencer_data[author] = {
                    'mentions': [],
                    'total_engagement': 0,
                    'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0}
                }
            
            influencer_data[author]['mentions'].append(mention)
            influencer_data[author]['total_engagement'] += mention.engagement_score
            
            if mention.sentiment:
                influencer_data[author]['sentiment_distribution'][mention.sentiment] += 1
        
        # Créer le tableau des influenceurs
        influencers_table = []
        for author, data in influencer_data.items():
            mention_count = len(data['mentions'])
            avg_engagement = data['total_engagement'] / mention_count if mention_count > 0 else 0
            
            # Calculer le score de sentiment
            sentiment_dist = data['sentiment_distribution']
            total_sentiment = sum(sentiment_dist.values())
            
            if total_sentiment > 0:
                pos_ratio = sentiment_dist['positive'] / total_sentiment
                neg_ratio = sentiment_dist['negative'] / total_sentiment
                
                if pos_ratio > 0.6:
                    sentiment_tendency = "Favorable"
                    risk_level = "Faible"
                elif neg_ratio > 0.6:
                    sentiment_tendency = "Critique"
                    risk_level = "Élevé"
                else:
                    sentiment_tendency = "Mitigé"
                    risk_level = "Modéré"
            else:
                sentiment_tendency = "Indéterminé"
                risk_level = "Modéré"
            
            # Identifier la plateforme principale
            sources = [m.source for m in data['mentions']]
            main_platform = max(set(sources), key=sources.count) if sources else "Inconnu"
            
            # Portée estimée (basée sur l'engagement)
            if avg_engagement > 1000:
                estimated_reach = "Très Élevée"
            elif avg_engagement > 500:
                estimated_reach = "Élevée"
            elif avg_engagement > 100:
                estimated_reach = "Modérée"
            else:
                estimated_reach = "Limitée"
            
            influencers_table.append({
                'name': author,
                'platform': main_platform,
                'mentions_count': mention_count,
                'total_engagement': int(data['total_engagement']),
                'avg_engagement': int(avg_engagement),
                'sentiment_tendency': sentiment_tendency,
                'risk_level': risk_level,
                'estimated_reach': estimated_reach,
                'last_activity': max([m.published_at for m in data['mentions'] if m.published_at]).strftime('%d/%m/%Y') if data['mentions'] else 'N/A'
            })
        
        # Trier par engagement total
        influencers_table.sort(key=lambda x: x['total_engagement'], reverse=True)
        
        return {
            'total_identified': len(influencers_table),
            'analysis': f"L'analyse identifie {len(influencers_table)} influenceurs actifs sur la période, constituant un écosystème d'opinion leaders aux orientations variées. Leur capacité de mobilisation et leur portée médiatique en font des acteurs stratégiques dans la formation de l'opinion publique camerounaise.",
            'influencers_table': influencers_table,
            'strategic_context': "Ces influenceurs représentent des relais d'opinion cruciaux dans l'espace numérique camerounais. Leur engagement, positif ou négatif, peut amplifier considérablement la portée des messages institutionnels ou, inversement, alimenter des dynamiques de contestation. Une stratégie d'influence ciblée s'impose pour optimiser leur contribution à la communication gouvernementale."
        }
    
    def _extract_positive_themes(self, content: str) -> List[str]:
        """Extraire les thèmes positifs du contenu"""
        positive_keywords = [
            'progrès', 'développement', 'amélioration', 'succès', 'réussite',
            'bon', 'bien', 'excellent', 'félicitations', 'bravo',
            'croissance', 'avancée', 'innovation', 'modernisation'
        ]
        
        themes = []
        content_lower = content.lower()
        for keyword in positive_keywords:
            if keyword in content_lower:
                themes.append(keyword.title())
        
        return themes[:10]  # Limiter à 10 thèmes
    
    def _extract_negative_themes(self, content: str) -> List[str]:
        """Extraire les préoccupations du contenu négatif"""
        negative_keywords = [
            'problème', 'crise', 'échec', 'corruption', 'mauvais',
            'inquiétude', 'préoccupation', 'critique', 'opposition',
            'manifestation', 'grève', 'protestation', 'colère'
        ]
        
        concerns = []
        content_lower = content.lower()
        for keyword in negative_keywords:
            if keyword in content_lower:
                concerns.append(keyword.title())
        
        return concerns[:10]
    
    def _extract_neutral_themes(self, content: str) -> List[str]:
        """Extraire les thèmes d'observation neutre"""
        neutral_keywords = [
            'analyse', 'étude', 'rapport', 'données', 'statistiques',
            'observation', 'constat', 'information', 'annonce',
            'décision', 'mesure', 'politique', 'programme'
        ]
        
        themes = []
        content_lower = content.lower()
        for keyword in neutral_keywords:
            if keyword in content_lower:
                themes.append(keyword.title())
        
        return themes[:10]
    
    def _generate_strategic_recommendation(self, pos_pct: float, neg_pct: float, neu_pct: float) -> str:
        """Générer une recommandation stratégique basée sur la distribution"""
        if pos_pct > 50:
            return "Capitaliser sur l'élan positif en amplifiant les messages qui résonnent favorablement auprès du public. Maintenir la dynamique par une communication cohérente et régulière."
        elif neg_pct > 50:
            return "Mise en place urgente d'une stratégie de gestion de crise : identifier les sources de mécontentement, développer des contre-narratifs factuels, et engager un dialogue constructif avec les parties prenantes."
        elif neu_pct > 40:
            return "Opportunité de conquête : cibler les audiences neutres avec des messages persuasifs et des preuves tangibles pour les convertir en soutiens actifs."
        else:
            return "Approche équilibrée recommandée : consolider les acquis positifs tout en adressant proactivement les préoccupations exprimées par les voix critiques."

    def generate_cameroon_html_report(self, report_data: Dict) -> str:
        """Générer le rapport HTML avec la structure en 5 sections"""
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{ size: A4; margin: 1.5cm; }}
                body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #333; line-height: 1.6; font-size: 11pt; }}
                .header {{ text-align: center; padding: 15px 0; border-bottom: 3px solid #667eea; margin-bottom: 20px; }}
                .header h1 {{ color: #667eea; font-size: 20pt; margin: 0 0 5px 0; }}
                .header .subtitle {{ color: #666; font-size: 10pt; }}
                .page-break {{ page-break-after: always; }}
                .section-title {{ color: #667eea; font-size: 14pt; font-weight: bold; margin: 25px 0 15px 0; padding-bottom: 8px; border-bottom: 2px solid #e5e7eb; }}
                .section-intro {{ background: #f8fafc; padding: 15px; border-left: 4px solid #667eea; margin: 15px 0; font-style: italic; }}
                .risk-box {{ padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 5px solid; }}
                .risk-high {{ background: #fef2f2; border-color: #ef4444; }}
                .risk-medium {{ background: #fffbeb; border-color: #f59e0b; }}
                .risk-low {{ background: #f0fdf4; border-color: #10b981; }}
                .sentiment-positive {{ background: #f0fdf4; border-left: 4px solid #10b981; padding: 15px; margin: 10px 0; }}
                .sentiment-negative {{ background: #fef2f2; border-left: 4px solid #ef4444; padding: 15px; margin: 10px 0; }}
                .sentiment-neutral {{ background: #f9fafb; border-left: 4px solid #6b7280; padding: 15px; margin: 10px 0; }}
                .metrics-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 15px 0; }}
                .metric-card {{ background: #f9fafb; padding: 15px; border-radius: 8px; text-align: center; }}
                .metric-value {{ font-size: 24pt; font-weight: bold; color: #667eea; }}
                .metric-label {{ font-size: 10pt; color: #6b7280; margin-top: 5px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 9pt; }}
                th {{ background: #667eea; color: white; padding: 10px 8px; text-align: left; font-weight: bold; }}
                td {{ padding: 8px; border-bottom: 1px solid #e5e7eb; vertical-align: top; }}
                tr:nth-child(even) {{ background: #f9fafb; }}
                .influencer-risk-high {{ background: #fef2f2; }}
                .influencer-risk-medium {{ background: #fffbeb; }}
                .influencer-risk-low {{ background: #f0fdf4; }}
                .footer {{ position: fixed; bottom: 0; left: 0; right: 0; text-align: center; font-size: 8pt; color: #9ca3af; padding: 10px; border-top: 1px solid #e5e7eb; }}
                .mention-quote {{ font-style: italic; background: #f8fafc; padding: 10px; border-left: 3px solid #ccc; margin: 10px 0; }}
                .synthesis-box {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 20px; border-radius: 10px; margin: 20px 0; }}
            </style>
        </head>
        <body>
        
        <!-- En-tête -->
        <div class="header">
            <h1>🇨🇲 RAPPORT D'ANALYSE - OPINION PUBLIQUE CAMEROUNAISE</h1>
            <div class="subtitle">
                <strong>{report_data['report_object']}</strong><br>
                Période: {report_data['period_days']} jours | 
                Généré le: {report_data['generated_at'].strftime('%d/%m/%Y à %H:%M')}<br>
                <em>Mots-clés analysés: {', '.join(report_data['keywords'])}</em>
            </div>
        </div>
        """
        
        # 1. Évaluation de gravité
        if 'risk_assessment' in report_data:
            risk = report_data['risk_assessment']
            risk_class = 'risk-high' if risk['risk_level'] == 'ÉLEVÉ' else 'risk-medium' if risk['risk_level'] == 'MODÉRÉ' else 'risk-low'
            
            html += f"""
            <div class="section-title">🚨 ÉVALUATION DE LA GRAVITÉ</div>
            <div class="risk-box {risk_class}">
                <h3 style="margin: 0 0 10px 0;">NIVEAU DE RISQUE: {risk['risk_level']} ({risk['risk_score']}/100)</h3>
                <p><strong>Analyse:</strong> {risk['explanation']}</p>
                
            </div>
            """
        
        # 2. Jugements positifs
        if 'positive_analysis' in report_data:
            pos = report_data['positive_analysis']
            html += f"""
            <div class="section-title">😊 JUGEMENTS POSITIFS DES INTERNAUTES</div>
            
            <div class="sentiment-positive">
                <h4>Analyse des Réactions Favorables ({pos['count']} mentions)</h4>
                <p>{pos['analysis']}</p>
                
            </div>
            """
        
        # 3. Jugements négatifs
        if 'negative_analysis' in report_data:
            neg = report_data['negative_analysis']
            html += f"""
            <div class="section-title">😞 JUGEMENTS NÉGATIFS DES INTERNAUTES</div>
            <div class="sentiment-negative">
                <h4>Analyse des Réactions Critiques ({neg['count']} mentions)</h4>
                <p>{neg['analysis']}</p>
                
            </div>
            """
        
        # 4. Jugements neutres
        if 'neutral_analysis' in report_data:
            neu = report_data['neutral_analysis']
            html += f"""
            <div class="section-title">😐 JUGEMENTS NEUTRES DES INTERNAUTES</div>
            <div class="sentiment-neutral">
                <h4>Analyse des Réactions Neutres ({neu['count']} mentions)</h4>
                <p>{neu['analysis']}</p>
                
               
            </div>
            """
        
        # 5. Synthèse des jugements
        if 'judgment_synthesis' in report_data:
            synth = report_data['judgment_synthesis']
            html += f"""
            <div class="section-title">📊 SYNTHÈSE DES JUGEMENTS</div>
            <div class="synthesis-box">
                <h4 style="margin-top: 0; color: white;">Tendance Dominante: {synth['dominant_trend']}</h4>
                <p style="margin-bottom: 0;">{synth['strategic_assessment']}</p>
            </div>
            
            
            """
        
        # 6. Influenceurs engagés
        if 'engaged_influencers' in report_data:
            inf = report_data['engaged_influencers']
            html += f"""
            <div class="section-title">👑 Principaux influenceurs engagés </div>
            
            <p><strong>Analyse:</strong> {inf['analysis']}</p>
            
            <table>
                <tr>
                    <th>Influenceur</th>
                    <th>Plateforme</th>
                    <th>Mentions</th>
                    <th>Engagement Total</th>
                    <th>Portée Estimée</th>
                    <th>Niveau de Risque</th>
                    <th>Dernière Activité</th>
                </tr>
            """
            
            for influencer in inf['influencers_table']:
                risk_class = 'influencer-risk-high' if influencer['risk_level'] == 'Élevé' else 'influencer-risk-medium' if influencer['risk_level'] == 'Modéré' else 'influencer-risk-low'
                
                html += f"""
                    <tr class="{risk_class}">
                        <td><strong>{influencer['name']}</strong></td>
                        <td>{influencer['platform']}</td>
                        <td>{influencer['mentions_count']}</td>
                        <td>{influencer['total_engagement']:,}</td>
                        <td>{influencer['estimated_reach']}</td>
                        <td><strong>{influencer['risk_level']}</strong></td>
                        <td>{influencer['last_activity']}</td>
                    </tr>
                """
            
            html += "</table>"
        
        html += """
            <div class="footer">
                Rapport généré par Superviseur MINDEF | Confidentiel - Usage interne uniquement | République du Cameroun
            </div>
        </body>
        </html>
        """
        
        return html

    def generate_cameroon_pdf(self, report_data: Dict) -> bytes:
        """Générer le PDF du rapport camerounais"""
        try:
            from weasyprint import HTML
            
            html_content = self.generate_cameroon_html_report(report_data)
            pdf_bytes = HTML(string=html_content).write_pdf()
            
            return pdf_bytes
            
        except ImportError:
            logger.warning("WeasyPrint not available, generating HTML only")
            html_content = self.generate_cameroon_html_report(report_data)
            return html_content.encode('utf-8')