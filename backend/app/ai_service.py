"""
Service IA pour les agents de génération de rapports intelligents
Utilise des modèles LLM open source (Ollama + HuggingFace Transformers en fallback)
"""

import logging
import json
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import re

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


class LLMService:
    """Service de gestion des modèles LLM"""
    
    def __init__(self):
        self.ollama_available = False
        self.hf_available = False
        self.current_model = None
        self.initialize_models()
    
    def initialize_models(self):
        """Initialise les modèles disponibles"""
        # Essayer Ollama en premier
        try:
            import ollama
            self.ollama_client = ollama.Client()
            # Tester la connexion
            models = self.ollama_client.list()
            self.ollama_available = True
            logger.info("Ollama disponible avec les modèles : %s", [m['name'] for m in models['models']])
        except Exception as e:
            logger.warning(f"Ollama non disponible : {e}")
        
        # Fallback vers HuggingFace Transformers
        try:
            from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
            import torch
            
            self.device = 0 if torch.cuda.is_available() else -1
            self.hf_available = True
            logger.info("HuggingFace Transformers disponible (GPU: %s)", torch.cuda.is_available())
        except ImportError:
            logger.warning("HuggingFace Transformers non disponible")
    
    async def generate_text(self, prompt: str, model: str = "mistral:7b", max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Génère du texte avec le modèle spécifié"""
        try:
            if self.ollama_available:
                return await self._generate_with_ollama(prompt, model, max_tokens, temperature)
            elif self.hf_available:
                return await self._generate_with_hf(prompt, max_tokens, temperature)
            else:
                logger.error("Aucun modèle LLM disponible")
                return "Erreur : Aucun modèle IA disponible pour l'analyse."
        except Exception as e:
            logger.error(f"Erreur génération de texte : {e}")
            return f"Erreur d'analyse : {str(e)}"
    
    async def _generate_with_ollama(self, prompt: str, model: str, max_tokens: int, temperature: float) -> str:
        """Génération avec Ollama"""
        try:
            response = self.ollama_client.generate(
                model=model,
                prompt=prompt,
                options={
                    'num_predict': max_tokens,
                    'temperature': temperature,
                    'stop': ['</analysis>', '<|endoftext|>']
                }
            )
            return response['response'].strip()
        except Exception as e:
            logger.error(f"Erreur Ollama : {e}")
            # Si le modèle n'existe pas, essayer avec un modèle par défaut
            if "model not found" in str(e).lower():
                try:
                    # Essayer de télécharger le modèle
                    self.ollama_client.pull(model)
                    response = self.ollama_client.generate(model=model, prompt=prompt)
                    return response['response'].strip()
                except:
                    # Utiliser un modèle disponible
                    models = self.ollama_client.list()
                    if models['models']:
                        fallback_model = models['models'][0]['name']
                        response = self.ollama_client.generate(model=fallback_model, prompt=prompt)
                        return response['response'].strip()
            raise e
    
    async def _generate_with_hf(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Génération avec HuggingFace Transformers"""
        try:
            from transformers import pipeline
            
            # Utiliser un modèle optimisé pour l'analyse
            if not hasattr(self, 'hf_pipeline'):
                self.hf_pipeline = pipeline(
                    "text-generation",
                    model="microsoft/DialoGPT-small",  # Modèle léger
                    device=self.device,
                    trust_remote_code=True
                )
            
            outputs = self.hf_pipeline(
                prompt,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True,
                pad_token_id=self.hf_pipeline.tokenizer.eos_token_id
            )
            
            generated_text = outputs[0]['generated_text']
            # Retirer le prompt original
            result = generated_text[len(prompt):].strip()
            return result
        except Exception as e:
            logger.error(f"Erreur HuggingFace : {e}")
            return "Modèle HuggingFace indisponible pour l'analyse."
    
    def is_available(self) -> bool:
        """Vérifie si au moins un modèle est disponible"""
        return self.ollama_available or self.hf_available


class BaseAgent:
    """Agent IA de base pour l'analyse"""
    
    def __init__(self, llm_service: LLMService, agent_name: str):
        self.llm_service = llm_service
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"agent.{agent_name}")
    
    def _clean_analysis_text(self, text: str) -> str:
        """Nettoie le texte généré par l'IA"""
        # Supprimer les balises et artifacts
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Markdown bold
        text = re.sub(r'\*([^*]+)\*', r'\1', text)      # Markdown italic
        
        # Nettoyer les espaces et lignes vides
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n'.join(lines)
    
    async def analyze(self, context: AnalysisContext) -> Dict[str, Any]:
        """Méthode d'analyse à implémenter par chaque agent"""
        raise NotImplementedError


class SentimentAnalysisAgent(BaseAgent):
    """Agent spécialisé dans l'analyse de sentiment avancée"""
    
    def __init__(self, llm_service: LLMService):
        super().__init__(llm_service, "sentiment_analyst")
    
    async def analyze(self, context: AnalysisContext) -> Dict[str, Any]:
        """Analyse approfondie des sentiments avec insights contextuels"""
        
        # Préparer les données de sentiment
        sentiment_data = context.sentiment_distribution
        total_mentions = sum(sentiment_data.values()) if sentiment_data.values() else 1
        
        # Extraire quelques mentions représentatives
        sample_positive = [m for m in context.mentions if m.get('sentiment') == 'positive'][:3]
        sample_negative = [m for m in context.mentions if m.get('sentiment') == 'negative'][:3]
        
        prompt = f"""Tu es un expert analyste en communication et opinion publique. Analyse cette distribution de sentiment et rédige une analyse approfondie.

DONNÉES CONTEXTUELLES:
- Période analysée: {context.period_days} jours
- Mots-clés surveillés: {', '.join(context.keywords)}
- Total mentions: {context.total_mentions}

DISTRIBUTION SENTIMENT:
- Positif: {sentiment_data.get('positive', 0)} ({sentiment_data.get('positive', 0)/total_mentions*100:.1f}%)
- Neutre: {sentiment_data.get('neutral', 0)} ({sentiment_data.get('neutral', 0)/total_mentions*100:.1f}%)
- Négatif: {sentiment_data.get('negative', 0)} ({sentiment_data.get('negative', 0)/total_mentions*100:.1f}%)

EXEMPLES MENTIONS POSITIVES:
{chr(10).join([f"- {m.get('title', '')} (source: {m.get('source', '')})" for m in sample_positive])}

EXEMPLES MENTIONS NÉGATIVES:
{chr(10).join([f"- {m.get('title', '')} (source: {m.get('source', '')})" for m in sample_negative])}

INSTRUCTIONS:
1. Analyse la polarisation de l'opinion (forte/modérée/équilibrée)
2. Identifie les signaux d'alarme ou d'opportunité
3. Détecte les nuances dans les sentiments (pas seulement pos/neg/neutre)
4. Propose des insights stratégiques basés sur cette distribution
5. Évite les phrases génériques, sois spécifique aux données

Rédige une analyse en français, structurée et actionnable en 200-300 mots."""

        analysis_text = await self.llm_service.generate_text(prompt, max_tokens=500)
        cleaned_text = self._clean_analysis_text(analysis_text)
        
        return {
            'type': 'sentiment_analysis',
            'analysis': cleaned_text,
            'key_insights': self._extract_key_insights(sentiment_data, total_mentions),
            'sentiment_score': self._calculate_sentiment_score(sentiment_data),
            'polarization_level': self._assess_polarization(sentiment_data)
        }
    
    def _extract_key_insights(self, sentiment_data: Dict, total: int) -> List[str]:
        """Extrait des insights clés basés sur les données"""
        insights = []
        
        pos_pct = sentiment_data.get('positive', 0) / total * 100
        neg_pct = sentiment_data.get('negative', 0) / total * 100
        neu_pct = sentiment_data.get('neutral', 0) / total * 100
        
        if pos_pct > 60:
            insights.append(f"Opinion très favorable ({pos_pct:.1f}%) - Opportunité de capitaliser")
        elif neg_pct > 50:
            insights.append(f"Sentiment critique prédominant ({neg_pct:.1f}%) - Gestion de crise nécessaire")
        elif neu_pct > 60:
            insights.append(f"Audience indécise ({neu_pct:.1f}%) - Potentiel de conversion élevé")
        
        if abs(pos_pct - neg_pct) < 10:
            insights.append("Opinion publique très polarisée - Communication ciblée recommandée")
        
        return insights
    
    def _calculate_sentiment_score(self, sentiment_data: Dict) -> float:
        """Calcule un score de sentiment global"""
        total = sum(sentiment_data.values())
        if total == 0:
            return 0
        
        score = (sentiment_data.get('positive', 0) * 1 + 
                sentiment_data.get('neutral', 0) * 0 + 
                sentiment_data.get('negative', 0) * -1) / total
        return round(score, 3)
    
    def _assess_polarization(self, sentiment_data: Dict) -> str:
        """Évalue le niveau de polarisation"""
        total = sum(sentiment_data.values())
        if total == 0:
            return "indéterminé"
        
        pos_pct = sentiment_data.get('positive', 0) / total
        neg_pct = sentiment_data.get('negative', 0) / total
        neu_pct = sentiment_data.get('neutral', 0) / total
        
        if neu_pct > 0.6:
            return "faible"
        elif abs(pos_pct - neg_pct) < 0.15:
            return "élevée"
        else:
            return "modérée"


class TrendAnalysisAgent(BaseAgent):
    """Agent spécialisé dans l'analyse des tendances temporelles"""
    
    def __init__(self, llm_service: LLMService):
        super().__init__(llm_service, "trend_analyst")
    
    async def analyze(self, context: AnalysisContext) -> Dict[str, Any]:
        """Analyse les tendances et évolutions temporelles"""
        
        trends = context.time_trends
        if not trends:
            return {'type': 'trend_analysis', 'analysis': 'Données de tendance insuffisantes.'}
        
        # Calculer les métriques de tendance
        trend_metrics = self._calculate_trend_metrics(trends)
        
        prompt = f"""Tu es un expert analyste en tendances et signaux faibles. Analyse cette évolution temporelle et identifie les patterns significatifs.

DONNÉES TEMPORELLES ({context.period_days} jours):
Evolution des mentions:
{chr(10).join([f"- {t.get('date', '')}: {t.get('count', 0)} mentions" for t in trends[-7:]])}

MÉTRIQUES CALCULÉES:
- Variation totale: {trend_metrics['total_change']:.1f}%
- Volatilité: {trend_metrics['volatility']:.1f}
- Pics détectés: {trend_metrics['peaks_detected']}
- Tendance générale: {trend_metrics['overall_trend']}
- Jours de forte activité: {trend_metrics['high_activity_days']}

CONTEXTE:
- Mots-clés: {', '.join(context.keywords)}
- Période: {context.period_days} jours

INSTRUCTIONS:
1. Identifie les patterns temporels significatifs (pics, creux, cycles)
2. Détermine les possibles déclencheurs d'évènements
3. Évalue la prévisibilité des tendances
4. Détecte les signaux d'alerte précoce
5. Propose des hypothèses sur les causes des variations
6. Sois spécifique aux données, évite les généralités

Rédige une analyse perspicace en français en 250-350 mots."""

        analysis_text = await self.llm_service.generate_text(prompt, max_tokens=600)
        cleaned_text = self._clean_analysis_text(analysis_text)
        
        return {
            'type': 'trend_analysis',
            'analysis': cleaned_text,
            'trend_metrics': trend_metrics,
            'predictions': self._generate_predictions(trends),
            'alert_level': self._assess_alert_level(trend_metrics)
        }
    
    def _calculate_trend_metrics(self, trends: List[Dict]) -> Dict[str, Any]:
        """Calcule les métriques de tendance"""
        if len(trends) < 2:
            return {'total_change': 0, 'volatility': 0, 'peaks_detected': 0, 'overall_trend': 'stable'}
        
        values = [t.get('count', 0) for t in trends]
        
        # Variation totale
        total_change = ((values[-1] - values[0]) / max(values[0], 1)) * 100
        
        # Volatilité (écart-type relatif)
        import statistics
        volatility = statistics.stdev(values) / max(statistics.mean(values), 1) * 100
        
        # Détection de pics
        peaks = 0
        for i in range(1, len(values)-1):
            if values[i] > values[i-1] and values[i] > values[i+1] and values[i] > statistics.mean(values) * 1.5:
                peaks += 1
        
        # Tendance générale
        if total_change > 20:
            trend = "croissante"
        elif total_change < -20:
            trend = "décroissante"
        else:
            trend = "stable"
        
        # Jours de forte activité (> moyenne + 1 écart-type)
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values) if len(values) > 1 else 0
        high_activity_days = sum(1 for v in values if v > mean_val + std_val)
        
        return {
            'total_change': total_change,
            'volatility': volatility,
            'peaks_detected': peaks,
            'overall_trend': trend,
            'high_activity_days': high_activity_days,
            'mean_daily': mean_val,
            'max_daily': max(values),
            'min_daily': min(values)
        }
    
    def _generate_predictions(self, trends: List[Dict]) -> Dict[str, Any]:
        """Génère des prédictions basées sur les tendances"""
        if len(trends) < 3:
            return {'confidence': 'low', 'prediction': 'Données insuffisantes'}
        
        values = [t.get('count', 0) for t in trends[-7:]]  # 7 derniers jours
        
        # Tendance récente
        recent_trend = (values[-1] - values[0]) / max(values[0], 1) * 100
        
        if abs(recent_trend) < 10:
            prediction = "Maintien du niveau actuel attendu"
            confidence = "medium"
        elif recent_trend > 20:
            prediction = "Poursuite probable de la croissance à court terme"
            confidence = "medium"
        else:
            prediction = "Possible ralentissement ou stabilisation"
            confidence = "low"
        
        return {
            'prediction': prediction,
            'confidence': confidence,
            'recent_trend': recent_trend
        }
    
    def _assess_alert_level(self, metrics: Dict) -> str:
        """Évalue le niveau d'alerte basé sur les métriques"""
        if metrics['peaks_detected'] > 2 or metrics['volatility'] > 100:
            return "élevé"
        elif metrics['volatility'] > 50 or abs(metrics['total_change']) > 50:
            return "modéré"
        else:
            return "normal"


class InfluencerAnalysisAgent(BaseAgent):
    """Agent spécialisé dans l'analyse des influenceurs"""
    
    def __init__(self, llm_service: LLMService):
        super().__init__(llm_service, "influencer_analyst")
    
    async def analyze(self, context: AnalysisContext) -> Dict[str, Any]:
        """Analyse les influenceurs et leur impact"""
        
        influencers = context.influencers_data
        if not influencers:
            return {'type': 'influencer_analysis', 'analysis': 'Aucun influenceur identifié sur cette période.'}
        
        # Analyser les top influenceurs
        top_influencers = influencers[:5]
        risk_analysis = self._assess_influencer_risks(influencers)
        
        prompt = f"""Tu es un expert en analyse d'influence et de réputation numérique. Analyse ces profils d'influenceurs et leur impact potentiel.

TOP INFLUENCEURS IDENTIFIÉS:
{chr(10).join([f"- {inf.get('author', 'Inconnu')} ({inf.get('source', '')}) : {inf.get('total_engagement', 0)} engagement, {inf.get('mention_count', 0)} mentions" for inf in top_influenceurs])}

ANALYSE DE RISQUE:
- Influenceurs à risque élevé: {len(risk_analysis['high_risk'])}
- Influenceurs modérés: {len(risk_analysis['medium_risk'])}
- Sentiment majoritaire: {risk_analysis['majority_sentiment']}
- Portée estimée totale: {risk_analysis['estimated_reach']}

CONTEXTE:
- Mots-clés surveillés: {', '.join(context.keywords)}
- Période: {context.period_days} jours
- Sources principales: {', '.join(context.top_sources.keys())}

INSTRUCTIONS:
1. Identifie les influenceurs les plus impactants (positivement/négativement)
2. Évalue le potentiel de viralisation et l'effet de réseau
3. Détermine les profils à surveiller en priorité
4. Analyse la cohérence des messages entre influenceurs
5. Propose des stratégies d'engagement spécifiques
6. Évalue les risques de réputation et les opportunités

Rédige une analyse stratégique en français en 300-400 mots."""

        analysis_text = await self.llm_service.generate_text(prompt, max_tokens=700)
        cleaned_text = self._clean_analysis_text(analysis_text)
        
        return {
            'type': 'influencer_analysis',
            'analysis': cleaned_text,
            'risk_assessment': risk_analysis,
            'key_influencers': self._format_key_influencers(top_influencers),
            'recommended_actions': self._generate_action_recommendations(risk_analysis)
        }
    
    def _assess_influencer_risks(self, influencers: List[Dict]) -> Dict[str, Any]:
        """Évalue les risques liés aux influenceurs"""
        high_risk = []
        medium_risk = []
        low_risk = []
        
        total_engagement = 0
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        for inf in influencers:
            engagement = inf.get('total_engagement', 0)
            sentiment_score = inf.get('sentiment_score', 50)  # Score sur 100
            
            total_engagement += engagement
            
            # Classifier le sentiment majoritaire
            if sentiment_score > 70:
                sentiment_counts['positive'] += 1
            elif sentiment_score < 30:
                sentiment_counts['negative'] += 1
            else:
                sentiment_counts['neutral'] += 1
            
            # Évaluer le risque
            if sentiment_score < 30 and engagement > 1000:
                high_risk.append(inf)
            elif sentiment_score < 50 or engagement > 5000:
                medium_risk.append(inf)
            else:
                low_risk.append(inf)
        
        # Déterminer le sentiment majoritaire
        majority_sentiment = max(sentiment_counts, key=sentiment_counts.get)
        
        return {
            'high_risk': high_risk,
            'medium_risk': medium_risk,
            'low_risk': low_risk,
            'majority_sentiment': majority_sentiment,
            'estimated_reach': total_engagement * 2,  # Estimation simple
            'sentiment_distribution': sentiment_counts
        }
    
    def _format_key_influencers(self, influencers: List[Dict]) -> List[Dict]:
        """Formate les influenceurs clés pour le rapport"""
        return [
            {
                'name': inf.get('author', 'Inconnu'),
                'source': inf.get('source', ''),
                'engagement': inf.get('total_engagement', 0),
                'sentiment_score': inf.get('sentiment_score', 50),
                'risk_level': 'high' if inf.get('sentiment_score', 50) < 30 else 'medium' if inf.get('sentiment_score', 50) < 70 else 'low'
            }
            for inf in influencers
        ]
    
    def _generate_action_recommendations(self, risk_analysis: Dict) -> List[str]:
        """Génère des recommandations d'action"""
        recommendations = []
        
        if risk_analysis['high_risk']:
            recommendations.append(f"Engagement prioritaire avec {len(risk_analysis['high_risk'])} influenceur(s) à risque élevé")
        
        if risk_analysis['majority_sentiment'] == 'negative':
            recommendations.append("Stratégie de gestion de crise nécessaire - sentiment majoritairement négatif")
        
        if risk_analysis['estimated_reach'] > 50000:
            recommendations.append("Potentiel viral élevé - surveillance continue recommandée")
        
        return recommendations


class ReportIntelligenceAgent:
    """Agent principal qui orchestre l'analyse intelligente des rapports"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.agents = {
            'sentiment': SentimentAnalysisAgent(self.llm_service),
            'trends': TrendAnalysisAgent(self.llm_service),
            'influencers': InfluencerAnalysisAgent(self.llm_service)
        }
    
    async def generate_intelligent_analysis(self, context: AnalysisContext) -> Dict[str, Any]:
        """Génère une analyse complète avec tous les agents"""
        if not self.llm_service.is_available():
            logger.error("Aucun modèle LLM disponible")
            return {
                'error': 'Service IA indisponible',
                'fallback_analysis': self._generate_fallback_analysis(context)
            }
        
        results = {}
        
        try:
            # Exécuter les analyses en parallèle
            tasks = []
            for agent_name, agent in self.agents.items():
                tasks.append(self._safe_analyze(agent, context, agent_name))
            
            analyses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Traiter les résultats
            for i, (agent_name, _) in enumerate(self.agents.items()):
                result = analyses[i]
                if isinstance(result, Exception):
                    logger.error(f"Erreur agent {agent_name}: {result}")
                    results[agent_name] = {'error': str(result)}
                else:
                    results[agent_name] = result
            
            # Générer une synthèse exécutive
            results['executive_summary'] = await self._generate_executive_summary(results, context)
            
        except Exception as e:
            logger.error(f"Erreur génération analyse: {e}")
            results['error'] = str(e)
        
        return results
    
    async def _safe_analyze(self, agent, context, agent_name):
        """Analyse sécurisée avec gestion d'erreur"""
        try:
            return await agent.analyze(context)
        except Exception as e:
            logger.error(f"Erreur agent {agent_name}: {e}")
            return {'error': str(e), 'type': f'{agent_name}_analysis'}
    
    async def _generate_executive_summary(self, results: Dict, context: AnalysisContext) -> Dict[str, Any]:
        """Génère une synthèse exécutive basée on toutes les analyses"""
        
        # Extraire les insights clés
        key_insights = []
        for agent_result in results.values():
            if isinstance(agent_result, dict) and 'analysis' in agent_result:
                # Extraire la première phrase comme insight
                analysis = agent_result['analysis']
                first_sentence = analysis.split('.')[0] + '.' if '.' in analysis else analysis[:100] + '...'
                key_insights.append(first_sentence)
        
        prompt = f"""Tu es un directeur de l'analyse stratégique. Rédige une synthèse exécutive basée sur ces analyses d'experts.

CONTEXTE GLOBAL:
- Mots-clés: {', '.join(context.keywords)}
- Période: {context.period_days} jours
- Total mentions: {context.total_mentions}

INSIGHTS DES EXPERTS:
{chr(10).join([f"- {insight}" for insight in key_insights])}

INSTRUCTIONS:
1. Synthétise les points les plus critiques en 2-3 phrases
2. Identifie le niveau de priorité global (CRITIQUE/MODÉRÉ/NORMAL)
3. Propose 2-3 actions immédiates à entreprendre
4. Évalue l'évolution probable à court terme
5. Sois concis et actionnable - destiné à des décideurs

Rédige une synthèse de 150-200 mots en français."""

        summary_text = await self.llm_service.generate_text(prompt, max_tokens=400)
        cleaned_text = self._clean_analysis_text(summary_text)
        
        # Déterminer le niveau de priorité
        priority_level = self._assess_priority_level(results, context)
        
        return {
            'summary': cleaned_text,
            'priority_level': priority_level,
            'key_metrics': {
                'total_mentions': context.total_mentions,
                'analysis_confidence': self._calculate_confidence(results),
                'alert_status': self._determine_alert_status(results)
            }
        }
    
    def _clean_analysis_text(self, text: str) -> str:
        """Nettoie le texte généré par l'IA"""
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n'.join(lines)
    
    def _assess_priority_level(self, results: Dict, context: AnalysisContext) -> str:
        """Évalue le niveau de priorité global"""
        scores = []
        
        # Analyse de sentiment
        sentiment_result = results.get('sentiment', {})
        if 'sentiment_score' in sentiment_result:
            score = sentiment_result['sentiment_score']
            if score < -0.3:
                scores.append(3)  # Critique
            elif score < 0:
                scores.append(2)  # Modéré
            else:
                scores.append(1)  # Normal
        
        # Analyse de tendances
        trends_result = results.get('trends', {})
        if 'alert_level' in trends_result:
            alert = trends_result['alert_level']
            if alert == 'élevé':
                scores.append(3)
            elif alert == 'modéré':
                scores.append(2)
            else:
                scores.append(1)
        
        # Analyse d'influenceurs
        influencer_result = results.get('influencers', {})
        if 'risk_assessment' in influencer_result:
            high_risk_count = len(influencer_result['risk_assessment'].get('high_risk', []))
            if high_risk_count > 2:
                scores.append(3)
            elif high_risk_count > 0:
                scores.append(2)
            else:
                scores.append(1)
        
        # Déterminer le niveau global
        if not scores:
            return 'NORMAL'
        
        max_score = max(scores)
        if max_score >= 3:
            return 'CRITIQUE'
        elif max_score >= 2:
            return 'MODÉRÉ'
        else:
            return 'NORMAL'
    
    def _calculate_confidence(self, results: Dict) -> float:
        """Calcule un score de confiance pour l'analyse"""
        confidence_scores = []
        
        for result in results.values():
            if isinstance(result, dict) and 'error' not in result:
                confidence_scores.append(0.8)  # Bonne confiance si pas d'erreur
            else:
                confidence_scores.append(0.3)  # Faible confiance si erreur
        
        return sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
    
    def _determine_alert_status(self, results: Dict) -> str:
        """Détermine le statut d'alerte global"""
        alerts = []
        
        for result in results.values():
            if isinstance(result, dict):
                if 'alert_level' in result:
                    alerts.append(result['alert_level'])
                elif 'risk_assessment' in result and result['risk_assessment'].get('high_risk'):
                    alerts.append('élevé')
        
        if 'élevé' in alerts:
            return 'ALERTE ÉLEVÉE'
        elif 'modéré' in alerts:
            return 'SURVEILLANCE RENFORCÉE'
        else:
            return 'NORMAL'
    
    def _generate_fallback_analysis(self, context: AnalysisContext) -> Dict[str, Any]:
        """Génère une analyse de fallback si l'IA n'est pas disponible"""
        return {
            'summary': f"Analyse basique : {context.total_mentions} mentions sur {context.period_days} jours pour {', '.join(context.keywords)}. Service IA indisponible - analyse automatique limitée.",
            'priority_level': 'NORMAL',
            'note': 'Analyse générée sans IA - fonctionnalités limitées'
        }