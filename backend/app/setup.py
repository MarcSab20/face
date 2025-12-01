#!/usr/bin/env python3
"""
Script d'Initialisation Automatique - Brand Monitor
Vérifie et configure tout ce qui est nécessaire au démarrage
"""

import os
import sys
import subprocess
import time
from pathlib import Path


class Colors:
    """Couleurs pour terminal"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Afficher un header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def print_success(text):
    """Afficher un succès"""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")


def print_warning(text):
    """Afficher un avertissement"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")


def print_error(text):
    """Afficher une erreur"""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")


def print_info(text):
    """Afficher une info"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")


def run_command(command, description, check=True):
    """Exécuter une commande shell"""
    print(f"\n⏳ {description}...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=check,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print_success(description)
            return True
        else:
            if check:
                print_error(f"{description} - Erreur: {result.stderr}")
                return False
            return False
    except subprocess.CalledProcessError as e:
        print_error(f"{description} - Erreur: {e}")
        return False


def check_python_version():
    """Vérifier la version Python"""
    print_info("Vérification de Python...")
    version = sys.version_info
    
    if version.major == 3 and version.minor >= 11:
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python 3.11+ requis (trouvé: {version.major}.{version.minor})")
        return False


def check_docker():
    """Vérifier si Docker est disponible"""
    print_info("Vérification de Docker...")
    result = run_command("docker --version", "Docker disponible", check=False)
    return result


def check_ollama():
    """Vérifier si Ollama est disponible"""
    print_info("Vérification d'Ollama...")
    result = run_command("ollama --version", "Ollama disponible", check=False)
    return result


def download_ollama_models():
    """Télécharger les modèles Ollama nécessaires"""
    print_header("TÉLÉCHARGEMENT DES MODÈLES OLLAMA")
    
    if not check_ollama():
        print_warning("Ollama non installé. Installation requise:")
        print_info("   Visiter: https://ollama.ai/download")
        return False
    
    models = [
        ("gemma:2b", "Modèle principal (2GB)"),
        ("tinyllama", "Modèle de secours (600MB)")
    ]
    
    for model_name, description in models:
        print(f"\n📦 Téléchargement: {model_name} - {description}")
        
        # Vérifier si déjà téléchargé
        check_result = subprocess.run(
            f"ollama list | grep {model_name.split(':')[0]}",
            shell=True,
            capture_output=True
        )
        
        if check_result.returncode == 0:
            print_success(f"{model_name} déjà disponible")
            continue
        
        # Télécharger le modèle
        print_info(f"Téléchargement en cours (peut prendre plusieurs minutes)...")
        result = subprocess.run(
            f"ollama pull {model_name}",
            shell=True
        )
        
        if result.returncode == 0:
            print_success(f"{model_name} téléchargé")
        else:
            print_error(f"Échec téléchargement {model_name}")
    
    return True


def install_spacy_models():
    """Installer les modèles spaCy"""
    print_header("INSTALLATION DES MODÈLES SPACY")
    
    models = [
        ("fr_core_news_sm", "Modèle français"),
        ("en_core_web_sm", "Modèle anglais")
    ]
    
    for model_name, description in models:
        print(f"\n📦 Installation: {model_name} - {description}")
        result = run_command(
            f"python -m spacy download {model_name}",
            f"Installation {model_name}",
            check=False
        )
    
    return True


def install_nltk_data():
    """Télécharger les données NLTK"""
    print_header("TÉLÉCHARGEMENT DES DONNÉES NLTK")
    
    print_info("Téléchargement vader_lexicon...")
    
    try:
        import nltk
        nltk.download('vader_lexicon', quiet=True)
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        print_success("Données NLTK téléchargées")
        return True
    except Exception as e:
        print_error(f"Erreur téléchargement NLTK: {e}")
        return False


def install_playwright():
    """Installer les navigateurs Playwright (pour TikTok)"""
    print_header("INSTALLATION DE PLAYWRIGHT")
    
    print_info("Installation des navigateurs (pour TikTok)...")
    result = run_command(
        "playwright install",
        "Installation navigateurs Playwright",
        check=False
    )
    
    if not result:
        print_warning("Playwright non installé - TikTok collector non disponible")
    
    return True


def check_env_file():
    """Vérifier la présence du fichier .env"""
    print_header("VÉRIFICATION DE LA CONFIGURATION")
    
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    
    if not env_path.exists():
        if env_example_path.exists():
            print_warning(".env manquant")
            print_info("Copie de .env.example vers .env...")
            
            import shutil
            shutil.copy(env_example_path, env_path)
            
            print_success(".env créé depuis .env.example")
            print_warning("⚠️  IMPORTANT: Éditer .env et remplir les clés API")
            print_info("   Consultez: API_KEYS_SETUP_GUIDE.md")
            return False
        else:
            print_error(".env.example manquant!")
            return False
    else:
        print_success(".env trouvé")
    
    # Charger et vérifier les variables critiques
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        critical_vars = [
            "DATABASE_URL",
            "REDIS_URL",
            "OLLAMA_HOST"
        ]
        
        missing = []
        for var in critical_vars:
            if not os.getenv(var):
                missing.append(var)
        
        if missing:
            print_warning(f"Variables manquantes: {', '.join(missing)}")
            return False
        
        print_success("Variables critiques configurées")
        
        # Vérifier les APIs optionnelles
        optional_apis = {
            "GEMINI_API_KEY": "Google Gemini",
            "GROQ_API_KEY": "Groq",
            "YOUTUBE_API_KEY": "YouTube",
            "REDDIT_CLIENT_ID": "Reddit",
            "GNEWS_API_KEY": "Google News"
        }
        
        configured_apis = []
        for var, name in optional_apis.items():
            if os.getenv(var):
                configured_apis.append(name)
        
        if configured_apis:
            print_success(f"APIs configurées: {', '.join(configured_apis)}")
        else:
            print_warning("Aucune API externe configurée")
            print_info("   Le système utilisera uniquement Ollama local")
            print_info("   Pour de meilleurs résultats, configurer Gemini ou Groq")
        
        return True
        
    except Exception as e:
        print_error(f"Erreur vérification .env: {e}")
        return False


def init_database():
    """Initialiser la base de données"""
    print_header("INITIALISATION DE LA BASE DE DONNÉES")
    
    # Vérifier si Docker est utilisé
    if check_docker():
        print_info("Utilisation de Docker détectée")
        print_info("La base de données sera initialisée au démarrage de Docker")
        return True
    
    # Sinon, utiliser Alembic
    print_info("Initialisation avec Alembic...")
    
    # Vérifier si Alembic est configuré
    if not Path("alembic").exists():
        print_info("Configuration Alembic...")
        result = run_command(
            "alembic init alembic",
            "Initialisation Alembic",
            check=False
        )
    
    # Créer les tables
    try:
        from app.database import init_db
        init_db()
        print_success("Base de données initialisée")
        return True
    except Exception as e:
        print_warning(f"Base de données non initialisée: {e}")
        print_info("   Elle sera initialisée au premier démarrage")
        return True


def create_directories():
    """Créer les répertoires nécessaires"""
    print_header("CRÉATION DES RÉPERTOIRES")
    
    directories = [
        "reports",
        "logs",
        "backups",
        "temp"
    ]
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print_success(f"Répertoire créé: {directory}/")
        else:
            print_info(f"Répertoire existant: {directory}/")
    
    return True


def display_startup_instructions():
    """Afficher les instructions de démarrage"""
    print_header("INSTRUCTIONS DE DÉMARRAGE")
    
    print(f"{Colors.BOLD}Option 1: Docker (Recommandé){Colors.RESET}")
    print(f"  {Colors.GREEN}docker-compose up -d{Colors.RESET}")
    print(f"  {Colors.BLUE}→ Démarre tous les services automatiquement{Colors.RESET}\n")
    
    print(f"{Colors.BOLD}Option 2: Développement local{Colors.RESET}")
    print(f"  {Colors.GREEN}uvicorn app.main:app --reload{Colors.RESET}")
    print(f"  {Colors.BLUE}→ Démarrer le backend seulement{Colors.RESET}\n")
    
    print(f"{Colors.BOLD}Vérification:{Colors.RESET}")
    print(f"  {Colors.GREEN}curl http://localhost:8000/health{Colors.RESET}")
    print(f"  {Colors.BLUE}→ Tester que l'API répond{Colors.RESET}\n")
    
    print(f"{Colors.BOLD}Interface web:{Colors.RESET}")
    print(f"  {Colors.GREEN}http://localhost:8080{Colors.RESET}")
    print(f"  {Colors.BLUE}→ Accéder au frontend{Colors.RESET}\n")
    
    print(f"{Colors.BOLD}API Documentation:{Colors.RESET}")
    print(f"  {Colors.GREEN}http://localhost:8000/docs{Colors.RESET}")
    print(f"  {Colors.BLUE}→ Documentation interactive (Swagger){Colors.RESET}\n")


def main():
    """Fonction principale"""
    print_header("INITIALISATION BRAND MONITOR")
    
    print(f"{Colors.BOLD}Ce script va:{Colors.RESET}")
    print("  • Vérifier les prérequis")
    print("  • Télécharger les modèles IA")
    print("  • Installer les dépendances NLP")
    print("  • Configurer la base de données")
    print("  • Vérifier la configuration\n")
    
    input(f"{Colors.YELLOW}Appuyez sur Entrée pour continuer...{Colors.RESET}\n")
    
    # Étape 1: Prérequis
    print_header("ÉTAPE 1/7: VÉRIFICATION DES PRÉREQUIS")
    
    if not check_python_version():
        print_error("Python 3.11+ requis")
        sys.exit(1)
    
    docker_available = check_docker()
    ollama_available = check_ollama()
    
    if not ollama_available:
        print_warning("Ollama recommandé pour IA locale souveraine")
        print_info("   Installer depuis: https://ollama.ai/download")
    
    # Étape 2: Modèles Ollama
    print_header("ÉTAPE 2/7: MODÈLES OLLAMA")
    if ollama_available:
        download_ollama_models()
    else:
        print_warning("Ollama non disponible - Étape ignorée")
        print_info("   Le système utilisera uniquement les APIs externes")
    
    # Étape 3: Modèles spaCy
    print_header("ÉTAPE 3/7: MODÈLES SPACY")
    install_spacy_models()
    
    # Étape 4: Données NLTK
    print_header("ÉTAPE 4/7: DONNÉES NLTK")
    install_nltk_data()
    
    # Étape 5: Playwright (optionnel)
    print_header("ÉTAPE 5/7: PLAYWRIGHT")
    install_playwright()
    
    # Étape 6: Configuration
    print_header("ÉTAPE 6/7: CONFIGURATION")
    env_configured = check_env_file()
    
    # Étape 7: Base de données
    print_header("ÉTAPE 7/7: BASE DE DONNÉES")
    create_directories()
    init_database()
    
    # Résumé final
    print_header("INITIALISATION TERMINÉE")
    
    if env_configured and (ollama_available or os.getenv("GEMINI_API_KEY") or os.getenv("GROQ_API_KEY")):
        print_success("Système prêt à démarrer!")
        display_startup_instructions()
    else:
        print_warning("Configuration incomplète")
        print_info("Actions requises:")
        
        if not env_configured:
            print(f"  {Colors.YELLOW}1. Éditer le fichier .env{Colors.RESET}")
            print(f"  {Colors.YELLOW}2. Remplir les clés API (voir API_KEYS_SETUP_GUIDE.md){Colors.RESET}")
        
        if not ollama_available and not os.getenv("GEMINI_API_KEY"):
            print(f"  {Colors.YELLOW}3. Installer Ollama OU configurer Gemini/Groq{Colors.RESET}")
        
        print(f"\n{Colors.BLUE}Puis relancer: python setup.py{Colors.RESET}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Initialisation annulée{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n{Colors.RED}Erreur inattendue: {e}{Colors.RESET}")
        sys.exit(1)