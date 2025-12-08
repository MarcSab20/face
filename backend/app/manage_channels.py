#!/usr/bin/env python3
"""
Script CLI pour gérer les channels de monitoring Brand Monitor
Usage: python manage_channels.py [command] [options]
"""

import requests
import argparse
import sys
import json
from typing import List, Optional
from datetime import datetime
from tabulate import tabulate

# Configuration
BASE_URL = "http://localhost:8000/api"
WHATSAPP_BRIDGE_URL = "http://localhost:3500"


class ChannelManager:
    """Gestionnaire de channels de monitoring"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def _request(self, method: str, endpoint: str, **kwargs):
        """Effectuer une requête HTTP"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"❌ Erreur HTTP {e.response.status_code}: {e.response.text}")
            sys.exit(1)
        except requests.exceptions.ConnectionError:
            print(f"❌ Impossible de se connecter à {url}")
            print("💡 Vérifiez que le backend est démarré: docker-compose up -d")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Erreur: {e}")
            sys.exit(1)
    
    def list_channels(self, active_only: bool = False):
        """Lister tous les channels"""
        params = {"active_only": active_only} if active_only else {}
        channels = self._request("GET", "/channels/", params=params)
        
        if not channels:
            print("📭 Aucun channel configuré")
            print("💡 Ajoutez votre premier channel avec: python manage_channels.py add-youtube ...")
            return
        
        # Formater pour affichage
        table_data = []
        for ch in channels:
            table_data.append([
                ch["id"],
                ch["name"],
                ch["channel_type"],
                "✅" if ch["active"] else "❌",
                f"{ch['check_interval_minutes']} min",
                "🔔" if ch.get("enable_email_alerts") else "🔕",
                ch.get("last_check_at", "Jamais")[:19] if ch.get("last_check_at") else "Jamais"
            ])
        
        headers = ["ID", "Nom", "Type", "Actif", "Intervalle", "Alertes", "Dernière collecte"]
        print("\n" + tabulate(table_data, headers=headers, tablefmt="grid"))
        print(f"\n📊 Total: {len(channels)} channel(s)")
    
    def add_youtube_channel(
        self, 
        name: str, 
        channel_id: str,
        interval: int = 60,
        keywords: Optional[List[str]] = None,
        alert_emails: Optional[List[str]] = None
    ):
        """Ajouter une chaîne YouTube"""
        data = {
            "name": name,
            "channel_type": "youtube_rss",
            "channel_id": channel_id,
            "check_interval_minutes": interval,
            "enable_email_alerts": bool(keywords),
            "alert_keywords": keywords or [],
            "alert_emails": alert_emails or []
        }
        
        result = self._request("POST", "/channels/", json=data)
        print(f"✅ Chaîne YouTube '{name}' ajoutée avec succès!")
        print(f"   ID: {result['id']}")
        print(f"   Type: {result['channel_type']}")
        print(f"   Intervalle de collecte: {interval} minutes")
        if keywords:
            print(f"   Mots-clés d'alerte: {', '.join(keywords)}")
    
    def add_rss_feed(
        self,
        name: str,
        feed_url: str,
        interval: int = 30,
        keywords: Optional[List[str]] = None,
        alert_emails: Optional[List[str]] = None
    ):
        """Ajouter un flux RSS"""
        data = {
            "name": name,
            "channel_type": "web_rss",
            "channel_id": feed_url,
            "check_interval_minutes": interval,
            "enable_email_alerts": bool(keywords),
            "alert_keywords": keywords or [],
            "alert_emails": alert_emails or []
        }
        
        result = self._request("POST", "/channels/", json=data)
        print(f"✅ Flux RSS '{name}' ajouté avec succès!")
        print(f"   ID: {result['id']}")
        print(f"   URL: {feed_url}")
        print(f"   Intervalle de collecte: {interval} minutes")
        if keywords:
            print(f"   Mots-clés d'alerte: {', '.join(keywords)}")
    
    def add_telegram_channel(
        self,
        name: str,
        username: str,
        interval: int = 15,
        keywords: Optional[List[str]] = None,
        alert_emails: Optional[List[str]] = None
    ):
        """Ajouter une chaîne Telegram"""
        # S'assurer que username commence par @
        if not username.startswith("@"):
            username = f"@{username}"
        
        data = {
            "name": name,
            "channel_type": "telegram",
            "channel_id": username,
            "check_interval_minutes": interval,
            "enable_email_alerts": bool(keywords),
            "alert_keywords": keywords or [],
            "alert_emails": alert_emails or []
        }
        
        result = self._request("POST", "/channels/", json=data)
        print(f"✅ Chaîne Telegram '{name}' ajoutée avec succès!")
        print(f"   ID: {result['id']}")
        print(f"   Username: {username}")
        print(f"   Intervalle de collecte: {interval} minutes")
        if keywords:
            print(f"   Mots-clés d'alerte: {', '.join(keywords)}")
    
    def add_whatsapp_group(
        self,
        name: str,
        group_id: str,
        interval: int = 10,
        keywords: Optional[List[str]] = None,
        alert_emails: Optional[List[str]] = None
    ):
        """Ajouter un groupe WhatsApp"""
        data = {
            "name": name,
            "channel_type": "whatsapp",
            "channel_id": group_id,
            "check_interval_minutes": interval,
            "enable_email_alerts": bool(keywords),
            "alert_keywords": keywords or [],
            "alert_emails": alert_emails or []
        }
        
        result = self._request("POST", "/channels/", json=data)
        print(f"✅ Groupe WhatsApp '{name}' ajouté avec succès!")
        print(f"   ID: {result['id']}")
        print(f"   Group ID: {group_id}")
        print(f"   Intervalle de collecte: {interval} minutes")
        if keywords:
            print(f"   Mots-clés d'alerte: {', '.join(keywords)}")
    
    def remove_channel(self, channel_id: int):
        """Supprimer un channel"""
        # Demander confirmation
        response = input(f"⚠️  Êtes-vous sûr de vouloir supprimer le channel #{channel_id}? (oui/non): ")
        if response.lower() not in ["oui", "yes", "y", "o"]:
            print("❌ Annulé")
            return
        
        self._request("DELETE", f"/channels/{channel_id}")
        print(f"✅ Channel #{channel_id} supprimé avec succès!")
    
    def collect_channel(self, channel_id: int):
        """Collecter un channel spécifique"""
        print(f"🔄 Collecte du channel #{channel_id} en cours...")
        result = self._request("POST", f"/channels/{channel_id}/collect")
        
        print(f"✅ Collecte terminée!")
        print(f"   Items collectés: {result.get('items_collected', 0)}")
        print(f"   Alertes déclenchées: {result.get('alerts_triggered', 0)}")
    
    def collect_all(self):
        """Collecter tous les channels actifs"""
        print("🔄 Collecte de tous les channels actifs en cours...")
        result = self._request("POST", "/channels/collect-all")
        
        print(f"✅ Collecte terminée!")
        print(f"   Channels collectés: {result.get('channels_collected', 0)}")
        print(f"   Items collectés: {result.get('total_items_collected', 0)}")
        print(f"   Alertes déclenchées: {result.get('total_alerts_triggered', 0)}")
    
    def get_stats(self, channel_id: int, days: int = 7):
        """Obtenir les statistiques d'un channel"""
        params = {"days": days}
        stats = self._request("GET", f"/channels/{channel_id}/stats", params=params)
        
        print(f"\n📊 Statistiques du channel #{channel_id} (derniers {days} jours)")
        print("=" * 60)
        print(f"Nom: {stats.get('name', 'N/A')}")
        print(f"Type: {stats.get('channel_type', 'N/A')}")
        print(f"Total items: {stats.get('total_items', 0)}")
        print(f"Alertes déclenchées: {stats.get('alerts_triggered', 0)}")
        
        sentiment = stats.get('sentiment_distribution', {})
        if sentiment:
            print(f"\n🎭 Distribution du sentiment:")
            print(f"   Positif: {sentiment.get('positive', 0)}")
            print(f"   Neutre: {sentiment.get('neutral', 0)}")
            print(f"   Négatif: {sentiment.get('negative', 0)}")
        
        if stats.get('last_check_at'):
            print(f"\n🕐 Dernière collecte: {stats['last_check_at'][:19]}")
        if stats.get('last_item_at'):
            print(f"📅 Dernier item: {stats['last_item_at'][:19]}")
    
    def find_youtube_channel(self, search_query: str):
        """Rechercher une chaîne YouTube"""
        print(f"🔍 Recherche de '{search_query}' sur YouTube...")
        params = {"search": search_query}
        results = self._request("GET", "/channels/discover/youtube", params=params)
        
        if not results:
            print("❌ Aucun résultat trouvé")
            return
        
        print(f"\n✅ {len(results)} résultat(s) trouvé(s):")
        for i, channel in enumerate(results, 1):
            print(f"\n{i}. {channel['title']}")
            print(f"   ID: {channel['channel_id']}")
            print(f"   Abonnés: {channel.get('subscriber_count', 'N/A')}")
            if channel.get('description'):
                desc = channel['description'][:100] + "..." if len(channel['description']) > 100 else channel['description']
                print(f"   Description: {desc}")
    
    def discover_rss(self, website_url: str):
        """Découvrir les flux RSS d'un site web"""
        print(f"🔍 Recherche de flux RSS sur {website_url}...")
        params = {"website_url": website_url}
        feeds = self._request("GET", "/channels/discover/rss", params=params)
        
        if not feeds:
            print("❌ Aucun flux RSS trouvé")
            return
        
        print(f"\n✅ {len(feeds)} flux trouvé(s):")
        for i, feed in enumerate(feeds, 1):
            print(f"\n{i}. {feed['title']}")
            print(f"   URL: {feed['url']}")
            if feed.get('description'):
                print(f"   Description: {feed['description']}")
    
    def get_popular_presets(self):
        """Afficher les channels populaires pré-configurés"""
        presets = self._request("GET", "/channels/presets/popular")
        
        print("\n📺 Channels populaires pré-configurés")
        print("=" * 80)
        
        for category, channels in presets.items():
            print(f"\n{category.upper()}:")
            for channel in channels:
                print(f"  • {channel['name']}")
                print(f"    Type: {channel['channel_type']}")
                print(f"    ID: {channel['channel_id']}")
                if channel.get('description'):
                    print(f"    Description: {channel['description']}")
                print()


def main():
    parser = argparse.ArgumentParser(
        description="Gestionnaire de channels Brand Monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  # Lister tous les channels
  python manage_channels.py list
  
  # Ajouter une chaîne YouTube
  python manage_channels.py add-youtube "France 24" UCQfwfsi5VrQ8yKZ-UWmAEFg --interval 60 --keywords Cameroun,urgent
  
  # Ajouter un flux RSS
  python manage_channels.py add-rss "Journal" https://example.com/feed --keywords politique,économie
  
  # Ajouter une chaîne Telegram
  python manage_channels.py add-telegram "France24" france24_fr --interval 15
  
  # Ajouter un groupe WhatsApp
  python manage_channels.py add-whatsapp "Groupe Info" 120363xxx@g.us --interval 10
  
  # Collecter tous les channels
  python manage_channels.py collect-all
  
  # Voir les stats d'un channel
  python manage_channels.py stats 1 --days 30
  
  # Rechercher une chaîne YouTube
  python manage_channels.py find-youtube "France 24"
  
  # Découvrir les flux RSS d'un site
  python manage_channels.py discover-rss https://www.france24.com
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commande à exécuter")
    
    # Commande: list
    parser_list = subparsers.add_parser("list", help="Lister les channels")
    parser_list.add_argument("--active-only", action="store_true", help="Afficher seulement les channels actifs")
    
    # Commande: add-youtube
    parser_youtube = subparsers.add_parser("add-youtube", help="Ajouter une chaîne YouTube")
    parser_youtube.add_argument("name", help="Nom du channel")
    parser_youtube.add_argument("channel_id", help="ID de la chaîne YouTube")
    parser_youtube.add_argument("--interval", type=int, default=60, help="Intervalle de collecte en minutes (défaut: 60)")
    parser_youtube.add_argument("--keywords", help="Mots-clés d'alerte séparés par des virgules")
    parser_youtube.add_argument("--emails", help="Emails d'alerte séparés par des virgules")
    
    # Commande: add-rss
    parser_rss = subparsers.add_parser("add-rss", help="Ajouter un flux RSS")
    parser_rss.add_argument("name", help="Nom du channel")
    parser_rss.add_argument("feed_url", help="URL du flux RSS")
    parser_rss.add_argument("--interval", type=int, default=30, help="Intervalle de collecte en minutes (défaut: 30)")
    parser_rss.add_argument("--keywords", help="Mots-clés d'alerte séparés par des virgules")
    parser_rss.add_argument("--emails", help="Emails d'alerte séparés par des virgules")
    
    # Commande: add-telegram
    parser_telegram = subparsers.add_parser("add-telegram", help="Ajouter une chaîne Telegram")
    parser_telegram.add_argument("name", help="Nom du channel")
    parser_telegram.add_argument("username", help="Username Telegram (avec ou sans @)")
    parser_telegram.add_argument("--interval", type=int, default=15, help="Intervalle de collecte en minutes (défaut: 15)")
    parser_telegram.add_argument("--keywords", help="Mots-clés d'alerte séparés par des virgules")
    parser_telegram.add_argument("--emails", help="Emails d'alerte séparés par des virgules")
    
    # Commande: add-whatsapp
    parser_whatsapp = subparsers.add_parser("add-whatsapp", help="Ajouter un groupe WhatsApp")
    parser_whatsapp.add_argument("name", help="Nom du channel")
    parser_whatsapp.add_argument("group_id", help="ID du groupe WhatsApp (format: xxxxx@g.us)")
    parser_whatsapp.add_argument("--interval", type=int, default=10, help="Intervalle de collecte en minutes (défaut: 10)")
    parser_whatsapp.add_argument("--keywords", help="Mots-clés d'alerte séparés par des virgules")
    parser_whatsapp.add_argument("--emails", help="Emails d'alerte séparés par des virgules")
    
    # Commande: remove
    parser_remove = subparsers.add_parser("remove", help="Supprimer un channel")
    parser_remove.add_argument("channel_id", type=int, help="ID du channel à supprimer")
    
    # Commande: collect
    parser_collect = subparsers.add_parser("collect", help="Collecter un channel")
    parser_collect.add_argument("channel_id", type=int, help="ID du channel à collecter")
    
    # Commande: collect-all
    subparsers.add_parser("collect-all", help="Collecter tous les channels actifs")
    
    # Commande: stats
    parser_stats = subparsers.add_parser("stats", help="Voir les statistiques d'un channel")
    parser_stats.add_argument("channel_id", type=int, help="ID du channel")
    parser_stats.add_argument("--days", type=int, default=7, help="Nombre de jours (défaut: 7)")
    
    # Commande: find-youtube
    parser_find = subparsers.add_parser("find-youtube", help="Rechercher une chaîne YouTube")
    parser_find.add_argument("query", help="Terme de recherche")
    
    # Commande: discover-rss
    parser_discover = subparsers.add_parser("discover-rss", help="Découvrir les flux RSS d'un site")
    parser_discover.add_argument("url", help="URL du site web")
    
    # Commande: presets
    subparsers.add_parser("presets", help="Afficher les channels populaires pré-configurés")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    manager = ChannelManager()
    
    try:
        if args.command == "list":
            manager.list_channels(args.active_only)
        
        elif args.command == "add-youtube":
            keywords = args.keywords.split(",") if args.keywords else None
            emails = args.emails.split(",") if args.emails else None
            manager.add_youtube_channel(args.name, args.channel_id, args.interval, keywords, emails)
        
        elif args.command == "add-rss":
            keywords = args.keywords.split(",") if args.keywords else None
            emails = args.emails.split(",") if args.emails else None
            manager.add_rss_feed(args.name, args.feed_url, args.interval, keywords, emails)
        
        elif args.command == "add-telegram":
            keywords = args.keywords.split(",") if args.keywords else None
            emails = args.emails.split(",") if args.emails else None
            manager.add_telegram_channel(args.name, args.username, args.interval, keywords, emails)
        
        elif args.command == "add-whatsapp":
            keywords = args.keywords.split(",") if args.keywords else None
            emails = args.emails.split(",") if args.emails else None
            manager.add_whatsapp_group(args.name, args.group_id, args.interval, keywords, emails)
        
        elif args.command == "remove":
            manager.remove_channel(args.channel_id)
        
        elif args.command == "collect":
            manager.collect_channel(args.channel_id)
        
        elif args.command == "collect-all":
            manager.collect_all()
        
        elif args.command == "stats":
            manager.get_stats(args.channel_id, args.days)
        
        elif args.command == "find-youtube":
            manager.find_youtube_channel(args.query)
        
        elif args.command == "discover-rss":
            manager.discover_rss(args.url)
        
        elif args.command == "presets":
            manager.get_popular_presets()
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Annulé par l'utilisateur")
        sys.exit(1)


if __name__ == "__main__":
    main()