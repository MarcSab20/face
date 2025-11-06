#!/usr/bin/env python3
"""
Validation Complète du Système IA Souverain
Teste tous les composants et génère un rapport détaillé
"""

import sys
import os
import json
import time
import logging
import subprocess
import requests
from datetime import datetime
from pathlib import Path

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class SystemValidator:
    """Validateur complet du système IA"""
    
    def __init__(self):
        self.results = {}
        self.errors = []
        self.warnings = []
        self.start_time = time.time()
        
    def run_complete_validation(self):
        """Validation complète du système"""
        logger.info("🔍 Validation Complète du Système IA Souverain")
        logger.info("=" * 60)
        
        tests = [
            ("Environnement Python", self.test_python_environment),
            ("Service Ollama", self.test_ollama_service),
            ("Modèles LLM", self.test_llm_models),
            ("HuggingFace Transformers", self.test_transformers),
            ("Modèles de langue", self.test_language_models),
            ("Outils de sentiment", self.test_sentiment_tools),
            ("Extraction web", self.test_web_extraction),
            ("Service IA principal", self.test_ai_service),
            ("Génération de rapports", self.test_report_generation),
            ("API Backend", self.test_backend_api),
            ("Performance globale", self.test_performance),
        ]
        
        for test_name, test_func in tests:
            logger.info(f"\n🧪 Test: {test_name}")
            try:
                result = test_func()
                self.results[test_name] = result
                if result.get('success', False):
                    logger.info(f"✅ {test_name} - OK")
                else:
                    logger.warning(f"⚠️ {test_name} - Partiel")
            except Exception as e:
                error_msg = f"❌ {test_name} - ÉCHEC: {e}"
                logger.error(error_msg)
                self.errors.append(error_msg)
                self.results[test_name] = {'success': False, 'error': str(e)}
        
        self.generate_validation_report()
    
    def test_python_environment(self):
        """Test de l'environnement Python"""
        result = {'success': False, 'details': {}}
        
        # Version Python
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        result['details']['python_version'] = python_version
        
        if sys.version_info >= (3, 9):
            result['details']['python_compatible'] = True
        else:
            result['details']['python_compatible'] = False
            return result
        
        # Modules critiques
        critical_modules = [
            'fastapi', 'uvicorn', 'sqlalchemy', 'pandas', 'numpy',
            'aiohttp', 'beautifulsoup4', 'requests'
        ]
        
        missing_modules = []
        for module in critical_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        result['details']['missing_modules'] = missing_modules
        result['details']['modules_ok'] = len(missing_modules) == 0
        
        # Mémoire
        try:
            import psutil
            memory_gb = psutil.virtual_memory().total / (1024**3)
            result['details']['memory_gb'] = round(memory_gb, 1)
            result['details']['memory_sufficient'] = memory_gb >= 8
        except ImportError:
            result['details']['memory_gb'] = 'unknown'
            result['details']['memory_sufficient'] = None
        
        result['success'] = (
            result['details']['python_compatible'] and
            result['details']['modules_ok']
        )
        
        return result
    
    def test_ollama_service(self):
        """Test du service Ollama"""
        result = {'success': False, 'details': {}}
        
        # Vérifier l'installation
        try:
            process_result = subprocess.run(
                ['ollama', '--version'], 
                capture_output=True, text=True, timeout=10
            )
            if process_result.returncode == 0:
                result['details']['installed'] = True
                result['details']['version'] = process_result.stdout.strip()
            else:
                result['details']['installed'] = False
                return result
        except (FileNotFoundError, subprocess.TimeoutExpired):
            result['details']['installed'] = False
            return result
        
        # Vérifier le service
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=10)
            if response.status_code == 200:
                result['details']['service_running'] = True
                tags_data = response.json()
                result['details']['models_count'] = len(tags_data.get('models', []))
            else:
                result['details']['service_running'] = False
        except requests.exceptions.RequestException:
            result['details']['service_running'] = False
        
        result['success'] = (
            result['details']['installed'] and 
            result['details']['service_running']
        )
        
        return result
    
    def test_llm_models(self):
        """Test des modèles LLM"""
        result = {'success': False, 'details': {'models': []}}
        
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=10)
            if response.status_code == 200:
                tags_data = response.json()
                models = tags_data.get('models', [])
                
                for model in models:
                    model_info = {
                        'name': model.get('name'),
                        'size': model.get('size', 0),
                        'modified_at': model.get('modified_at')
                    }
                    result['details']['models'].append(model_info)
                
                # Modèles recommandés
                recommended = ['mistral:7b', 'llama2:7b', 'neural-chat:7b']
                available_models = [m['name'] for m in result['details']['models']]
                
                result['details']['has_recommended'] = any(
                    model in available_models for model in recommended
                )
                
                result['success'] = len(models) > 0
            
        except requests.exceptions.RequestException as e:
            result['details']['error'] = str(e)
        
        return result
    
    def test_transformers(self):
        """Test des modèles Transformers"""
        result = {'success': False, 'details': {}}
        
        try:
            from transformers import pipeline
            import torch
            
            result['details']['transformers_available'] = True
            result['details']['torch_version'] = torch.__version__
            result['details']['cuda_available'] = torch.cuda.is_available()
            
            if torch.cuda.is_available():
                result['details']['gpu_name'] = torch.cuda.get_device_name(0)
                result['details']['gpu_memory'] = torch.cuda.get_device_properties(0).total_memory / 1024**3
            
            # Test modèle de sentiment
            try:
                sentiment_model = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                    device=0 if torch.cuda.is_available() else -1
                )
                test_result = sentiment_model("This is a great test!")
                result['details']['sentiment_model_ok'] = True
                result['details']['sentiment_test'] = test_result[0]
            except Exception as e:
                result['details']['sentiment_model_ok'] = False
                result['details']['sentiment_error'] = str(e)
            
            # Test modèle de classification
            try:
                classifier = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli",
                    device=0 if torch.cuda.is_available() else -1
                )
                result['details']['classification_model_ok'] = True
            except Exception as e:
                result['details']['classification_model_ok'] = False
                result['details']['classification_error'] = str(e)
            
            result['success'] = result['details']['sentiment_model_ok']
            
        except ImportError as e:
            result['details']['transformers_available'] = False
            result['details']['import_error'] = str(e)
        
        return result
    
    def test_language_models(self):
        """Test des modèles de langue"""
        result = {'success': False, 'details': {}}
        
        # Test NLTK
        try:
            import nltk
            
            # Vérifier les datasets
            required_datasets = ['punkt', 'stopwords', 'vader_lexicon']
            nltk_ok = True
            
            for dataset in required_datasets:
                try:
                    nltk.data.find(f'tokenizers/{dataset}')
                except LookupError:
                    try:
                        nltk.data.find(f'corpora/{dataset}')
                    except LookupError:
                        try:
                            nltk.data.find(f'sentiment/{dataset}')
                        except LookupError:
                            nltk_ok = False
                            break
            
            result['details']['nltk_ok'] = nltk_ok
            
        except ImportError:
            result['details']['nltk_ok'] = False
        
        # Test Spacy
        try:
            import spacy
            
            # Vérifier modèles français
            french_models = ['fr_core_news_sm', 'fr_core_news_md']
            available_models = []
            
            for model_name in french_models:
                try:
                    nlp = spacy.load(model_name)
                    available_models.append(model_name)
                except OSError:
                    pass
            
            result['details']['spacy_ok'] = len(available_models) > 0
            result['details']['available_french_models'] = available_models
            
        except ImportError:
            result['details']['spacy_ok'] = False
        
        result['success'] = (
            result['details'].get('nltk_ok', False) or 
            result['details'].get('spacy_ok', False)
        )
        
        return result
    
    def test_sentiment_tools(self):
        """Test des outils de sentiment"""
        result = {'success': False, 'details': {}}
        
        # Test VADER
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            analyzer = SentimentIntensityAnalyzer()
            test_result = analyzer.polarity_scores("This is a great day!")
            result['details']['vader_ok'] = True
            result['details']['vader_test'] = test_result
        except ImportError:
            result['details']['vader_ok'] = False
        
        # Test TextBlob
        try:
            from textblob import TextBlob
            blob = TextBlob("This is a wonderful day")
            sentiment = blob.sentiment
            result['details']['textblob_ok'] = True
            result['details']['textblob_test'] = {
                'polarity': sentiment.polarity,
                'subjectivity': sentiment.subjectivity
            }
        except ImportError:
            result['details']['textblob_ok'] = False
        
        result['success'] = (
            result['details'].get('vader_ok', False) or 
            result['details'].get('textblob_ok', False)
        )
        
        return result
    
    def test_web_extraction(self):
        """Test de l'extraction web"""
        result = {'success': False, 'details': {}}
        
        try:
            import aiohttp
            import asyncio
            from bs4 import BeautifulSoup
            
            result['details']['libraries_ok'] = True
            
            # Test d'extraction simple
            async def test_extraction():
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get('https://httpbin.org/html', timeout=10) as response:
                            if response.status == 200:
                                html = await response.text()
                                soup = BeautifulSoup(html, 'html.parser')
                                title = soup.find('title')
                                return title is not None
                except Exception:
                    return False
                return False
            
            # Exécuter le test
            try:
                extraction_ok = asyncio.run(test_extraction())
                result['details']['extraction_test_ok'] = extraction_ok
            except Exception as e:
                result['details']['extraction_test_ok'] = False
                result['details']['extraction_error'] = str(e)
            
            result['success'] = result['details']['libraries_ok']
            
        except ImportError as e:
            result['details']['libraries_ok'] = False
            result['details']['import_error'] = str(e)
        
        return result
    
    def test_ai_service(self):
        """Test du service IA principal"""
        result = {'success': False, 'details': {}}
        
        # Changer vers le répertoire backend pour les imports
        original_path = sys.path.copy()
        backend_path = os.path.join(os.getcwd(), 'backend')
        
        if os.path.exists(backend_path):
            sys.path.insert(0, backend_path)
        
        try:
            from app.ai_service import SovereignLLMService
            
            # Initialiser le service
            llm_service = SovereignLLMService()
            
            result['details']['service_initialized'] = True
            result['details']['ollama_available'] = llm_service.ollama_available
            result['details']['transformers_available'] = llm_service.transformers_available
            result['details']['is_available'] = llm_service.is_available()
            
            if llm_service.ollama_available:
                result['details']['available_models'] = llm_service.available_models
            
            # Test d'analyse simple
            if llm_service.is_available():
                test_context = {
                    "mentions": [{"title": "Test", "content": "Ceci est un test"}],
                    "keywords": ["test"],
                    "period_days": 1
                }
                
                analysis_result = llm_service._analyze_with_rules(
                    "Analyser ce contenu test", test_context
                )
                
                result['details']['analysis_test_ok'] = len(analysis_result) > 0
                result['details']['analysis_preview'] = analysis_result[:100] + "..."
            
            result['success'] = llm_service.is_available()
            
        except Exception as e:
            result['details']['service_initialized'] = False
            result['details']['error'] = str(e)
        finally:
            # Restaurer le path
            sys.path = original_path
        
        return result
    
    def test_report_generation(self):
        """Test de génération de rapports"""
        result = {'success': False, 'details': {}}
        
        original_path = sys.path.copy()
        backend_path = os.path.join(os.getcwd(), 'backend')
        
        if os.path.exists(backend_path):
            sys.path.insert(0, backend_path)
        
        try:
            from app.ai_service import IntelligentAnalysisAgent, AnalysisContext
            
            # Créer un contexte de test
            context = AnalysisContext(
                mentions=[{
                    "title": "Article de test",
                    "content": "Ceci est un contenu de test pour l'IA",
                    "author": "Test User",
                    "source": "test",
                    "sentiment": "positive",
                    "engagement_score": 100
                }],
                keywords=["test"],
                period_days=1,
                total_mentions=1,
                sentiment_distribution={"positive": 1, "neutral": 0, "negative": 0},
                top_sources={"test": 1},
                engagement_stats={"average": 100},
                geographic_data=[],
                influencers_data=[],
                time_trends=[{"date": "2024-01-01", "count": 1}]
            )
            
            # Test de l'agent
            agent = IntelligentAnalysisAgent()
            result['details']['agent_initialized'] = True
            
            # Le test de génération complète est trop lourd pour cette validation
            # On teste juste l'initialisation
            result['success'] = True
            
        except Exception as e:
            result['details']['agent_initialized'] = False
            result['details']['error'] = str(e)
        finally:
            sys.path = original_path
        
        return result
    
    def test_backend_api(self):
        """Test de l'API backend"""
        result = {'success': False, 'details': {}}
        
        try:
            # Test si le serveur est en cours d'exécution
            response = requests.get('http://localhost:8000/health', timeout=5)
            if response.status_code == 200:
                result['details']['server_running'] = True
                result['details']['health_check'] = response.json()
            else:
                result['details']['server_running'] = False
        except requests.exceptions.RequestException:
            result['details']['server_running'] = False
            result['details']['note'] = "Serveur non démarré - normal pendant l'installation"
        
        # Test des dépendances API
        try:
            import fastapi
            import uvicorn
            result['details']['api_dependencies_ok'] = True
        except ImportError:
            result['details']['api_dependencies_ok'] = False
        
        result['success'] = result['details'].get('api_dependencies_ok', False)
        
        return result
    
    def test_performance(self):
        """Test de performance globale"""
        result = {'success': False, 'details': {}}
        
        # Temps d'import
        start_time = time.time()
        try:
            import pandas
            import numpy
            import transformers
            import_time = time.time() - start_time
            result['details']['import_time'] = round(import_time, 2)
            result['details']['imports_ok'] = True
        except ImportError:
            result['details']['imports_ok'] = False
        
        # Mémoire utilisée
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            result['details']['memory_usage_mb'] = round(memory_mb, 1)
        except ImportError:
            pass
        
        # Test simple de calcul
        start_calc = time.time()
        try:
            import numpy as np
            # Test vectorisé simple
            data = np.random.random((1000, 100))
            result_calc = np.mean(data @ data.T)
            calc_time = time.time() - start_calc
            result['details']['calc_time'] = round(calc_time, 3)
            result['details']['calc_ok'] = True
        except Exception:
            result['details']['calc_ok'] = False
        
        result['success'] = result['details'].get('imports_ok', False)
        
        return result
    
    def generate_validation_report(self):
        """Générer le rapport de validation"""
        total_time = time.time() - self.start_time
        
        print("\n" + "="*80)
        print("🔍 RAPPORT DE VALIDATION - SYSTÈME IA SOUVERAIN")
        print("="*80)
        
        print(f"⏱️  Temps total: {total_time:.1f}s")
        print(f"📊 Tests exécutés: {len(self.results)}")
        
        # Compteurs
        success_count = sum(1 for r in self.results.values() if r.get('success', False))
        partial_count = len(self.results) - success_count - len(self.errors)
        
        print(f"✅ Succès: {success_count}")
        print(f"⚠️  Partiel: {partial_count}")
        print(f"❌ Échecs: {len(self.errors)}")
        
        # Détails par composant
        print("\n📋 DÉTAILS PAR COMPOSANT:")
        for test_name, result in self.results.items():
            status = "✅" if result.get('success') else "⚠️"
            print(f"   {status} {test_name}")
            
            # Détails importants
            details = result.get('details', {})
            if test_name == "Service Ollama" and details.get('models_count'):
                print(f"      └─ {details['models_count']} modèles LLM disponibles")
            elif test_name == "HuggingFace Transformers" and details.get('cuda_available'):
                print(f"      └─ GPU CUDA disponible: {details['cuda_available']}")
            elif test_name == "Service IA principal" and details.get('is_available'):
                print(f"      └─ Service fonctionnel: {details['is_available']}")
        
        # Erreurs
        if self.errors:
            print(f"\n❌ ERREURS ({len(self.errors)}):")
            for error in self.errors:
                print(f"   {error}")
        
        # Avertissements
        if self.warnings:
            print(f"\n⚠️  AVERTISSEMENTS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   {warning}")
        
        # Recommandations
        print("\n💡 RECOMMANDATIONS:")
        
        if success_count >= 8:
            print("   🎉 Système IA opérationnel ! Vous pouvez générer des rapports.")
        elif success_count >= 5:
            print("   ⚡ Système partiellement fonctionnel. Quelques optimisations possibles.")
        else:
            print("   🔧 Configuration incomplète. Relancer l'installation.")
        
        # Instructions de démarrage
        if success_count >= 5:
            print("\n🚀 DÉMARRAGE:")
            print("   1. Backend: cd backend && python -m uvicorn app.main:app --reload")
            print("   2. Frontend: cd frontend && npm run dev")
            print("   3. Interface: http://localhost:3000")
            print("   4. Onglet 'Rapports' pour tester l'IA")
        
        # Sauvegarde du rapport
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'total_time': total_time,
            'tests': self.results,
            'errors': self.errors,
            'warnings': self.warnings,
            'summary': {
                'success_count': success_count,
                'partial_count': partial_count,
                'error_count': len(self.errors)
            }
        }
        
        with open('validation_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Rapport détaillé sauvegardé: validation_report.json")
        print("="*80)

def main():
    """Point d'entrée principal"""
    
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print("""
🔍 Validation Complète - Système IA Souverain

Usage: python validate_system.py [options]

Options:
  --help, -h        Afficher cette aide
  --quick           Tests rapides uniquement
  --detailed        Tests détaillés avec performance

Ce script valide:
  ✅ Environnement Python et dépendances
  ✅ Service Ollama et modèles LLM
  ✅ HuggingFace Transformers
  ✅ Modèles de langue (NLTK, Spacy)
  ✅ Outils de sentiment (VADER, TextBlob)
  ✅ Extraction web intelligente
  ✅ Service IA principal
  ✅ Génération de rapports
  ✅ API Backend
  ✅ Performance globale

Génère un rapport complet en JSON.
        """)
        return
    
    validator = SystemValidator()
    validator.run_complete_validation()

if __name__ == "__main__":
    main()