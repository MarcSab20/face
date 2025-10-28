# Brand Monitor - Système de Surveillance des Mentions

## 🎯 Vue d'ensemble

Système de surveillance des mentions en ligne gratuit utilisant des sources publiques et APIs gratuites.

### Sources intégrées
- ✅ RSS Feeds (illimité, gratuit)
- ✅ Reddit API (gratuit, 100 requêtes/minute)
- ✅ YouTube Data API (10,000 requêtes/jour gratuit)
- ✅ TikTok (scraping public)
- ✅ Google Alerts (via email parsing)
- ✅ Google Custom Search (100 requêtes/jour gratuit)

## 🏗️ Architecture

```
brand-monitor/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration
│   │   ├── models.py            # Modèles de données
│   │   ├── database.py          # PostgreSQL setup
│   │   └── collectors/          # Collecteurs de données
│   │       ├── rss_collector.py
│   │       ├── reddit_collector.py
│   │       ├── youtube_collector.py
│   │       ├── tiktok_collector.py
│   │       ├── google_alerts_collector.py
│   │       └── google_search_collector.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html               # Dashboard simple
│   ├── app.js
│   └── styles.css
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🚀 Installation Rapide

### Prérequis
- Docker & Docker Compose
- Comptes gratuits : Google Cloud, Reddit

### 1. Cloner et configurer

```bash
cd brand-monitor
cp .env.example .env
# Éditer .env avec vos clés API
```

### 2. Obtenir les clés API (GRATUIT)

**Google Custom Search API :**
1. https://console.cloud.google.com/
2. Créer un projet → Activer "Custom Search API"
3. Créer une clé API
4. Créer un Search Engine ID : https://programmablesearchengine.google.com/

**Reddit API :**
1. https://www.reddit.com/prefs/apps
2. Créer une app (script)
3. Copier client_id et client_secret

**YouTube API :**
1. https://console.cloud.google.com/
2. Activer "YouTube Data API v3"
3. Créer une clé API

### 3. Lancer l'application

```bash
docker-compose up -d
```

Accéder à :
- Dashboard : http://localhost:8080
- API : http://localhost:8000/docs

## 📊 Utilisation

### Ajouter des mots-clés

```bash
curl -X POST http://localhost:8000/api/keywords \
  -H "Content-Type: application/json" \
  -d '{"keyword": "votre marque", "sources": ["reddit", "youtube", "rss"]}'
```

### Lancer une collecte

```bash
curl -X POST http://localhost:8000/api/collect
```

### Voir les résultats

```bash
curl http://localhost:8000/api/mentions?keyword=votre%20marque
```

## 🔧 Configuration Avancée

### Planification automatique (Cron)

Ajouter dans `docker-compose.yml` :
```yaml
  scheduler:
    build: ./backend
    command: python -m app.scheduler
    depends_on:
      - db
      - redis
```

### Alertes Email

Configurer dans `.env` :
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=votre@email.com
SMTP_PASSWORD=votre_mot_de_passe
ALERT_EMAIL=destination@email.com
```

## 💰 Limites Gratuites

| Source | Limite Gratuite | Suffisant pour |
|--------|----------------|----------------|
| Reddit | 100 req/min | 5-10 marques |
| YouTube | 10,000/jour | 20-30 marques |
| Google Search | 100/jour | 5 marques |
| RSS | Illimité | Illimité |
| TikTok | ~50/heure | 10 marques |

## 📈 Évolution

Pour dépasser les limites gratuites :
1. Multiplier les comptes Google (plusieurs projets)
2. Ajouter cache Redis (réduire requêtes)
3. Rotation de proxies pour scraping
4. APIs premium si besoin

## 🔒 Sécurité

- Toutes les clés API dans `.env` (jamais commitées)
- Rate limiting intégré
- Validation des entrées
- Logs de toutes les requêtes

## 📝 Licence

MIT - Libre d'utilisation commerciale