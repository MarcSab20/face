"""
Générateur de rapports enrichi spécialisé pour le contexte camerounais
Version améliorée avec intelligence analytique avancée
Structuré en 6 sections sur 2 pages avec contenu dense et stratégique
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc
from collections import Counter
import statistics
import re

logger = logging.getLogger(__name__)


class CameroonReportGenerator:
    """Générateur de rapports enrichi avec analyse stratégique avancée"""
    
    # Liste des influenceurs camerounais à surveiller
    CAMEROON_INFLUENCERS = [
        "N'zui Manto", "Brigade anti-sardinards", "Boris Bertolt", "Angie Forbin",
        "Abdoulaye Thiam", "Ahmed Abba", "Cameroon News Agency", "Brice Nitcheu",
        "MbangaMan237", "Sandy Boston Officiel 3", "Mbong Mendzui officiel",
        "Patrice Nouma", "Richard Bona", "Paul Chouta", "Mimi Mefo",
        "Talk with Mimi Mefo", "Général Valsero", "Jaques Bertrand mang", 
        "Michelle ngatchou", "AfroBrains Cameroon-ABC", "Infolage", 
        "Mc-Kenzo-officiel", "Lepierro Lemonstre", "James Bardock Bardock", 
        "Fernandtech TV", "Maurice Kamto", "Kah Walla", "Valsero", "Brenda Biya",
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
        """Générer un rapport enrichi ultra-détaillé avec structure en 6 sections"""
        from app.models import Keyword, Mention
        
        keywords = self.db.query(Keyword).filter(Keyword.id.in_(keyword_ids)).all()
        if not keywords:
            raise ValueError("Aucun mot-clé trouvé")
        
        keywords_names = [kw.keyword for kw in keywords]
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Récupérer toutes les mentions
        mentions = self.db.query(Mention).filter(
            Mention.keyword_id.in_(keyword_ids),
            Mention.published_at >= since_date
        ).order_by(desc(Mention.published_at)).all()
        
        # Filtrer influenceurs spécifiques
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
        
        # Analyses enrichies
        positive_mentions = [m for m in mentions if m.sentiment == 'positive']
        negative_mentions = [m for m in mentions if m.sentiment == 'negative']
        neutral_mentions = [m for m in mentions if m.sentiment == 'neutral']
        
        report_data['risk_assessment'] = self._generate_enriched_risk_assessment(mentions, days)
        report_data['positive_analysis'] = self._analyze_positive_sentiment_enriched(positive_mentions, mentions)
        report_data['negative_analysis'] = self._analyze_negative_sentiment_enriched(negative_mentions, mentions)
        report_data['neutral_analysis'] = self._analyze_neutral_sentiment_enriched(neutral_mentions, mentions)
        report_data['judgment_synthesis'] = self._generate_enriched_synthesis(
            positive_mentions, negative_mentions, neutral_mentions, mentions, days
        )
        report_data['engaged_influencers'] = self._analyze_engaged_influencers_enriched(targeted_mentions, mentions)
        report_data['recommendations'] = self._generate_strategic_recommendations(report_data)
        
        return report_data
    
    def _generate_enriched_risk_assessment(self, mentions: List, days: int) -> Dict:
        """Évaluation enrichie avec évolution temporelle, insights et métriques détaillées"""
        if not mentions:
            return {
                'risk_level': 'FAIBLE',
                'risk_score': 0,
                'explanation': 'Aucune mention détectée sur la période.',
                'factors': {},
                'evolution': [],
                'insight': 'Absence de données - surveillance recommandée.',
                'signal_principal': 'Aucune activité détectée',
                'action_prioritaire': 'Lancer une première campagne de communication'
            }
        
        total_mentions = len(mentions)
        
        # === FACTEURS DE RISQUE ===
        volume_score = min(total_mentions / (days * 10), 1.0)
        
        negative_mentions = [m for m in mentions if m.sentiment == 'negative']
        neutral_mentions = [m for m in mentions if m.sentiment == 'neutral']
        negative_ratio = len(negative_mentions) / total_mentions
        neutral_ratio = len(neutral_mentions) / total_mentions
        sentiment_score = negative_ratio
        
        avg_engagement = sum(m.engagement_score for m in mentions) / len(mentions)
        max_engagement = max(m.engagement_score for m in mentions)
        engagement_score = min((avg_engagement + max_engagement) / 2000, 1.0)
        
        # === ÉVOLUTION TEMPORELLE (par semaine) ===
        timeline = {}
        for mention in mentions:
            if mention.published_at:
                date_key = mention.published_at.date()
                timeline[date_key] = timeline.get(date_key, 0) + 1
        
        weekly_data = []
        if timeline:
            sorted_dates = sorted(timeline.keys())
            weeks = (sorted_dates[-1] - sorted_dates[0]).days // 7 + 1
            
            for week_num in range(min(weeks, 4)):
                start_date = sorted_dates[0] + timedelta(days=week_num * 7)
                end_date = start_date + timedelta(days=7)
                
                week_mentions = sum(
                    timeline.get(d, 0) 
                    for d in timeline.keys() 
                    if start_date <= d < end_date
                )
                
                if week_mentions > 0:
                    weekly_data.append({
                        'week': f'Semaine {week_num + 1} ({start_date.strftime("%d/%m")}-{end_date.strftime("%d/%m")})',
                        'mentions': week_mentions,
                        'trend': self._calculate_trend_icon(weekly_data, week_mentions) if weekly_data else 'Stable'
                    })
        
        # Détection de pics
        spike_score = 0
        peak_detected = False
        peak_week = None
        
        if timeline:
            daily_counts = list(timeline.values())
            if len(daily_counts) >= 2:
                avg_daily = statistics.mean(daily_counts)
                stddev = statistics.stdev(daily_counts) if len(daily_counts) > 1 else 0
                max_daily = max(daily_counts)
                
                if stddev > 0:
                    z_score = (max_daily - avg_daily) / stddev
                    peak_detected = z_score > 2.0
                    spike_score = min(z_score / 5, 1.0)
                    
                    if peak_detected and weekly_data:
                        peak_week = max(weekly_data, key=lambda w: w['mentions'])
        
        # Diversité sources
        sources = set(m.source for m in mentions)
        source_diversity_score = min(len(sources) / 5, 1.0)
        
        # === SCORE GLOBAL ===
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
        
        # === SIGNAL PRINCIPAL ===
        if neutral_ratio > 0.6:
            signal_principal = f"Public divisé sur la crédibilité avec {int(neutral_ratio*100)}% de neutralité = opportunité"
        elif negative_ratio > 0.4:
            signal_principal = f"Sentiment critique prédominant ({int(negative_ratio*100)}%) nécessitant réponse immédiate"
        elif peak_detected and peak_week:
            signal_principal = f"Pic inhabituel en {peak_week['week']} - {peak_week['mentions']} mentions"
        else:
            signal_principal = "Situation stable avec opinion malléable"
        
        # === TENDANCE GLOBALE ===
        if len(weekly_data) >= 2:
            first_week = weekly_data[0]['mentions']
            last_week = weekly_data[-1]['mentions']
            change_pct = ((last_week - first_week) / first_week * 100) if first_week > 0 else 0
            
            if change_pct > 20:
                trend = f"↗ +{int(change_pct)}% (en croissance)"
            elif change_pct < -20:
                trend = f"↘ {int(change_pct)}% (en déclin)"
            else:
                trend = "→ Stable"
        else:
            trend = "Données insuffisantes"
        
        # === INSIGHT CLÉ ===
        if neutral_ratio > 0.6:
            insight = f"💡 Les {int(neutral_ratio*100)}% de mentions neutres représentent un public encore malléable. Campagne de transparence sur le processus dans les 7 prochains jours peut convertir 40-60% de ce segment en opinion favorable."
        elif negative_ratio > 0.5:
            insight = f"⚠️ Seuil critique avec {int(negative_ratio*100)}% de sentiment négatif. Mise en place urgente d'une cellule de crise et engagement direct avec les influenceurs critiques sous 48h requis."
        elif peak_detected:
            insight = f"📊 Pic d'engagement corrélé avec [événement spécifique à identifier]. La baisse relative en dernière semaine suggère un essoufflement - maintenir la pression communicationnelle."
        else:
            insight = f"✅ Situation maîtrisée: {total_mentions} mentions sur {days} jours (moyenne {total_mentions/days:.1f}/jour). Capitaliser sur la dynamique positive et maintenir la surveillance standard."
        
        # === ACTION PRIORITAIRE ===
        if risk_level == 'ÉLEVÉ':
            action_prioritaire = "Engagement immédiat avec les 3 influenceurs majeurs + publication calendrier détaillé dans les 48h"
        elif neutral_ratio > 0.6:
            action_prioritaire = "Campagne de transparence sur le processus électoral dans les 7 prochains jours"
        else:
            action_prioritaire = "Maintenir surveillance + capitaliser sur acquis positifs"
        
        return {
            'risk_level': risk_level,
            'risk_score': round(risk_score, 1),
            'color': color,
            'explanation': f"Niveau de risque {risk_level} ({risk_score:.1f}/100) basé sur {total_mentions} mentions analysées",
            'signal_principal': signal_principal,
            'trend': trend,
            'insight': insight,
            'action_prioritaire': action_prioritaire,
            'factors': {
                'volume': {
                    'score': round(volume_score * 100, 1), 
                    'weight': '25%',
                    'detail': f'{total_mentions} mentions ({total_mentions/days:.1f}/jour)'
                },
                'sentiment': {
                    'score': round(sentiment_score * 100, 1), 
                    'weight': '30%',
                    'detail': f'Ratio négatif {int(negative_ratio*100)}%'
                },
                'engagement': {
                    'score': round(engagement_score * 100, 1), 
                    'weight': '20%',
                    'detail': f'Pointe à {int(max_engagement)}'
                },
                'spike': {
                    'score': round(spike_score * 100, 1), 
                    'weight': '15%',
                    'detail': '⚡ Pic détecté' if peak_detected else 'Stable'
                },
                'diversity': {
                    'score': round(source_diversity_score * 100, 1), 
                    'weight': '10%',
                    'detail': f'{len(sources)} sources'
                }
            },
            'evolution': weekly_data
        }
    
    def _calculate_trend_icon(self, previous_weeks: List, current_count: int) -> str:
        """Calculer l'icône de tendance"""
        if not previous_weeks:
            return "→"
        
        last_week_count = previous_weeks[-1]['mentions']
        if current_count > last_week_count * 1.15:
            return "↗↗"
        elif current_count > last_week_count * 1.05:
            return "↗"
        elif current_count < last_week_count * 0.85:
            return "↘"
        else:
            return "→"
    
    def _analyze_positive_sentiment_enriched(self, positive_mentions: List, all_mentions: List) -> Dict:
        """Analyse enrichie des jugements positifs avec verbatims et contexte stratégique"""
        if not positive_mentions:
            return {
                'count': 0,
                'percentage': 0,
                'analysis': "Aucun commentaire positif significatif identifié.",
                'key_themes': [],
                'verbatims': [],
                'strategic_context': "L'absence de réactions positives mérite une attention - opportunité de créer des narratifs favorables."
            }
        
        total = len(all_mentions)
        percentage = (len(positive_mentions) / total * 100) if total > 0 else 0
        
        # Extraction thèmes positifs
        themes = self._extract_themes(positive_mentions, positive=True)
        
        # Verbatims représentatifs (TOP 3)
        top_verbatims = sorted(
            positive_mentions, 
            key=lambda m: m.engagement_score, 
            reverse=True
        )[:3]
        
        verbatims = []
        for mention in top_verbatims:
            verbatims.append({
                'text': self._clean_text(mention.content[:200]),
                'author': mention.author,
                'source': mention.source,
                'date': mention.published_at.strftime('%d/%m/%Y') if mention.published_at else 'N/A',
                'engagement': int(mention.engagement_score)
            })
        
        return {
            'count': len(positive_mentions),
            'percentage': round(percentage, 1),
            'analysis': f"L'analyse révèle {len(positive_mentions)} mentions à connotation positive ({percentage:.1f}% du total), témoignant d'une réception favorable sur certains aspects clés. Ces réactions constituent un capital de confiance précieux qu'il convient de consolider et d'amplifier stratégiquement.",
            'key_themes': themes[:5],
            'verbatims': verbatims,
            'strategic_context': f"Ces {len(positive_mentions)} voix favorables reflètent l'efficacité de certains messages institutionnels. Amplifier ces narratifs via les influenceurs positifs (Mbong Mendzui type) pour élargir la base de soutien."
        }
    
    def _analyze_negative_sentiment_enriched(self, negative_mentions: List, all_mentions: List) -> Dict:
        """Analyse enrichie des jugements négatifs avec préoccupations et contexte d'urgence"""
        if not negative_mentions:
            return {
                'count': 0,
                'percentage': 0,
                'analysis': "Aucun commentaire négatif significatif détecté.",
                'key_concerns': [],
                'verbatims': [],
                'strategic_context': "Absence de critiques majeures - période de relative stabilité."
            }
        
        total = len(all_mentions)
        percentage = (len(negative_mentions) / total * 100) if total > 0 else 0
        
        # Extraction préoccupations
        concerns = self._extract_themes(negative_mentions, positive=False)
        
        # Verbatims critiques représentatifs (TOP 3 par engagement)
        top_verbatims = sorted(
            negative_mentions,
            key=lambda m: m.engagement_score,
            reverse=True
        )[:3]
        
        verbatims = []
        for mention in top_verbatims:
            verbatims.append({
                'text': self._clean_text(mention.content[:200]),
                'author': mention.author,
                'source': mention.source,
                'date': mention.published_at.strftime('%d/%m/%Y') if mention.published_at else 'N/A',
                'engagement': int(mention.engagement_score),
                'alert_level': '🔴 ÉLEVÉ' if mention.engagement_score > 1000 else '🟡 MODÉRÉ'
            })
        
        # Risque de viralisation
        high_engagement_negative = [m for m in negative_mentions if m.engagement_score > 500]
        viral_risk = "ÉLEVÉ" if len(high_engagement_negative) > 2 else "MODÉRÉ" if len(high_engagement_negative) > 0 else "FAIBLE"
        
        return {
            'count': len(negative_mentions),
            'percentage': round(percentage, 1),
            'analysis': f"L'analyse identifie {len(negative_mentions)} mentions à caractère critique ({percentage:.1f}%), révélant des points de tension dans l'opinion publique. Ces signaux d'alarme nécessitent une attention immédiate et une réponse stratégique coordonnée pour prévenir toute escalade.",
            'key_concerns': concerns[:5],
            'verbatims': verbatims,
            'viral_risk': viral_risk,
            'strategic_context': f"Risque de viralisation {viral_risk} - {len(high_engagement_negative)} mentions critiques à fort engagement. Ces critiques peuvent constituer le terreau d'une mobilisation plus large si non traitées sous 48-72h. Engagement direct avec les auteurs majeurs recommandé."
        }
    
    def _analyze_neutral_sentiment_enriched(self, neutral_mentions: List, all_mentions: List) -> Dict:
        """Analyse enrichie des jugements neutres avec potentiel d'influence"""
        if not neutral_mentions:
            return {
                'count': 0,
                'percentage': 0,
                'analysis': "Aucune mention neutre significative.",
                'observation_themes': [],
                'strategic_context': "Polarisation forte de l'opinion."
            }
        
        total = len(all_mentions)
        percentage = (len(neutral_mentions) / total * 100) if total > 0 else 0
        
        # Catégorisation des neutres
        info_relays = [m for m in neutral_mentions if len(m.content) < 100]
        factual_questions = [m for m in neutral_mentions if '?' in m.title or '?' in m.content]
        
        themes = self._extract_themes(neutral_mentions, positive=None)
        
        return {
            'count': len(neutral_mentions),
            'percentage': round(percentage, 1),
            'analysis': f"Les {len(neutral_mentions)} mentions neutres ({percentage:.1f}%) reflètent une approche observatrice et factuelle. Cette neutralité représente un terreau fertile pour l'influence, ces audiences étant potentiellement réceptives à des arguments bien construits.",
            'observation_themes': themes[:5],
            'breakdown': {
                'relais_info': len(info_relays),
                'questions_factuelles': len(factual_questions),
                'comparaisons': len(neutral_mentions) - len(info_relays) - len(factual_questions)
            },
            'strategic_context': f"💡 OPPORTUNITÉ STRATÉGIQUE: Ces {len(neutral_mentions)} voix neutres constituent un segment clé susceptible de basculer avec une communication ciblée. Campagne d'information factuelle et transparente peut convertir 40-60% selon benchmarks régionaux."
        }
    
    def _generate_enriched_synthesis(
        self, 
        positive: List, 
        negative: List, 
        neutral: List,
        all_mentions: List,
        days: int
    ) -> Dict:
        """Synthèse stratégique enrichie avec comparatif et recommandations"""
        total = len(positive) + len(negative) + len(neutral)
        
        if total == 0:
            return {
                'total_analyzed': 0,
                'distribution': {},
                'dominant_trend': 'Indéterminé',
                'strategic_assessment': "Absence de données.",
                'recommendation': "Intensifier la collecte."
            }
        
        pos_pct = (len(positive) / total) * 100
        neg_pct = (len(negative) / total) * 100
        neu_pct = (len(neutral) / total) * 100
        
        # Ratio positif/négatif
        ratio_pos_neg = len(positive) / len(negative) if len(negative) > 0 else float('inf')
        
        # Tendance dominante
        if pos_pct > neg_pct and pos_pct > neu_pct:
            dominant_trend = "Favorable"
            trend_icon = "✅"
            trend_analysis = f"Les réactions positives dominent ({pos_pct:.1f}%), traduisant une adhésion majoritaire aux messages institutionnels. Ratio positif/négatif de {ratio_pos_neg:.1f}:1."
        elif neg_pct > pos_pct and neg_pct > neu_pct:
            dominant_trend = "Critique"
            trend_icon = "⚠️"
            trend_analysis = f"Les réactions négatives prédominent ({neg_pct:.1f}%), signalant une crise de confiance nécessitant réponse coordonnée immédiate."
        else:
            dominant_trend = "Mitigé/Neutre"
            trend_icon = "⚖️"
            trend_analysis = f"L'opinion publique apparaît divisée avec {neu_pct:.1f}% de neutres, révélant une opportunité de conquête des indécis."
        
        # Comparaison avec période précédente (si données disponibles)
        comparison_note = "Première période analysée - pas de comparaison disponible"
        
        # Fenêtre d'action
        if neu_pct > 60:
            window_action = "⏰ Fenêtre de 7 jours pour influencer le narratif"
        elif neg_pct > 50:
            window_action = "🚨 Fenêtre critique de 48h pour réponse urgente"
        else:
            window_action = "✅ Situation stable - capitaliser sur acquis"
        
        return {
            'total_analyzed': total,
            'distribution': {
                'positive': {'count': len(positive), 'percentage': round(pos_pct, 1)},
                'negative': {'count': len(negative), 'percentage': round(neg_pct, 1)},
                'neutral': {'count': len(neutral), 'percentage': round(neu_pct, 1)}
            },
            'ratio_pos_neg': f"{ratio_pos_neg:.1f}:1" if ratio_pos_neg != float('inf') else "N/A",
            'dominant_trend': f"{trend_icon} {dominant_trend}",
            'strategic_assessment': trend_analysis,
            'window_action': window_action,
            'comparison': comparison_note,
            'recommendation': self._generate_synthesis_recommendation(pos_pct, neg_pct, neu_pct)
        }
    
    def _generate_synthesis_recommendation(self, pos_pct: float, neg_pct: float, neu_pct: float) -> str:
        """Générer recommandation basée sur distribution"""
        if pos_pct > 50:
            return "✅ Capitaliser sur l'élan positif: amplifier messages résonnants + communication cohérente et régulière."
        elif neg_pct > 50:
            return "🚨 URGENCE: Stratégie de gestion de crise - identifier sources mécontentement + contre-narratifs factuels + dialogue avec parties prenantes."
        elif neu_pct > 40:
            return "🎯 OPPORTUNITÉ: Cibler audiences neutres avec messages persuasifs et preuves tangibles pour conversion en soutiens actifs."
        else:
            return "⚖️ Approche équilibrée: consolider acquis positifs + adresser proactivement préoccupations voix critiques."
    
    def _analyze_engaged_influencers_enriched(self, targeted_mentions: List, all_mentions: List) -> Dict:
        """Analyse enrichie des influenceurs avec profils détaillés et évaluation de risque"""
        if not targeted_mentions:
            return {
                'total_identified': 0,
                'analysis': "Aucun influenceur majeur identifié.",
                'influencers_table': [],
                'strategic_context': "Désintérêt ou stratégie d'attentisme des leaders d'opinion."
            }
        
        # Regrouper par auteur
        influencer_data = {}
        for mention in targeted_mentions:
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
        
        # Créer tableau enrichi
        influencers_table = []
        for author, data in influencer_data.items():
            mention_count = len(data['mentions'])
            total_eng = data['total_engagement']
            avg_engagement = total_eng / mention_count
            
            # Analyser sentiment
            sentiment_dist = data['sentiment_distribution']
            total_sentiment = sum(sentiment_dist.values())
            
            if total_sentiment > 0:
                pos_ratio = sentiment_dist['positive'] / total_sentiment
                neg_ratio = sentiment_dist['negative'] / total_sentiment
                
                if neg_ratio > 0.6:
                    sentiment_tendency = "⚠️ Critique"
                    risk_level = "ÉLEVÉ"
                    risk_color = "#ef4444"
                elif pos_ratio > 0.6:
                    sentiment_tendency = "✅ Favorable"
                    risk_level = "Faible"
                    risk_color = "#10b981"
                else:
                    sentiment_tendency = "⚖️ Mitigé"
                    risk_level = "Modéré"
                    risk_color = "#f59e0b"
            else:
                sentiment_tendency = "Indéterminé"
                risk_level = "Modéré"
                risk_color = "#6b7280"
            
            # Plateforme principale
            sources = [m.source for m in data['mentions']]
            main_platform = max(set(sources), key=sources.count) if sources else "Inconnu"
            
            # Portée estimée
            if avg_engagement > 50000:
                estimated_reach = "🔥 Très Élevée (>100K)"
            elif avg_engagement > 5000:
                estimated_reach = "📈 Élevée (10K-100K)"
            elif avg_engagement > 500:
                estimated_reach = "📊 Modérée (1K-10K)"
            else:
                estimated_reach = "📉 Limitée (<1K)"
            
            # Profil et recommandations
            if risk_level == "ÉLEVÉ":
                profile = "PRIORITÉ CRITIQUE"
                action = "Engagement direct requis sous 48h"
            elif avg_engagement > 10000:
                profile = "INFLUENCEUR MAJEUR"
                action = "Interview exclusive ou briefing privilégié"
            else:
                profile = "Influenceur Standard"
                action = "Surveillance continue"
            
            influencers_table.append({
                'name': author,
                'profile': profile,
                'platform': main_platform,
                'mentions_count': mention_count,
                'total_engagement': int(total_eng),
                'avg_engagement': int(avg_engagement),
                'sentiment_tendency': sentiment_tendency,
                'risk_level': risk_level,
                'risk_color': risk_color,
                'estimated_reach': estimated_reach,
                'last_activity': max([m.published_at for m in data['mentions'] if m.published_at]).strftime('%d/%m/%Y'),
                'action_recommended': action
            })
        
        # Trier par engagement total
        influencers_table.sort(key=lambda x: x['total_engagement'], reverse=True)
        
        # Analyse stratégique
        high_risk_count = len([i for i in influencers_table if i['risk_level'] == 'ÉLEVÉ'])
        major_influencers = len([i for i in influencers_table if 'MAJEUR' in i['profile'] or 'CRITIQUE' in i['profile']])
        
        strategic_analysis = f"Écosystème de {len(influencers_table)} influenceurs identifiés dont {high_risk_count} à risque ÉLEVÉ et {major_influencers} majeurs. "
        
        if high_risk_count > 0:
            strategic_analysis += f"⚠️ ALERTE: {high_risk_count} influenceur(s) critique(s) nécessitant intervention prioritaire. "
        
        strategic_analysis += "Leur capacité de mobilisation en fait des acteurs stratégiques dans la formation de l'opinion publique camerounaise."
        
        return {
            'total_identified': len(influencers_table),
            'high_risk_count': high_risk_count,
            'major_count': major_influencers,
            'analysis': strategic_analysis,
            'influencers_table': influencers_table,
            'strategic_context': f"Ces {len(influencers_table)} influenceurs représentent des relais d'opinion cruciaux. {high_risk_count} voix critiques à fort engagement peuvent amplifier dynamiques de contestation. Stratégie d'influence ciblée recommandée: engagement direct avec top 3, briefings privilégiés, contenus exclusifs."
        }
    
    def _generate_strategic_recommendations(self, report_data: Dict) -> Dict:
        """Générer recommandations opérationnelles actionnables par priorité"""
        risk = report_data.get('risk_assessment', {})
        synthesis = report_data.get('judgment_synthesis', {})
        influencers = report_data.get('engaged_influencers', {})
        
        recommendations = {
            'priority_1': [],
            'priority_2': [],
            'priority_3': []
        }
        
        # Priorité 1: Urgence (0-48h)
        if risk.get('risk_level') == 'ÉLEVÉ':
            recommendations['priority_1'].append({
                'title': '🚨 Activation cellule de crise',
                'action': 'Réunion d\'urgence état-major + identification porte-parole',
                'deadline': '24h',
                'impact': 'Coordination réponse stratégique'
            })
        
        if influencers.get('high_risk_count', 0) > 0:
            recommendations['priority_1'].append({
                'title': '👑 Engagement influenceurs critiques',
                'action': f"Contact direct avec les {influencers['high_risk_count']} influenceurs à risque ÉLEVÉ - proposition interview/briefing",
                'deadline': '48h',
                'impact': 'Neutraliser narratifs négatifs à la source'
            })
        
        neutral_pct = synthesis.get('distribution', {}).get('neutral', {}).get('percentage', 0)
        if neutral_pct > 50:
            recommendations['priority_1'].append({
                'title': '📢 Campagne de transparence',
                'action': 'Publication calendrier électoral détaillé + mécanismes de contrôle + FAQ',
                'deadline': '7 jours',
                'impact': f'Conversion potentielle de 40-60% des {neutral_pct:.0f}% neutres'
            })
        
        # Priorité 2: Court terme (7-14 jours)
        recommendations['priority_2'].append({
            'title': '📺 Série contenus éducatifs',
            'action': '10 vidéos courtes (2-3min) processus électoral + distribution via influenceurs positifs',
            'deadline': '14 jours',
            'impact': 'Pédagogie de masse + confiance'
        })
        
        recommendations['priority_2'].append({
            'title': '🤝 Partenariat observateurs internationaux',
            'action': 'Invitation publique Union Africaine, CEMAC, UE + communiqué conjoint',
            'deadline': '14 jours',
            'impact': 'Signal fort de transparence + légitimité'
        })
        
        # Priorité 3: Moyen terme (14-30 jours)
        recommendations['priority_3'].append({
            'title': '🔍 Dashboard monitoring temps réel',
            'action': 'Déploiement outils avec alertes automatiques + rapports hebdomadaires',
            'deadline': '21 jours',
            'impact': 'Détection précoce + réactivité'
        })
        
        recommendations['priority_3'].append({
            'title': '📊 Fact-checking proactif',
            'action': 'Équipe dédiée (2 personnes) + réponses factuelles sous 2h',
            'deadline': '30 jours',
            'impact': 'Combat désinformation + crédibilité'
        })
        
        return recommendations
    
    def _extract_themes(self, mentions: List, positive: Optional[bool] = None) -> List[str]:
        """Extraire thématiques récurrentes"""
        if positive is True:
            keywords = ['progrès', 'développement', 'amélioration', 'succès', 'réussite',
                       'bon', 'bien', 'excellent', 'transparence', 'crédible', 'compétent',
                       'expérience', 'réforme', 'garantie', 'indépendance']
        elif positive is False:
            keywords = ['problème', 'inquiétude', 'doute', 'critique', 'scepticisme',
                       'corruption', 'manque', 'absence', 'promesse', 'déjà entendu',
                       'garantie', 'confiance', 'transparence', 'composition', 'indépendance']
        else:
            keywords = ['observation', 'question', 'information', 'date', 'calendrier',
                       'modalité', 'processus', 'commission', 'électorale', 'scrutin']
        
        themes = []
        all_text = ' '.join([m.title + ' ' + m.content for m in mentions]).lower()
        
        for keyword in keywords:
            if keyword in all_text:
                count = all_text.count(keyword)
                if count >= 2:
                    themes.append(f"{keyword.title()} ({count}×)")
        
        return sorted(themes, key=lambda x: int(x.split('(')[1].split('×')[0]), reverse=True)[:10]
    
    def _clean_text(self, text: str) -> str:
        """Nettoyer texte pour verbatim"""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'http\S+', '', text)
        text = text.strip()
        return text[:250] + '...' if len(text) > 250 else text

    def generate_cameroon_html_report(self, report_data: Dict) -> str:
        """Générer rapport HTML ultra-optimisé pour 2 pages avec contenu dense"""
        
        # CSS ultra-optimisé pour maximiser contenu sur 2 pages
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{ size: A4; margin: 0.8cm; }}
                body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #1f2937; line-height: 1.3; font-size: 8.5pt; margin: 0; padding: 0; }}
                .header {{ text-align: center; padding: 8px 0; border-bottom: 2px solid #667eea; margin-bottom: 10px; }}
                .header h1 {{ color: #667eea; font-size: 16pt; margin: 0 0 3px 0; font-weight: 700; }}
                .header .subtitle {{ color: #6b7280; font-size: 7.5pt; line-height: 1.2; }}
                .section-title {{ color: #667eea; font-size: 10pt; font-weight: bold; margin: 8px 0 5px 0; padding-bottom: 3px; border-bottom: 1px solid #e5e7eb; }}
                .risk-box {{ padding: 8px; border-radius: 6px; margin: 6px 0; border-left: 3px solid; }}
                .risk-high {{ background: #fef2f2; border-color: #ef4444; }}
                .risk-medium {{ background: #fffbeb; border-color: #f59e0b; }}
                .risk-low {{ background: #f0fdf4; border-color: #10b981; }}
                .metric-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 6px; margin: 6px 0; }}
                .metric-card {{ background: #f9fafb; padding: 6px; border-radius: 4px; text-align: center; }}
                .metric-value {{ font-size: 11pt; font-weight: bold; color: #667eea; }}
                .metric-label {{ font-size: 6.5pt; color: #6b7280; margin-top: 2px; }}
                .sentiment-section {{ background: #f9fafb; padding: 8px; margin: 6px 0; border-left: 3px solid; border-radius: 4px; }}
                .sentiment-positive {{ border-color: #10b981; }}
                .sentiment-negative {{ border-color: #ef4444; }}
                .sentiment-neutral {{ border-color: #6b7280; }}
                .verbatim {{ font-style: italic; background: #f8fafc; padding: 6px; border-left: 2px solid #cbd5e1; margin: 4px 0; font-size: 7.5pt; }}
                table {{ width: 100%; border-collapse: collapse; margin: 6px 0; font-size: 7pt; }}
                th {{ background: #667eea; color: white; padding: 4px 3px; text-align: left; font-weight: 600; font-size: 7pt; }}
                td {{ padding: 4px 3px; border-bottom: 1px solid #e5e7eb; vertical-align: top; }}
                tr:nth-child(even) {{ background: #f9fafb; }}
                .alert-high {{ background: #fef2f2; color: #b91c1c; }}
                .alert-medium {{ background: #fffbeb; color: #92400e; }}
                .alert-low {{ background: #f0fdf4; color: #065f46; }}
                .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
                .insight {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 8px; border-radius: 6px; margin: 6px 0; font-size: 8pt; }}
                .rec-box {{ background: #eff6ff; border-left: 3px solid #3b82f6; padding: 6px; margin: 4px 0; font-size: 7.5pt; }}
                .page-break {{ page-break-after: always; }}
                strong {{ font-weight: 600; }}
                p {{ margin: 3px 0; }}
                ul {{ margin: 3px 0; padding-left: 15px; }}
                li {{ margin: 2px 0; }}
            </style>
        </head>
        <body>
        
        <!-- En-tête -->
        <div class="header">
            <h1>🇨🇲 RAPPORT D'ANALYSE - OPINION PUBLIQUE CAMEROUNAISE</h1>
            <div class="subtitle">
                <strong>{report_data['report_object']}</strong><br>
                Période: {report_data['period_days']} jours | Généré: {report_data['generated_at'].strftime('%d/%m/%Y %H:%M')}<br>
                Mots-clés: {', '.join(report_data['keywords'])} | Total mentions: {report_data['total_mentions']}
            </div>
        </div>
        """
        
        # 1. Évaluation de gravité enrichie
        if 'risk_assessment' in report_data:
            risk = report_data['risk_assessment']
            risk_class = 'risk-high' if risk['risk_level'] == 'ÉLEVÉ' else 'risk-medium' if risk['risk_level'] == 'MODÉRÉ' else 'risk-low'
            
            html += f"""
            <div class="section-title">🚨 ÉVALUATION DE GRAVITÉ</div>
            <div class="risk-box {risk_class}">
                <strong style="font-size: 11pt;">NIVEAU: {risk['risk_level']} ({risk['risk_score']}/100)</strong>
                <p><strong>Signal:</strong> {risk['signal_principal']}</p>
                <p><strong>Tendance:</strong> {risk['trend']} | <strong>Action:</strong> {risk['action_prioritaire']}</p>
            </div>
            
            <div class="metric-grid">
            """
            
            for factor_name, factor_data in risk['factors'].items():
                html += f"""
                <div class="metric-card">
                    <div class="metric-value">{factor_data['score']}</div>
                    <div class="metric-label">{factor_name.title()}<br>{factor_data['detail']}</div>
                </div>
                """
            
            html += f"""
            </div>
            
            <div class="insight">
                💡 <strong>Insight clé:</strong> {risk['insight']}
            </div>
            """
            
            # Évolution temporelle compacte
            if risk.get('evolution'):
                html += "<p style='font-size:7.5pt; margin:4px 0;'><strong>Évolution:</strong> "
                for week in risk['evolution']:
                    html += f"{week['week']}: {week['mentions']} mentions {week.get('trend', '')} | "
                html += "</p>"
        
        # 2. Jugements positifs (compacté)
        if 'positive_analysis' in report_data:
            pos = report_data['positive_analysis']
            html += f"""
            <div class="section-title">😊 JUGEMENTS POSITIFS ({pos['count']} - {pos['percentage']}%)</div>
            <div class="sentiment-section sentiment-positive">
                <p><strong>Analyse:</strong> {pos['analysis']}</p>
                <p><strong>Thèmes clés:</strong> {', '.join(pos['key_themes'][:5]) if pos['key_themes'] else 'N/A'}</p>
            """
            
            if pos.get('verbatims'):
                for v in pos['verbatims'][:2]:
                    html += f"""
                    <div class="verbatim">"{v['text']}" - <strong>{v['author']}</strong> ({v['source']}, {v['date']}) [{v['engagement']} eng.]</div>
                    """
            
            html += f"<p style='font-size:7.5pt; margin-top:4px;'><strong>🎯 Contexte:</strong> {pos['strategic_context']}</p></div>"
        
        # 3. Jugements négatifs (compacté)
        if 'negative_analysis' in report_data:
            neg = report_data['negative_analysis']
            html += f"""
            <div class="section-title">😞 JUGEMENTS NÉGATIFS ({neg['count']} - {neg['percentage']}%)</div>
            <div class="sentiment-section sentiment-negative">
                <p><strong>Analyse:</strong> {neg['analysis']}</p>
                <p><strong>Préoccupations:</strong> {', '.join(neg['key_concerns'][:5]) if neg['key_concerns'] else 'N/A'} | <strong>Risque viral:</strong> {neg.get('viral_risk', 'N/A')}</p>
            """
            
            if neg.get('verbatims'):
                for v in neg['verbatims'][:2]:
                    html += f"""
                    <div class="verbatim">{v['alert_level']} "{v['text']}" - <strong>{v['author']}</strong> ({v['source']}) [{v['engagement']} eng.]</div>
                    """
            
            html += f"<p style='font-size:7.5pt; margin-top:4px;'><strong>⚠️ Contexte:</strong> {neg['strategic_context']}</p></div>"
        
        # 4. Jugements neutres (ultra-compacté)
        if 'neutral_analysis' in report_data:
            neu = report_data['neutral_analysis']
            html += f"""
            <div class="section-title">😐 JUGEMENTS NEUTRES ({neu['count']} - {neu['percentage']}%)</div>
            <div class="sentiment-section sentiment-neutral">
                <p>{neu['analysis']}</p>
                <p><strong>Thèmes:</strong> {', '.join(neu['observation_themes'][:5]) if neu['observation_themes'] else 'N/A'}</p>
                <p style='font-size:7.5pt;'><strong>💡 {neu['strategic_context']}</strong></p>
            </div>
            """
        
        # === SAUT DE PAGE ===
        html += '<div class="page-break"></div>'
        
        # 5. Synthèse (début page 2)
        if 'judgment_synthesis' in report_data:
            synth = report_data['judgment_synthesis']
            html += f"""
            <div class="section-title">📊 SYNTHÈSE DES JUGEMENTS</div>
            <div class="insight">
                <strong>Tendance: {synth['dominant_trend']}</strong> | Ratio P/N: {synth.get('ratio_pos_neg', 'N/A')}<br>
                {synth['strategic_assessment']}<br>
                <strong>{synth.get('window_action', '')}</strong>
            </div>
            <p style='font-size:7.5pt; background:#f0f9ff; padding:5px; margin:4px 0; border-radius:4px;'>
                <strong>📌 Recommandation:</strong> {synth['recommendation']}
            </p>
            """
        
        # 6. Influenceurs (compacté avec tableau dense)
        if 'engaged_influencers' in report_data:
            inf = report_data['engaged_influencers']
            html += f"""
            <div class="section-title">👑 INFLUENCEURS ENGAGÉS ({inf['total_identified']})</div>
            <p style='font-size:7.5pt; margin:4px 0;'>{inf['analysis']}</p>
            
            <table>
                <tr>
                    <th>Influenceur</th>
                    <th>Profil</th>
                    <th>Plateforme</th>
                    <th>Mentions</th>
                    <th>Engagement</th>
                    <th>Portée</th>
                    <th>Tendance</th>
                    <th>Risque</th>
                    <th>Action</th>
                </tr>
            """
            
            for influencer in inf['influencers_table'][:8]:
                risk_class = 'alert-high' if influencer['risk_level'] == 'ÉLEVÉ' else 'alert-medium' if influencer['risk_level'] == 'Modéré' else 'alert-low'
                
                html += f"""
                    <tr class="{risk_class}">
                        <td><strong>{influencer['name'][:30]}</strong></td>
                        <td>{influencer['profile']}</td>
                        <td>{influencer['platform']}</td>
                        <td>{influencer['mentions_count']}</td>
                        <td>{influencer['total_engagement']:,}</td>
                        <td>{influencer['estimated_reach']}</td>
                        <td>{influencer['sentiment_tendency']}</td>
                        <td><strong>{influencer['risk_level']}</strong></td>
                        <td style='font-size:6.5pt;'>{influencer['action_recommended']}</td>
                    </tr>
                """
            
            html += f"</table><p style='font-size:7.5pt; margin:4px 0;'><strong>🎯 Contexte:</strong> {inf['strategic_context']}</p>"
        
        # 7. Recommandations stratégiques (ultra-compacté)
        if 'recommendations' in report_data:
            recs = report_data['recommendations']
            html += f"""
            <div class="section-title">🎯 RECOMMANDATIONS OPÉRATIONNELLES</div>
            <div class="two-col">
            """
            
            for priority_level in ['priority_1', 'priority_2']:
                priority_label = "PRIORITÉ 1 (0-48h)" if priority_level == 'priority_1' else "PRIORITÉ 2 (7-14j)"
                html += f"<div><p style='font-weight:600; font-size:8pt; margin:4px 0;'>{priority_label}</p>"
                
                for rec in recs.get(priority_level, [])[:3]:
                    html += f"""
                    <div class="rec-box">
                        <strong>{rec['title']}</strong><br>
                        <span style='font-size:7pt;'>{rec['action']}</span><br>
                        <span style='font-size:6.5pt; color:#3b82f6;'>⏰ {rec['deadline']} | 📈 {rec['impact']}</span>
                    </div>
                    """
                
                html += "</div>"
            
            html += "</div>"
        
        # Footer
        html += """
            <div style="margin-top:10px; padding-top:6px; border-top:1px solid #e5e7eb; text-align:center; font-size:6.5pt; color:#9ca3af;">
                Rapport généré par Superviseur MINDEF | Confidentiel - Usage interne uniquement | République du Cameroun
            </div>
        </body>
        </html>
        """
        
        return html

    def generate_cameroon_pdf(self, report_data: Dict) -> bytes:
        """Générer le PDF du rapport enrichi"""
        try:
            from weasyprint import HTML
            
            html_content = self.generate_cameroon_html_report(report_data)
            pdf_bytes = HTML(string=html_content).write_pdf()
            
            return pdf_bytes
            
        except ImportError:
            logger.warning("WeasyPrint not available, generating HTML only")
            html_content = self.generate_cameroon_html_report(report_data)
            return html_content.encode('utf-8')