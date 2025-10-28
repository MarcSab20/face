"""
Module d'analyse de sentiment pour Brand Monitor
Supporte français et anglais
"""

import logging
from typing import Dict, Tuple
import re

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """Analyseur de sentiment multilingue"""
    
    def __init__(self):
        self.vader_available = False
        self.textblob_available = False
        
        # Tenter d'importer VADER (meilleur pour les réseaux sociaux)
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            self.vader = SentimentIntensityAnalyzer()
            self.vader_available = True
            logger.info("VADER sentiment analyzer loaded")
        except ImportError:
            logger.warning("VADER not available. Install with: pip install vaderSentiment")
        
        # Tenter d'importer TextBlob (bon pour le texte général)
        try:
            from textblob import TextBlob
            self.TextBlob = TextBlob
            self.textblob_available = True
            logger.info("TextBlob sentiment analyzer loaded")
        except ImportError:
            logger.warning("TextBlob not available. Install with: pip install textblob")
        
        # Dictionnaire de mots français pour analyse basique
        self.positive_words_fr = {
            'excellent', 'superbe', 'génial', 'parfait', 'incroyable', 'magnifique',
            'formidable', 'extraordinaire', 'remarquable', 'fantastique', 'merveilleux',
            'adore', 'aime', 'j\'aime', 'bravo', 'félicitations', 'impressionnant',
            'meilleur', 'top', 'super', 'cool', 'bien', 'bon', 'très bien',
            'satisfait', 'content', 'heureux', 'joie', 'succès', 'réussi',
            'positif', 'agréable', 'plaisant', 'recommande', 'qualité'
        }
        
        self.negative_words_fr = {
            'mauvais', 'horrible', 'nul', 'terrible', 'catastrophique', 'désastreux',
            'médiocre', 'décevant', 'déçu', 'déception', 'problème', 'défaut',
            'erreur', 'bug', 'cassé', 'ne fonctionne pas', 'pas bien', 'raté',
            'échec', 'pire', 'horreur', 'cauchemar', 'déteste', 'haine',
            'arnaque', 'escroc', 'fraude', 'scandale', 'inadmissible',
            'inacceptable', 'lent', 'cher', 'éviter', 'déconseille'
        }
    
    def analyze(self, text: str, language: str = 'auto') -> Dict:
        """
        Analyser le sentiment d'un texte
        
        Args:
            text: Texte à analyser
            language: 'fr', 'en', ou 'auto' pour détection automatique
            
        Returns:
            Dict avec sentiment, score et détails
        """
        if not text or len(text.strip()) < 3:
            return {
                'sentiment': 'neutral',
                'score': 0.0,
                'confidence': 0.0,
                'method': 'empty_text'
            }
        
        # Détecter la langue si auto
        if language == 'auto':
            language = self._detect_language(text)
        
        # Utiliser la meilleure méthode disponible
        if language == 'en' and self.vader_available:
            return self._analyze_vader(text)
        elif self.textblob_available:
            return self._analyze_textblob(text)
        else:
            return self._analyze_basic(text, language)
    
    def _detect_language(self, text: str) -> str:
        """Détecter la langue du texte (basique)"""
        # Mots français courants
        french_indicators = ['le', 'la', 'les', 'de', 'du', 'des', 'et', 'est', 'que', 'qui']
        
        text_lower = text.lower()
        french_count = sum(1 for word in french_indicators if f' {word} ' in f' {text_lower} ')
        
        return 'fr' if french_count >= 2 else 'en'
    
    def _analyze_vader(self, text: str) -> Dict:
        """Analyser avec VADER (optimal pour anglais et réseaux sociaux)"""
        scores = self.vader.polarity_scores(text)
        
        # Déterminer le sentiment
        compound = scores['compound']
        if compound >= 0.05:
            sentiment = 'positive'
        elif compound <= -0.05:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'score': compound,
            'confidence': max(scores['pos'], scores['neg'], scores['neu']),
            'details': scores,
            'method': 'vader'
        }
    
    def _analyze_textblob(self, text: str) -> Dict:
        """Analyser avec TextBlob"""
        try:
            blob = self.TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 to 1
            subjectivity = blob.sentiment.subjectivity  # 0 to 1
            
            # Déterminer le sentiment
            if polarity > 0.1:
                sentiment = 'positive'
            elif polarity < -0.1:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            return {
                'sentiment': sentiment,
                'score': polarity,
                'confidence': abs(polarity),
                'subjectivity': subjectivity,
                'method': 'textblob'
            }
        except Exception as e:
            logger.error(f"TextBlob analysis error: {e}")
            return self._analyze_basic(text, 'en')
    
    def _analyze_basic(self, text: str, language: str) -> Dict:
        """Analyse basique par comptage de mots"""
        text_lower = text.lower()
        
        # Choisir le dictionnaire selon la langue
        if language == 'fr':
            positive_words = self.positive_words_fr
            negative_words = self.negative_words_fr
        else:
            # Mots anglais basiques
            positive_words = {
                'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
                'love', 'best', 'awesome', 'perfect', 'happy', 'brilliant'
            }
            negative_words = {
                'bad', 'terrible', 'horrible', 'awful', 'worst', 'hate',
                'poor', 'disappointing', 'useless', 'broken', 'failed'
            }
        
        # Compter les occurrences
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        # Calculer le score
        total = positive_count + negative_count
        if total == 0:
            score = 0.0
            sentiment = 'neutral'
            confidence = 0.0
        else:
            score = (positive_count - negative_count) / total
            confidence = total / (len(text_lower.split()) + 1)
            
            if score > 0.2:
                sentiment = 'positive'
            elif score < -0.2:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'score': score,
            'confidence': min(confidence, 1.0),
            'positive_words': positive_count,
            'negative_words': negative_count,
            'method': f'basic_{language}'
        }
    
    def analyze_batch(self, texts: list) -> list:
        """Analyser plusieurs textes en batch"""
        return [self.analyze(text) for text in texts]
    
    def get_emoji(self, sentiment: str) -> str:
        """Obtenir un emoji pour un sentiment"""
        emojis = {
            'positive': '😊',
            'negative': '😞',
            'neutral': '😐'
        }
        return emojis.get(sentiment, '😐')
    
    def get_color(self, sentiment: str) -> str:
        """Obtenir une couleur pour un sentiment"""
        colors = {
            'positive': '#28a745',  # vert
            'negative': '#dc3545',  # rouge
            'neutral': '#6c757d'    # gris
        }
        return colors.get(sentiment, '#6c757d')