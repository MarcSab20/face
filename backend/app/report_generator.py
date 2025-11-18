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
        """Analyse fallback avec contenu réel basé sur les données"""
        
        if not mentions:
            return self._generate_empty_analysis()
        
        # Analyser les données réelles
        negative_count = sum(1 for m in mentions if m.sentiment == 'negative')
        positive_count = sum(1 for m in mentions if m.sentiment == 'positive')
        neutral_count = sum(1 for m in mentions if m.sentiment == 'neutral')
        total = len(mentions)
        
        negative_ratio = negative_count / total
        positive_ratio = positive_count / total
        
        # Analyser les sources
        sources = {}
        for m in mentions:
            sources[m.source] = sources.get(m.source, 0) + 1
        top_sources = sorted(sources.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Analyser les auteurs les plus actifs
        authors = {}
        for m in mentions:
            authors[m.author] = authors.get(m.author, 0) + 1
        top_authors = sorted(authors.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Déterminer criticité
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
        
        # GÉNÉRER SYNTHÈSE NARRATIVE RÉELLE
        synthese_text = f"""L'analyse de {total} publications sur une période de {len(set(m.source for m in mentions))} sources distinctes révèle une situation {paix.lower()}. """
        
        if negative_ratio > 0.5:
            synthese_text += f"Le sentiment négatif domine largement ({negative_ratio:.0%}), reflétant des préoccupations marquées au sein de l'opinion publique surveillée. "
        elif positive_ratio > 0.5:
            synthese_text += f"Le sentiment positif domine ({positive_ratio:.0%}), indiquant une opinion publique plutôt favorable. "
        else:
            synthese_text += f"Le ton reste globalement partagé entre opinions positives ({positive_ratio:.0%}) et négatives ({negative_ratio:.0%}). "
        
        synthese_text += f"\n\nLes trois principales sources de publications sont {', '.join([s[0] for s in top_sources[:2]])} et {top_sources[2][0] if len(top_sources) > 2 else 'autres'}. "
        
        if menace == 'OUI':
            synthese_text += f"Les intérêts de l'État sont potentiellement menacés compte tenu du niveau élevé de critiques détectées. "
        else:
            synthese_text += f"Les intérêts de l'État ne semblent pas directement menacés dans l'immédiat. "
        
            if len(web_contents) > 0:
                total_comments = sum(len(wc.get('comments', [])) for wc in web_contents)
                synthese_text += f"\n\nL'examen de {total_comments} commentaires d'internautes sur {len(web_contents)} articles permet de mieux cerner les véritables préoccupations citoyennes au-delà des publications officielles."
            
            # GÉNÉRER ANALYSE DE SITUATION
            analyse_sit_text = f"""Les {total} publications analysées couvrent principalement les plateformes {', '.join([s[0] for s in top_sources])}. """
            
            # Identifier les thèmes à partir des titres
            all_titles = ' '.join([m.title for m in mentions]).lower()
            themes_detectes = []
            
            theme_keywords = {
                'politique': ['gouvernement', 'ministre', 'président', 'élection', 'politique'],
                'économie': ['économie', 'argent', 'prix', 'inflation', 'budget'],
                'social': ['social', 'société', 'peuple', 'manifestation', 'grève'],
                'sécurité': ['sécurité', 'police', 'crime', 'violence', 'danger']
            }
            
            for theme, keywords in theme_keywords.items():
                if any(kw in all_titles for kw in keywords):
                    themes_detectes.append(theme)
            
            if themes_detectes:
                analyse_sit_text += f"Les thèmes dominants identifiés concernent : {', '.join(themes_detectes)}. "
            
            # Analyser les auteurs influents
            analyse_sit_text += f"\n\nParmi les contributeurs les plus actifs, on retrouve {top_authors[0][0]} avec {top_authors[0][1]} publications, "
            if len(top_authors) > 1:
                analyse_sit_text += f"suivi de {top_authors[1][0]} ({top_authors[1][1]} publications). "
            
            if negative_ratio > 0.5:
                analyse_sit_text += f"\n\nLe ton critique prédominant suggère une insatisfaction face à certains aspects de la situation actuelle. "
            
            # ÉVALUATION DES MENACES
            eval_menaces_text = f"""Sur la base des {total} contenus analysés, l'évaluation des menaces révèle les éléments suivants. """
            
            # Chercher des mots-clés de menace
            threat_keywords = ['crise', 'danger', 'menace', 'violence', 'guerre', 'conflit']
            threats_found = []
            for m in mentions:
                content_lower = f"{m.title} {m.content}".lower()
                for threat in threat_keywords:
                    if threat in content_lower:
                        threats_found.append(threat)
                        break
            
            if threats_found:
                eval_menaces_text += f"Des mentions de termes sensibles ont été détectées ({len(threats_found)} occurrences), incluant des références à {', '.join(set(threats_found)[:3])}. "
            else:
                eval_menaces_text += f"Aucun terme explicitement menaçant n'a été détecté dans le corpus analysé. "
            
            # Engagement
            high_engagement = [m for m in mentions if m.engagement_score > 10000]
            if high_engagement:
                eval_menaces_text += f"\n\n{len(high_engagement)} publication(s) ont généré un engagement particulièrement élevé (>10K), suggérant une forte résonance auprès du public. "
            
            if negative_ratio > 0.6:
                eval_menaces_text += f"\n\nLe niveau élevé de sentiment négatif ({negative_ratio:.0%}) combiné à l'engagement détecté nécessite une surveillance accrue et une possible stratégie de communication corrective."
            else:
                eval_menaces_text += f"\n\nLe niveau global de menace reste maîtrisable à ce stade, bien qu'une vigilance continue soit recommandée."
            
            return {
                'synthese_executive': {
                    'texte': synthese_text,
                    'niveau_criticite': criticite,
                    'menace_etat': menace,
                    'paix_publique': paix
                },
                'analyse_situation': {
                    'texte': analyse_sit_text,
                    'themes_dominants': themes_detectes,
                    'sentiment_general': 'négatif' if negative_ratio > 0.5 else ('positif' if positive_ratio > 0.5 else 'mitigé')
                },
                'evaluation_menaces': {
                    'texte': eval_menaces_text,
                    'menaces_identifiees': threats_found[:3],
                    'niveau_mobilisation': "ÉLEVÉ" if len(high_engagement) > 10 else ("MOYEN" if len(high_engagement) > 5 else "FAIBLE")
                }
            }

    def _generate_empty_analysis(self) -> Dict:
        """Analyse vide si aucune donnée"""
        return {
            'synthese_executive': {
                'texte': "Aucune donnée disponible pour générer une analyse pertinente.",
                'niveau_criticite': 'FAIBLE',
                'menace_etat': 'NON',
                'paix_publique': 'STABLE'
            },
            'analyse_situation': {
                'texte': "Impossible de produire une analyse faute de données sur la période sélectionnée.",
                'themes_dominants': [],
                'sentiment_general': 'inconnu'
            },
            'evaluation_menaces': {
                'texte': "Aucune menace identifiable en l'absence de données à analyser.",
                'menaces_identifiees': [],
                'niveau_mobilisation': 'FAIBLE'
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