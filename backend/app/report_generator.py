"""
Générateur de Rapports Stratégiques V3 - Style Narratif pour Ministre
Analyse stratégique rédigée avec argumentaire structuré
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from collections import Counter, defaultdict
import asyncio

from app.ai_service import SovereignLLMService, WebContentExtractor
from app.models import Keyword, Mention

logger = logging.getLogger(__name__)


class StrategicReportGeneratorV3:
    """Générateur V3 - Rapport narratif pour décideurs"""
    
    KNOWN_ACTIVISTS = [
        "Général Valsero", "Michel Biem Tong", "Maurice Kamto", 
        "Brenda Biya", "Patrice Nganang", "Brigade anti-sardinards"
    ]
    
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = SovereignLLMService()
        self.web_extractor = WebContentExtractor()
    
    async def generate_ministerial_report(
        self,
        keyword_ids: List[int],
        days: int = 30,
        report_title: str = "Rapport Stratégique"
    ) -> Dict:
        """
        Générer un rapport narratif pour ministre/DG
        """
        logger.info(f"📝 Génération rapport ministériel V3: {len(keyword_ids)} mots-clés")
        
        # 1. Collecter les données
        since_date = datetime.utcnow() - timedelta(days=days)
        mentions = self.db.query(Mention).filter(
            Mention.keyword_id.in_(keyword_ids),
            Mention.published_at >= since_date
        ).order_by(desc(Mention.engagement_score)).all()
        
        if not mentions:
            return self._generate_empty_report(keyword_ids, days, report_title)
        
        # 2. Lecture web approfondie
        logger.info("🌐 Lecture contenu web + commentaires...")
        web_contents = await self._deep_read_web_content(mentions[:15])
        
        # 3. Analyse stratégique narrative
        logger.info("🎯 Analyse stratégique en cours...")
        strategic_analysis = await self._generate_strategic_narrative(
            mentions, web_contents, keyword_ids, days
        )
        
        # 4. Synthèse des commentaires par thème
        logger.info("💬 Synthèse commentaires par thème...")
        comments_synthesis = await self._synthesize_comments_by_theme(web_contents)
        
        # 5. Identification activistes critiques seulement
        logger.info("🚨 Identification activistes critiques...")
        critical_activists = self._identify_critical_activists_only(mentions)
        
        # 6. Recommandations opérationnelles
        logger.info("📋 Génération recommandations...")
        recommendations = await self._generate_operational_recommendations(
            strategic_analysis, critical_activists, comments_synthesis
        )
        
        # Compiler le rapport final
        report_data = {
            'metadata': {
                'title': report_title,
                'keywords': [self._get_keyword_name(kid) for kid in keyword_ids],
                'period_days': days,
                'generated_at': datetime.utcnow(),
                'classification': 'CONFIDENTIEL - DIFFUSION RESTREINTE'
            },
            'synthese_executive': strategic_analysis.get('synthese_executive'),
            'analyse_situation': strategic_analysis.get('analyse_situation'),
            'evaluation_menaces': strategic_analysis.get('evaluation_menaces'),
            'synthese_commentaires': comments_synthesis,
            'activistes_critiques': critical_activists,
            'recommandations': recommendations,
            'contenus_viraux': self._identify_viral_content(mentions),
            'metriques': self._generate_metrics(mentions, web_contents)
        }
        
        logger.info("✅ Rapport ministériel V3 généré")
        return report_data
    
    async def _generate_strategic_narrative(
        self,
        mentions: List[Mention],
        web_contents: List[Dict],
        keyword_ids: List[int],
        days: int
    ) -> Dict:
        """
        Générer une analyse stratégique narrative (style rédactionnel)
        """
        
        # Préparer le contexte complet
        full_context = self._prepare_narrative_context(mentions, web_contents)
        
        # Extraire keywords
        keywords_str = ', '.join([self._get_keyword_name(kid) for kid in keyword_ids])
        
        # PROMPT CRITIQUE - Force le style narratif
        prompt = f"""Tu es un analyste stratégique senior rédigeant un rapport CONFIDENTIEL pour le Ministre.

CONTEXTE:
- Surveillance: {keywords_str}
- Période: {days} jours  
- Sources: {len(mentions)} publications + {len(web_contents)} articles analysés en profondeur
- Niveau: DIFFUSION RESTREINTE

DONNÉES ANALYSÉES:
{full_context[:12000]}

=== INSTRUCTIONS CRITIQUES ===

Tu dois rédiger une analyse stratégique en TEXTE CONTINU (PAS de listes à puces).
Style: Rédaction fluide, paragraphes argumentés, comme un brief confidentiel.

STRUCTURE OBLIGATOIRE:

**1. SYNTHÈSE EXÉCUTIVE** (3-4 paragraphes rédigés)
Commence par: "L'analyse de [X] publications sur [période] révèle..."
Rédige un texte fluide qui répond à:
- Quelle est la situation globale ?
- Les intérêts de l'État sont-ils menacés ?
- La République est-elle en danger, en paix, ou sous tension ?
- Niveau de criticité: FAIBLE / MODÉRÉ / ÉLEVÉ / CRITIQUE

**2. ANALYSE DE LA SITUATION** (4-5 paragraphes rédigés)
Rédige en paragraphes continus qui expliquent:
- Quels sont les thèmes dominants dans le discours public ?
- Que pensent réellement les citoyens ? (analyse des commentaires)
- Y a-t-il des narratifs dangereux qui se propagent ?
- Quelles sont les revendications exprimées ?

Utilise des phrases comme:
"Les publications analysées montrent que..."
"Un examen approfondi des commentaires révèle..."
"Il ressort de cette analyse que..."

**3. ÉVALUATION DES MENACES** (3-4 paragraphes rédigés)
Identifie et argumente:
- Existe-t-il des appels à la violence ou à la contestation ?
- Y a-t-il une mobilisation organisée ?
- Quel est le niveau d'engagement populaire ?
- Les activistes connus sont-ils actifs ?

CONTRAINTES ABSOLUES:
- ZÉRO liste à puces
- Texte rédigé en paragraphes fluides
- Citations entre guillemets si nécessaires
- Ton professionnel mais accessible
- Français soutenu
- Pas de jargon technique
- Conclusions claires et actionnables

Réponds UNIQUEMENT en JSON structuré:
{{
    "synthese_executive": {{
        "texte": "<3-4 paragraphes rédigés>",
        "niveau_criticite": "FAIBLE|MODÉRÉ|ÉLEVÉ|CRITIQUE",
        "menace_etat": "OUI|NON",
        "paix_publique": "STABLE|FRAGILE|TENDUE|CRITIQUE"
    }},
    "analyse_situation": {{
        "texte": "<4-5 paragraphes rédigés sur les thèmes et l'opinion>",
        "themes_dominants": ["<thème 1>", "<thème 2>", "<thème 3>"],
        "sentiment_general": "<positif|mitigé|négatif>"
    }},
    "evaluation_menaces": {{
        "texte": "<3-4 paragraphes rédigés sur les menaces identifiées>",
        "menaces_identifiees": ["<menace 1>", "<menace 2>"],
        "niveau_mobilisation": "FAIBLE|MOYEN|ÉLEVÉ"
    }}
}}
"""
        
        try:
            context_data = {
                'mentions': [self._mention_to_dict(m) for m in mentions[:20]],
                'web_content': web_contents[:10],
                'keywords': keywords_str,
                'period_days': days
            }
            
            response = await self.llm_service.analyze_with_local_llm(prompt, context_data)
            
            # Parser la réponse JSON
            import re
            import json
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result
            
            # Fallback
            return self._fallback_narrative_analysis(mentions, web_contents)
            
        except Exception as e:
            logger.error(f"Erreur analyse narrative: {e}")
            return self._fallback_narrative_analysis(mentions, web_contents)
    
    async def _synthesize_comments_by_theme(self, web_contents: List[Dict]) -> Dict:
        """
        Synthétiser tous les commentaires par thème (en texte rédigé)
        """
        
        all_comments = []
        for wc in web_contents:
            comments = wc.get('comments', [])
            for comment in comments:
                all_comments.append({
                    'text': comment.get('text', ''),
                    'author': comment.get('author', 'Anonyme'),
                    'likes': comment.get('likes', 0),
                    'source_url': wc.get('url', '')
                })
        
        if not all_comments:
            return {
                'synthese': "Aucun commentaire n'a pu être extrait des sources analysées.",
                'themes': []
            }
        
        # Préparer le contexte des commentaires
        comments_text = '\n'.join([
            f"- {c['text'][:200]}... (👤 {c['author']}, 👍 {c['likes']})"
            for c in all_comments[:50]  # Top 50 commentaires
        ])
        
        prompt = f"""Tu analyses {len(all_comments)} commentaires d'internautes.

COMMENTAIRES:
{comments_text}

Rédige une SYNTHÈSE EN TEXTE CONTINU (pas de listes) qui répond à:
- Que pensent globalement les internautes ?
- Quels sont les thèmes récurrents dans leurs réactions ?
- Y a-t-il des commentaires incitant à la violence ou à la contestation ?
- Quel est le ton général: soutien, critique, neutre ?

Réponds en JSON:
{{
    "synthese": "<4-5 paragraphes rédigés analysant l'opinion des commentateurs>",
    "themes_commentaires": ["<thème 1>", "<thème 2>", "<thème 3>"],
    "commentaire_plus_engage": "<texte du commentaire ayant le plus de likes>",
    "appels_action": "OUI|NON"
}}
"""
        
        try:
            context_data = {'comments': all_comments[:30]}
            response = await self.llm_service.analyze_with_local_llm(prompt, context_data)
            
            import re, json
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            return self._fallback_comments_synthesis(all_comments)
            
        except Exception as e:
            logger.error(f"Erreur synthèse commentaires: {e}")
            return self._fallback_comments_synthesis(all_comments)
    
    def _identify_critical_activists_only(self, mentions: List[Mention]) -> Dict:
        """
        Identifier SEULEMENT les activistes critiques (connus + 4-5 nouveaux max)
        """
        activists_data = defaultdict(lambda: {
            'contents': 0,
            'engagement': 0,
            'is_known': False,
            'peak_engagement': 0
        })
        
        for mention in mentions:
            author = mention.author
            engagement = mention.engagement_score
            
            # Vérifier si activiste connu
            is_known = any(
                activist.lower() in author.lower() 
                for activist in self.KNOWN_ACTIVISTS
            )
            
            # Ne garder que si connu OU très engageant
            if is_known or engagement > 5000:
                activists_data[author]['contents'] += 1
                activists_data[author]['engagement'] += engagement
                activists_data[author]['is_known'] = is_known
                if engagement > activists_data[author]['peak_engagement']:
                    activists_data[author]['peak_engagement'] = engagement
        
        # Filtrer: tous les connus + top 5 nouveaux
        known_activists = [
            {'nom': author, **data}
            for author, data in activists_data.items()
            if data['is_known']
        ]
        
        new_activists = [
            {'nom': author, **data}
            for author, data in activists_data.items()
            if not data['is_known']
        ]
        new_activists.sort(key=lambda x: x['engagement'], reverse=True)
        new_activists = new_activists[:5]  # Max 5 nouveaux
        
        critical_list = known_activists + new_activists
        critical_list.sort(key=lambda x: x['engagement'], reverse=True)
        
        return {
            'total': len(critical_list),
            'connus': len(known_activists),
            'nouveaux': len(new_activists),
            'liste': critical_list
        }
    
    def _identify_viral_content(self, mentions: List[Mention]) -> Dict:
        """
        Identifier le contenu le plus viral/partagé
        """
        top_viral = sorted(mentions, key=lambda m: m.engagement_score, reverse=True)[:5]
        
        return {
            'plus_engage': {
                'titre': top_viral[0].title if top_viral else 'N/A',
                'auteur': top_viral[0].author if top_viral else 'N/A',
                'engagement': int(top_viral[0].engagement_score) if top_viral else 0,
                'source': top_viral[0].source if top_viral else 'N/A',
                'url': top_viral[0].source_url if top_viral else ''
            },
            'top_5': [
                {
                    'titre': m.title,
                    'engagement': int(m.engagement_score),
                    'source': m.source
                }
                for m in top_viral
            ]
        }
    
    async def _generate_operational_recommendations(
        self,
        strategic_analysis: Dict,
        critical_activists: Dict,
        comments_synthesis: Dict
    ) -> Dict:
        """
        Générer des recommandations opérationnelles en texte rédigé
        """
        
        criticite = strategic_analysis.get('synthese_executive', {}).get('niveau_criticite', 'MODÉRÉ')
        menace_etat = strategic_analysis.get('synthese_executive', {}).get('menace_etat', 'NON')
        
        prompt = f"""Tu es conseiller stratégique. Rédige des recommandations opérationnelles.

SITUATION:
- Criticité: {criticite}
- Menace État: {menace_etat}
- Activistes critiques: {critical_activists['total']} ({critical_activists['connus']} connus)
- Appels à l'action: {comments_synthesis.get('appels_action', 'NON')}

Rédige en TEXTE CONTINU (pas de liste) des recommandations organisées en:

1. ACTIONS IMMÉDIATES (0-24h)
2. ACTIONS COURT TERME (1-7 jours)
3. ACTIONS MOYEN TERME (1 mois)

Style: Impératif, clair, actionnable.

Réponds en JSON:
{{
    "actions_immediates": "<paragraphe rédigé avec 2-3 actions urgentes>",
    "actions_court_terme": "<paragraphe rédigé avec 3-4 actions à 7 jours>",
    "actions_moyen_terme": "<paragraphe rédigé avec 2-3 actions stratégiques>"
}}
"""
        
        try:
            response = await self.llm_service.analyze_with_local_llm(prompt, {
                'criticite': criticite,
                'menace': menace_etat
            })
            
            import re, json
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            return self._fallback_recommendations(criticite)
            
        except Exception as e:
            logger.error(f"Erreur recommandations: {e}")
            return self._fallback_recommendations(criticite)
    
    # ... (Méthodes utilitaires: _prepare_narrative_context, _fallback_*, _mention_to_dict, etc.)
    
    async def _deep_read_web_content(self, mentions: List[Mention]) -> List[Dict]:
        """Lecture web approfondie"""
        web_contents = []
        urls = set()
        
        for mention in mentions:
            if mention.source_url and mention.source_url.startswith('http'):
                urls.add(mention.source_url)
        
        urls_list = list(urls)[:15]
        
        async with self.web_extractor as extractor:
            semaphore = asyncio.Semaphore(3)
            
            async def extract_with_semaphore(url):
                async with semaphore:
                    return await extractor.extract_content_and_comments(url)
            
            tasks = [extract_with_semaphore(url) for url in urls_list]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, dict) and 'content' in result:
                    web_contents.append(result)
        
        return web_contents
    
    def _prepare_narrative_context(self, mentions: List[Mention], web_contents: List[Dict]) -> str:
        """Préparer contexte pour prompt narratif"""
        context_parts = []
        
        context_parts.append("=== PUBLICATIONS ANALYSÉES ===")
        for i, mention in enumerate(mentions[:10], 1):
            context_parts.append(f"\n{i}. [{mention.source}] {mention.title}")
            context_parts.append(f"   Auteur: {mention.author} | Engagement: {mention.engagement_score}")
            context_parts.append(f"   {mention.content[:250]}...")
        
        if web_contents:
            context_parts.append("\n\n=== CONTENU WEB + COMMENTAIRES ===")
            for i, wc in enumerate(web_contents[:5], 1):
                content = wc.get('content', {})
                comments = wc.get('comments', [])
                
                context_parts.append(f"\n{i}. {content.get('title', 'Sans titre')}")
                context_parts.append(f"   Article: {content.get('text', '')[:300]}...")
                
                if comments:
                    context_parts.append(f"   Commentaires ({len(comments)}):")
                    for comment in comments[:3]:
                        context_parts.append(f"   - {comment.get('text', '')[:120]}...")
        
        return '\n'.join(context_parts)
    
    def _fallback_narrative_analysis(self, mentions: List[Mention], web_contents: List[Dict]) -> Dict:
        """Analyse fallback narrative"""
        negative_count = sum(1 for m in mentions if m.sentiment == 'negative')
        negative_ratio = negative_count / len(mentions) if mentions else 0
        
        if negative_ratio > 0.6:
            criticite = "ÉLEVÉ"
            menace = "OUI"
            paix = "TENDUE"
        elif negative_ratio > 0.3:
            criticite = "MODÉRÉ"
            menace = "NON"
            paix = "FRAGILE"
        else:
            criticite = "FAIBLE"
            menace = "NON"
            paix = "STABLE"
        
        synthese_text = f"""L'analyse de {len(mentions)} publications sur {len(set(m.source for m in mentions))} sources révèle une situation {paix.lower()}. """
        
        if negative_ratio > 0.5:
            synthese_text += f"Le sentiment négatif domine ({negative_ratio:.0%}), reflétant des préoccupations marquées au sein de l'opinion publique. "
        else:
            synthese_text += f"Le ton reste globalement modéré, bien que {negative_ratio:.0%} des contenus expriment des critiques. "
        
        synthese_text += f"Les intérêts de l'État {'sont potentiellement menacés' if menace == 'OUI' else 'ne semblent pas directement menacés'} dans l'immédiat. "
        
        if len(web_contents) > 0:
            total_comments = sum(len(wc.get('comments', [])) for wc in web_contents)
            synthese_text += f"L'examen de {total_comments} commentaires d'internautes permet de mieux cerner les véritables préoccupations citoyennes."
        
        return {
            'synthese_executive': {
                'texte': synthese_text,
                'niveau_criticite': criticite,
                'menace_etat': menace,
                'paix_publique': paix
            },
            'analyse_situation': {
                'texte': "L'analyse détaillée des thématiques dominantes sera produite avec un modèle IA plus performant (Mistral recommandé).",
                'themes_dominants': [],
                'sentiment_general': 'négatif' if negative_ratio > 0.5 else 'mitigé'
            },
            'evaluation_menaces': {
                'texte': "L'évaluation approfondie des menaces nécessite un modèle IA plus puissant pour une analyse sémantique avancée.",
                'menaces_identifiees': [],
                'niveau_mobilisation': "MOYEN" if len(mentions) > 50 else "FAIBLE"
            }
        }
    
    def _fallback_comments_synthesis(self, comments: List[Dict]) -> Dict:
        """Synthèse commentaires fallback"""
        if not comments:
            return {
                'synthese': "Aucun commentaire disponible pour analyse.",
                'themes_commentaires': [],
                'commentaire_plus_engage': '',
                'appels_action': 'NON'
            }
        
        top_comment = max(comments, key=lambda c: c.get('likes', 0))
        
        return {
            'synthese': f"L'analyse de {len(comments)} commentaires d'internautes révèle un engagement significatif. Le commentaire le plus apprécié a reçu {top_comment['likes']} réactions, indiquant une forte résonance auprès du public.",
            'themes_commentaires': ['Opinion publique', 'Engagement citoyen'],
            'commentaire_plus_engage': top_comment['text'][:200],
            'appels_action': 'À DÉTERMINER'
        }
    
    def _fallback_recommendations(self, criticite: str) -> Dict:
        """Recommandations fallback"""
        if criticite in ['CRITIQUE', 'ÉLEVÉ']:
            immediates = "Activer immédiatement la cellule de veille stratégique. Préparer des éléments de communication officielle pour répondre aux préoccupations identifiées."
            court_terme = "Engager un dialogue avec les influenceurs clés identifiés dans ce rapport. Mettre en place un monitoring renforcé H24 pour détecter toute escalade."
            moyen_terme = "Développer une stratégie de communication de long terme pour restaurer la confiance. Analyser les causes profondes des tensions identifiées."
        else:
            immediates = "Maintenir la surveillance habituelle. Aucune action d'urgence n'est requise à ce stade."
            court_terme = "Continuer le monitoring des sources identifiées. Préparer des messages de clarification sur les points sensibles détectés."
            moyen_terme = "Consolider la stratégie de communication digitale. Renforcer les canaux d'écoute de l'opinion publique."
        
        return {
            'actions_immediates': immediates,
            'actions_court_terme': court_terme,
            'actions_moyen_terme': moyen_terme
        }
    
    def _generate_metrics(self, mentions: List[Mention], web_contents: List[Dict]) -> Dict:
        """Générer métriques"""
        total_engagement = sum(m.engagement_score for m in mentions)
        total_comments = sum(len(wc.get('comments', [])) for wc in web_contents)
        
        return {
            'total_publications': len(mentions),
            'total_engagement': int(total_engagement),
            'engagement_moyen': int(total_engagement / len(mentions)) if mentions else 0,
            'sources_analysees': len(set(m.source for m in mentions)),
            'articles_lus': len(web_contents),
            'commentaires_analyses': total_comments
        }
    
    def _mention_to_dict(self, mention: Mention) -> Dict:
        """Convertir mention en dict"""
        return {
            'title': mention.title,
            'content': mention.content,
            'author': mention.author,
            'source': mention.source,
            'engagement_score': mention.engagement_score,
            'sentiment': mention.sentiment
        }
    
    def _get_keyword_name(self, keyword_id: int) -> str:
        """Obtenir nom mot-clé"""
        kw = self.db.query(Keyword).filter(Keyword.id == keyword_id).first()
        return kw.keyword if kw else f"Mot-clé #{keyword_id}"
    
    def _generate_empty_report(self, keyword_ids: List[int], days: int, title: str) -> Dict:
        """Rapport vide"""
        return {
            'metadata': {
                'title': title,
                'keywords': [self._get_keyword_name(kid) for kid in keyword_ids],
                'period_days': days,
                'generated_at': datetime.utcnow(),
                'classification': 'CONFIDENTIEL'
            },
            'error': 'Aucune donnée disponible pour cette période'
        }