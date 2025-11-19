"""
Service de Résumé Hiérarchique Intelligent
Résout le problème de contexte limité en résumant par lots puis en agrégeant
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ContentBatch:
    """Un lot de contenus à résumer"""
    batch_id: int
    contents: List[Dict]
    summary: Optional[str] = None
    key_points: Optional[List[str]] = None
    sentiment_aggregate: Optional[Dict] = None


@dataclass
class HierarchicalSummary:
    """Résumé hiérarchique complet"""
    final_summary: str
    key_insights: List[str]
    sentiment_analysis: Dict
    themes: List[str]
    batch_summaries: List[str]
    total_contents_analyzed: int
    processing_time: float


class HierarchicalSummarizer:
    """
    Résumeur hiérarchique intelligent
    
    Principe:
    1. Diviser le contenu en lots gérables (batch)
    2. Résumer chaque lot individuellement
    3. Agréger les résumés de lots
    4. Générer la synthèse finale
    
    Permet de traiter des milliers de documents sans dépasser les limites de contexte
    """
    
    def __init__(
        self,
        llm_service,  # Service LLM (Ollama, Gemini, Groq, etc.)
        batch_size: int = 20,  # Nombre de contenus par lot
        max_content_length: int = 500  # Taille max par contenu
    ):
        self.llm_service = llm_service
        self.batch_size = batch_size
        self.max_content_length = max_content_length
        logger.info(f"HierarchicalSummarizer initialisé (batch_size={batch_size})")
    
    async def summarize_large_dataset(
        self,
        contents: List[Dict],
        context: str = "analyse générale"
    ) -> HierarchicalSummary:
        """
        Résumer un grand ensemble de données de manière hiérarchique
        
        Args:
            contents: Liste de contenus (posts, commentaires, etc.)
            context: Contexte de l'analyse
            
        Returns:
            Résumé hiérarchique complet
        """
        start_time = datetime.utcnow()
        logger.info(f"📊 Démarrage résumé hiérarchique: {len(contents)} contenus")
        
        if not contents:
            return self._empty_summary()
        
        # ÉTAPE 1: Diviser en lots
        batches = self._create_batches(contents)
        logger.info(f"   ✓ Divisé en {len(batches)} lots de ~{self.batch_size} contenus")
        
        # ÉTAPE 2: Résumer chaque lot en parallèle
        logger.info(f"   🔄 Résumé des lots en cours...")
        batch_summaries = await self._summarize_batches(batches, context)
        logger.info(f"   ✓ {len(batch_summaries)} lots résumés")
        
        # ÉTAPE 3: Agréger les sentiments
        sentiment_aggregate = self._aggregate_sentiments(contents)
        
        # ÉTAPE 4: Extraire les thèmes dominants
        themes = self._extract_themes(batch_summaries)
        
        # ÉTAPE 5: Synthèse finale des résumés de lots
        logger.info(f"   🎯 Génération synthèse finale...")
        final_summary, key_insights = await self._generate_final_synthesis(
            batch_summaries,
            sentiment_aggregate,
            themes,
            context
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"✅ Résumé hiérarchique terminé en {processing_time:.1f}s")
        
        return HierarchicalSummary(
            final_summary=final_summary,
            key_insights=key_insights,
            sentiment_analysis=sentiment_aggregate,
            themes=themes,
            batch_summaries=[b.summary for b in batches if b.summary],
            total_contents_analyzed=len(contents),
            processing_time=processing_time
        )
    
    def _create_batches(self, contents: List[Dict]) -> List[ContentBatch]:
        """Diviser les contenus en lots gérables"""
        batches = []
        
        for i in range(0, len(contents), self.batch_size):
            batch_contents = contents[i:i + self.batch_size]
            
            batches.append(ContentBatch(
                batch_id=len(batches) + 1,
                contents=batch_contents
            ))
        
        return batches
    
    async def _summarize_batches(
        self,
        batches: List[ContentBatch],
        context: str
    ) -> List[ContentBatch]:
        """Résumer tous les lots en parallèle"""
        
        tasks = [
            self._summarize_single_batch(batch, context)
            for batch in batches
        ]
        
        # Exécuter en parallèle avec limite de concurrence
        semaphore = asyncio.Semaphore(3)  # Max 3 résumés simultanés
        
        async def bounded_task(task):
            async with semaphore:
                return await task
        
        summarized_batches = await asyncio.gather(
            *[bounded_task(task) for task in tasks],
            return_exceptions=True
        )
        
        # Filtrer les erreurs
        valid_batches = [
            batch for batch in summarized_batches
            if not isinstance(batch, Exception) and batch.summary
        ]
        
        return valid_batches
    
    async def _summarize_single_batch(
        self,
        batch: ContentBatch,
        context: str
    ) -> ContentBatch:
        """
        Résumer un seul lot de contenus
        
        Le résumé doit capturer l'essentiel en quelques phrases
        """
        
        # Préparer le texte du lot
        batch_text = self._format_batch_for_summarization(batch.contents)
        
        prompt = f"""Résume ce lot de {len(batch.contents)} contenus sur '{context}'.

CONTENUS:
{batch_text}

Fournis un résumé en 3-5 phrases capturant:
1. Les idées principales exprimées
2. Le ton général (positif/négatif/neutre)
3. Les points de discussion récurrents

Sois factuel et concis. NE PAS mentionner "lot" ou "batch".

RÉSUMÉ:"""
        
        try:
            # Utiliser le service LLM
            response = await self.llm_service.analyze_with_local_llm(
                prompt,
                {'batch_size': len(batch.contents)}
            )
            
            # Nettoyer la réponse
            summary = self._clean_summary(response)
            
            # Extraire les points clés
            key_points = self._extract_key_points(batch.contents, summary)
            
            batch.summary = summary
            batch.key_points = key_points
            
            return batch
            
        except Exception as e:
            logger.error(f"Erreur résumé lot {batch.batch_id}: {e}")
            # Fallback: résumé basique par règles
            batch.summary = self._fallback_batch_summary(batch.contents)
            return batch
    
    def _format_batch_for_summarization(self, contents: List[Dict]) -> str:
        """Formater un lot de contenus pour le résumé"""
        
        formatted_lines = []
        
        for i, content in enumerate(contents[:self.batch_size], 1):
            # Extraire le texte principal
            title = content.get('title', '')
            text = content.get('content', '') or content.get('text', '')
            author = content.get('author', 'Anonyme')
            
            # Limiter la taille
            combined_text = f"{title} {text}"[:self.max_content_length]
            
            formatted_lines.append(f"{i}. [{author}] {combined_text}")
        
        return '\n'.join(formatted_lines)
    
    def _clean_summary(self, raw_summary: str) -> str:
        """Nettoyer le résumé généré par le LLM"""
        import re
        
        # Enlever les préfixes communs
        summary = re.sub(r'^(Résumé|Summary|RÉSUMÉ):\s*', '', raw_summary, flags=re.IGNORECASE)
        
        # Enlever les balises markdown restantes
        summary = re.sub(r'\*\*([^*]+)\*\*', r'\1', summary)
        summary = re.sub(r'\*([^*]+)\*', r'\1', summary)
        
        # Nettoyer les espaces multiples
        summary = re.sub(r'\s+', ' ', summary)
        
        return summary.strip()
    
    def _extract_key_points(self, contents: List[Dict], summary: str) -> List[str]:
        """Extraire les points clés d'un lot"""
        
        key_points = []
        
        # Points basés sur l'engagement
        high_engagement = sorted(
            contents,
            key=lambda x: x.get('engagement_score', 0),
            reverse=True
        )[:3]
        
        for content in high_engagement:
            title = content.get('title', '')
            if title and len(title) > 10:
                key_points.append(title[:100])
        
        return key_points
    
    def _fallback_batch_summary(self, contents: List[Dict]) -> str:
        """Résumé de secours basé sur des règles simples"""
        
        total = len(contents)
        authors = set(c.get('author', 'Anonyme') for c in contents)
        
        # Analyser les sentiments
        sentiments = [c.get('sentiment') for c in contents if c.get('sentiment')]
        sentiment_counts = {}
        for s in sentiments:
            sentiment_counts[s] = sentiment_counts.get(s, 0) + 1
        
        dominant_sentiment = max(sentiment_counts, key=sentiment_counts.get) if sentiment_counts else 'neutre'
        
        # Compter les mots-clés fréquents
        from collections import Counter
        all_text = ' '.join([
            f"{c.get('title', '')} {c.get('content', '')}"
            for c in contents
        ]).lower()
        
        # Mots communs à ignorer
        stop_words = {'le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'et', 'ou', 'mais', 'est', 'sont', 'a', 'the', 'and', 'or', 'is', 'are'}
        words = [w for w in all_text.split() if len(w) > 4 and w not in stop_words]
        common_words = Counter(words).most_common(3)
        
        summary = f"Analyse de {total} contenus de {len(authors)} auteur(s). "
        summary += f"Ton général: {dominant_sentiment}. "
        
        if common_words:
            themes = ', '.join([word for word, count in common_words])
            summary += f"Thèmes récurrents: {themes}."
        
        return summary
    
    def _aggregate_sentiments(self, contents: List[Dict]) -> Dict:
        """Agréger les sentiments de tous les contenus"""
        
        sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0, 'unknown': 0}
        
        for content in contents:
            sentiment = content.get('sentiment', 'unknown')
            if sentiment in sentiment_counts:
                sentiment_counts[sentiment] += 1
            else:
                sentiment_counts['unknown'] += 1
        
        total = len(contents)
        
        return {
            'distribution': sentiment_counts,
            'percentages': {
                k: round((v / total) * 100, 1) if total > 0 else 0
                for k, v in sentiment_counts.items()
            },
            'dominant': max(sentiment_counts, key=sentiment_counts.get),
            'total_analyzed': total
        }
    
    def _extract_themes(self, batches: List[ContentBatch]) -> List[str]:
        """Extraire les thèmes dominants des résumés de lots"""
        
        # Combiner tous les résumés
        all_summaries = ' '.join([b.summary for b in batches if b.summary])
        
        # Extraire les mots-clés fréquents (simple)
        from collections import Counter
        
        stop_words = {
            'le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'et', 'ou', 'mais',
            'est', 'sont', 'a', 'ont', 'pour', 'dans', 'sur', 'avec', 'par',
            'the', 'and', 'or', 'is', 'are', 'of', 'to', 'in', 'for', 'with'
        }
        
        words = [
            w.lower() for w in all_summaries.split()
            if len(w) > 4 and w.lower() not in stop_words
        ]
        
        # Les 5 mots les plus fréquents = thèmes
        common = Counter(words).most_common(5)
        themes = [word.capitalize() for word, count in common if count >= 2]
        
        return themes
    
    async def _generate_final_synthesis(
        self,
        batches: List[ContentBatch],
        sentiment_aggregate: Dict,
        themes: List[str],
        context: str
    ) -> Tuple[str, List[str]]:
        """
        Générer la synthèse finale à partir des résumés de lots
        
        C'est l'étape finale qui crée le rapport narratif
        """
        
        # Combiner les résumés de lots
        batch_summaries_text = '\n\n'.join([
            f"Lot {b.batch_id}: {b.summary}"
            for b in batches if b.summary
        ])
        
        sentiment_summary = (
            f"{sentiment_aggregate['percentages']['positive']:.0f}% positif, "
            f"{sentiment_aggregate['percentages']['neutral']:.0f}% neutre, "
            f"{sentiment_aggregate['percentages']['negative']:.0f}% négatif"
        )
        
        prompt = f"""Tu es un analyste stratégique. Synthétise ces résumés en un rapport narratif cohérent.

CONTEXTE: {context}
CONTENUS ANALYSÉS: {sentiment_aggregate['total_analyzed']}
SENTIMENT GLOBAL: {sentiment_summary}
THÈMES: {', '.join(themes)}

RÉSUMÉS PAR LOT:
{batch_summaries_text}

INSTRUCTIONS:
Rédige une synthèse narrative en 5-7 paragraphes qui:
1. Présente la situation globale
2. Analyse les tendances et opinions dominantes
3. Identifie les préoccupations récurrentes
4. Évalue le ton et l'engagement
5. Conclut avec les insights principaux

Style: Professionnel, factuel, paragraphes fluides (PAS de listes à puces).

SYNTHÈSE:"""
        
        try:
            synthesis = await self.llm_service.analyze_with_local_llm(
                prompt,
                {'total_batches': len(batches)}
            )
            
            # Nettoyer
            synthesis = self._clean_summary(synthesis)
            
            # Extraire les insights clés
            key_insights = self._extract_final_insights(batches, sentiment_aggregate, themes)
            
            return synthesis, key_insights
            
        except Exception as e:
            logger.error(f"Erreur synthèse finale: {e}")
            # Fallback
            return self._fallback_final_synthesis(
                batches, sentiment_aggregate, themes, context
            )
    
    def _extract_final_insights(
        self,
        batches: List[ContentBatch],
        sentiment_aggregate: Dict,
        themes: List[str]
    ) -> List[str]:
        """Extraire les insights clés de l'analyse"""
        
        insights = []
        
        # Insight sur le volume
        total = sentiment_aggregate['total_analyzed']
        insights.append(f"{total} contenus analysés sur {len(batches)} sources")
        
        # Insight sur le sentiment
        neg_ratio = sentiment_aggregate['percentages']['negative']
        if neg_ratio > 60:
            insights.append(f"⚠️ Sentiment critique dominant ({neg_ratio:.0f}% négatif)")
        elif neg_ratio < 20:
            insights.append(f"✅ Sentiment majoritairement positif")
        
        # Insight sur les thèmes
        if themes:
            insights.append(f"Thèmes principaux: {', '.join(themes[:3])}")
        
        # Insight sur l'engagement
        all_contents = []
        for batch in batches:
            all_contents.extend(batch.contents)
        
        if all_contents:
            avg_engagement = sum(c.get('engagement_score', 0) for c in all_contents) / len(all_contents)
            high_engagement_count = len([c for c in all_contents if c.get('engagement_score', 0) > avg_engagement * 2])
            
            if high_engagement_count > len(all_contents) * 0.2:
                insights.append(f"Forte viralité détectée ({high_engagement_count} contenus très engageants)")
        
        return insights[:5]  # Top 5 insights
    
    def _fallback_final_synthesis(
        self,
        batches: List[ContentBatch],
        sentiment_aggregate: Dict,
        themes: List[str],
        context: str
    ) -> Tuple[str, List[str]]:
        """Synthèse de secours basée sur des règles"""
        
        total = sentiment_aggregate['total_analyzed']
        neg_pct = sentiment_aggregate['percentages']['negative']
        pos_pct = sentiment_aggregate['percentages']['positive']
        
        synthesis = f"L'analyse de {total} contenus sur '{context}' révèle les éléments suivants. "
        
        if neg_pct > 50:
            synthesis += f"Le ton est majoritairement critique ({neg_pct:.0f}% de sentiment négatif), "
            synthesis += "reflétant des préoccupations marquées au sein de l'opinion surveillée. "
        elif pos_pct > 50:
            synthesis += f"Le ton est globalement favorable ({pos_pct:.0f}% de sentiment positif). "
        else:
            synthesis += "Le ton reste partagé entre opinions positives et négatives. "
        
        if themes:
            synthesis += f"Les thèmes dominants identifiés sont: {', '.join(themes)}. "
        
        synthesis += f"Cette analyse couvre {len(batches)} sources distinctes collectées sur la période de surveillance."
        
        insights = self._extract_final_insights(batches, sentiment_aggregate, themes)
        
        return synthesis, insights
    
    def _empty_summary(self) -> HierarchicalSummary:
        """Retourner un résumé vide"""
        return HierarchicalSummary(
            final_summary="Aucun contenu à analyser.",
            key_insights=[],
            sentiment_analysis={'distribution': {}, 'percentages': {}, 'dominant': 'unknown', 'total_analyzed': 0},
            themes=[],
            batch_summaries=[],
            total_contents_analyzed=0,
            processing_time=0.0
        )


# Fonction utilitaire pour estimer la taille d'un prompt
def estimate_token_count(text: str) -> int:
    """
    Estimer le nombre de tokens (approximatif)
    1 token ≈ 4 caractères en moyenne
    """
    return len(text) // 4


# Exemple d'utilisation
async def demo_hierarchical_summarization():
    """Démonstration du résumé hiérarchique"""
    
    # Simuler un grand dataset
    fake_contents = [
        {
            'title': f'Post {i}',
            'content': f'Contenu du post {i}' * 10,
            'author': f'User{i % 10}',
            'sentiment': ['positive', 'neutral', 'negative'][i % 3],
            'engagement_score': (i * 13) % 1000
        }
        for i in range(100)  # 100 contenus
    ]
    
    # Créer un mock LLM service
    class MockLLMService:
        async def analyze_with_local_llm(self, prompt, context):
            # Simuler une réponse
            await asyncio.sleep(0.5)  # Simuler le temps de traitement
            return "Résumé généré par le LLM."
    
    mock_llm = MockLLMService()
    summarizer = HierarchicalSummarizer(mock_llm, batch_size=20)
    
    result = await summarizer.summarize_large_dataset(
        fake_contents,
        context="test de résumé hiérarchique"
    )
    
    print(f"\n✅ Résumé terminé:")
    print(f"   - {result.total_contents_analyzed} contenus analysés")
    print(f"   - {len(result.batch_summaries)} lots traités")
    print(f"   - Temps: {result.processing_time:.1f}s")
    print(f"\n📊 Synthèse finale:")
    print(f"   {result.final_summary}")


if __name__ == '__main__':
    asyncio.run(demo_hierarchical_summarization())