# Brand Monitor - Système de Surveillance des Mentions

# Brand Monitor v2.0 - Système Professionnel de Surveillance

> Système de surveillance et d'analyse d'opinion publique avec IA souveraine

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()

## 🚀 Caractéristiques Principales

### Surveillance Multi-Sources
- **Réseaux Sociaux**: YouTube, Reddit, TikTok, Telegram, Mastodon, Bluesky
- **Médias**: Google News, RSS Feeds, Web Scraping
- **Commentaires Complets**: Récupération de tous les commentaires et threads

### Intelligence Artificielle Multi-Niveaux
**Priorité automatique des services IA:**
1. **Google Gemini** (prioritaire) - Synthèses de haute qualité
2. **Groq** (secondaire) - Rapidité et efficacité
3. **Ollama Local** (souverain) - Autonomie et confidentialité

### Analyses Avancées
- **Résumé Hiérarchique**: Traitement de milliers de contenus
- **Détection d'Anomalies**: Pics d'activité, changements de sentiment
- **Topic Modeling**: Extraction automatique des thèmes (BERTopic)
- **Analyse de Réseau**: Cartographie des influenceurs et communautés

### Gestion des Influenceurs
- **Activistes Surveillés**: Liste prédéfinie avec profils détaillés
- **Influenceurs Émergents**: Détection automatique
- **Médias Officiels**: Suivi des sources institutionnelles

## 📋 Prérequis

### Obligatoires
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Ollama (pour IA locale)

### Recommandés
- Docker & Docker Compose
- 8 GB RAM minimum
- 20 GB espace disque

## ⚡ Installation Rapide

### Option 1: Docker (Recommandé)

```bash
# Cloner le projet
git clone <repo>
cd brand-monitor

# Copier et configurer .env
cp .env.example .env
nano .env  # Ajouter vos clés API

# Démarrer tous les services
docker-compose up -d

# Télécharger les modèles Ollama
docker exec brandmonitor_ollama ollama pull gemma:2b
docker exec brandmonitor_ollama ollama pull tinyllama
```

### Option 2: Installation Manuelle

```bash
# 1. Installer les dépendances
cd backend
pip install -r requirements.txt

# 2. Télécharger les modèles NLP
python -m spacy download fr_core_news_sm
python -m spacy download en_core_web_sm
python -c "import nltk; nltk.download('vader_lexicon')"

# 3. Installer Ollama et télécharger les modèles
# Voir: https://ollama.ai/download
ollama pull gemma:2b
ollama pull tinyllama

# 4. Configuration
cp .env.example .env
nano .env  # Configurer les clés API

# 5. Initialisation
python backend/app/setup.py

# 6. Démarrer le backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 7. Servir le frontend (terminal séparé)
cd frontend
python -m http.server 8080
```

## 🔑 Configuration des Clés API

### Services IA (Recommandés)

#### Google Gemini (Prioritaire)
**Gratuit**: 15 req/min, 1M tokens/mois
```bash
# 1. Aller sur https://makersuite.google.com/app/apikey
# 2. Se connecter et créer une clé
# 3. Ajouter dans .env:
GEMINI_API_KEY=votre_cle_gemini
```

#### Groq (Secondaire)
**Gratuit**: 30 req/min
```bash
# 1. Aller sur https://console.groq.com
# 2. Créer un compte et une clé API
# 3. Ajouter dans .env:
GROQ_API_KEY=votre_cle_groq
```

### Collecteurs (Optionnels)

#### YouTube
```bash
# Google Cloud Console > APIs > YouTube Data API v3
YOUTUBE_API_KEY=votre_cle_youtube
```

#### Reddit
```bash
# https://www.reddit.com/prefs/apps
REDDIT_CLIENT_ID=votre_client_id
REDDIT_CLIENT_SECRET=votre_secret
REDDIT_USER_AGENT=BrandMonitor/2.0
```

#### Google News
```bash
# https://gnews.io/ (100 req/jour gratuit)
GNEWS_API_KEY=votre_cle_gnews
```

## 🎯 Utilisation

### Accès à l'Interface

- **Frontend**: http://localhost:8080
- **API Documentation**: http://localhost:8000/docs
- **API Alternative**: http://localhost:8000/redoc

### Workflow Typique

1. **Créer des Mots-clés**
   - Aller dans "Mots-clés"
   - Cliquer "Nouveau Mot-clé"
   - Sélectionner les sources
   
2. **Lancer une Collecte**
   - Vue "Mots-clés" > Bouton "Collecter"
   - Ou collecte automatique configurée

3. **Analyser les Résultats**
   - Dashboard: Vue d'ensemble
   - Mentions: Détails complets
   - Influenceurs: Profils et risques

4. **Générer des Analyses IA**
   - Vue "Analyse IA"
   - Résumé hiérarchique
   - Détection d'anomalies
   - Extraction de topics

5. **Exporter des Rapports**
   - Vue "Rapports"
   - Sélectionner critères
   - Générer PDF

## 🏗️ Architecture

```
┌─────────────────┐
│   Frontend      │  Vue.js-like SPA (Vanilla JS)
│   (Port 8080)   │  Charts.js, Modern CSS
└────────┬────────┘
         │
         ↓ HTTP/REST
┌─────────────────┐
│   Backend       │  FastAPI + SQLAlchemy
│   (Port 8000)   │  Routes Advanced
└────────┬────────┘
         │
         ↓
┌─────────────────┐     ┌──────────────────┐
│   PostgreSQL    │     │   Redis Cache    │
│   (Port 5432)   │     │   (Port 6379)    │
└─────────────────┘     └──────────────────┘
         │
         ↓
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Gemini API     │ →   │    Groq API      │ →   │  Ollama Local    │
│  (Prioritaire)  │     │  (Secondaire)    │     │  (Souverain)     │
└─────────────────┘     └──────────────────┘     └──────────────────┘
```

## 📊 Services IA - Ordre de Priorité

Le système utilise automatiquement les services dans cet ordre:

### 1. Google Gemini (Si configuré)
- **Modèle**: gemini-1.5-flash
- **Avantages**: Synthèses de très haute qualité, multilingue
- **Limites**: 15 req/min (gratuit)
- **Usage**: Résumés exécutifs, analyses complexes

### 2. Groq (Si configuré)
- **Modèle**: llama-3.1-8b-instant
- **Avantages**: Très rapide, 30 req/min
- **Limites**: Textes plus courts
- **Usage**: Analyses rapides, classifications

### 3. Ollama Local (Toujours disponible)
- **Modèle**: gemma:2b (par défaut)
- **Avantages**: Souveraineté totale, pas de limite, confidentialité
- **Limites**: Plus lent, qualité variable
- **Usage**: Fallback, analyses sensibles

**La priorité peut être inversée** en mettant `USE_EXTERNAL_AI_PRIORITY=false` dans .env.

## 🔒 Sécurité & Confidentialité

### Souveraineté des Données
- ✅ Ollama tourne localement (pas de fuite de données)
- ✅ Base de données locale
- ✅ Pas de dépendance obligatoire aux APIs externes

### Bonnes Pratiques
- Changer `SECRET_KEY` en production
- Utiliser HTTPS en production
- Configurer les CORS correctement
- Limiter l'accès à PostgreSQL
- Sauvegardes automatiques

## 📈 Performance

### Capacités Testées
- **Collecte**: 10,000+ mentions/heure
- **Analyse**: 1,000+ contenus/minute (résumé hiérarchique)
- **Stockage**: Millions de mentions
- **Concurrence**: Plusieurs utilisateurs simultanés

### Optimisations
- Mise en cache Redis
- Traitement asynchrone
- Batch processing intelligent
- Indexation PostgreSQL

## 🐛 Dépannage

### Ollama ne répond pas
```bash
# Vérifier si Ollama tourne
curl http://localhost:11434/api/tags

# Redémarrer Ollama
# Sur macOS/Linux:
ollama serve

# Docker:
docker restart brandmonitor_ollama
```

### Erreur de connexion PostgreSQL
```bash
# Vérifier la connexion
docker exec -it brandmonitor_db psql -U brandmonitor -d brandmonitor

# Recréer la base
docker-compose down -v
docker-compose up -d
```

### Services IA tous indisponibles
```bash
# Tester chaque service
curl http://localhost:8000/api/advanced/ai/health

# Vérifier les logs
docker-compose logs backend
```

## 📚 Documentation API

### Endpoints Principaux

#### Mots-clés
- `GET /api/keywords` - Liste des mots-clés
- `POST /api/keywords` - Créer un mot-clé
- `DELETE /api/keywords/{id}` - Supprimer

#### Mentions
- `GET /api/mentions` - Liste avec filtres
- `GET /api/mentions/{id}` - Détails

#### Collecte
- `POST /api/collect` - Lancer une collecte
- `POST /api/analyze-sentiment/{id}` - Analyser le sentiment

#### Analyse Avancée
- `POST /api/advanced/summarize` - Résumé hiérarchique
- `GET /api/advanced/influencers` - Analyse des influenceurs
- `GET /api/advanced/anomalies` - Détection d'anomalies
- `GET /api/advanced/topics` - Extraction de topics
- `GET /api/advanced/network` - Réseau d'influence

#### IA
- `GET /api/advanced/ai/health` - Santé des services IA
- `POST /api/advanced/ai/test` - Tester la génération

## 🤝 Support & Contribution

### Rapporter un Bug
Créer une issue avec:
- Description du problème
- Étapes pour reproduire
- Logs pertinents
- Configuration (sans clés API!)

### Développement
```bash
# Backend
cd backend
pip install -r requirements.txt
pytest  # Tests

# Frontend
cd frontend
# Pas de build nécessaire (vanilla JS)
```

## 📝 Licence

Propriétaire - Tous droits réservés

## 🎓 Crédits

- **FastAPI** - Framework web
- **Ollama** - IA locale souveraine
- **BERTopic** - Topic modeling
- **Chart.js** - Visualisations
- **spaCy & NLTK** - NLP

---

**Version**: 2.0.0  
**Dernière mise à jour**: Décembre 2024  
**Support**: [Contact]