"""
Générateur de Rapports Stratégiques pour Communication et Contre-Information
Version Optimisée - Focus Décisionnel et Actionnable
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from collections import Counter
import json
import asyncio
import statistics

from app.ai_service import SovereignLLMService
from app.models import Keyword, Mention

logger = logging.getLogger(__name__)


class StrategicReportGenerator:
    """Générateur de rapports stratégiques pour division communication/contre-information"""
    
    # Liste des activistes et comptes sensibles à surveiller
    KNOWN_ACTIVISTS = [
        "N'zui Manto", "Brigade anti-sardinards", "Boris Bertolt", "Angie Forbin",
        "Abdoulaye Thiam", "Ahmed Abba", "Cameroon News Agency", "Brice Nitcheu",
        "MbangaMan237", "Sandy Boston Officiel 3", "Mbong Mendzui officiel",
        "Patrice Nouma", "Richard Bona", "Paul Chouta", "Mimi Mefo",
        "Général Valsero", "Jaques Bertrand mang", "Michelle ngatchou",
        "AfroBrains Cameroon-ABC", "Infolage", "Mc-Kenzo-officiel",
        "Lepierro Lemonstre", "James Bardock Bardock", "Fernandtech TV",
        "Maurice Kamto", "Kah Walla", "Brenda Biya", "Calibri Calibro",
        "Patrice Nganang", "Wilfried Ekanga", "Abdouraman Hamadou",
        "Ernest Obama", "Christian Penda Ekoka", "Fabrice Lena",
        "Michel Biem Tong", "Armand Okol", "Claude Wilfried Ekanga",
        "Paul Éric Kingué", "Célestin Djamen", "C'est le hoohaaa"
    ]
    
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = SovereignLLMService()
    
    async def generate_strategic_report(
        self,
        keyword_ids: List[int],
        days: int = 14,
        report_title: str = "Rapport Stratégique"
    ) -> Dict:
        """
        Générer un rapport stratégique complet avec 5 sections majeures
        """
        logger.info(f"🎯 Génération rapport stratégique: {len(keyword_ids)} mots-clés, {days} jours")
        
        # 1. Collecter toutes les données
        since_date = datetime.utcnow() - timedelta(days=days)
        
        mentions = self.db.query(Mention).filter(
            Mention.keyword_id.in_(keyword_ids),
            Mention.published_at >= since_date
        ).order_by(desc(Mention.published_at)).all()
        
        if not mentions:
            return self._generate_empty_report(keyword_ids, days, report_title)
        
        logger.info(f"📊 {len(mentions)} mentions à analyser")
        
        # 2. Classifier les contenus par tonalité (avec IA)
        classified_contents = await self._classify_by_tone(mentions)
        
        # 3. Identifier les activistes et comptes sensibles
        activists_analysis = await self._identify_activists(mentions, classified_contents)
        
        # 4. Générer les 5 sections principales
        
        ## Section 1: Tonalité Positive
        positive_section = await self._generate_positive_section(
            classified_contents['positive'] + classified_contents['very_positive']
        )
        
        ## Section 2: Tonalité Négative  
        negative_section = await self._generate_negative_section(
            classified_contents['negative'] + classified_contents['very_negative']
        )
        
        ## Section 3: Tonalité Neutre
        neutral_section = await self._generate_neutral_section(
            classified_contents['neutral']
        )
        
        ## Section 4: Synthèse Générale Stratégique
        synthesis_section = await self._generate_strategic_synthesis(
            classified_contents, activists_analysis, keyword_ids, days
        )
        
        ## Section 5: Activistes et Comptes Sensibles
        activists_section = self._generate_activists_section(activists_analysis)
        
        # 5. Compiler le rapport final
        report_data = {
            'metadata': {
                'title': report_title,
                'keywords': [self._get_keyword_name(kid) for kid in keyword_ids],
                'period_days': days,
                'generated_at': datetime.utcnow(),
                'total_contents': len(mentions)
            },
            'tonalite_positive': positive_section,
            'tonalite_negative': negative_section,
            'tonalite_neutre': neutral_section,
            'synthese_generale': synthesis_section,
            'activistes_comptes_sensibles': activists_section,
            'statistics': self._generate_statistics(mentions, classified_contents)
        }
        
        logger.info("✅ Rapport stratégique généré avec succès")
        return report_data
    
    async def _classify_by_tone(self, mentions: List[Mention]) -> Dict[str, List[Dict]]:
        """Classifier les contenus par tonalité avec analyse IA fine"""
        
        logger.info("🤖 Classification par tonalité avec IA...")
        
        classified = {
            'very_positive': [],
            'positive': [],
            'neutral': [],
            'negative': [],
            'very_negative': []
        }
        
        for idx, mention in enumerate(mentions):
            try:
                # Construire le texte complet
                full_text = f"{mention.title}\n\n{mention.content}"
                
                # Analyser avec IA
                tone_analysis = await self._analyze_tone_ai(full_text, mention)
                
                content_data = {
                    'id': mention.id,
                    'title': mention.title,
                    'content': mention.content,
                    'full_text': full_text,
                    'author': mention.author,
                    'source': mention.source,
                    'source_url': mention.source_url,
                    'published_at': mention.published_at.isoformat() if mention.published_at else None,
                    'engagement_score': mention.engagement_score,
                    'tone_category': tone_analysis['category'],
                    'tone_score': tone_analysis['score'],
                    'tone_reasoning': tone_analysis['reasoning'],
                    'strategic_impact': tone_analysis.get('strategic_impact', 'moyen')
                }
                
                classified[tone_analysis['category']].append(content_data)
                
                if (idx + 1) % 50 == 0:
                    logger.info(f"Progression: {idx + 1}/{len(mentions)} contenus analysés")
            
            except Exception as e:
                logger.error(f"Erreur analyse contenu {idx+1}: {e}")
                # Fallback: classer comme neutre
                content_data = {
                    'id': mention.id,
                    'title': mention.title,
                    'content': mention.content,
                    'author': mention.author,
                    'source': mention.source,
                    'tone_category': 'neutral',
                    'tone_score': 0
                }
                classified['neutral'].append(content_data)
        
        logger.info(f"✅ Classification terminée: "
                   f"{len(classified['very_positive'])} très positifs, "
                   f"{len(classified['positive'])} positifs, "
                   f"{len(classified['neutral'])} neutres, "
                   f"{len(classified['negative'])} négatifs, "
                   f"{len(classified['very_negative'])} très négatifs")
        
        return classified
    
    async def _analyze_tone_ai(self, text: str, mention: Mention) -> Dict:
        """Analyser la tonalité avec IA de manière approfondie"""
        
        if not text or len(text.strip()) < 10:
            return {
                'category': 'neutral',
                'score': 0,
                'reasoning': 'Contenu trop court',
                'strategic_impact': 'faible'
            }
        
        if not self.llm_service.is_available():
            return self._fallback_tone_analysis(text, mention)
        
        prompt = f"""
Tu es un analyste stratégique en communication pour une institution gouvernementale.

Analyse ce contenu et détermine sa tonalité vis-à-vis de l'image de l'institution:

TITRE: {mention.title}
AUTEUR: {mention.author}
SOURCE: {mention.source}

CONTENU:
{text[:2000]}

Évalue:
1. La tonalité générale (très positif / positif / neutre / négatif / très négatif)
2. L'impact stratégique (critique / élevé / moyen / faible)
3. Les éléments clés qui justifient cette classification

Réponds UNIQUEMENT en JSON:
{{
    "category": "very_positive|positive|neutral|negative|very_negative",
    "score": <-10 à +10>,
    "reasoning": "<explication en 2-3 phrases>",
    "strategic_impact": "critique|élevé|moyen|faible",
    "key_points": ["point1", "point2", "point3"]
}}
"""
        
        try:
            context = {'mentions': [{'content': text}], 'keywords': [], 'period_days': 1}
            response = await self.llm_service.analyze_with_local_llm(prompt, context)
            
            # Parser JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                # Valider
                required_fields = ['category', 'score', 'reasoning', 'strategic_impact']
                if all(field in result for field in required_fields):
                    valid_categories = ['very_positive', 'positive', 'neutral', 'negative', 'very_negative']
                    if result['category'] in valid_categories:
                        return result
            
            return self._fallback_tone_analysis(text, mention)
        
        except Exception as e:
            logger.warning(f"Erreur analyse IA: {e}")
            return self._fallback_tone_analysis(text, mention)
    
    def _fallback_tone_analysis(self, text: str, mention: Mention) -> Dict:
        """Analyse de tonalité fallback basée sur des règles"""
        
        text_lower = text.lower()
        
        # Mots indicateurs
        very_positive_words = ['excellent', 'extraordinaire', 'remarquable', 'succès', 'victoire', 
                               'félicitations', 'exemplaire', 'modèle', 'innovation']
        positive_words = ['bon', 'bien', 'positif', 'amélioration', 'progrès', 'efficace']
        negative_words = ['problème', 'échec', 'critique', 'insuffisant', 'préoccupant']
        very_negative_words = ['scandale', 'catastrophe', 'corruption', 'fraude', 'crise', 
                               'dictature', 'répression', 'violence']
        
        # Compter
        very_pos = sum(1 for w in very_positive_words if w in text_lower)
        pos = sum(1 for w in positive_words if w in text_lower)
        neg = sum(1 for w in negative_words if w in text_lower)
        very_neg = sum(1 for w in very_negative_words if w in text_lower)
        
        # Score
        score = (very_pos * 2 + pos) - (neg + very_neg * 2)
        
        # Déterminer catégorie
        if score >= 3:
            category = 'very_positive'
            impact = 'moyen'
        elif score >= 1:
            category = 'positive'
            impact = 'faible'
        elif score <= -3:
            category = 'very_negative'
            impact = 'critique'
        elif score <= -1:
            category = 'negative'
            impact = 'élevé'
        else:
            category = 'neutral'
            impact = 'faible'
        
        # Vérifier engagement pour ajuster l'impact
        if mention.engagement_score > 1000:
            if impact == 'moyen':
                impact = 'élevé'
            elif impact == 'faible':
                impact = 'moyen'
        
        return {
            'category': category,
            'score': score,
            'reasoning': f"Analyse par mots-clés: {very_pos+pos} positifs, {neg+very_neg} négatifs",
            'strategic_impact': impact
        }
    
    async def _identify_activists(self, mentions: List[Mention], classified_contents: Dict) -> Dict:
        """Identifier les activistes et comptes sensibles"""
        
        logger.info("🎯 Identification des activistes et comptes sensibles...")
        
        activists_found = []
        suspicious_accounts = []
        
        # Analyser chaque mention
        for mention in mentions:
            author = mention.author
            is_known_activist = any(
                activist.lower() in author.lower() 
                for activist in self.KNOWN_ACTIVISTS
            )
            
            # Déterminer la tonalité de ce contenu
            tone_category = None
            for category, contents in classified_contents.items():
                if any(c['id'] == mention.id for c in contents):
                    tone_category = category
                    break
            
            # Si activiste connu ou contenu négatif avec fort engagement
            if is_known_activist or (
                tone_category in ['negative', 'very_negative'] and mention.engagement_score > 500
            ):
                
                activist_data = {
                    'author': author,
                    'is_known_activist': is_known_activist,
                    'content_title': mention.title,
                    'content_url': mention.source_url,
                    'source': mention.source,
                    'tone': tone_category,
                    'engagement': mention.engagement_score,
                    'published_at': mention.published_at.isoformat() if mention.published_at else None,
                    'content_preview': mention.content[:200] + '...' if len(mention.content) > 200 else mention.content
                }
                
                if is_known_activist:
                    activists_found.append(activist_data)
                else:
                    suspicious_accounts.append(activist_data)
        
        # Regrouper par auteur
        activists_by_author = {}
        for activist in activists_found:
            author = activist['author']
            if author not in activists_by_author:
                activists_by_author[author] = {
                    'author': author,
                    'is_known': True,
                    'total_contents': 0,
                    'total_engagement': 0,
                    'tones': [],
                    'contents': []
                }
            
            activists_by_author[author]['total_contents'] += 1
            activists_by_author[author]['total_engagement'] += activist['engagement']
            activists_by_author[author]['tones'].append(activist['tone'])
            activists_by_author[author]['contents'].append(activist)
        
        # Trier par engagement total
        activists_list = sorted(
            activists_by_author.values(),
            key=lambda x: x['total_engagement'],
            reverse=True
        )
        
        # Regrouper comptes suspects
        suspicious_by_author = {}
        for suspect in suspicious_accounts:
            author = suspect['author']
            if author not in suspicious_by_author:
                suspicious_by_author[author] = {
                    'author': author,
                    'is_known': False,
                    'total_contents': 0,
                    'total_engagement': 0,
                    'tones': [],
                    'contents': []
                }
            
            suspicious_by_author[author]['total_contents'] += 1
            suspicious_by_author[author]['total_engagement'] += suspect['engagement']
            suspicious_by_author[author]['tones'].append(suspect['tone'])
            suspicious_by_author[author]['contents'].append(suspect)
        
        suspicious_list = sorted(
            suspicious_by_author.values(),
            key=lambda x: x['total_engagement'],
            reverse=True
        )[:10]  # Top 10 suspects
        
        logger.info(f"✅ {len(activists_list)} activistes connus détectés, "
                   f"{len(suspicious_list)} comptes suspects identifiés")
        
        return {
            'known_activists': activists_list,
            'suspicious_accounts': suspicious_list,
            'total_activists': len(activists_list),
            'total_suspicious': len(suspicious_list)
        }
    
    async def _generate_positive_section(self, positive_contents: List[Dict]) -> Dict:
        """Générer la section des contenus positifs avec analyse stratégique"""
        
        if not positive_contents:
            return {
                'count': 0,
                'synthesis': "Aucun contenu positif identifié durant cette période. "
                            "Cela représente une opportunité pour renforcer la communication positive.",
                'key_messages': [],
                'top_contents': [],
                'recommendations': [
                    "Développer une stratégie de contenu positif proactive",
                    "Identifier et engager des ambassadeurs de marque",
                    "Créer des récits positifs autour des réalisations"
                ]
            }
        
        logger.info(f"📝 Génération section positive ({len(positive_contents)} contenus)...")
        
        # Synthèse narrative avec IA
        synthesis = await self._generate_narrative_synthesis(
            positive_contents,
            "Ces contenus positifs mettent en avant des aspects favorables. "
            "Identifie les messages clés, les sources principales et l'impact potentiel."
        )
        
        # Extraire les messages clés
        key_messages = self._extract_key_messages(positive_contents)
        
        # Top contenus par engagement
        top_contents = sorted(
            positive_contents,
            key=lambda x: x.get('engagement_score', 0),
            reverse=True
        )[:5]
        
        # Recommandations stratégiques
        recommendations = self._generate_positive_recommendations(positive_contents)
        
        return {
            'count': len(positive_contents),
            'synthesis': synthesis,
            'key_messages': key_messages,
            'top_contents': top_contents,
            'recommendations': recommendations
        }
    
    async def _generate_negative_section(self, negative_contents: List[Dict]) -> Dict:
        """Générer la section des contenus négatifs avec analyse des risques"""
        
        if not negative_contents:
            return {
                'count': 0,
                'synthesis': "Aucun contenu négatif majeur détecté. La période est relativement calme. "
                            "Maintenir la vigilance sur les signaux faibles.",
                'risk_level': 'FAIBLE',
                'key_criticisms': [],
                'top_contents': [],
                'recommendations': [
                    "Maintenir le monitoring actif",
                    "Préparer des éléments de langage préventifs"
                ]
            }
        
        logger.info(f"⚠️ Génération section négative ({len(negative_contents)} contenus)...")
        
        # Synthèse narrative
        synthesis = await self._generate_narrative_synthesis(
            negative_contents,
            "Ces contenus négatifs critiquent ou remettent en question l'institution. "
            "Identifie les principales critiques, les arguments récurrents et le niveau de risque."
        )
        
        # Évaluer le niveau de risque global
        risk_level = self._assess_risk_level(negative_contents)
        
        # Extraire les critiques principales
        key_criticisms = self._extract_key_criticisms(negative_contents)
        
        # Top contenus critiques
        top_contents = sorted(
            negative_contents,
            key=lambda x: x.get('engagement_score', 0) * (2 if x.get('strategic_impact') == 'critique' else 1),
            reverse=True
        )[:5]
        
        # Recommandations contre-information
        recommendations = self._generate_counter_recommendations(negative_contents, risk_level)
        
        return {
            'count': len(negative_contents),
            'synthesis': synthesis,
            'risk_level': risk_level,
            'key_criticisms': key_criticisms,
            'top_contents': top_contents,
            'recommendations': recommendations
        }
    
    async def _generate_neutral_section(self, neutral_contents: List[Dict]) -> Dict:
        """Générer la section des contenus neutres avec opportunités"""
        
        if not neutral_contents:
            return {
                'count': 0,
                'synthesis': "Aucun contenu neutre identifié.",
                'opportunities': [],
                'top_contents': []
            }
        
        logger.info(f"📄 Génération section neutre ({len(neutral_contents)} contenus)...")
        
        # Synthèse
        synthesis = await self._generate_narrative_synthesis(
            neutral_contents,
            "Ces contenus neutres représentent une opportunité de positionnement. "
            "Identifie les thématiques abordées et comment orienter la perception."
        )
        
        # Identifier les opportunités
        opportunities = [
            f"{len(neutral_contents)} contenus neutres représentent des audiences réceptives",
            "Opportunité d'orienter la perception avec une communication proactive",
            "Potentiel d'engagement avec des créateurs de contenu neutres"
        ]
        
        # Top contenus neutres par engagement
        top_contents = sorted(
            neutral_contents,
            key=lambda x: x.get('engagement_score', 0),
            reverse=True
        )[:3]
        
        return {
            'count': len(neutral_contents),
            'synthesis': synthesis,
            'opportunities': opportunities,
            'top_contents': top_contents
        }
    
    async def _generate_strategic_synthesis(
        self,
        classified_contents: Dict,
        activists_analysis: Dict,
        keyword_ids: List[int],
        days: int
    ) -> Dict:
        """Générer la synthèse générale stratégique"""
        
        logger.info("🎯 Génération synthèse stratégique générale...")
        
        total = sum(len(contents) for contents in classified_contents.values())
        
        # Calculer les ratios
        positive_count = len(classified_contents['positive']) + len(classified_contents['very_positive'])
        negative_count = len(classified_contents['negative']) + len(classified_contents['very_negative'])
        neutral_count = len(classified_contents['neutral'])
        
        positive_ratio = positive_count / total if total > 0 else 0
        negative_ratio = negative_count / total if total > 0 else 0
        neutral_ratio = neutral_count / total if total > 0 else 0
        
        # Déterminer la tonalité générale
        if positive_ratio > 0.6:
            overall_tone = "majoritairement positive"
            emoji = "😊"
            strategic_assessment = "favorable"
        elif negative_ratio > 0.5:
            overall_tone = "majoritairement négative"
            emoji = "😟"
            strategic_assessment = "préoccupante"
        elif abs(positive_ratio - negative_ratio) < 0.1:
            overall_tone = "très polarisée"
            emoji = "⚖️"
            strategic_assessment = "instable"
        else:
            overall_tone = "mitigée"
            emoji = "😐"
            strategic_assessment = "neutre"
        
        # Synthèse narrative globale avec IA
        synthesis_text = await self._generate_global_synthesis(
            classified_contents, activists_analysis, days, overall_tone
        )
        
        # Points clés stratégiques
        strategic_points = self._identify_strategic_points(
            classified_contents, activists_analysis
        )
        
        # Recommandations prioritaires
        priority_recommendations = self._generate_priority_recommendations(
            classified_contents, activists_analysis, strategic_assessment
        )
        
        return {
            'total_contents': total,
            'period_days': days,
            'overall_tone': overall_tone,
            'emoji': emoji,
            'strategic_assessment': strategic_assessment,
            'breakdown': {
                'positive': positive_count,
                'negative': negative_count,
                'neutral': neutral_count,
                'positive_ratio': round(positive_ratio * 100, 1),
                'negative_ratio': round(negative_ratio * 100, 1),
                'neutral_ratio': round(neutral_ratio * 100, 1)
            },
            'synthesis_text': synthesis_text,
            'strategic_points': strategic_points,
            'priority_recommendations': priority_recommendations
        }
    
    def _generate_activists_section(self, activists_analysis: Dict) -> Dict:
        """Générer la section des activistes et comptes sensibles"""
        
        logger.info("🚨 Génération section activistes...")
        
        known = activists_analysis['known_activists']
        suspicious = activists_analysis['suspicious_accounts']
        
        # Synthèse
        if not known and not suspicious:
            synthesis = "Aucun activiste connu ou compte suspect détecté durant cette période. " \
                       "Maintenir la surveillance sur les comptes émergents."
        else:
            synthesis = f"Détection de {len(known)} activiste(s) connu(s) et {len(suspicious)} " \
                       f"compte(s) suspect(s) durant la période analysée. " \
                       f"Ces acteurs nécessitent une attention particulière pour la contre-information."
        
        # Activistes prioritaires (fort engagement + contenu négatif)
        priority_activists = []
        for activist in known:
            neg_ratio = sum(1 for t in activist['tones'] if t in ['negative', 'very_negative']) / len(activist['tones'])
            if neg_ratio > 0.5 and activist['total_engagement'] > 1000:
                priority_activists.append({
                    'author': activist['author'],
                    'total_engagement': activist['total_engagement'],
                    'total_contents': activist['total_contents'],
                    'negative_ratio': round(neg_ratio * 100, 1),
                    'alert_level': 'CRITIQUE' if neg_ratio > 0.8 else 'ÉLEVÉ'
                })
        
        return {
            'synthesis': synthesis,
            'known_activists': known,
            'suspicious_accounts': suspicious,
            'priority_activists': sorted(priority_activists, key=lambda x: x['total_engagement'], reverse=True),
            'total_known': len(known),
            'total_suspicious': len(suspicious),
            'total_priority': len(priority_activists)
        }
    
    # Méthodes utilitaires
    
    async def _generate_narrative_synthesis(self, contents: List[Dict], context_prompt: str) -> str:
        """Générer une synthèse narrative avec IA"""
        
        if not self.llm_service.is_available() or not contents:
            return self._fallback_narrative_synthesis(contents, context_prompt)
        
        # Préparer un échantillon de contenus
        sample_texts = []
        for content in contents[:10]:
            sample_texts.append(f"• {content['title']}: {content.get('content', '')[:200]}")
        
        combined_text = '\n'.join(sample_texts)
        
        prompt = f"""
Tu es un analyste stratégique senior en communication gouvernementale.

Contexte: {context_prompt}

Voici {len(contents)} contenus à analyser:

{combined_text}

Rédige une synthèse narrative de 3-4 paragraphes qui:
1. Résume les points saillants de manière factuelle
2. Identifie les messages dominants et leur impact
3. Propose une lecture stratégique pour la communication

Style: Professionnel, factuel, orienté décision. Pas de listes, que de la prose.
"""
        
        try:
            context_data = {'mentions': contents[:5], 'keywords': [], 'period_days': 1}
            response = await self.llm_service.analyze_with_local_llm(prompt, context_data)
            return response.strip()
        except Exception as e:
            logger.warning(f"Erreur synthèse IA: {e}")
            return self._fallback_narrative_synthesis(contents, context_prompt)
    
    def _fallback_narrative_synthesis(self, contents: List[Dict], context_prompt: str) -> str:
        """Synthèse narrative fallback"""
        
        if not contents:
            return "Aucun contenu dans cette catégorie."
        
        sources = list(set(c['source'] for c in contents))
        top_engagement = sorted(contents, key=lambda x: x.get('engagement_score', 0), reverse=True)[:3]
        
        synthesis = f"Durant la période analysée, {len(contents)} contenus ont été identifiés dans cette catégorie, "
        synthesis += f"principalement sur {', '.join(sources[:3])}. "
        
        if top_engagement:
            synthesis += f"Les contenus les plus engageants proviennent de {', '.join([c['author'] for c in top_engagement[:2]])}. "
        
        return synthesis
    
    def _extract_key_messages(self, contents: List[Dict]) -> List[str]:
        """Extraire les messages clés"""
        
        # Analyser les titres pour identifier les thèmes
        all_titles = ' '.join([c['title'] for c in contents])
        words = all_titles.lower().split()
        word_counts = Counter([w for w in words if len(w) > 5])
        
        top_words = [word for word, count in word_counts.most_common(5) if count > 1]
        
        messages = [f"Mention récurrente de: {word}" for word in top_words[:3]]
        
        if len(contents) > 10:
            messages.append(f"Volume significatif de {len(contents)} contenus")
        
        return messages[:5]
    
    def _extract_key_criticisms(self, contents: List[Dict]) -> List[str]:
        """Extraire les principales critiques"""
        
        criticisms = []
        
        # Mots-clés critiques fréquents
        critical_keywords = ['corruption', 'fraude', 'dictature', 'répression', 'échec', 'scandale']
        
        all_text = ' '.join([c['title'] + ' ' + c.get('content', '') for c in contents]).lower()
        
        for keyword in critical_keywords:
            if keyword in all_text:
                criticisms.append(f"Accusations de {keyword}")
        
        # Analyser les titres
        titles = [c['title'] for c in contents]
        if len(titles) > 3:
            criticisms.append(f"Thématique critique récurrente dans {len(titles)} contenus")
        
        return criticisms[:5]
    
    def _assess_risk_level(self, negative_contents: List[Dict]) -> str:
        """Évaluer le niveau de risque"""
        
        if not negative_contents:
            return 'FAIBLE'
        
        # Compter les contenus critiques
        critical_count = sum(1 for c in negative_contents if c.get('strategic_impact') == 'critique')
        
        # Engagement total
        total_engagement = sum(c.get('engagement_score', 0) for c in negative_contents)
        
        # Évaluation
        if critical_count > 3 or total_engagement > 10000:
            return 'ÉLEVÉ'
        elif critical_count > 1 or total_engagement > 5000:
            return 'MODÉRÉ'
        else:
            return 'FAIBLE'
    
    def _generate_positive_recommendations(self, contents: List[Dict]) -> List[str]:
        """Générer des recommandations pour contenus positifs"""
        
        recommendations = []
        
        if len(contents) > 5:
            recommendations.append(
                "Amplifier ces messages positifs via les canaux officiels et partenaires"
            )
        
        recommendations.append(
            "Identifier et engager les créateurs de contenu positif comme ambassadeurs"
        )
        
        recommendations.append(
            "Capitaliser sur ces narratives favorables dans la communication externe"
        )
        
        return recommendations
    
    def _generate_counter_recommendations(self, contents: List[Dict], risk_level: str) -> List[str]:
        """Générer des recommandations de contre-information"""
        
        recommendations = []
        
        if risk_level == 'ÉLEVÉ':
            recommendations.extend([
                "Activation immédiate de la cellule de contre-information",
                "Préparation d'éléments de langage et de réponses factuelles",
                "Engagement direct avec les sources critiques pour clarification",
                "Monitoring renforcé H24 des développements"
            ])
        elif risk_level == 'MODÉRÉ':
            recommendations.extend([
                "Préparer des éléments de réponse préventifs",
                "Surveiller l'évolution du narratif dans les 48h",
                "Engagement sélectif avec les acteurs clés"
            ])
        else:
            recommendations.extend([
                "Maintenir la surveillance active",
                "Documenter les arguments pour référence future"
            ])
        
        return recommendations
    
    async def _generate_global_synthesis(
        self, classified_contents: Dict, activists_analysis: Dict, days: int, overall_tone: str
    ) -> str:
        """Générer la synthèse globale narrative"""
        
        total = sum(len(contents) for contents in classified_contents.values())
        
        if not self.llm_service.is_available():
            return self._fallback_global_synthesis(total, days, overall_tone)
        
        # Préparer le contexte pour l'IA
        prompt = f"""
Tu es le directeur de la communication qui rédige un brief stratégique pour le directeur général.

DONNÉES D'ANALYSE:
- Période: {days} jours
- Total contenus: {total}
- Tonalité: {overall_tone}
- Activistes détectés: {activists_analysis['total_activists']}
- Comptes suspects: {activists_analysis['total_suspicious']}

Rédige une synthèse exécutive de 4-5 paragraphes qui:
1. Dresse le tableau général de la situation
2. Identifie les enjeux stratégiques majeurs
3. Évalue les risques et opportunités
4. Propose une orientation pour l'action

Style: Direct, factuel, orienté décision. Comme un brief au DG.
Ton: Professionnel mais accessible.
"""
        
        try:
            context_data = {'mentions': [], 'keywords': [], 'period_days': days}
            response = await self.llm_service.analyze_with_local_llm(prompt, context_data)
            return response.strip()
        except Exception as e:
            logger.warning(f"Erreur synthèse globale IA: {e}")
            return self._fallback_global_synthesis(total, days, overall_tone)
    
    def _fallback_global_synthesis(self, total: int, days: int, overall_tone: str) -> str:
        """Synthèse globale fallback"""
        
        synthesis = f"Sur les {days} derniers jours, {total} contenus ont été analysés. "
        synthesis += f"La tonalité générale est {overall_tone}. "
        synthesis += "Une surveillance continue est recommandée pour anticiper les évolutions du narratif."
        
        return synthesis
    
    def _identify_strategic_points(self, classified_contents: Dict, activists_analysis: Dict) -> List[str]:
        """Identifier les points stratégiques clés"""
        
        points = []
        
        # Points basés sur les ratios
        negative_count = len(classified_contents['negative']) + len(classified_contents['very_negative'])
        total = sum(len(contents) for contents in classified_contents.values())
        
        if negative_count > total * 0.5:
            points.append(
                "Dominance de contenus négatifs nécessitant une réponse communication active"
            )
        
        # Points basés sur les activistes
        if activists_analysis['total_activists'] > 0:
            points.append(
                f"{activists_analysis['total_activists']} activiste(s) connu(s) détecté(s) - "
                "surveillance renforcée requise"
            )
        
        # Opportunités
        neutral_count = len(classified_contents['neutral'])
        if neutral_count > total * 0.3:
            points.append(
                "Volume significatif de contenus neutres - opportunité de positionnement"
            )
        
        return points[:5]
    
    def _generate_priority_recommendations(
        self, classified_contents: Dict, activists_analysis: Dict, assessment: str
    ) -> List[Dict]:
        """Générer les recommandations prioritaires"""
        
        recommendations = []
        
        if assessment == 'préoccupante':
            recommendations.append({
                'priority': 'URGENT',
                'action': "Activation cellule de contre-information",
                'timeline': 'Immédiat (0-24h)'
            })
        
        if activists_analysis['total_activists'] > 0:
            recommendations.append({
                'priority': 'ÉLEVÉE',
                'action': f"Surveillance renforcée des {activists_analysis['total_activists']} activistes détectés",
                'timeline': 'Court terme (1-3 jours)'
            })
        
        recommendations.append({
            'priority': 'MOYENNE',
            'action': "Développer une stratégie de contenu proactive",
            'timeline': 'Moyen terme (1-2 semaines)'
        })
        
        return recommendations
    
    def _generate_statistics(self, mentions: List[Mention], classified_contents: Dict) -> Dict:
        """Générer les statistiques du rapport"""
        
        total = len(mentions)
        
        if total == 0:
            return {}
        
        # Distribution par source
        sources = Counter([m.source for m in mentions])
        
        # Engagement
        total_engagement = sum(m.engagement_score for m in mentions)
        avg_engagement = total_engagement / total
        
        return {
            'total_contents': total,
            'sources_distribution': dict(sources.most_common()),
            'total_engagement': total_engagement,
            'average_engagement': round(avg_engagement, 1),
            'sentiment_breakdown': {
                'very_positive': len(classified_contents['very_positive']),
                'positive': len(classified_contents['positive']),
                'neutral': len(classified_contents['neutral']),
                'negative': len(classified_contents['negative']),
                'very_negative': len(classified_contents['very_negative'])
            }
        }
    
    def _get_keyword_name(self, keyword_id: int) -> str:
        """Obtenir le nom d'un mot-clé"""
        keyword = self.db.query(Keyword).filter(Keyword.id == keyword_id).first()
        return keyword.keyword if keyword else f"Mot-clé #{keyword_id}"
    
    def _generate_empty_report(self, keyword_ids: List[int], days: int, title: str) -> Dict:
        """Générer un rapport vide"""
        return {
            'metadata': {
                'title': title,
                'keywords': [self._get_keyword_name(kid) for kid in keyword_ids],
                'period_days': days,
                'generated_at': datetime.utcnow(),
                'total_contents': 0
            },
            'error': 'Aucune donnée disponible pour cette période'
        }