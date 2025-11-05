"""
Service IA Souverain pour l'analyse intelligente des mentions
Système complet d'agents IA sans dépendance externe (OpenAI, Claude, etc.)
Utilise Ollama + HuggingFace Transformers pour une IA locale
"""

import logging
import json
import asyncio
import aiohttp
import ssl
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import re
import statistics
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from sqlalchemy.orm import Session
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class AnalysisContext:
    """Contexte d'analyse pour les agents IA"""
    mentions: List[Dict]
    keywords: List[str]
    period_days: int
    total_mentions: int
    sentiment_distribution: Dict[str, int]
    top_sources: Dict[str, int]
    engagement_stats: Dict[str, float]
    geographic_data: List[Dict]
    influencers_data: List[Dict]
    time_trends: List[Dict]
    web_content: List[Dict] = None


@dataclass
class AIInsight:
    """Insight généré par l'IA"""
    type: str
    confidence: float
    message: str
    data: Dict
    priority: int = 1  # 1=faible, 5=critique


class SovereignLLMService:
    """Service LLM souverain - aucune dépendance externe"""
    
    def __init__(self):
        self.ollama_available = False
        self.transformers_available = False
        self.current_model = None
        
        # Initialiser les modèles locaux
        self._initialize_ollama()
        self._initialize_transformers()
        
        # Dictionnaires de patterns pour l'analyse
        self._init_analysis_patterns()
    
    def _initialize_ollama(self):
        """Initialiser Ollama (modèles LLM locaux)"""
        try:
            import ollama
            self.ollama_client = ollama.Client()
            # Tester la disponibilité
            models = self.ollama_client.list()
            self.ollama_available = True
            self.available_models = [m['name'] for m in models.get('models', [])]
            logger.info(f"Ollama disponible avec {len(self.available_models)} modèles")
        except Exception as e:
            logger.warning(f"Ollama non disponible: {e}")
            self.ollama_available = False
    
    def _initialize_transformers(self):
        """Initialiser HuggingFace Transformers"""
        try:
            from transformers import pipeline, AutoTokenizer
            import torch
            
            self.device = 0 if torch.cuda.is_available() else -1
            self.transformers_available = True
            
            # Charger les modèles spécialisés
            self._load_specialized_models()
            logger.info("HuggingFace Transformers initialisé")
        except ImportError:
            logger.warning("HuggingFace Transformers non disponible")
            self.transformers_available = False
    
    def _load_specialized_models(self):
        """Charger les modèles spécialisés"""
        try:
            from transformers import pipeline
            
            # Modèle de sentiment français/anglais
            self.sentiment_model = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=self.device
            )
            
            # Modèle de classification de contenu
            self.classification_model = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=self.device
            )
            
            # Modèle de résumé
            self.summarization_model = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=self.device
            )
            
        except Exception as e:
            logger.warning(f"Erreur chargement modèles spécialisés: {e}")
    
    def _init_analysis_patterns(self):
        """Initialiser les patterns d'analyse"""
        self.risk_indicators = {
            'high': [
                'scandale', 'catastrophe', 'désastre', 'corruption', 'fraude',
                'boycott', 'grève', 'manifestation', 'crise', 'polémique'
            ],
            'medium': [
                'problème', 'difficulté', 'retard', 'erreur', 'bug',
                'plainte', 'réclamation', 'insatisfaction'
            ]
        }
        
        self.opportunity_indicators = [
            'innovation', 'succès', 'performance', 'croissance', 'amélioration',
            'félicitations', 'récompense', 'prix', 'reconnaissance'
        ]
        
        self.influence_indicators = [
            'expert', 'spécialiste', 'journaliste', 'influenceur', 'leader',
            'officiel', 'porte-parole', 'analyste'
        ]
    
    async def analyze_with_local_llm(self, prompt: str, context_data: Dict) -> str:
        """Analyser avec un modèle LLM local"""
        if self.ollama_available:
            return await self._analyze_with_ollama(prompt, context_data)
        elif self.transformers_available:
            return await self._analyze_with_transformers(prompt, context_data)
        else:
            return self._analyze_with_rules(prompt, context_data)
    
    async def _analyze_with_ollama(self, prompt: str, context_data: Dict) -> str:
        """Analyse avec Ollama"""
        try:
            # Choisir le meilleur modèle disponible
            model = self._select_best_model()
            
            # Construire le prompt enrichi
            enriched_prompt = self._build_enriched_prompt(prompt, context_data)
            
            response = self.ollama_client.generate(
                model=model,
                prompt=enriched_prompt,
                options={
                    'num_predict': 500,
                    'temperature': 0.3,  # Moins créatif, plus factuel
                    'top_p': 0.9,
                    'stop': ['</analysis>', '<|endoftext|>']
                }
            )
            
            return self._clean_llm_response(response['response'])
            
        except Exception as e:
            logger.error(f"Erreur Ollama: {e}")
            return self._analyze_with_rules(prompt, context_data)
    
    async def _analyze_with_transformers(self, prompt: str, context_data: Dict) -> str:
        """Analyse avec Transformers"""
        try:
            # Utiliser le modèle de résumé pour générer une analyse
            text_to_analyze = self._extract_text_from_context(context_data)
            
            if hasattr(self, 'summarization_model') and text_to_analyze:
                summary = self.summarization_model(
                    text_to_analyze[:1000],  # Limiter la taille
                    max_length=200,
                    min_length=50,
                    do_sample=False
                )
                
                # Enrichir avec analyse de sentiment
                sentiment_analysis = self._analyze_sentiment_batch(context_data.get('mentions', []))
                
                return self._combine_analysis_results(summary[0]['summary_text'], sentiment_analysis, context_data)
            else:
                return self._analyze_with_rules(prompt, context_data)
                
        except Exception as e:
            logger.error(f"Erreur Transformers: {e}")
            return self._analyze_with_rules(prompt, context_data)
    
    def _analyze_with_rules(self, prompt: str, context_data: Dict) -> str:
        """Analyse basée sur des règles (fallback)"""
        logger.info("Utilisation de l'analyse par règles")
        
        mentions = context_data.get('mentions', [])
        if not mentions:
            return "Aucune donnée à analyser."
        
        # Analyser les patterns
        risk_level = self._assess_risk_level(mentions)
        sentiment_summary = self._analyze_sentiment_distribution(context_data.get('sentiment_distribution', {}))
        engagement_insights = self._analyze_engagement_patterns(mentions)
        temporal_insights = self._analyze_temporal_patterns(context_data.get('time_trends', []))
        
        # Construire le rapport
        analysis = f"""
        Analyse basée sur {len(mentions)} mentions:
        
        NIVEAU DE RISQUE: {risk_level['level']} ({risk_level['score']:.1f}/10)
        Facteurs: {', '.join(risk_level['factors'])}
        
        SENTIMENT: {sentiment_summary}
        
        ENGAGEMENT: {engagement_insights}
        
        TENDANCES: {temporal_insights}
        
        RECOMMANDATIONS:
        {chr(10).join(['- ' + rec for rec in self._generate_recommendations(risk_level, context_data)])}
        """
        
        return analysis.strip()
    
    def _select_best_model(self) -> str:
        """Sélectionner le meilleur modèle Ollama disponible"""
        preferred_models = [
            'mistral:7b', 'llama2:7b', 'codellama:7b', 
            'neural-chat:7b', 'llama2:chat'
        ]
        
        for model in preferred_models:
            if model in self.available_models:
                return model
        
        # Prendre le premier disponible
        return self.available_models[0] if self.available_models else 'llama2'
    
    def _build_enriched_prompt(self, base_prompt: str, context_data: Dict) -> str:
        """Construire un prompt enrichi avec le contexte"""
        mentions = context_data.get('mentions', [])
        keywords = context_data.get('keywords', [])
        
        context_info = f"""
        CONTEXTE D'ANALYSE:
        - Mots-clés surveillés: {', '.join(keywords)}
        - Nombre de mentions: {len(mentions)}
        - Période: {context_data.get('period_days', 30)} jours
        - Sources principales: {', '.join(context_data.get('top_sources', {}).keys())}
        
        DONNÉES À ANALYSER:
        {self._format_mentions_for_prompt(mentions[:10])}  # Top 10 mentions
        
        INSTRUCTION:
        {base_prompt}
        
        RÉPONSE ATTENDUE:
        Fournis une analyse factuelle, objective et structurée en français.
        Base-toi uniquement sur les données fournies.
        Évite les spéculations et reste concret.
        """
        
        return context_info
    
    def _format_mentions_for_prompt(self, mentions: List[Dict]) -> str:
        """Formater les mentions pour le prompt"""
        formatted = []
        for i, mention in enumerate(mentions[:5], 1):
            formatted.append(f"""
            {i}. [{mention.get('source', 'unknown')}] {mention.get('title', 'Sans titre')}
               Auteur: {mention.get('author', 'Inconnu')}
               Sentiment: {mention.get('sentiment', 'N/A')}
               Engagement: {mention.get('engagement_score', 0)}
               Contenu: {mention.get('content', '')[:200]}...
            """)
        
        return '\n'.join(formatted)
    
    def _clean_llm_response(self, response: str) -> str:
        """Nettoyer la réponse du LLM"""
        # Supprimer les balises et artefacts
        response = re.sub(r'<[^>]+>', '', response)
        response = re.sub(r'\*\*([^*]+)\*\*', r'\1', response)
        response = re.sub(r'\*([^*]+)\*', r'\1', response)
        
        # Nettoyer les espaces multiples
        response = re.sub(r'\n\s*\n', '\n\n', response)
        response = re.sub(r' +', ' ', response)
        
        return response.strip()
    
    def _assess_risk_level(self, mentions: List[Dict]) -> Dict:
        """Évaluer le niveau de risque"""
        if not mentions:
            return {'level': 'FAIBLE', 'score': 0, 'factors': []}
        
        risk_score = 0
        risk_factors = []
        
        # Analyser le contenu pour les indicateurs de risque
        all_text = ' '.join([
            f"{m.get('title', '')} {m.get('content', '')}" 
            for m in mentions
        ]).lower()
        
        # Indicateurs de risque élevé
        for indicator in self.risk_indicators['high']:
            if indicator in all_text:
                risk_score += 2
                risk_factors.append(f"Mention de '{indicator}'")
        
        # Indicateurs de risque moyen
        for indicator in self.risk_indicators['medium']:
            if indicator in all_text:
                risk_score += 1
                risk_factors.append(f"Problème potentiel: '{indicator}'")
        
        # Analyser le sentiment
        negative_count = sum(1 for m in mentions if m.get('sentiment') == 'negative')
        negative_ratio = negative_count / len(mentions)
        
        if negative_ratio > 0.6:
            risk_score += 3
            risk_factors.append(f"Sentiment négatif dominant ({negative_ratio:.1%})")
        elif negative_ratio > 0.3:
            risk_score += 1
            risk_factors.append(f"Sentiment négatif significatif ({negative_ratio:.1%})")
        
        # Analyser l'engagement
        high_engagement = [m for m in mentions if m.get('engagement_score', 0) > 1000]
        if len(high_engagement) > len(mentions) * 0.3:
            risk_score += 1
            risk_factors.append("Forte viralité détectée")
        
        # Déterminer le niveau
        if risk_score >= 5:
            level = 'CRITIQUE'
        elif risk_score >= 3:
            level = 'ÉLEVÉ'
        elif risk_score >= 1:
            level = 'MODÉRÉ'
        else:
            level = 'FAIBLE'
        
        return {
            'level': level,
            'score': min(risk_score, 10),
            'factors': risk_factors[:5]  # Top 5 facteurs
        }
    
    def _analyze_sentiment_distribution(self, sentiment_dist: Dict) -> str:
        """Analyser la distribution des sentiments"""
        if not sentiment_dist:
            return "Distribution de sentiment non disponible"
        
        total = sum(sentiment_dist.values())
        if total == 0:
            return "Aucune donnée de sentiment"
        
        pos_pct = sentiment_dist.get('positive', 0) / total * 100
        neg_pct = sentiment_dist.get('negative', 0) / total * 100
        neu_pct = sentiment_dist.get('neutral', 0) / total * 100
        
        # Déterminer la tonalité générale
        if pos_pct > 60:
            tone = "majoritairement positif"
        elif neg_pct > 50:
            tone = "préoccupant avec majorité négative"
        elif neu_pct > 60:
            tone = "neutre, opinion pas encore formée"
        elif abs(pos_pct - neg_pct) < 10:
            tone = "très polarisé"
        else:
            tone = "mitigé"
        
        return f"{tone} ({pos_pct:.0f}% pos, {neu_pct:.0f}% neu, {neg_pct:.0f}% neg)"
    
    def _analyze_engagement_patterns(self, mentions: List[Dict]) -> str:
        """Analyser les patterns d'engagement"""
        if not mentions:
            return "Aucune donnée d'engagement"
        
        engagements = [m.get('engagement_score', 0) for m in mentions]
        
        if not any(engagements):
            return "Engagement faible sur toutes les mentions"
        
        avg_engagement = statistics.mean(engagements)
        max_engagement = max(engagements)
        
        high_engagement_count = sum(1 for e in engagements if e > avg_engagement * 2)
        
        if high_engagement_count > len(mentions) * 0.3:
            pattern = "Forte viralité"
        elif max_engagement > avg_engagement * 5:
            pattern = "Quelques contenus très viraux"
        elif avg_engagement > 100:
            pattern = "Engagement soutenu"
        else:
            pattern = "Engagement modéré"
        
        return f"{pattern} (moy: {avg_engagement:.0f}, max: {max_engagement:.0f})"
    
    def _analyze_temporal_patterns(self, time_trends: List[Dict]) -> str:
        """Analyser les patterns temporels"""
        if not time_trends or len(time_trends) < 3:
            return "Données temporelles insuffisantes"
        
        counts = [t.get('count', 0) for t in time_trends]
        
        # Détecter les tendances
        recent_avg = statistics.mean(counts[-3:])  # 3 derniers points
        earlier_avg = statistics.mean(counts[:3])   # 3 premiers points
        
        if recent_avg > earlier_avg * 1.5:
            trend = "Tendance croissante marquée"
        elif recent_avg < earlier_avg * 0.7:
            trend = "Tendance décroissante"
        else:
            trend = "Tendance stable"
        
        # Détecter les pics
        if counts:
            mean_count = statistics.mean(counts)
            std_count = statistics.stdev(counts) if len(counts) > 1 else 0
            peaks = [c for c in counts if c > mean_count + 2 * std_count]
            
            if peaks:
                trend += f", {len(peaks)} pic(s) détecté(s)"
        
        return trend
    
    def _generate_recommendations(self, risk_level: Dict, context_data: Dict) -> List[str]:
        """Générer des recommandations basées sur l'analyse"""
        recommendations = []
        
        level = risk_level['level']
        
        if level == 'CRITIQUE':
            recommendations.extend([
                "Activation immédiate de la cellule de crise",
                "Communication officielle urgente recommandée",
                "Surveillance renforcée H24"
            ])
        elif level == 'ÉLEVÉ':
            recommendations.extend([
                "Préparation d'une réponse communication",
                "Engagement avec les influenceurs clés",
                "Monitoring continu pendant 48h"
            ])
        elif level == 'MODÉRÉ':
            recommendations.extend([
                "Observation attentive de l'évolution",
                "Préparation de messages de clarification"
            ])
        else:
            recommendations.append("Maintien de la surveillance habituelle")
        
        # Recommandations basées sur le sentiment
        sentiment_dist = context_data.get('sentiment_distribution', {})
        if sentiment_dist:
            total = sum(sentiment_dist.values())
            neg_ratio = sentiment_dist.get('negative', 0) / total if total > 0 else 0
            
            if neg_ratio > 0.5:
                recommendations.append("Stratégie de correction de l'image nécessaire")
            elif neg_ratio > 0.3:
                recommendations.append("Actions proactives pour améliorer la perception")
        
        return recommendations[:5]  # Limiter à 5 recommandations
    
    def _analyze_sentiment_batch(self, mentions: List[Dict]) -> Dict:
        """Analyser le sentiment en lot avec Transformers"""
        if not hasattr(self, 'sentiment_model') or not mentions:
            return {'distribution': {}, 'confidence': 0}
        
        try:
            texts = [
                f"{m.get('title', '')} {m.get('content', '')[:200]}"
                for m in mentions[:20]  # Limiter pour la performance
            ]
            
            results = self.sentiment_model(texts)
            
            # Convertir les résultats
            sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
            confidences = []
            
            for result in results:
                label = result['label'].lower()
                confidence = result['score']
                confidences.append(confidence)
                
                # Mapper les labels du modèle
                if 'pos' in label:
                    sentiment_counts['positive'] += 1
                elif 'neg' in label:
                    sentiment_counts['negative'] += 1
                else:
                    sentiment_counts['neutral'] += 1
            
            return {
                'distribution': sentiment_counts,
                'confidence': statistics.mean(confidences) if confidences else 0
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse sentiment batch: {e}")
            return {'distribution': {}, 'confidence': 0}
    
    def _extract_text_from_context(self, context_data: Dict) -> str:
        """Extraire le texte du contexte pour l'analyse"""
        mentions = context_data.get('mentions', [])
        
        if not mentions:
            return ""
        
        # Extraire et combiner les textes
        texts = []
        for mention in mentions[:10]:  # Limiter pour la performance
            title = mention.get('title', '')
            content = mention.get('content', '')[:300]  # Limiter la taille
            texts.append(f"{title}. {content}")
        
        return ' '.join(texts)
    
    def _combine_analysis_results(self, summary: str, sentiment_analysis: Dict, context_data: Dict) -> str:
        """Combiner les résultats d'analyse"""
        analysis_parts = [f"RÉSUMÉ AUTOMATIQUE: {summary}"]
        
        # Ajouter l'analyse de sentiment
        if sentiment_analysis.get('distribution'):
            dist = sentiment_analysis['distribution']
            total = sum(dist.values())
            if total > 0:
                analysis_parts.append(
                    f"SENTIMENT: {dist['positive']}/{total} positif, "
                    f"{dist['negative']}/{total} négatif, "
                    f"{dist['neutral']}/{total} neutre "
                    f"(confiance: {sentiment_analysis.get('confidence', 0):.1%})"
                )
        
        # Ajouter des insights contextuels
        mentions_count = len(context_data.get('mentions', []))
        sources = list(context_data.get('top_sources', {}).keys())
        
        analysis_parts.append(
            f"CONTEXTE: {mentions_count} mentions analysées "
            f"sur {len(sources)} sources principales"
        )
        
        return '\n\n'.join(analysis_parts)
    
    def is_available(self) -> bool:
        """Vérifier si au moins un service IA est disponible"""
        return self.ollama_available or self.transformers_available


class WebContentExtractor:
    """Extracteur de contenu web intelligent"""
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; BrandMonitor/1.0; +https://example.com/bot)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(ssl=ssl.create_default_context(), limit=5)
        timeout = aiohttp.ClientTimeout(total=20, connect=10)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def extract_content_and_comments(self, url: str) -> Dict:
        """Extraire le contenu et les commentaires d'une URL"""
        try:
            if not self.session:
                logger.error("Session non initialisée")
                return {'error': 'Session non initialisée'}
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    return {'error': f'HTTP {response.status}'}
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extraire le contenu principal
                content = self._extract_main_content(soup)
                
                # Extraire les commentaires
                comments = self._extract_comments(soup)
                
                # Extraire les métadonnées
                metadata = self._extract_metadata(soup, url)
                
                return {
                    'url': url,
                    'content': content,
                    'comments': comments,
                    'metadata': metadata,
                    'extracted_at': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Erreur extraction {url}: {e}")
            return {'error': str(e)}
    
    def _extract_main_content(self, soup: BeautifulSoup) -> Dict:
        """Extraire le contenu principal de l'article"""
        # Supprimer les éléments indésirables
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Extraire le titre
        title = ""
        if soup.title:
            title = soup.title.string.strip()
        elif soup.find('h1'):
            title = soup.find('h1').get_text().strip()
        
        # Extraire le contenu principal
        content_text = ""
        
        # Chercher le contenu dans l'ordre de priorité
        main_selectors = [
            'main', 'article', '[role="main"]',
            '.content', '.post-content', '.article-content',
            '.entry-content', '.post-body'
        ]
        
        for selector in main_selectors:
            main_element = soup.select_one(selector)
            if main_element:
                paragraphs = main_element.find_all(['p', 'div'], string=True)
                content_text = ' '.join([
                    p.get_text().strip() 
                    for p in paragraphs 
                    if len(p.get_text().strip()) > 20
                ])
                break
        
        # Fallback: extraire tous les paragraphes
        if not content_text:
            paragraphs = soup.find_all('p')
            content_text = ' '.join([
                p.get_text().strip() 
                for p in paragraphs 
                if len(p.get_text().strip()) > 20
            ])
        
        return {
            'title': title,
            'text': content_text[:3000],  # Limiter la taille
            'word_count': len(content_text.split()),
            'paragraph_count': len([p for p in content_text.split('\n') if p.strip()])
        }
    
    def _extract_comments(self, soup: BeautifulSoup) -> List[Dict]:
        """Extraire les commentaires"""
        comments = []
        
        # Patterns de sélecteurs de commentaires
        comment_patterns = [
            {'container': '.comments', 'item': '.comment', 'author': '.author', 'text': '.text'},
            {'container': '#comments', 'item': '.comment-item', 'author': '.comment-author', 'text': '.comment-text'},
            {'container': '[class*="comment"]', 'item': '[class*="comment-item"]', 'author': '[class*="author"]', 'text': '[class*="text"]'},
            {'container': '.discussion', 'item': '.reply', 'author': '.user', 'text': '.message'},
        ]
        
        for pattern in comment_patterns:
            container = soup.select_one(pattern['container'])
            if not container:
                continue
            
            comment_items = container.select(pattern['item'])
            
            for item in comment_items[:20]:  # Limiter à 20 commentaires
                try:
                    author_elem = item.select_one(pattern['author'])
                    text_elem = item.select_one(pattern['text'])
                    
                    if text_elem:
                        comment_text = text_elem.get_text().strip()
                        if len(comment_text) > 10:  # Éviter les commentaires trop courts
                            author = author_elem.get_text().strip() if author_elem else 'Anonyme'
                            
                            # Extraire les likes/votes si disponibles
                            likes = self._extract_comment_likes(item)
                            
                            comments.append({
                                'author': author[:50],  # Limiter la taille
                                'text': comment_text[:500],  # Limiter la taille
                                'likes': likes,
                                'timestamp': self._extract_comment_timestamp(item),
                                'replies_count': self._count_replies(item)
                            })
                            
                except Exception as e:
                    logger.debug(f"Erreur extraction commentaire: {e}")
                    continue
            
            if comments:  # Si on a trouvé des commentaires, arrêter
                break
        
        return comments
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extraire les métadonnées de la page"""
        metadata = {
            'domain': urlparse(url).netloc,
            'url': url
        }
        
        # Extraire la description
        desc_meta = soup.find('meta', attrs={'name': 'description'})
        if desc_meta:
            metadata['description'] = desc_meta.get('content', '')[:200]
        
        # Extraire l'auteur
        author_meta = soup.find('meta', attrs={'name': 'author'})
        if author_meta:
            metadata['author'] = author_meta.get('content', '')
        
        # Extraire la date de publication
        date_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="publishdate"]',
            'time[datetime]',
            '.published-date',
            '.date'
        ]
        
        for selector in date_selectors:
            elem = soup.select_one(selector)
            if elem:
                date_value = elem.get('content') or elem.get('datetime') or elem.get_text()
                if date_value:
                    metadata['published_date'] = date_value
                    break
        
        # Extraire la langue
        html_elem = soup.find('html')
        if html_elem:
            metadata['language'] = html_elem.get('lang', 'unknown')
        
        return metadata
    
    def _extract_comment_likes(self, comment_elem) -> int:
        """Extraire le nombre de likes d'un commentaire"""
        like_selectors = [
            '.likes', '.upvotes', '.score', '.points',
            '[class*="like"]', '[class*="vote"]', '[class*="score"]'
        ]
        
        for selector in like_selectors:
            like_elem = comment_elem.select_one(selector)
            if like_elem:
                text = like_elem.get_text().strip()
                numbers = re.findall(r'\d+', text)
                if numbers:
                    return int(numbers[0])
        
        return 0
    
    def _extract_comment_timestamp(self, comment_elem) -> Optional[str]:
        """Extraire le timestamp d'un commentaire"""
        time_selectors = [
            'time', '.timestamp', '.date', '[class*="time"]', '[class*="date"]'
        ]
        
        for selector in time_selectors:
            time_elem = comment_elem.select_one(selector)
            if time_elem:
                return time_elem.get('datetime') or time_elem.get_text().strip()
        
        return None
    
    def _count_replies(self, comment_elem) -> int:
        """Compter les réponses à un commentaire"""
        reply_selectors = [
            '.replies', '.children', '[class*="reply"]', '[class*="child"]'
        ]
        
        for selector in reply_selectors:
            replies_container = comment_elem.select_one(selector)
            if replies_container:
                replies = replies_container.select('[class*="comment"], [class*="reply"]')
                return len(replies)
        
        return 0


class IntelligentAnalysisAgent:
    """Agent principal d'analyse intelligente"""
    
    def __init__(self):
        self.llm_service = SovereignLLMService()
        self.web_extractor = WebContentExtractor()
        
    async def generate_intelligent_report(self, context: AnalysisContext, db_session: Session = None) -> Dict:
        """Générer un rapport intelligent complet"""
        logger.info("Début génération rapport intelligent")
        
        # 1. Enrichir le contexte avec le contenu web
        if db_session:
            context = await self._enrich_context_with_web_content(context, db_session)
        
        # 2. Générer les analyses spécialisées
        analyses = {}
        
        # Analyse de sentiment avancée
        analyses['sentiment'] = await self._analyze_sentiment_advanced(context)
        
        # Analyse des tendances
        analyses['trends'] = await self._analyze_trends(context)
        
        # Analyse des influenceurs
        analyses['influencers'] = await self._analyze_influencers(context)
        
        # Analyse du contenu web
        if context.web_content:
            analyses['web_content'] = await self._analyze_web_content(context)
        
        # 3. Synthèse intelligente
        analyses['synthesis'] = await self._generate_synthesis(context, analyses)
        
        # 4. Recommandations actionnables
        analyses['recommendations'] = await self._generate_recommendations(context, analyses)
        
        logger.info("Rapport intelligent généré avec succès")
        return analyses
    
    async def _enrich_context_with_web_content(self, context: AnalysisContext, db_session: Session) -> AnalysisContext:
        """Enrichir le contexte avec le contenu web extrait"""
        web_contents = []
        
        try:
            # Extraire les URLs uniques des mentions
            urls = set()
            for mention in context.mentions:
                url = mention.get('source_url')
                if url and url.startswith('http'):
                    urls.add(url)
            
            # Limiter le nombre d'URLs pour éviter la surcharge
            urls_to_process = list(urls)[:10]
            
            logger.info(f"Extraction contenu web: {len(urls_to_process)} URLs")
            
            async with self.web_extractor as extractor:
                # Traiter les URLs en parallèle avec limitation
                semaphore = asyncio.Semaphore(3)  # Max 3 requêtes simultanées
                
                async def extract_with_semaphore(url):
                    async with semaphore:
                        return await extractor.extract_content_and_comments(url)
                
                tasks = [extract_with_semaphore(url) for url in urls_to_process]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, dict) and 'content' in result:
                        web_contents.append(result)
                    elif isinstance(result, Exception):
                        logger.debug(f"Erreur extraction: {result}")
            
            logger.info(f"Contenu web extrait: {len(web_contents)} pages")
            
        except Exception as e:
            logger.error(f"Erreur enrichissement contenu web: {e}")
        
        # Mettre à jour le contexte
        context.web_content = web_contents
        return context
    
    async def _analyze_sentiment_advanced(self, context: AnalysisContext) -> Dict:
        """Analyse de sentiment avancée"""
        prompt = f"""
        Analyse le sentiment de ces {len(context.mentions)} mentions sur {context.period_days} jours.
        
        Distribution actuelle:
        - Positif: {context.sentiment_distribution.get('positive', 0)}
        - Neutre: {context.sentiment_distribution.get('neutral', 0)}
        - Négatif: {context.sentiment_distribution.get('negative', 0)}
        
        Fournis une analyse nuancée du sentiment, identifie les émotions dominantes,
        et évalue la polarisation de l'opinion publique.
        """
        
        analysis = await self.llm_service.analyze_with_local_llm(prompt, {
            'mentions': context.mentions,
            'sentiment_distribution': context.sentiment_distribution,
            'period_days': context.period_days
        })
        
        return {
            'type': 'sentiment_analysis',
            'analysis': analysis,
            'distribution': context.sentiment_distribution,
            'insights': self._extract_sentiment_insights(context)
        }
    
    async def _analyze_trends(self, context: AnalysisContext) -> Dict:
        """Analyse des tendances temporelles"""
        if not context.time_trends:
            return {
                'type': 'trend_analysis',
                'analysis': 'Données de tendance insuffisantes',
                'trends': []
            }
        
        prompt = f"""
        Analyse ces tendances temporelles sur {context.period_days} jours:
        
        Évolution: {', '.join([f"{t.get('date')}: {t.get('count')}" for t in context.time_trends[-7:]])}
        
        Identifie les patterns, pics d'activité, et signaux d'alerte.
        Propose des hypothèses sur les causes des variations.
        """
        
        analysis = await self.llm_service.analyze_with_local_llm(prompt, {
            'time_trends': context.time_trends,
            'mentions': context.mentions,
            'period_days': context.period_days
        })
        
        return {
            'type': 'trend_analysis',
            'analysis': analysis,
            'trends': context.time_trends,
            'patterns': self._detect_trend_patterns(context.time_trends)
        }
    
    async def _analyze_influencers(self, context: AnalysisContext) -> Dict:
        """Analyse des influenceurs"""
        if not context.influencers_data:
            return {
                'type': 'influencer_analysis',
                'analysis': 'Aucun influenceur identifié',
                'influencers': []
            }
        
        top_influencers = context.influencers_data[:10]
        
        prompt = f"""
        Analyse ces {len(top_influencers)} top influenceurs:
        
        {chr(10).join([f"- {inf.get('author')} ({inf.get('source')}): {inf.get('total_engagement')} engagement, sentiment {inf.get('sentiment_score', 0)}%" for inf in top_influencers])}
        
        Évalue leur impact, identifie les risques et opportunités,
        et propose des stratégies d'engagement.
        """
        
        analysis = await self.llm_service.analyze_with_local_llm(prompt, {
            'influencers_data': context.influencers_data,
            'mentions': context.mentions
        })
        
        return {
            'type': 'influencer_analysis',
            'analysis': analysis,
            'top_influencers': top_influencers,
            'risk_assessment': self._assess_influencer_risks(context.influencers_data)
        }
    
    async def _analyze_web_content(self, context: AnalysisContext) -> Dict:
        """Analyse du contenu web extrait"""
        if not context.web_content:
            return {
                'type': 'web_content_analysis',
                'analysis': 'Aucun contenu web analysé',
                'content': []
            }
        
        # Résumer le contenu web
        total_comments = sum(len(wc.get('comments', [])) for wc in context.web_content)
        domains = list(set(wc.get('metadata', {}).get('domain', '') for wc in context.web_content))
        
        prompt = f"""
        Analyse ce contenu web extrait:
        
        - {len(context.web_content)} articles analysés
        - {total_comments} commentaires extraits
        - Domaines: {', '.join(domains[:5])}
        
        Compare le sentiment des articles vs les commentaires.
        Identifie les discussions les plus engageantes.
        Évalue l'authenticité des interactions.
        """
        
        analysis = await self.llm_service.analyze_with_local_llm(prompt, {
            'web_content': context.web_content,
            'total_comments': total_comments
        })
        
        return {
            'type': 'web_content_analysis',
            'analysis': analysis,
            'articles_count': len(context.web_content),
            'comments_count': total_comments,
            'top_domains': domains[:5],
            'engagement_analysis': self._analyze_web_engagement(context.web_content)
        }
    
    async def _generate_synthesis(self, context: AnalysisContext, analyses: Dict) -> Dict:
        """Générer une synthèse intelligente"""
        prompt = f"""
        Synthétise cette analyse complète de {context.total_mentions} mentions 
        sur {context.period_days} jours pour les mots-clés: {', '.join(context.keywords)}
        
        Points clés des analyses:
        - Sentiment: {analyses.get('sentiment', {}).get('analysis', 'N/A')[:100]}...
        - Tendances: {analyses.get('trends', {}).get('analysis', 'N/A')[:100]}...
        - Influenceurs: {analyses.get('influencers', {}).get('analysis', 'N/A')[:100]}...
        
        Fournis une synthèse exécutive en 3-4 points clés avec un niveau de priorité.
        """
        
        synthesis = await self.llm_service.analyze_with_local_llm(prompt, {
            'context': context.__dict__,
            'analyses': analyses
        })
        
        # Déterminer le niveau de priorité
        priority = self._determine_priority_level(context, analyses)
        
        return {
            'type': 'executive_synthesis',
            'synthesis': synthesis,
            'priority_level': priority,
            'key_metrics': {
                'total_mentions': context.total_mentions,
                'period_days': context.period_days,
                'web_content_analyzed': len(context.web_content) if context.web_content else 0,
                'top_sources': list(context.top_sources.keys())[:3]
            }
        }
    
    async def _generate_recommendations(self, context: AnalysisContext, analyses: Dict) -> Dict:
        """Générer des recommandations actionnables"""
        priority = analyses.get('synthesis', {}).get('priority_level', 'NORMAL')
        
        prompt = f"""
        Basé sur cette analyse complète (priorité: {priority}), 
        fournis 3-5 recommandations actionnables concrètes.
        
        Classe-les par urgence:
        - Actions immédiates (0-24h)
        - Actions court terme (1-7 jours)  
        - Actions long terme (1+ mois)
        
        Sois spécifique et actionnable.
        """
        
        recommendations_text = await self.llm_service.analyze_with_local_llm(prompt, {
            'context': context.__dict__,
            'analyses': analyses,
            'priority': priority
        })
        
        return {
            'type': 'actionable_recommendations',
            'recommendations': recommendations_text,
            'priority_level': priority,
            'urgent_actions': self._extract_urgent_actions(context, analyses)
        }
    
    def _extract_sentiment_insights(self, context: AnalysisContext) -> List[str]:
        """Extraire des insights de sentiment"""
        insights = []
        
        dist = context.sentiment_distribution
        total = sum(dist.values()) if dist.values() else 1
        
        if total > 0:
            pos_pct = dist.get('positive', 0) / total * 100
            neg_pct = dist.get('negative', 0) / total * 100
            
            if pos_pct > 70:
                insights.append(f"Sentiment très positif ({pos_pct:.0f}%) - Opportunité de capitaliser")
            elif neg_pct > 60:
                insights.append(f"Sentiment critique ({neg_pct:.0f}%) - Gestion de crise nécessaire")
            elif abs(pos_pct - neg_pct) < 10:
                insights.append("Opinion très polarisée - Communication ciblée requise")
        
        return insights
    
    def _detect_trend_patterns(self, time_trends: List[Dict]) -> Dict:
        """Détecter les patterns dans les tendances"""
        if not time_trends or len(time_trends) < 3:
            return {'pattern': 'insufficient_data'}
        
        counts = [t.get('count', 0) for t in time_trends]
        
        # Calculs statistiques
        mean_count = statistics.mean(counts)
        
        # Détecter les pics
        peaks = []
        for i, count in enumerate(counts):
            if count > mean_count * 1.5:
                peaks.append({'index': i, 'value': count, 'date': time_trends[i].get('date')})
        
        # Tendance générale
        if len(counts) >= 2:
            recent_avg = statistics.mean(counts[-3:])
            earlier_avg = statistics.mean(counts[:3])
            
            if recent_avg > earlier_avg * 1.3:
                trend = 'increasing'
            elif recent_avg < earlier_avg * 0.7:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'unknown'
        
        return {
            'pattern': trend,
            'peaks_detected': len(peaks),
            'peaks': peaks[:5],  # Top 5 pics
            'mean_activity': mean_count,
            'volatility': statistics.stdev(counts) if len(counts) > 1 else 0
        }
    
    def _assess_influencer_risks(self, influencers_data: List[Dict]) -> Dict:
        """Évaluer les risques liés aux influenceurs"""
        if not influencers_data:
            return {'high_risk': [], 'medium_risk': [], 'low_risk': []}
        
        high_risk = []
        medium_risk = []
        low_risk = []
        
        for influencer in influencers_data:
            sentiment_score = influencer.get('sentiment_score', 50)
            engagement = influencer.get('total_engagement', 0)
            
            # Critères de risque
            if sentiment_score < 30 and engagement > 1000:
                high_risk.append(influencer)
            elif sentiment_score < 50 or engagement > 5000:
                medium_risk.append(influencer)
            else:
                low_risk.append(influencer)
        
        return {
            'high_risk': high_risk,
            'medium_risk': medium_risk,
            'low_risk': low_risk,
            'total_analyzed': len(influencers_data)
        }
    
    def _analyze_web_engagement(self, web_content: List[Dict]) -> Dict:
        """Analyser l'engagement du contenu web"""
        if not web_content:
            return {}
        
        total_comments = 0
        total_likes = 0
        active_commenters = set()
        
        for content in web_content:
            comments = content.get('comments', [])
            total_comments += len(comments)
            
            for comment in comments:
                total_likes += comment.get('likes', 0)
                active_commenters.add(comment.get('author', 'unknown'))
        
        return {
            'total_comments': total_comments,
            'total_likes': total_likes,
            'unique_commenters': len(active_commenters),
            'avg_likes_per_comment': total_likes / max(total_comments, 1),
            'engagement_rate': len(active_commenters) / max(total_comments, 1) if total_comments > 0 else 0
        }
    
    def _determine_priority_level(self, context: AnalysisContext, analyses: Dict) -> str:
        """Déterminer le niveau de priorité global"""
        priority_score = 0
        
        # Facteurs de risque
        
        # 1. Sentiment négatif
        dist = context.sentiment_distribution
        total = sum(dist.values()) if dist.values() else 1
        if total > 0:
            neg_ratio = dist.get('negative', 0) / total
            if neg_ratio > 0.6:
                priority_score += 3
            elif neg_ratio > 0.4:
                priority_score += 2
            elif neg_ratio > 0.2:
                priority_score += 1
        
        # 2. Volume de mentions élevé
        if context.total_mentions > 1000:
            priority_score += 2
        elif context.total_mentions > 100:
            priority_score += 1
        
        # 3. Influenceurs à risque
        influencer_risks = analyses.get('influencers', {}).get('risk_assessment', {})
        high_risk_count = len(influencer_risks.get('high_risk', []))
        if high_risk_count > 2:
            priority_score += 3
        elif high_risk_count > 0:
            priority_score += 1
        
        # 4. Pics d'activité
        trend_patterns = analyses.get('trends', {}).get('patterns', {})
        peaks_count = trend_patterns.get('peaks_detected', 0)
        if peaks_count > 3:
            priority_score += 2
        elif peaks_count > 1:
            priority_score += 1
        
        # Déterminer le niveau
        if priority_score >= 6:
            return 'CRITIQUE'
        elif priority_score >= 4:
            return 'ÉLEVÉ'
        elif priority_score >= 2:
            return 'MODÉRÉ'
        else:
            return 'NORMAL'
    
    def _extract_urgent_actions(self, context: AnalysisContext, analyses: Dict) -> List[str]:
        """Extraire les actions urgentes"""
        urgent_actions = []
        
        priority = analyses.get('synthesis', {}).get('priority_level', 'NORMAL')
        
        if priority == 'CRITIQUE':
            urgent_actions.extend([
                "Activation cellule de crise dans les 2 heures",
                "Communication officielle urgente",
                "Monitoring H24 activé"
            ])
        
        # Actions basées sur les risques influenceurs
        influencer_risks = analyses.get('influencers', {}).get('risk_assessment', {})
        high_risk_influencers = influencer_risks.get('high_risk', [])
        if high_risk_influencers:
            urgent_actions.append(
                f"Contact immédiat avec {len(high_risk_influencers)} influenceur(s) critique(s)"
            )
        
        # Actions basées sur le sentiment
        dist = context.sentiment_distribution
        total = sum(dist.values()) if dist.values() else 1
        if total > 0:
            neg_ratio = dist.get('negative', 0) / total
            if neg_ratio > 0.6:
                urgent_actions.append("Stratégie de gestion de crise - sentiment majoritairement négatif")
        
        return urgent_actions[:5]  # Limiter à 5 actions urgentes