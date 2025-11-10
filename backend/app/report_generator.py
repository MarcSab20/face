"""
Générateur de Rapports Exécutifs Intelligents
Version Dirigeant - Synthèse Narrative et Actionnable
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from collections import Counter
import json
import asyncio
from io import BytesIO

from app.ai_service import IntelligentAnalysisAgent, AnalysisContext, SovereignLLMService
from app.models import Keyword, Mention

logger = logging.getLogger(__name__)


class IntelligentReportGenerator:
    """Générateur de rapports exécutifs pour décideurs"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_agent = IntelligentAnalysisAgent()
        self.llm_service = SovereignLLMService()
    
    async def generate_executive_report(
        self,
        keyword_ids: List[int],
        days: int = 30,
        report_title: str = "",
        format_type: str = "pdf"
    ) -> Dict:
        """Générer un rapport exécutif narratif"""
        
        logger.info(f"🎯 Génération rapport exécutif: {len(keyword_ids)} mots-clés, {days} jours")
        
        # 1. Récupérer et lire TOUS les contenus
        all_contents = await self._read_all_contents(keyword_ids, days)
        
        # 2. Classifier les contenus par sentiment
        classified_contents = await self._classify_contents_by_sentiment(all_contents)
        
        # 3. Générer des résumés intelligents par catégorie
        summaries = await self._generate_intelligent_summaries(classified_contents)
        
        # 4. Créer la synthèse exécutive narrative
        executive_synthesis = await self._create_executive_synthesis(
            summaries, classified_contents, keyword_ids, days
        )
        
        # 5. Identifier les messages clés et tendances
        key_messages = await self._extract_key_messages(all_contents, classified_contents)
        
        # 6. Générer les recommandations stratégiques
        strategic_recommendations = await self._generate_strategic_recommendations(
            executive_synthesis, key_messages, classified_contents
        )
        
        # 7. Compiler le rapport final
        report_data = {
            'metadata': {
                'title': report_title or "Rapport Exécutif - Analyse de Réputation",
                'keywords': [self._get_keyword_name(kid) for kid in keyword_ids],
                'period_days': days,
                'generated_at': datetime.utcnow(),
                'format': format_type,
                'total_contents_analyzed': len(all_contents)
            },
            'executive_synthesis': executive_synthesis,
            'content_summaries': summaries,
            'key_messages': key_messages,
            'strategic_recommendations': strategic_recommendations,
            'classified_contents': classified_contents,
            'statistics': self._generate_executive_statistics(all_contents, classified_contents)
        }
        
        logger.info("✅ Rapport exécutif généré avec succès")
        return report_data
    
    async def _read_all_contents(self, keyword_ids: List[int], days: int) -> List[Dict]:
        """Lire TOUS les contenus complets des mentions"""
        
        since_date = datetime.utcnow() - timedelta(days=days)
        
        mentions = self.db.query(Mention).filter(
            Mention.keyword_id.in_(keyword_ids),
            Mention.published_at >= since_date
        ).order_by(desc(Mention.published_at)).all()
        
        logger.info(f"📖 Lecture de {len(mentions)} contenus complets...")
        
        all_contents = []
        
        for mention in mentions:
            # Construire le texte complet
            full_text = f"{mention.title}\n\n{mention.content}"
            
            content_data = {
                'id': mention.id,
                'title': mention.title,
                'full_content': mention.content,
                'full_text': full_text,
                'author': mention.author,
                'source': mention.source,
                'source_url': mention.source_url,
                'published_at': mention.published_at.isoformat() if mention.published_at else None,
                'engagement_score': mention.engagement_score,
                'original_sentiment': mention.sentiment,
                'metadata': json.loads(mention.mention_metadata) if mention.mention_metadata else {}
            }
            
            all_contents.append(content_data)
        
        logger.info(f"✅ {len(all_contents)} contenus lus")
        return all_contents
    
    async def _classify_contents_by_sentiment(self, contents: List[Dict]) -> Dict[str, List[Dict]]:
        """Classifier intelligemment les contenus par sentiment réel"""
        
        logger.info("🤖 Classification IA des contenus par sentiment...")
        
        classified = {
            'very_positive': [],
            'positive': [],
            'neutral': [],
            'negative': [],
            'very_negative': []
        }
        
        for content in contents:
            # Analyser le sentiment réel avec l'IA
            sentiment_analysis = await self._analyze_content_sentiment(content['full_text'])
            
            content['ai_sentiment'] = sentiment_analysis['category']
            content['ai_sentiment_score'] = sentiment_analysis['score']
            content['ai_sentiment_reasoning'] = sentiment_analysis['reasoning']
            
            # Classer dans la bonne catégorie
            classified[sentiment_analysis['category']].append(content)
        
        logger.info(f"✅ Classification terminée: {len(classified['very_positive'])} très positifs, "
                   f"{len(classified['positive'])} positifs, {len(classified['neutral'])} neutres, "
                   f"{len(classified['negative'])} négatifs, {len(classified['very_negative'])} très négatifs")
        
        return classified
    
    async def _analyze_content_sentiment(self, text: str) -> Dict:
        """Analyser le sentiment réel d'un contenu avec l'IA"""
        
        if not self.llm_service.is_available():
            # Fallback simple
            return self._simple_sentiment_analysis(text)
        
        prompt = f"""
Analyse le sentiment de ce contenu et évalue s'il est positif, négatif ou neutre 
pour l'image d'une organisation/personnalité publique.

CONTENU À ANALYSER:
{text[:2000]}

Réponds UNIQUEMENT avec ce format JSON:
{{
    "category": "very_positive" | "positive" | "neutral" | "negative" | "very_negative",
    "score": <-10 à +10>,
    "reasoning": "<explication courte en 1-2 phrases>"
}}

Sois précis et objectif. Base-toi sur le ton, les mots utilisés, et l'intention apparente.
"""
        
        try:
            context = {'mentions': [{'content': text}], 'keywords': [], 'period_days': 1}
            response = await self.llm_service.analyze_with_local_llm(prompt, context)
            
            # Parser la réponse JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result
            else:
                return self._simple_sentiment_analysis(text)
                
        except Exception as e:
            logger.warning(f"Erreur analyse sentiment IA: {e}")
            return self._simple_sentiment_analysis(text)
    
    def _simple_sentiment_analysis(self, text: str) -> Dict:
        """Analyse de sentiment simple (fallback)"""
        
        text_lower = text.lower()
        
        # Mots fortement positifs
        very_positive_words = ['excellent', 'extraordinaire', 'remarquable', 'brillant', 'génial', 
                               'succès', 'victoire', 'triomphe', 'félicitations', 'innovation']
        
        # Mots positifs
        positive_words = ['bon', 'bien', 'positif', 'amélioration', 'progrès', 'efficace',
                         'satisfaisant', 'apprécié', 'soutien', 'reconnaissance']
        
        # Mots négatifs
        negative_words = ['mauvais', 'problème', 'échec', 'erreur', 'difficulté', 'critique',
                         'insuffisant', 'décevant', 'préoccupant', 'insatisfaction']
        
        # Mots fortement négatifs
        very_negative_words = ['scandale', 'catastrophe', 'désastre', 'corruption', 'fraude',
                              'crise', 'effondrement', 'inacceptable', 'honte', 'tragédie']
        
        # Compter les occurrences
        very_pos_count = sum(1 for word in very_positive_words if word in text_lower)
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        very_neg_count = sum(1 for word in very_negative_words if word in text_lower)
        
        # Calculer le score
        score = (very_pos_count * 2 + pos_count) - (neg_count + very_neg_count * 2)
        
        # Déterminer la catégorie
        if score >= 3:
            category = 'very_positive'
            reasoning = "Ton très positif avec de nombreux termes élogieux"
        elif score >= 1:
            category = 'positive'
            reasoning = "Ton globalement positif"
        elif score <= -3:
            category = 'very_negative'
            reasoning = "Ton très négatif avec termes critiques"
        elif score <= -1:
            category = 'negative'
            reasoning = "Ton globalement négatif"
        else:
            category = 'neutral'
            reasoning = "Ton neutre et factuel"
        
        return {
            'category': category,
            'score': score,
            'reasoning': reasoning
        }
    
    async def _generate_intelligent_summaries(self, classified_contents: Dict[str, List[Dict]]) -> Dict:
        """Générer des résumés intelligents pour chaque catégorie"""
        
        logger.info("📝 Génération des résumés intelligents par catégorie...")
        
        summaries = {}
        
        for category, contents in classified_contents.items():
            if not contents:
                summaries[category] = {
                    'count': 0,
                    'summary': "Aucun contenu dans cette catégorie.",
                    'key_themes': [],
                    'representative_excerpts': []
                }
                continue
            
            # Générer un résumé IA de cette catégorie
            summary_text = await self._summarize_category(category, contents)
            
            # Extraire les thèmes clés
            key_themes = self._extract_key_themes(contents)
            
            # Sélectionner des extraits représentatifs
            excerpts = self._select_representative_excerpts(contents[:5])  # Top 5
            
            summaries[category] = {
                'count': len(contents),
                'summary': summary_text,
                'key_themes': key_themes,
                'representative_excerpts': excerpts
            }
        
        return summaries
    
    async def _summarize_category(self, category: str, contents: List[Dict]) -> str:
        """Résumer intelligemment une catégorie de contenus"""
        
        if not self.llm_service.is_available():
            return self._simple_category_summary(category, contents)
        
        # Préparer le texte à résumer (limiter la taille)
        texts_sample = []
        for content in contents[:10]:  # Max 10 contenus
            texts_sample.append(f"• {content['title']}: {content['full_content'][:300]}")
        
        combined_text = '\n'.join(texts_sample)
        
        category_labels = {
            'very_positive': 'TRÈS POSITIFS',
            'positive': 'POSITIFS',
            'neutral': 'NEUTRES',
            'negative': 'NÉGATIFS',
            'very_negative': 'TRÈS NÉGATIFS'
        }
        
        prompt = f"""
Tu es un analyste senior qui rédige un résumé exécutif pour un directeur général.

Voici {len(contents)} contenus classés comme {category_labels[category]}:

{combined_text}

Rédige un paragraphe de synthèse (3-5 phrases) qui explique:
1. Ce que disent ces contenus (les faits, pas les chiffres)
2. Les messages principaux qui ressortent
3. L'impact potentiel sur la réputation

Sois factuel, concis et orienté décision. Évite le jargon technique.
Écris à la 3e personne, ton professionnel.
"""
        
        try:
            context = {'mentions': contents[:5], 'keywords': [], 'period_days': 1}
            summary = await self.llm_service.analyze_with_local_llm(prompt, context)
            return summary.strip()
        except Exception as e:
            logger.warning(f"Erreur résumé catégorie: {e}")
            return self._simple_category_summary(category, contents)
    
    def _simple_category_summary(self, category: str, contents: List[Dict]) -> str:
        """Résumé simple d'une catégorie (fallback)"""
        
        count = len(contents)
        sources = list(set(c['source'] for c in contents))
        
        category_descriptions = {
            'very_positive': f"{count} contenus très positifs détectés, principalement sur {', '.join(sources[:3])}. "
                            f"Ces mentions mettent en avant des aspects très favorables et utilisent un ton élogieux.",
            
            'positive': f"{count} contenus positifs identifiés sur {', '.join(sources[:3])}. "
                       f"Ces mentions présentent une image généralement favorable avec des aspects appréciés.",
            
            'neutral': f"{count} contenus neutres recensés, essentiellement sur {', '.join(sources[:3])}. "
                      f"Ces mentions sont factuelles sans orientation positive ou négative marquée.",
            
            'negative': f"{count} contenus négatifs repérés sur {', '.join(sources[:3])}. "
                       f"Ces mentions expriment des critiques ou soulèvent des problèmes préoccupants.",
            
            'very_negative': f"{count} contenus très négatifs détectés sur {', '.join(sources[:3])}. "
                            f"Ces mentions sont fortement critiques et peuvent avoir un impact significatif sur la réputation."
        }
        
        return category_descriptions.get(category, f"{count} contenus dans cette catégorie.")
    
    def _extract_key_themes(self, contents: List[Dict]) -> List[str]:
        """Extraire les thèmes clés des contenus"""
        
        # Mots-clés fréquents (approche simple)
        all_words = []
        
        for content in contents:
            words = content['full_text'].lower().split()
            # Filtrer les mots courts et communs
            filtered_words = [
                w for w in words 
                if len(w) > 4 and w not in ['avoir', 'être', 'faire', 'dire', 'pouvoir', 'devoir']
            ]
            all_words.extend(filtered_words)
        
        # Compter les plus fréquents
        word_counts = Counter(all_words)
        top_words = [word for word, count in word_counts.most_common(10) if count > 1]
        
        return top_words[:5]  # Top 5 thèmes
    
    def _select_representative_excerpts(self, contents: List[Dict]) -> List[Dict]:
        """Sélectionner des extraits représentatifs"""
        
        excerpts = []
        
        for content in contents[:3]:  # Max 3 extraits
            # Prendre un extrait significatif du contenu
            excerpt_text = content['full_content'][:250] + "..."
            
            excerpts.append({
                'title': content['title'],
                'excerpt': excerpt_text,
                'source': content['source'],
                'url': content['source_url'],
                'date': content['published_at']
            })
        
        return excerpts
    
    async def _create_executive_synthesis(
        self, 
        summaries: Dict, 
        classified_contents: Dict, 
        keyword_ids: List[int], 
        days: int
    ) -> Dict:
        """Créer la synthèse exécutive narrative"""
        
        logger.info("🎯 Création de la synthèse exécutive...")
        
        total_contents = sum(len(contents) for contents in classified_contents.values())
        
        # Compter par catégorie
        very_pos = len(classified_contents['very_positive'])
        pos = len(classified_contents['positive'])
        neu = len(classified_contents['neutral'])
        neg = len(classified_contents['negative'])
        very_neg = len(classified_contents['very_negative'])
        
        # Déterminer la tonalité générale
        positive_total = very_pos + pos
        negative_total = neg + very_neg
        
        if positive_total > negative_total * 2:
            overall_tone = "majoritairement positive"
            sentiment_emoji = "😊"
        elif negative_total > positive_total * 2:
            overall_tone = "majoritairement négative"
            sentiment_emoji = "😟"
        elif positive_total > negative_total:
            overall_tone = "légèrement positive"
            sentiment_emoji = "🙂"
        elif negative_total > positive_total:
            overall_tone = "légèrement négative"
            sentiment_emoji = "😐"
        else:
            overall_tone = "neutre et équilibrée"
            sentiment_emoji = "😶"
        
        # Générer le résumé exécutif narratif avec l'IA
        synthesis_text = await self._generate_narrative_synthesis(
            summaries, overall_tone, total_contents, days
        )
        
        return {
            'total_contents_analyzed': total_contents,
            'period_days': days,
            'overall_tone': overall_tone,
            'sentiment_emoji': sentiment_emoji,
            'breakdown': {
                'very_positive': very_pos,
                'positive': pos,
                'neutral': neu,
                'negative': neg,
                'very_negative': very_neg
            },
            'synthesis_text': synthesis_text,
            'critical_points': self._identify_critical_points(classified_contents),
            'opportunities': self._identify_opportunities(classified_contents)
        }
    
    async def _generate_narrative_synthesis(
        self, 
        summaries: Dict, 
        overall_tone: str, 
        total_contents: int, 
        days: int
    ) -> str:
        """Générer une synthèse narrative avec l'IA"""
        
        if not self.llm_service.is_available():
            return self._simple_narrative_synthesis(summaries, overall_tone, total_contents, days)
        
        # Préparer le contexte pour l'IA
        summaries_text = []
        for category, data in summaries.items():
            if data['count'] > 0:
                summaries_text.append(f"{category.upper().replace('_', ' ')}: {data['summary']}")
        
        combined_summaries = '\n\n'.join(summaries_text)
        
        prompt = f"""
Tu es un directeur de la communication qui rédige une synthèse exécutive pour le PDG.

DONNÉES D'ANALYSE ({total_contents} contenus sur {days} jours):

{combined_summaries}

Tonalité générale: {overall_tone}

Rédige une synthèse narrative de 2-3 paragraphes qui:
1. RÉSUME l'essentiel de ce qui se dit (pas de statistiques, juste les faits marquants)
2. EXPLIQUE ce que cela signifie pour l'organisation
3. INDIQUE les points d'attention prioritaires

Style: Direct, factuel, orienté action. Comme dans un brief de 5 minutes au PDG.
Ton: Professionnel mais accessible. Évite le jargon.
Perspective: "Voici ce que nous observons et ce qu'il faut retenir"
"""
        
        try:
            context = {'mentions': [], 'keywords': [], 'period_days': days}
            synthesis = await self.llm_service.analyze_with_local_llm(prompt, context)
            return synthesis.strip()
        except Exception as e:
            logger.warning(f"Erreur génération synthèse narrative: {e}")
            return self._simple_narrative_synthesis(summaries, overall_tone, total_contents, days)
    
    def _simple_narrative_synthesis(
        self, 
        summaries: Dict, 
        overall_tone: str, 
        total_contents: int, 
        days: int
    ) -> str:
        """Synthèse narrative simple (fallback)"""
        
        synthesis_parts = []
        
        # Introduction
        synthesis_parts.append(
            f"Sur les {days} derniers jours, nous avons analysé {total_contents} contenus. "
            f"La tonalité générale est {overall_tone}."
        )
        
        # Points saillants par catégorie
        priority_categories = ['very_negative', 'very_positive', 'negative', 'positive']
        
        for category in priority_categories:
            data = summaries.get(category, {})
            if data.get('count', 0) > 0:
                synthesis_parts.append(data['summary'])
        
        # Contexte neutre si significatif
        if summaries.get('neutral', {}).get('count', 0) > total_contents * 0.4:
            synthesis_parts.append(summaries['neutral']['summary'])
        
        return ' '.join(synthesis_parts)
    
    def _identify_critical_points(self, classified_contents: Dict) -> List[str]:
        """Identifier les points critiques nécessitant attention"""
        
        critical_points = []
        
        # Points très négatifs
        very_neg_count = len(classified_contents['very_negative'])
        if very_neg_count > 0:
            critical_points.append(
                f"🚨 {very_neg_count} contenu(s) très négatif(s) identifié(s) - "
                f"Risque réputationnel élevé nécessitant une attention immédiate"
            )
        
        # Points négatifs nombreux
        neg_count = len(classified_contents['negative'])
        if neg_count > 5:
            critical_points.append(
                f"⚠️ {neg_count} contenus négatifs détectés - "
                f"Tendance défavorable à surveiller de près"
            )
        
        # Manque de contenu positif
        pos_total = len(classified_contents['positive']) + len(classified_contents['very_positive'])
        total = sum(len(contents) for contents in classified_contents.values())
        
        if pos_total < total * 0.2:  # Moins de 20% positif
            critical_points.append(
                f"📉 Faible présence de contenus positifs ({pos_total}/{total}) - "
                f"Opportunité de renforcer la communication positive"
            )
        
        return critical_points[:5]  # Top 5 points critiques
    
    def _identify_opportunities(self, classified_contents: Dict) -> List[str]:
        """Identifier les opportunités"""
        
        opportunities = []
        
        # Contenus très positifs
        very_pos_count = len(classified_contents['very_positive'])
        if very_pos_count > 0:
            opportunities.append(
                f"✨ {very_pos_count} contenu(s) très positif(s) - "
                f"Amplifier ces messages favorables via la communication"
            )
        
        # Forte proportion de contenus positifs
        pos_total = len(classified_contents['positive']) + len(classified_contents['very_positive'])
        total = sum(len(contents) for contents in classified_contents.values())
        
        if pos_total > total * 0.5:  # Plus de 50% positif
            opportunities.append(
                f"🎯 Majorité de contenus positifs ({pos_total}/{total}) - "
                f"Momentum favorable à capitaliser"
            )
        
        # Beaucoup de contenu neutre = opportunité de positionnement
        neu_count = len(classified_contents['neutral'])
        if neu_count > total * 0.4:  # Plus de 40% neutre
            opportunities.append(
                f"💡 {neu_count} contenus neutres - "
                f"Opportunité d'orienter la perception avec une communication proactive"
            )
        
        return opportunities[:3]  # Top 3 opportunités
    
    async def _extract_key_messages(
        self, 
        all_contents: List[Dict], 
        classified_contents: Dict
    ) -> Dict:
        """Extraire les messages clés de toutes les catégories"""
        
        logger.info("🔑 Extraction des messages clés...")
        
        key_messages = {
            'most_discussed_topics': self._identify_main_topics(all_contents),
            'emerging_narratives': self._identify_narratives(classified_contents),
            'influential_voices': self._identify_influential_voices(all_contents),
            'critical_claims': await self._extract_critical_claims(classified_contents)
        }
        
        return key_messages
    
    def _identify_main_topics(self, contents: List[Dict]) -> List[str]:
        """Identifier les sujets principaux discutés"""
        
        # Extraire les mots clés de tous les titres
        all_titles = ' '.join([c['title'] for c in contents])
        
        words = all_titles.lower().split()
        word_counts = Counter([w for w in words if len(w) > 5])
        
        top_topics = [word for word, count in word_counts.most_common(5)]
        
        return top_topics
    
    def _identify_narratives(self, classified_contents: Dict) -> List[Dict]:
        """Identifier les narratives émergentes"""
        
        narratives = []
        
        # Narrative négative dominante
        neg_contents = classified_contents['negative'] + classified_contents['very_negative']
        if neg_contents:
            neg_themes = self._extract_key_themes(neg_contents)
            if neg_themes:
                narratives.append({
                    'type': 'negative',
                    'description': f"Narrative critique autour de: {', '.join(neg_themes[:3])}",
                    'content_count': len(neg_contents)
                })
        
        # Narrative positive émergente
        pos_contents = classified_contents['positive'] + classified_contents['very_positive']
        if pos_contents:
            pos_themes = self._extract_key_themes(pos_contents)
            if pos_themes:
                narratives.append({
                    'type': 'positive',
                    'description': f"Narrative positive sur: {', '.join(pos_themes[:3])}",
                    'content_count': len(pos_contents)
                })
        
        return narratives
    
    def _identify_influential_voices(self, contents: List[Dict]) -> List[Dict]:
        """Identifier les voix influentes"""
        
        # Grouper par auteur et source
        author_stats = {}
        
        for content in contents:
            author = content['author']
            if author not in author_stats:
                author_stats[author] = {
                    'author': author,
                    'content_count': 0,
                    'total_engagement': 0,
                    'sources': set()
                }
            
            author_stats[author]['content_count'] += 1
            author_stats[author]['total_engagement'] += content['engagement_score']
            author_stats[author]['sources'].add(content['source'])
        
        # Trier par engagement
        sorted_authors = sorted(
            author_stats.values(), 
            key=lambda x: x['total_engagement'], 
            reverse=True
        )
        
        # Formater les top 5
        top_voices = []
        for author in sorted_authors[:5]:
            top_voices.append({
                'name': author['author'],
                'mentions': author['content_count'],
                'engagement': author['total_engagement'],
                'platforms': list(author['sources'])
            })
        
        return top_voices
    
    async def _extract_critical_claims(self, classified_contents: Dict) -> List[str]:
        """Extraire les affirmations critiques nécessitant réponse"""
        
        critical_contents = (
            classified_contents['very_negative'] + 
            classified_contents['negative']
        )
        
        if not critical_contents:
            return []
        
        # Extraire les phrases clés des contenus critiques
        critical_claims = []
        
        for content in critical_contents[:5]:  # Top 5 plus critiques
            # Prendre la première phrase significative
            sentences = content['full_content'].split('.')
            for sentence in sentences:
                if len(sentence.strip()) > 50:  # Phrases substantielles
                    critical_claims.append(sentence.strip() + ".")
                    break
        
        return critical_claims[:5]  # Max 5 affirmations critiques
    
    async def _generate_strategic_recommendations(
        self,
        executive_synthesis: Dict,
        key_messages: Dict,
        classified_contents: Dict
    ) -> List[Dict]:
        """Générer des recommandations stratégiques actionnables"""
        
        logger.info("🎯 Génération des recommandations stratégiques...")
        
        recommendations = []
        
        # Basé sur le niveau de criticité
        very_neg_count = len(classified_contents['very_negative'])
        neg_count = len(classified_contents['negative'])
        
        if very_neg_count > 0:
            recommendations.append({
                'priority': 'URGENT',
                'category': 'Gestion de crise',
                'action': "Mise en place d'une cellule de crise communication",
                'rationale': f"{very_neg_count} contenu(s) très négatif(s) identifié(s) avec risque réputationnel élevé",
                'timeline': 'Immédiat (0-24h)'
            })
        
        if neg_count > 5:
            recommendations.append({
                'priority': 'ÉLEVÉE',
                'category': 'Réponse proactive',
                'action': "Préparer des éléments de langage et réponses factuelles",
                'rationale': f"Volume significatif de contenus négatifs ({neg_count}) nécessitant clarifications",
                'timeline': 'Court terme (1-3 jours)'
            })
        
        # Opportunités positives
        pos_total = len(classified_contents['positive']) + len(classified_contents['very_positive'])
        if pos_total > 5:
            recommendations.append({
                'priority': 'MOYENNE',
                'category': 'Amplification',
                'action': "Amplifier les messages positifs via nos canaux officiels",
                'rationale': f"{pos_total} contenus positifs identifiés - momentum favorable à capitaliser",
                'timeline': 'Court terme (1-5 jours)'
            })
        
        # Contenu neutre = opportunité
        neu_count = len(classified_contents['neutral'])
        total = sum(len(contents) for contents in classified_contents.values())
        if neu_count > total * 0.3:
            recommendations.append({
                'priority': 'MOYENNE',
                'category': 'Positionnement',
                'action': "Développer une stratégie de contenu pour orienter la perception",
                'rationale': f"{neu_count} contenus neutres - audience réceptive à un positionnement clair",
                'timeline': 'Moyen terme (1-2 semaines)'
            })
        
        # Voix influentes
        top_voices = key_messages.get('influential_voices', [])
        if top_voices:
            recommendations.append({
                'priority': 'MOYENNE',
                'category': 'Relations influenceurs',
                'action': f"Engagement ciblé avec les {len(top_voices)} voix influentes identifiées",
                'rationale': "Construire ou renforcer les relations avec les acteurs clés du débat",
                'timeline': 'Moyen terme (2-4 semaines)'
            })
        
        return sorted(recommendations, key=lambda x: {'URGENT': 0, 'ÉLEVÉE': 1, 'MOYENNE': 2}.get(x['priority'], 3))
    
    def _generate_executive_statistics(
        self, 
        all_contents: List[Dict], 
        classified_contents: Dict
    ) -> Dict:
        """Générer des statistiques pour le rapport"""
        
        total = len(all_contents)
        
        if total == 0:
            return {}
        
        # Distribution par source
        sources = Counter([c['source'] for c in all_contents])
        
        # Engagement total
        total_engagement = sum(c['engagement_score'] for c in all_contents)
        avg_engagement = total_engagement / total if total > 0 else 0
        
        # Distribution temporelle (par jour)
        dates = [c['published_at'][:10] for c in all_contents if c['published_at']]
        temporal_dist = Counter(dates)
        
        return {
            'total_contents': total,
            'sources_distribution': dict(sources.most_common()),
            'total_engagement': total_engagement,
            'average_engagement': round(avg_engagement, 1),
            'temporal_distribution': dict(temporal_dist),
            'sentiment_breakdown': {
                'very_positive_pct': round(len(classified_contents['very_positive']) / total * 100, 1),
                'positive_pct': round(len(classified_contents['positive']) / total * 100, 1),
                'neutral_pct': round(len(classified_contents['neutral']) / total * 100, 1),
                'negative_pct': round(len(classified_contents['negative']) / total * 100, 1),
                'very_negative_pct': round(len(classified_contents['very_negative']) / total * 100, 1)
            }
        }
    
    def _get_keyword_name(self, keyword_id: int) -> str:
        """Obtenir le nom d'un mot-clé"""
        keyword = self.db.query(Keyword).filter(Keyword.id == keyword_id).first()
        return keyword.keyword if keyword else f"Mot-clé #{keyword_id}"
    
    async def generate_html_report(self, report_data: Dict) -> str:
        """Générer le rapport HTML exécutif"""
        
        # À implémenter avec un template HTML professionnel
        pass
    
    async def generate_pdf_report(self, report_data: Dict) -> bytes:
        """Générer le rapport PDF exécutif"""
        
        # À implémenter avec WeasyPrint
        pass