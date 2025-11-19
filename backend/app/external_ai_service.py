"""
Service d'IA Externe Gratuit
Intègre Gemini (Google) et Groq pour des synthèses de qualité supérieure
"""

import logging
import asyncio
import aiohttp
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class APIQuota:
    """Suivi du quota d'une API"""
    requests_made: int
    requests_limit: int
    reset_at: datetime
    is_available: bool


class ExternalAIService:
    """
    Service d'IA externe gratuit
    
    APIs gratuites disponibles:
    - Google Gemini: 15 req/min (60 req/h) gratuit
    - Groq: 30 req/min gratuit  
    
    Gère intelligemment les quotas et bascule entre les services
    """
    
    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        groq_api_key: Optional[str] = None
    ):
        self.gemini_api_key = gemini_api_key
        self.groq_api_key = groq_api_key
        
        # Quotas
        self.gemini_quota = APIQuota(0, 15, datetime.utcnow() + timedelta(minutes=1), bool(gemini_api_key))
        self.groq_quota = APIQuota(0, 30, datetime.utcnow() + timedelta(minutes=1), bool(groq_api_key))
        
        # URLs
        self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        self.groq_url = "https://api.groq.com/openai/v1/chat/completions"
        
        self.session = None
        
        # Log des services disponibles
        available = []
        if gemini_api_key:
            available.append("Gemini")
        if groq_api_key:
            available.append("Groq")
        
        if available:
            logger.info(f"✅ Services IA externes disponibles: {', '.join(available)}")
        else:
            logger.warning("⚠️ Aucun service IA externe configuré. Utilisation des LLM locaux uniquement.")
    
    async def __aenter__(self):
        """Context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.session:
            await self.session.close()
    
    async def generate_smart_synthesis(
        self,
        prompt: str,
        context_data: Dict,
        max_tokens: int = 1000,
        temperature: float = 0.3
    ) -> Dict:
        """
        Générer une synthèse intelligente en choisissant le meilleur service disponible
        
        Args:
            prompt: Prompt pour le LLM
            context_data: Données contextuelles
            max_tokens: Nombre max de tokens
            temperature: Température (0-1)
            
        Returns:
            Dict avec la réponse et les métadonnées
        """
        
        # Choisir le meilleur service disponible
        service = self._select_best_service()
        
        if service == 'gemini':
            return await self._generate_with_gemini(prompt, max_tokens, temperature)
        elif service == 'groq':
            return await self._generate_with_groq(prompt, max_tokens, temperature)
        else:
            return {
                'text': None,
                'service': 'none',
                'error': 'Aucun service IA externe disponible'
            }
    
    def _select_best_service(self) -> str:
        """Sélectionner le meilleur service selon la disponibilité et les quotas"""
        
        now = datetime.utcnow()
        
        # Reset des quotas si nécessaire
        if now >= self.gemini_quota.reset_at:
            self.gemini_quota.requests_made = 0
            self.gemini_quota.reset_at = now + timedelta(minutes=1)
        
        if now >= self.groq_quota.reset_at:
            self.groq_quota.requests_made = 0
            self.groq_quota.reset_at = now + timedelta(minutes=1)
        
        # Vérifier Gemini
        if (self.gemini_quota.is_available and 
            self.gemini_quota.requests_made < self.gemini_quota.requests_limit):
            return 'gemini'
        
        # Sinon Groq
        if (self.groq_quota.is_available and 
            self.groq_quota.requests_made < self.groq_quota.requests_limit):
            return 'groq'
        
        return 'none'
    
    async def _generate_with_gemini(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict:
        """
        Générer avec Google Gemini API
        
        Gemini 1.5 Flash: gratuit, rapide, bon pour résumés
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            url = f"{self.gemini_url}?key={self.gemini_api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                    "topP": 0.95,
                    "topK": 40
                }
            }
            
            async with self.session.post(url, json=payload, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extraire le texte de la réponse
                    text = data['candidates'][0]['content']['parts'][0]['text']
                    
                    # Incrémenter le quota
                    self.gemini_quota.requests_made += 1
                    
                    logger.info(f"✅ Gemini: {len(text)} caractères générés (quota: {self.gemini_quota.requests_made}/{self.gemini_quota.requests_limit})")
                    
                    return {
                        'text': text,
                        'service': 'gemini',
                        'model': 'gemini-1.5-flash',
                        'tokens_used': len(text) // 4,  # Approximation
                        'success': True
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Erreur Gemini {response.status}: {error_text}")
                    return {'text': None, 'service': 'gemini', 'error': error_text}
                    
        except asyncio.TimeoutError:
            logger.error("Timeout Gemini API")
            return {'text': None, 'service': 'gemini', 'error': 'Timeout'}
        except Exception as e:
            logger.error(f"Erreur Gemini: {e}")
            return {'text': None, 'service': 'gemini', 'error': str(e)}
    
    async def _generate_with_groq(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict:
        """
        Générer avec Groq API
        
        Groq: Très rapide, gratuit, bon pour résumés courts
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            headers = {
                'Authorization': f'Bearer {self.groq_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "model": "llama-3.1-8b-instant",  # Modèle rapide
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": 0.95
            }
            
            async with self.session.post(
                self.groq_url,
                headers=headers,
                json=payload,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    text = data['choices'][0]['message']['content']
                    
                    # Incrémenter le quota
                    self.groq_quota.requests_made += 1
                    
                    logger.info(f"✅ Groq: {len(text)} caractères générés (quota: {self.groq_quota.requests_made}/{self.groq_quota.requests_limit})")
                    
                    return {
                        'text': text,
                        'service': 'groq',
                        'model': 'llama-3.1-8b-instant',
                        'tokens_used': data['usage']['total_tokens'],
                        'success': True
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Erreur Groq {response.status}: {error_text}")
                    return {'text': None, 'service': 'groq', 'error': error_text}
                    
        except asyncio.TimeoutError:
            logger.error("Timeout Groq API")
            return {'text': None, 'service': 'groq', 'error': 'Timeout'}
        except Exception as e:
            logger.error(f"Erreur Groq: {e}")
            return {'text': None, 'service': 'groq', 'error': str(e)}
    
    def get_quota_status(self) -> Dict:
        """Obtenir le statut des quotas"""
        return {
            'gemini': {
                'available': self.gemini_quota.is_available,
                'used': self.gemini_quota.requests_made,
                'limit': self.gemini_quota.requests_limit,
                'reset_in_seconds': (self.gemini_quota.reset_at - datetime.utcnow()).seconds
            },
            'groq': {
                'available': self.groq_quota.is_available,
                'used': self.groq_quota.requests_made,
                'limit': self.groq_quota.requests_limit,
                'reset_in_seconds': (self.groq_quota.reset_at - datetime.utcnow()).seconds
            }
        }
    
    async def generate_executive_summary(
        self,
        batch_summaries: List[str],
        sentiment_data: Dict,
        themes: List[str],
        context: str,
        total_contents: int
    ) -> str:
        """
        Générer un résumé exécutif de haute qualité
        
        Utilise le meilleur modèle disponible pour une synthèse professionnelle
        """
        
        sentiment_summary = (
            f"{sentiment_data['percentages']['positive']:.0f}% positif, "
            f"{sentiment_data['percentages']['neutral']:.0f}% neutre, "
            f"{sentiment_data['percentages']['negative']:.0f}% négatif"
        )
        
        prompt = f"""Tu es un analyste stratégique senior. Rédige un résumé exécutif professionnel.

CONTEXTE: {context}
VOLUME: {total_contents} contenus analysés
SENTIMENT GLOBAL: {sentiment_summary}
THÈMES DOMINANTS: {', '.join(themes)}

RÉSUMÉS PAR SECTION:
{chr(10).join([f"Section {i+1}: {summary}" for i, summary in enumerate(batch_summaries)])}

INSTRUCTIONS CRITIQUES:
Rédige un résumé exécutif en 5-7 paragraphes fluides et narratifs (PAS de listes à puces).

Le résumé doit:
1. Commencer par une vue d'ensemble de la situation
2. Analyser les tendances et opinions dominantes
3. Identifier les préoccupations ou opportunités
4. Évaluer le niveau de risque ou d'engagement
5. Conclure avec les insights stratégiques principaux

Style: Professionnel, factuel, paragraphes rédigés, français soutenu.
Ton: Neutre et objectif, adapté à un briefing ministériel.

RÉSUMÉ EXÉCUTIF:"""
        
        result = await self.generate_smart_synthesis(
            prompt,
            context_data={'total_contents': total_contents},
            max_tokens=800,
            temperature=0.2  # Basse température pour plus de factuel
        )
        
        if result.get('success') and result.get('text'):
            logger.info(f"✅ Résumé exécutif généré via {result['service'].upper()}")
            return result['text']
        else:
            logger.warning("⚠️ Échec génération via API externe, utilisation fallback")
            return self._fallback_executive_summary(
                batch_summaries, sentiment_data, themes, context, total_contents
            )
    
    def _fallback_executive_summary(
        self,
        batch_summaries: List[str],
        sentiment_data: Dict,
        themes: List[str],
        context: str,
        total_contents: int
    ) -> str:
        """Résumé exécutif de secours basé sur des règles"""
        
        neg_pct = sentiment_data['percentages']['negative']
        pos_pct = sentiment_data['percentages']['positive']
        
        summary = f"L'analyse de {total_contents} contenus sur '{context}' révèle les éléments suivants. "
        
        # Paragraphe 1: Sentiment global
        if neg_pct > 60:
            summary += f"Le sentiment global est majoritairement critique ({neg_pct:.0f}% négatif), "
            summary += "reflétant des préoccupations marquées au sein de l'opinion surveillée. "
        elif pos_pct > 60:
            summary += f"Le sentiment global est favorable ({pos_pct:.0f}% positif), "
            summary += "indiquant une réception généralement positive. "
        else:
            summary += "Le sentiment reste partagé entre opinions positives et critiques, "
            summary += "suggérant une polarisation de l'opinion publique. "
        
        # Paragraphe 2: Thèmes
        if themes:
            summary += f"\n\nLes thèmes dominants identifiés sont: {', '.join(themes)}. "
            summary += "Ces sujets concentrent la majorité des discussions et reflètent les préoccupations actuelles. "
        
        # Paragraphe 3: Volume et sources
        summary += f"\n\nCette analyse couvre {len(batch_summaries)} sources distinctes collectées sur la période de surveillance. "
        summary += "La distribution des contenus indique une activité soutenue sur l'ensemble des plateformes monitorées. "
        
        # Paragraphe 4: Conclusion
        if neg_pct > 50:
            summary += "\n\nLa prépondérance du sentiment critique nécessite une attention particulière et pourrait justifier des actions de communication corrective."
        else:
            summary += "\n\nLa situation demeure sous contrôle et ne requiert pas d'action immédiate, bien qu'une surveillance continue soit recommandée."
        
        return summary


# Fonctions utilitaires pour obtenir les clés API
def get_gemini_setup_instructions() -> str:
    """Instructions pour obtenir une clé Gemini gratuitement"""
    return """
    🔑 Comment obtenir une clé API Gemini GRATUITE:
    
    1. Aller sur: https://makersuite.google.com/app/apikey
    2. Se connecter avec un compte Google
    3. Cliquer sur "Create API key"
    4. Copier la clé générée
    5. Ajouter dans .env: GEMINI_API_KEY=votre_cle
    
    Limites gratuites:
    - 15 requêtes/minute
    - 1 million tokens/mois
    - Idéal pour les résumés !
    """


def get_groq_setup_instructions() -> str:
    """Instructions pour obtenir une clé Groq gratuitement"""
    return """
    🔑 Comment obtenir une clé API Groq GRATUITE:
    
    1. Aller sur: https://console.groq.com
    2. Créer un compte (gratuit)
    3. Aller dans "API Keys"
    4. Créer une nouvelle clé
    5. Copier la clé générée
    6. Ajouter dans .env: GROQ_API_KEY=votre_cle
    
    Limites gratuites:
    - 30 requêtes/minute
    - Très rapide !
    - Parfait pour les analyses
    """


# Test du service
async def test_external_ai_service():
    """Tester les services IA externes"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    gemini_key = os.getenv('GEMINI_API_KEY')
    groq_key = os.getenv('GROQ_API_KEY')
    
    if not gemini_key and not groq_key:
        print("❌ Aucune clé API configurée")
        print("\n" + get_gemini_setup_instructions())
        print("\n" + get_groq_setup_instructions())
        return
    
    async with ExternalAIService(gemini_key, groq_key) as ai_service:
        
        print("\n🔍 Test de génération de résumé...")
        
        test_prompt = """Résume en 3 phrases:
        L'intelligence artificielle transforme le monde du travail. 
        De nombreuses entreprises adoptent l'IA pour améliorer leur productivité.
        Cependant, des questions éthiques se posent sur l'automatisation.
        """
        
        result = await ai_service.generate_smart_synthesis(
            test_prompt,
            context_data={},
            max_tokens=200
        )
        
        if result.get('success'):
            print(f"\n✅ Service utilisé: {result['service'].upper()}")
            print(f"📝 Résumé généré:\n{result['text']}")
        else:
            print(f"\n❌ Échec: {result.get('error')}")
        
        # Afficher les quotas
        print("\n📊 Statut des quotas:")
        quotas = ai_service.get_quota_status()
        for service, info in quotas.items():
            if info['available']:
                print(f"   {service.upper()}: {info['used']}/{info['limit']} requêtes")


if __name__ == '__main__':
    asyncio.run(test_external_ai_service())