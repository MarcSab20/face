"""
Analyseur de Sentiment Simple
"""

import logging
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import Dict

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Analyseur de sentiment utilisant VADER"""
    
    def __init__(self):
        try:
            self.analyzer = SentimentIntensityAnalyzer()
            logger.info("✅ SentimentAnalyzer initialisé")
        except Exception as e:
            logger.error(f"❌ Erreur SentimentAnalyzer: {e}")
            self.analyzer = None
    
    def analyze(self, text: str) -> Dict:
        """Analyser le sentiment d'un texte"""
        if not self.analyzer or not text:
            return {
                'sentiment': 'neutral',
                'score': 0.0,
                'compound': 0.0
            }
        
        try:
            scores = self.analyzer.polarity_scores(text)
            compound = scores['compound']
            
            if compound >= 0.05:
                sentiment = 'positive'
            elif compound <= -0.05:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            return {
                'sentiment': sentiment,
                'score': abs(compound),
                'compound': compound,
                'positive': scores['pos'],
                'neutral': scores['neu'],
                'negative': scores['neg']
            }
        except Exception as e:
            logger.error(f"Erreur analyse sentiment: {e}")
            return {
                'sentiment': 'neutral',
                'score': 0.0,
                'compound': 0.0
            }