"""
Générateur de Rapports Stratégiques V2
Focus: Analyse thématique approfondie avec lecture réelle du contenu
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from collections import Counter, defaultdict
import json
import asyncio
import statistics
import re

from app.ai_service import SovereignLLMService, WebContentExtractor
from app.models import Keyword, Mention

logger = logging.getLogger(__name__)


class StrategicReportGeneratorV2:
    """Générateur de rapports stratégiques v2 - Analyse thématique approfondie"""
    
    # Liste des activistes connus
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
        "Paul Éric Kingué", "Célestin Djamen", "C'est le hoohaaa",
        "Les Zanalyses de Arthur", "Cameroon Liberation Streams", 
        "Africa Daily Report"
    ]
    
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = SovereignLLMService()
        self.web_extractor = WebContentExtractor()
    
    async def generate_strategic_report(
        self,
        keyword_ids: List[int],
        days: int = 14,
        report_title: str = "Rapport Stratégique"
    ) -> Dict:
        """
        Générer un rapport stratégique avec analyse thématique approfondie
        """
        logger.info(f"🎯 Génération rapport stratégique V2: {len(keyword_ids)} mots-clés, {days} jours")
        
        # 1. Collecter les mentions
        since_date = datetime.utcnow() - timedelta(days=days)
        mentions = self.db.query(Mention).filter(
            Mention.keyword_id.in_(keyword_ids),
            Mention.published_at >= since_date
        ).order_by(desc(Mention.published_at)).all()
        
        if not mentions:
            return self._generate_empty_report(keyword_ids, days, report_title)
        
        logger.info(f"📊 {len(mentions)} mentions à analyser")
        
        # 2. Lecture approfondie du contenu web
        logger.info("🌐 Lecture approfondie du contenu web...")
        web_contents = await self._deep_read_web_content(mentions[:20])  # Top 20 pour perf
        
        # 3. Analyse thématique avec IA
        logger.info("🤖 Analyse thématique avec IA...")
        thematic_analysis = await self._analyze_themes_with_ai(mentions, web_contents)
        
        # 4. Identifier les activistes
        logger.info("🚨 Identification des activistes...")
        activists_data = self._identify_activists_simple(mentions)
        
        # 5. Synthèse stratégique générale
        logger.info("📝 Génération synthèse stratégique...")
        strategic_synthesis = await self._generate_strategic_synthesis(
            mentions, thematic_analysis, activists_data, keyword_ids, days
        )
        
        # 6. Compiler le rapport final
        report_data = {
            'metadata': {
                'title': report_title,
                'keywords': [self._get_keyword_name(kid) for kid in keyword_ids],
                'period_days': days,
                'generated_at': datetime.utcnow(),
                'total_contents': len(mentions),
                'web_sources_analyzed': len(web_contents)
            },
            'synthese_strategique': strategic_synthesis,
            'problematiques_identifiees': thematic_analysis.get('problematiques', []),
            'activistes_comptes_sensibles': activists_data,
            'statistiques': self._generate_statistics(mentions)
        }
        
        logger.info("✅ Rapport stratégique V2 généré avec succès")
        return report_data
    
    async def _deep_read_web_content(self, mentions: List[Mention]) -> List[Dict]:
        """
        Lecture approfondie du contenu web (articles + commentaires)
        """
        web_contents = []
        
        # Extraire les URLs uniques
        urls = set()
        for mention in mentions:
            if mention.source_url and mention.source_url.startswith('http'):
                urls.add(mention.source_url)
        
        urls_list = list(urls)[:15]  # Limiter à 15 pour la performance
        logger.info(f"Lecture de {len(urls_list)} sources web...")
        
        async with self.web_extractor as extractor:
            # Traiter les URLs en parallèle
            semaphore = asyncio.Semaphore(3)
            
            async def extract_with_semaphore(url):
                async with semaphore:
                    return await extractor.extract_content_and_comments(url)
            
            tasks = [extract_with_semaphore(url) for url in urls_list]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, dict) and 'content' in result:
                    web_contents.append(result)
        
        logger.info(f"✅ {len(web_contents)} sources web lues avec succès")
        return web_contents
    
    async def _analyze_themes_with_ai(
        self, 
        mentions: List[Mention], 
        web_contents: List[Dict]
    ) -> Dict:
        """
        Analyser les thèmes et problématiques avec IA
        """
        # Préparer le contexte complet
        full_context = self._prepare_full_context(mentions, web_contents)
        
        # Préparer les mots-clés uniques (CORRECTION ICI)
        all_keywords = set()
        for m in mentions[:5]:
            if m.title:
                all_keywords.update(m.title.split()[:3])
        keywords_str = ', '.join(list(all_keywords)[:10]) if all_keywords else 'non disponibles'

        # Prompt pour l'analyse thématique
        prompt = f"""
Tu es un analyste stratégique senior. Analyse ces {len(mentions)} contenus collectés sur Internet.

CONTEXTE:
- {len(mentions)} publications analysées
- {len(web_contents)} sources web lues en profondeur (articles + commentaires)
- Mots-clés: {keywords_str}

CONTENU À ANALYSER:
{full_context[:8000]}

MISSION:
Identifie les 3-5 PROBLÉMATIQUES MAJEURES qui ressortent de ces contenus.

Pour chaque problématique:
1. Titre court et factuel (5-8 mots max)
2. Description concise (2-3 phrases) expliquant l'enjeu
3. Citations ou éléments clés (ce qui est dit exactement)
4. Niveau d'importance (critique/élevé/moyen)

CONTRAINTES:
- Sois FACTUEL, ne spécule pas
- Base-toi uniquement sur le contenu fourni
- Identifie les vrais enjeux stratégiques
- Évite les généralités

Réponds UNIQUEMENT en JSON:
{{
    "problematiques": [
        {{
            "titre": "<titre court>",
            "description": "<2-3 phrases factuelles>",
            "elements_cles": ["<citation 1>", "<citation 2>"],
            "importance": "critique|élevé|moyen",
            "nombre_mentions": <nombre>,
            "sources": ["<source 1>", "<source 2>"]
        }}
    ],
    "synthese_generale": "<vision globale en 3-4 phrases>"
}}
"""
        try:
            context_data = {
                'mentions': [self._mention_to_dict(m) for m in mentions[:10]],
                'web_content': web_contents[:5],
                'keywords': [],
                'period_days': 1
            }
            
            response = await self.llm_service.analyze_with_local_llm(prompt, context_data)
            
            # Parser la réponse JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                if 'problematiques' in result:
                    return result
            
            # Fallback si parsing échoue
            return self._fallback_thematic_analysis(mentions, web_contents)
            
        except Exception as e:
            logger.error(f"Erreur analyse thématique IA: {e}")
            return self._fallback_thematic_analysis(mentions, web_contents)
    
    def _prepare_full_context(self, mentions: List[Mention], web_contents: List[Dict]) -> str:
        """Préparer le contexte complet pour l'IA"""
        
        context_parts = []
        
        # Ajouter les mentions principales
        context_parts.append("=== PUBLICATIONS ===")
        for i, mention in enumerate(mentions[:15], 1):
            context_parts.append(f"\n{i}. [{mention.source}] {mention.title}")
            context_parts.append(f"   Auteur: {mention.author}")
            context_parts.append(f"   {mention.content[:300]}...")
        
        # Ajouter le contenu web lu
        if web_contents:
            context_parts.append("\n\n=== CONTENU WEB APPROFONDI ===")
            for i, wc in enumerate(web_contents[:5], 1):
                content = wc.get('content', {})
                context_parts.append(f"\n{i}. {content.get('title', 'Sans titre')}")
                context_parts.append(f"   {content.get('text', '')[:400]}...")
                
                # Ajouter quelques commentaires
                comments = wc.get('comments', [])[:3]
                if comments:
                    context_parts.append("   Commentaires:")
                    for comment in comments:
                        context_parts.append(f"   - {comment.get('text', '')[:150]}...")
        
        return '\n'.join(context_parts)
    
    def _fallback_thematic_analysis(
        self, 
        mentions: List[Mention], 
        web_contents: List[Dict]
    ) -> Dict:
        """Analyse thématique fallback basée sur des règles"""
        
        # Extraire tous les textes
        all_texts = []
        for mention in mentions:
            all_texts.append(mention.title + " " + mention.content)
        
        for wc in web_contents:
            content = wc.get('content', {})
            all_texts.append(content.get('title', '') + " " + content.get('text', ''))
            
            for comment in wc.get('comments', [])[:10]:
                all_texts.append(comment.get('text', ''))
        
        combined_text = ' '.join(all_texts).lower()
        
        # Mots-clés thématiques
        themes = {
            'gouvernance': ['gouvernement', 'autorité', 'pouvoir', 'régime', 'état', 'dictature', 'démocratie'],
            'économie': ['économie', 'argent', 'prix', 'inflation', 'corruption', 'pauvreté', 'salaire'],
            'sécurité': ['sécurité', 'armée', 'police', 'violence', 'guerre', 'conflit', 'militaire'],
            'social': ['population', 'peuple', 'citoyens', 'société', 'manifestation', 'protestation'],
            'élections': ['élection', 'vote', 'candidat', 'scrutin', 'campagne', 'opposition']
        }
        
        # Identifier les thèmes présents
        problematiques = []
        for theme_name, keywords in themes.items():
            count = sum(1 for kw in keywords if kw in combined_text)
            if count >= 3:
                # Extraire quelques mentions pertinentes
                relevant_mentions = [
                    m for m in mentions 
                    if any(kw in (m.title + " " + m.content).lower() for kw in keywords)
                ][:3]
                
                problematiques.append({
                    'titre': f"Problématique: {theme_name.capitalize()}",
                    'description': f"Plusieurs contenus abordent des questions liées à {theme_name}. "
                                 f"{len(relevant_mentions)} publications principales identifiées.",
                    'elements_cles': [m.title for m in relevant_mentions],
                    'importance': 'élevé' if count > 5 else 'moyen',
                    'nombre_mentions': len(relevant_mentions),
                    'sources': list(set(m.source for m in relevant_mentions))
                })
        
        return {
            'problematiques': problematiques[:5],
            'synthese_generale': f"Analyse de {len(mentions)} contenus révélant {len(problematiques)} problématiques majeures."
        }
    
    def _identify_activists_simple(self, mentions: List[Mention]) -> Dict:
        """
        Identifier les activistes de manière simple (tableau uniquement)
        """
        activists_data = defaultdict(lambda: {'contents': 0, 'engagement': 0, 'sources': set()})
        
        for mention in mentions:
            author = mention.author
            
            # Vérifier si activiste connu
            is_known = any(
                activist.lower() in author.lower() 
                for activist in self.KNOWN_ACTIVISTS
            )
            
            if is_known or mention.engagement_score > 1000:
                activists_data[author]['contents'] += 1
                activists_data[author]['engagement'] += mention.engagement_score
                activists_data[author]['sources'].add(mention.source)
                activists_data[author]['is_known'] = is_known
        
        # Convertir en liste triée
        activists_list = []
        for author, data in activists_data.items():
            activists_list.append({
                'nom': author,
                'is_known': data['is_known'],
                'contenus': data['contents'],
                'engagement_total': int(data['engagement']),
                'sources': ', '.join(sorted(data['sources']))
            })
        
        # Trier par engagement
        activists_list.sort(key=lambda x: x['engagement_total'], reverse=True)
        
        return {
            'total_detectes': len(activists_list),
            'activistes_connus': sum(1 for a in activists_list if a['is_known']),
            'comptes_suspects': sum(1 for a in activists_list if not a['is_known']),
            'liste': activists_list[:30]  # Top 30
        }
    
    async def _generate_strategic_synthesis(
        self,
        mentions: List[Mention],
        thematic_analysis: Dict,
        activists_data: Dict,
        keyword_ids: List[int],
        days: int
    ) -> Dict:
        """
        Générer la synthèse stratégique générale
        """
        # Prompt pour synthèse
        problematiques_summary = '\n'.join([
            f"- {p['titre']}: {p['importance']}" 
            for p in thematic_analysis.get('problematiques', [])[:5]
        ])
        
        prompt = f"""
Tu es le directeur de la communication qui rédige un brief au DG.

SITUATION:
- Période: {days} jours
- Contenus analysés: {len(mentions)}
- Activistes détectés: {activists_data['total_detectes']}
- Problématiques identifiées:
{problematiques_summary}

Rédige une synthèse exécutive de 3 paragraphes maximum:
1. Vue d'ensemble de la situation
2. Enjeux stratégiques majeurs
3. Évaluation du niveau de risque (Faible/Modéré/Élevé/Critique)

Style: Direct, factuel, concis. Phrases courtes.
"""
        
        try:
            context_data = {
                'mentions': [self._mention_to_dict(m) for m in mentions[:5]],
                'keywords': [],
                'period_days': days
            }
            
            synthesis_text = await self.llm_service.analyze_with_local_llm(prompt, context_data)
            
        except Exception as e:
            logger.warning(f"Erreur synthèse IA: {e}")
            synthesis_text = self._fallback_synthesis(len(mentions), activists_data, days)
        
        # Déterminer le niveau de risque
        risk_level = self._assess_risk_level(mentions, thematic_analysis, activists_data)
        
        return {
            'synthese_text': synthesis_text.strip(),
            'niveau_risque': risk_level,
            'metriques_cles': {
                'total_contenus': len(mentions),
                'periode_jours': days,
                'problematiques_identifiees': len(thematic_analysis.get('problematiques', [])),
                'activistes_detectes': activists_data['total_detectes']
            }
        }
    
    def _assess_risk_level(
        self,
        mentions: List[Mention],
        thematic_analysis: Dict,
        activists_data: Dict
    ) -> str:
        """Évaluer le niveau de risque global"""
        
        risk_score = 0
        
        # Facteur: Problématiques critiques
        critical_issues = sum(
            1 for p in thematic_analysis.get('problematiques', []) 
            if p.get('importance') == 'critique'
        )
        risk_score += critical_issues * 3
        
        # Facteur: Volume de mentions
        if len(mentions) > 100:
            risk_score += 2
        elif len(mentions) > 50:
            risk_score += 1
        
        # Facteur: Activistes connus
        if activists_data['activistes_connus'] > 3:
            risk_score += 2
        elif activists_data['activistes_connus'] > 0:
            risk_score += 1
        
        # Facteur: Engagement élevé
        high_engagement = sum(1 for m in mentions if m.engagement_score > 1000)
        if high_engagement > 10:
            risk_score += 2
        elif high_engagement > 5:
            risk_score += 1
        
        # Déterminer le niveau
        if risk_score >= 7:
            return 'CRITIQUE'
        elif risk_score >= 5:
            return 'ÉLEVÉ'
        elif risk_score >= 3:
            return 'MODÉRÉ'
        else:
            return 'FAIBLE'
    
    def _fallback_synthesis(self, total_mentions: int, activists_data: Dict, days: int) -> str:
        """Synthèse fallback"""
        return f"""Sur les {days} derniers jours, {total_mentions} contenus ont été analysés. 
        
{activists_data['total_detectes']} comptes influents détectés dont {activists_data['activistes_connus']} activistes connus.

Surveillance continue recommandée pour anticiper les évolutions."""
    
    def _generate_statistics(self, mentions: List[Mention]) -> Dict:
        """Générer les statistiques du rapport"""
        
        total = len(mentions)
        
        if total == 0:
            return {}
        
        # Distribution par source
        sources = Counter([m.source for m in mentions])
        
        # Engagement
        total_engagement = sum(m.engagement_score for m in mentions)
        avg_engagement = total_engagement / total
        
        # Top auteurs
        authors = Counter([m.author for m in mentions])
        
        return {
            'total_contents': total,
            'sources_distribution': dict(sources.most_common(10)),
            'total_engagement': int(total_engagement),
            'average_engagement': round(avg_engagement, 1),
            'top_auteurs': dict(authors.most_common(10))
        }
    
    def _mention_to_dict(self, mention: Mention) -> Dict:
        """Convertir une mention en dict"""
        return {
            'id': mention.id,
            'title': mention.title,
            'content': mention.content,
            'author': mention.author,
            'source': mention.source,
            'source_url': mention.source_url,
            'engagement_score': mention.engagement_score,
            'published_at': mention.published_at.isoformat() if mention.published_at else None
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