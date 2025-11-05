#!/usr/bin/env python3
"""
Script de configuration automatique pour l'IA Souveraine
Installe et configure tous les composants nécessaires
"""

import os
import sys
import subprocess
import platform
import logging
import time
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class IASetup:
    """Configuration automatique du système IA"""
    
    def __init__(self):
        self.system = platform.system()
        self.python_version = sys.version_info
        self.errors = []
        self.warnings = []
        
    def run_setup(self):
        """Lancer la configuration complète"""
        logger.info("🤖 Début de la configuration de l'IA Souveraine")
        logger.info(f"Système: {self.system}, Python: {self.python_version.major}.{self.python_version.minor}")
        
        steps = [
            ("Vérification des prérequis", self.check_prerequisites),
            ("Installation des dépendances Python", self.install_python_dependencies),
            ("Configuration d'Ollama", self.setup_ollama),
            ("Téléchargement des modèles NLTK", self.setup_nltk),
            ("Configuration des modèles Spacy", self.setup_spacy),
            ("Test du service IA", self.test_ai_service),
            ("Configuration des variables d'environnement", self.setup_environment),
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n📋 {step_name}...")
            try:
                step_func()
                logger.info(f"✅ {step_name} - Terminé")
            except Exception as e:
                error_msg = f"❌ {step_name} - Erreur: {e}"
                logger.error(error_msg)
                self.errors.append(error_msg)
        
        self.print_summary()
    
    def check_prerequisites(self):
        """Vérifier les prérequis système"""
        
        # Vérifier Python 3.9+
        if self.python_version < (3, 9):
            raise Exception(f"Python 3.9+ requis, version détectée: {self.python_version.major}.{self.python_version.minor}")
        
        # Vérifier pip
        try:
            subprocess.run([sys.executable, "-m", "pip", "--version"], 
                         check=True, capture_output=True)
        except subprocess.CalledProcessError:
            raise Exception("pip n'est pas installé ou accessible")
        
        # Vérifier la mémoire disponible
        import psutil
        memory_gb = psutil.virtual_memory().total / (1024**3)
        if memory_gb < 4:
            self.warnings.append(f"Mémoire faible ({memory_gb:.1f}GB). 8GB+ recommandé pour l'IA")
        
        # Vérifier CUDA (optionnel)
        try:
            import torch
            if torch.cuda.is_available():
                logger.info(f"🎮 GPU CUDA détecté: {torch.cuda.get_device_name(0)}")
            else:
                self.warnings.append("GPU CUDA non détecté - performances CPU uniquement")
        except ImportError:
            logger.info("PyTorch pas encore installé - vérification GPU plus tard")
        
        logger.info("Prérequis système OK")
    
    def install_python_dependencies(self):
        """Installer les dépendances Python"""
        
        requirements_files = [
            "requirements_ia.txt",  # Dépendances IA spécifiques
            "requirements.txt"      # Dépendances générales
        ]
        
        for req_file in requirements_files:
            if os.path.exists(req_file):
                logger.info(f"Installation depuis {req_file}...")
                try:
                    subprocess.run([
                        sys.executable, "-m", "pip", "install", 
                        "-r", req_file, "--break-system-packages"
                    ], check=True, capture_output=True, text=True)
                except subprocess.CalledProcessError as e:
                    # Essayer sans --break-system-packages
                    subprocess.run([
                        sys.executable, "-m", "pip", "install", 
                        "-r", req_file
                    ], check=True)
            else:
                self.warnings.append(f"Fichier {req_file} non trouvé")
        
        # Installation spécifique PyTorch avec GPU si disponible
        self.install_pytorch()
    
    def install_pytorch(self):
        """Installer PyTorch avec support GPU si possible"""
        
        try:
            # Détecter CUDA
            nvidia_detect = subprocess.run(["nvidia-smi"], capture_output=True)
            cuda_available = nvidia_detect.returncode == 0
            
            if cuda_available:
                logger.info("🎮 Installation PyTorch avec support CUDA...")
                subprocess.run([
                    sys.executable, "-m", "pip", "install",
                    "torch", "torchvision", "torchaudio",
                    "--index-url", "https://download.pytorch.org/whl/cu118"
                ], check=True)
            else:
                logger.info("💻 Installation PyTorch CPU uniquement...")
                subprocess.run([
                    sys.executable, "-m", "pip", "install",
                    "torch", "torchvision", "torchaudio", "--index-url",
                    "https://download.pytorch.org/whl/cpu"
                ], check=True)
                
        except subprocess.CalledProcessError:
            self.warnings.append("Installation PyTorch échouée - utilisation version par défaut")
    
    def setup_ollama(self):
        """Configurer Ollama pour les modèles LLM locaux"""
        
        # Vérifier si Ollama est déjà installé
        try:
            result = subprocess.run(["ollama", "--version"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Ollama déjà installé: {result.stdout.strip()}")
            else:
                raise subprocess.CalledProcessError(1, "ollama")
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Installer Ollama
            self.install_ollama()
        
        # Télécharger les modèles recommandés
        self.download_ollama_models()
    
    def install_ollama(self):
        """Installer Ollama selon le système"""
        
        if self.system == "Linux":
            logger.info("📥 Installation d'Ollama sur Linux...")
            subprocess.run([
                "curl", "-fsSL", "https://ollama.ai/install.sh"
            ], check=True, stdout=subprocess.PIPE)
            subprocess.run(["sh"], input=b"curl -fsSL https://ollama.ai/install.sh | sh", check=True)
            
        elif self.system == "Darwin":  # macOS
            logger.info("📥 Installation d'Ollama sur macOS...")
            subprocess.run([
                "curl", "-fsSL", "https://ollama.ai/install.sh"
            ], check=True, stdout=subprocess.PIPE)
            subprocess.run(["sh"], input=b"curl -fsSL https://ollama.ai/install.sh | sh", check=True)
            
        elif self.system == "Windows":
            logger.info("📥 Ollama sur Windows - installation manuelle requise")
            logger.info("Téléchargez depuis: https://ollama.ai/download/windows")
            self.warnings.append("Installation manuelle d'Ollama requise sur Windows")
            return
        
        # Attendre qu'Ollama soit prêt
        time.sleep(5)
    
    def download_ollama_models(self):
        """Télécharger les modèles Ollama recommandés"""
        
        models = [
            ("mistral:7b", "Modèle Mistral 7B (Recommandé)"),
            ("llama2:7b", "Modèle Llama 2 7B"),
            ("neural-chat:7b", "Modèle Neural Chat 7B")
        ]
        
        for model_name, description in models:
            try:
                logger.info(f"📦 Téléchargement {description}...")
                # Timeout long car les modèles sont volumineux
                subprocess.run(["ollama", "pull", model_name], 
                             check=True, timeout=1800)  # 30 minutes max
                logger.info(f"✅ {description} téléchargé")
            except subprocess.TimeoutExpired:
                self.warnings.append(f"Timeout téléchargement {model_name}")
            except subprocess.CalledProcessError:
                self.warnings.append(f"Échec téléchargement {model_name}")
    
    def setup_nltk(self):
        """Configurer les données NLTK"""
        
        logger.info("📚 Téléchargement des données NLTK...")
        
        try:
            import nltk
            
            # Dossier de données NLTK
            nltk_data_dir = os.path.expanduser("~/nltk_data")
            if not os.path.exists(nltk_data_dir):
                os.makedirs(nltk_data_dir)
            
            # Télécharger les datasets nécessaires
            datasets = [
                'punkt',
                'stopwords', 
                'vader_lexicon',
                'averaged_perceptron_tagger',
                'wordnet'
            ]
            
            for dataset in datasets:
                try:
                    nltk.download(dataset, quiet=True)
                    logger.info(f"✅ NLTK {dataset} téléchargé")
                except Exception as e:
                    self.warnings.append(f"Échec téléchargement NLTK {dataset}: {e}")
                    
        except ImportError:
            raise Exception("NLTK non installé - vérifiez requirements_ia.txt")
    
    def setup_spacy(self):
        """Configurer les modèles Spacy"""
        
        logger.info("🧠 Configuration des modèles Spacy...")
        
        models = [
            ("fr_core_news_sm", "Modèle français léger"),
            ("fr_core_news_md", "Modèle français moyen (recommandé)"),
            ("en_core_web_sm", "Modèle anglais léger")
        ]
        
        for model_name, description in models:
            try:
                logger.info(f"📦 Installation {description}...")
                subprocess.run([
                    sys.executable, "-m", "spacy", "download", model_name
                ], check=True, capture_output=True)
                logger.info(f"✅ {description} installé")
            except subprocess.CalledProcessError:
                self.warnings.append(f"Échec installation modèle Spacy {model_name}")
    
    def test_ai_service(self):
        """Tester que le service IA fonctionne"""
        
        logger.info("🧪 Test du service IA...")
        
        test_code = '''
import sys
import os
sys.path.append(os.getcwd())

try:
    from ia_service import SovereignLLMService
    
    # Initialiser le service
    llm_service = SovereignLLMService()
    
    # Tester la disponibilité
    if llm_service.is_available():
        print("✅ Service IA disponible")
        
        if llm_service.ollama_available:
            print(f"✅ Ollama actif avec {len(llm_service.available_models)} modèle(s)")
        
        if llm_service.transformers_available:
            print("✅ HuggingFace Transformers actif")
        
        # Test d'analyse simple
        test_result = llm_service._analyze_with_rules(
            "test", 
            {"mentions": [{"title": "Test", "content": "Ceci est un test"}]}
        )
        print("✅ Analyse de test réussie")
        
    else:
        print("❌ Service IA non disponible")
        
except Exception as e:
    print(f"❌ Erreur test IA: {e}")
'''
        
        try:
            result = subprocess.run([
                sys.executable, "-c", test_code
            ], capture_output=True, text=True, cwd=os.getcwd())
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
                
            if "Service IA disponible" in result.stdout:
                logger.info("✅ Service IA opérationnel")
            else:
                self.warnings.append("Service IA partiellement fonctionnel")
                
        except Exception as e:
            self.warnings.append(f"Test IA échoué: {e}")
    
    def setup_environment(self):
        """Configurer les variables d'environnement"""
        
        env_file = ".env"
        env_vars = {
            "AI_SERVICE_ENABLED": "true",
            "OLLAMA_HOST": "http://localhost:11434",
            "HF_HOME": os.path.expanduser("~/.cache/huggingface"),
            "TRANSFORMERS_CACHE": os.path.expanduser("~/.cache/huggingface/transformers"),
            "TORCH_HOME": os.path.expanduser("~/.cache/torch"),
        }
        
        # Lire le fichier .env existant
        existing_vars = {}
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        existing_vars[key] = value
        
        # Ajouter les nouvelles variables
        updated = False
        for key, value in env_vars.items():
            if key not in existing_vars:
                existing_vars[key] = value
                updated = True
        
        if updated:
            # Réécrire le fichier .env
            with open(env_file, 'w') as f:
                f.write("# Configuration automatique IA\n")
                for key, value in existing_vars.items():
                    f.write(f"{key}={value}\n")
            
            logger.info(f"Variables d'environnement ajoutées à {env_file}")
        else:
            logger.info("Variables d'environnement déjà configurées")
    
    def print_summary(self):
        """Afficher le résumé de l'installation"""
        
        print("\n" + "="*60)
        print("🤖 RÉSUMÉ DE LA CONFIGURATION IA SOUVERAINE")
        print("="*60)
        
        if not self.errors:
            print("✅ Configuration terminée avec SUCCÈS!")
        else:
            print("⚠️  Configuration terminée avec des ERREURS")
        
        if self.warnings:
            print(f"\n⚠️  Avertissements ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        if self.errors:
            print(f"\n❌ Erreurs ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")
        
        print("\n📋 PROCHAINES ÉTAPES:")
        print("   1. Redémarrer votre terminal/IDE")
        print("   2. Tester l'API: python -m uvicorn app.main:app --reload")
        print("   3. Accéder à l'interface: http://localhost:3000")
        print("   4. Générer votre premier rapport IA dans la section Rapports")
        
        print("\n🔧 COMMANDES UTILES:")
        print("   • Tester l'IA: python -c \"from ia_service import SovereignLLMService; print('IA:', SovereignLLMService().is_available())\"")
        print("   • Lister modèles Ollama: ollama list")
        print("   • Logs Ollama: ollama logs")
        
        print("\n📚 DOCUMENTATION:")
        print("   • Ollama: https://ollama.ai/docs")
        print("   • HuggingFace: https://huggingface.co/docs/transformers")
        print("   • Configuration IA: Voir ia_service.py")
        
        print("\n🚀 Votre IA souveraine est prête à analyser!")
        print("="*60)


def main():
    """Point d'entrée principal"""
    
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print("""
🤖 Script de Configuration IA Souveraine

Usage: python setup_ia.py [options]

Options:
  --help, -h     Afficher cette aide
  --check-only   Vérifier uniquement les prérequis
  --no-models    Ne pas télécharger les modèles (plus rapide)

Ce script configure automatiquement:
  ✅ Dépendances Python pour l'IA
  ✅ Ollama et modèles LLM locaux
  ✅ Modèles NLTK et Spacy
  ✅ Variables d'environnement
  ✅ Test du service IA

Prérequis:
  • Python 3.9+
  • 8GB RAM recommandé
  • Connexion Internet pour téléchargements
  • Droits administrateur (selon système)
        """)
        return
    
    setup = IASetup()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--check-only':
        try:
            setup.check_prerequisites()
            print("✅ Tous les prérequis sont satisfaits")
        except Exception as e:
            print(f"❌ Prérequis manquants: {e}")
        return
    
    setup.run_setup()


if __name__ == "__main__":
    main()