"""
Service IA Unifié avec Priorité
Gemini (1er) → Groq (2ème) → Ollama Local (3ème)
"""

import logging
import asyncio
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class UnifiedAIService:
    """
    Service IA unifié qui gère intelligemment la priorité entre services
    
    Ordre de priorité:
    1. Google Gemini (si disponible)
    2. Groq (si disponible)
    3. Ollama Local (toujours disponible)
    """
    
    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        groq_api_key: Optional[str] = None,
        ollama_host: str = "http://localhost:11434",
        ollama_model: str = "gemma:2b"
    ):
        self.gemini_api_key = gemini_api_key
        self.groq_api_key = groq_api_key
        self.ollama_host = ollama_host
        self.ollama_model = ollama_model
        
        # Priorités
        self.services = []
        
        if gemini_api_key:
            self.services.append(('gemini', 'Google Gemini 1.5 Flash'))
            logger.info("✅ Service prioritaire: Google Gemini")
        
        if groq_api_key:
            self.services.append(('groq', 'Groq Llama 3.1'))
            logger.info("✅ Service secondaire: Groq")
        
        self.services.append(('ollama', f'Ollama {ollama_model}'))
        logger.info(f"✅ Service de secours: Ollama ({ollama_model})")
        
        if not self.services:
            raise ValueError("Aucun service IA disponible!")
        
        logger.info(f"🎯 Ordre de priorité: {' → '.join([s[1] for s in self.services])}")
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.3,
        context_data: Optional[Dict] = None
    ) -> Dict:
        """
        Générer une réponse en essayant les services par ordre de priorité
        
        Args:
            prompt: Le prompt à envoyer
            max_tokens: Nombre maximum de tokens
            temperature: Température (créativité)
            context_data: Données contextuelles optionnelles
            
        Returns:
            Dict avec 'text', 'service', 'model', 'success'
        """
        
        last_error = None
        
        # Essayer chaque service dans l'ordre de priorité
        for service_name, service_label in self.services:
            try:
                logger.info(f"🔄 Tentative avec {service_label}...")
                
                if service_name == 'gemini':
                    result = await self._generate_with_gemini(prompt, max_tokens, temperature)
                elif service_name == 'groq':
                    result = await self._generate_with_groq(prompt, max_tokens, temperature)
                elif service_name == 'ollama':
                    result = await self._generate_with_ollama(prompt, max_tokens, temperature)
                else:
                    continue
                
                if result.get('success'):
                    logger.info(f"✅ Succès avec {service_label}")
                    return result
                else:
                    logger.warning(f"⚠️ Échec avec {service_label}: {result.get('error')}")
                    last_error = result.get('error')
                    continue
                    
            except Exception as e:
                logger.error(f"❌ Erreur {service_label}: {e}")
                last_error = str(e)
                continue
        
        # Tous les services ont échoué
        return {
            'text': None,
            'service': 'none',
            'error': f'Tous les services ont échoué. Dernière erreur: {last_error}',
            'success': False
        }
    
    async def _generate_with_gemini(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict:
        """Générer avec Google Gemini"""
        
        import aiohttp
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "topP": 0.95,
                "topK": 40
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    text = data['candidates'][0]['content']['parts'][0]['text']
                    
                    return {
                        'text': text,
                        'service': 'gemini',
                        'model': 'gemini-1.5-flash',
                        'tokens_used': len(text) // 4,
                        'success': True
                    }
                else:
                    error_text = await response.text()
                    return {
                        'text': None,
                        'service': 'gemini',
                        'error': f"HTTP {response.status}: {error_text}",
                        'success': False
                    }
    
    async def _generate_with_groq(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict:
        """Générer avec Groq"""
        
        import aiohttp
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        headers = {
            'Authorization': f'Bearer {self.groq_api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 0.95
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    text = data['choices'][0]['message']['content']
                    
                    return {
                        'text': text,
                        'service': 'groq',
                        'model': 'llama-3.1-8b-instant',
                        'tokens_used': data['usage']['total_tokens'],
                        'success': True
                    }
                else:
                    error_text = await response.text()
                    return {
                        'text': None,
                        'service': 'groq',
                        'error': f"HTTP {response.status}: {error_text}",
                        'success': False
                    }
    
    async def _generate_with_ollama(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict:
        """Générer avec Ollama local"""
        
        import aiohttp
        
        url = f"{self.ollama_host}/api/generate"
        
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=60) as response:
                if response.status == 200:
                    data = await response.json()
                    text = data.get('response', '')
                    
                    return {
                        'text': text,
                        'service': 'ollama',
                        'model': self.ollama_model,
                        'tokens_used': len(text) // 4,
                        'success': True
                    }
                else:
                    error_text = await response.text()
                    return {
                        'text': None,
                        'service': 'ollama',
                        'error': f"HTTP {response.status}: {error_text}",
                        'success': False
                    }
    
    def get_available_services(self) -> List[Dict]:
        """Obtenir la liste des services disponibles"""
        return [
            {
                'name': name,
                'label': label,
                'priority': idx + 1
            }
            for idx, (name, label) in enumerate(self.services)
        ]
    
    async def health_check(self) -> Dict:
        """Vérifier la santé de tous les services"""
        
        health = {}
        
        for service_name, service_label in self.services:
            try:
                test_prompt = "Test de connexion. Réponds simplement 'OK'."
                
                result = await asyncio.wait_for(
                    self.generate(test_prompt, max_tokens=10, temperature=0.1),
                    timeout=10
                )
                
                health[service_name] = {
                    'label': service_label,
                    'status': 'healthy' if result.get('success') else 'unhealthy',
                    'error': result.get('error') if not result.get('success') else None
                }
                
            except asyncio.TimeoutError:
                health[service_name] = {
                    'label': service_label,
                    'status': 'timeout',
                    'error': 'Timeout après 10 secondes'
                }
            except Exception as e:
                health[service_name] = {
                    'label': service_label,
                    'status': 'error',
                    'error': str(e)
                }
        
        return health


# Test du service
async def test_unified_service():
    """Tester le service unifié"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    service = UnifiedAIService(
        gemini_api_key=os.getenv('GEMINI_API_KEY'),
        groq_api_key=os.getenv('GROQ_API_KEY'),
        ollama_host=os.getenv('OLLAMA_HOST', 'http://localhost:11434'),
        ollama_model=os.getenv('OLLAMA_DEFAULT_MODEL', 'gemma:2b')
    )
    
    print("\n📊 Services disponibles:")
    for svc in service.get_available_services():
        print(f"   {svc['priority']}. {svc['label']}")
    
    print("\n🔍 Test de génération...")
    result = await service.generate(
        prompt="Résume en une phrase: L'intelligence artificielle transforme le monde.",
        max_tokens=100,
        temperature=0.3
    )
    
    if result['success']:
        print(f"\n✅ Service utilisé: {result['service'].upper()}")
        print(f"📝 Réponse: {result['text']}")
    else:
        print(f"\n❌ Échec: {result['error']}")
    
    print("\n🏥 Health check des services...")
    health = await service.health_check()
    for svc_name, svc_health in health.items():
        status_emoji = "✅" if svc_health['status'] == 'healthy' else "❌"
        print(f"   {status_emoji} {svc_health['label']}: {svc_health['status']}")


if __name__ == '__main__':
    asyncio.run(test_unified_service())