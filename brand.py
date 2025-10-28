"""
Exemples d'utilisation de l'API Brand Monitor en Python
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
API_URL = "http://localhost:8000"

class BrandMonitorClient:
    """Client Python pour l'API Brand Monitor"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def add_keyword(self, keyword: str, sources: list = None):
        """Ajouter un mot-clé à surveiller"""
        if sources is None:
            sources = ["rss", "reddit", "youtube"]
        
        response = requests.post(
            f"{self.base_url}/api/keywords",
            json={"keyword": keyword, "sources": sources}
        )
        response.raise_for_status()
        return response.json()
    
    def get_keywords(self, active_only: bool = True):
        """Obtenir la liste des mots-clés"""
        params = {"active_only": active_only}
        response = requests.get(f"{self.base_url}/api/keywords", params=params)
        response.raise_for_status()
        return response.json()
    
    def delete_keyword(self, keyword_id: int):
        """Supprimer un mot-clé"""
        response = requests.delete(f"{self.base_url}/api/keywords/{keyword_id}")
        response.raise_for_status()
        return response.json()
    
    def collect(self, keyword_id: int = None, sources: list = None):
        """Lancer une collecte"""
        data = {}
        if keyword_id:
            data["keyword_id"] = keyword_id
        if sources:
            data["sources"] = sources
        
        response = requests.post(f"{self.base_url}/api/collect", json=data)
        response.raise_for_status()
        return response.json()
    
    def get_mentions(self, keyword: str = None, source: str = None, limit: int = 100):
        """Obtenir les mentions"""
        params = {"limit": limit}
        if keyword:
            params["keyword"] = keyword
        if source:
            params["source"] = source
        
        response = requests.get(f"{self.base_url}/api/mentions", params=params)
        response.raise_for_status()
        return response.json()
    
    def get_stats(self):
        """Obtenir les statistiques"""
        response = requests.get(f"{self.base_url}/api/stats")
        response.raise_for_status()
        return response.json()


# ============ Exemples d'utilisation ============

def exemple_1_ajouter_mots_cles():
    """Exemple 1: Ajouter plusieurs mots-clés"""
    print("Exemple 1: Ajout de mots-clés\n")
    
    client = BrandMonitorClient()
    
    mots_cles = [
        ("Apple", ["reddit", "youtube", "rss"]),
        ("Tesla", ["reddit", "youtube"]),
        ("Bitcoin", ["rss", "reddit", "google_search"]),
    ]
    
    for keyword, sources in mots_cles:
        try:
            result = client.add_keyword(keyword, sources)
            print(f"✅ {keyword} ajouté (ID: {result['id']})")
        except Exception as e:
            print(f"❌ Erreur pour {keyword}: {e}")


def exemple_2_collecter_et_analyser():
    """Exemple 2: Collecter des données et analyser"""
    print("\nExemple 2: Collecte et analyse\n")
    
    client = BrandMonitorClient()
    
    # Lancer la collecte
    print("Lancement de la collecte...")
    client.collect()
    print("✅ Collecte lancée\n")
    
    # Attendre un peu
    import time
    print("Attente de 10 secondes...")
    time.sleep(10)
    
    # Récupérer les statistiques
    stats = client.get_stats()
    print(f"📊 Statistiques:")
    print(f"   - Mots-clés: {stats['total_keywords']}")
    print(f"   - Mentions totales: {stats['total_mentions']}")
    print(f"   - Mentions aujourd'hui: {stats['mentions_today']}")
    print(f"\n📈 Par source:")
    for source, count in stats['mentions_by_source'].items():
        print(f"   - {source}: {count}")


def exemple_3_analyser_mentions():
    """Exemple 3: Analyser les mentions d'une marque"""
    print("\nExemple 3: Analyse des mentions\n")
    
    client = BrandMonitorClient()
    
    keyword = "Apple"
    mentions = client.get_mentions(keyword=keyword, limit=50)
    
    print(f"📰 Analyse pour '{keyword}' ({len(mentions)} mentions):\n")
    
    # Statistiques par source
    sources_count = {}
    total_engagement = 0
    
    for mention in mentions:
        source = mention['source']
        sources_count[source] = sources_count.get(source, 0) + 1
        total_engagement += mention.get('engagement_score', 0)
    
    print("Par source:")
    for source, count in sorted(sources_count.items(), key=lambda x: x[1], reverse=True):
        print(f"   - {source}: {count} mentions")
    
    print(f"\nEngagement total: {total_engagement:,.0f}")
    print(f"Engagement moyen: {total_engagement/len(mentions):,.0f}")
    
    # Top 5 mentions par engagement
    print("\n🔥 Top 5 mentions par engagement:")
    top_mentions = sorted(mentions, key=lambda x: x.get('engagement_score', 0), reverse=True)[:5]
    
    for i, mention in enumerate(top_mentions, 1):
        print(f"\n{i}. {mention['title'][:60]}...")
        print(f"   Source: {mention['source']}")
        print(f"   Score: {mention['engagement_score']:,.0f}")
        print(f"   URL: {mention['source_url'][:50]}...")


def exemple_4_monitoring_continue():
    """Exemple 4: Monitoring continu avec alertes"""
    print("\nExemple 4: Monitoring continu\n")
    
    client = BrandMonitorClient()
    
    # Seuil d'alerte
    SEUIL_ENGAGEMENT = 1000
    
    print(f"⚠️  Monitoring actif (seuil d'alerte: {SEUIL_ENGAGEMENT})\n")
    
    while True:
        try:
            # Collecter
            client.collect()
            
            # Récupérer les mentions récentes
            mentions = client.get_mentions(limit=20)
            
            # Vérifier les mentions importantes
            for mention in mentions:
                if mention['engagement_score'] >= SEUIL_ENGAGEMENT:
                    print(f"🚨 ALERTE - Mention importante détectée!")
                    print(f"   Titre: {mention['title']}")
                    print(f"   Source: {mention['source']}")
                    print(f"   Score: {mention['engagement_score']:,.0f}")
                    print(f"   URL: {mention['source_url']}")
                    print()
            
            # Attendre 1 heure avant la prochaine collecte
            import time
            print(f"Prochaine collecte dans 1 heure... (Ctrl+C pour arrêter)")
            time.sleep(3600)
            
        except KeyboardInterrupt:
            print("\n\n✋ Monitoring arrêté")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")
            import time
            time.sleep(60)


def exemple_5_rapport_quotidien():
    """Exemple 5: Générer un rapport quotidien"""
    print("\nExemple 5: Rapport quotidien\n")
    
    client = BrandMonitorClient()
    
    # Date du rapport
    date = datetime.now().strftime("%Y-%m-%d")
    
    print(f"📊 RAPPORT QUOTIDIEN - {date}")
    print("=" * 60)
    
    # Statistiques globales
    stats = client.get_stats()
    print(f"\n1. VUE D'ENSEMBLE")
    print(f"   - Mots-clés surveillés: {stats['total_keywords']}")
    print(f"   - Mentions totales: {stats['total_mentions']}")
    print(f"   - Mentions aujourd'hui: {stats['mentions_today']}")
    
    # Par source
    print(f"\n2. RÉPARTITION PAR SOURCE")
    for source, count in stats['mentions_by_source'].items():
        percentage = (count / stats['total_mentions'] * 100) if stats['total_mentions'] > 0 else 0
        print(f"   - {source}: {count} ({percentage:.1f}%)")
    
    # Top keywords
    print(f"\n3. TOP MOTS-CLÉS")
    for i, kw in enumerate(stats['top_keywords'][:5], 1):
        print(f"   {i}. {kw['keyword']}: {kw['mentions']} mentions")
    
    # Mentions récentes importantes
    print(f"\n4. MENTIONS IMPORTANTES (Score > 500)")
    mentions = client.get_mentions(limit=100)
    
    important = [m for m in mentions if m['engagement_score'] > 500]
    important.sort(key=lambda x: x['engagement_score'], reverse=True)
    
    for i, mention in enumerate(important[:10], 1):
        print(f"\n   {i}. {mention['title'][:70]}")
        print(f"      Source: {mention['source']} | Score: {mention['engagement_score']:,.0f}")
        print(f"      {mention['source_url'][:60]}...")
    
    print("\n" + "=" * 60)
    print("Fin du rapport\n")


def exemple_6_export_csv():
    """Exemple 6: Exporter les données en CSV"""
    print("\nExemple 6: Export CSV\n")
    
    import csv
    
    client = BrandMonitorClient()
    
    # Récupérer toutes les mentions
    mentions = client.get_mentions(limit=1000)
    
    # Nom du fichier
    filename = f"mentions_{datetime.now().strftime('%Y%m%d')}.csv"
    
    # Écrire le CSV
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['date', 'source', 'keyword', 'title', 'author', 'engagement', 'url']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for mention in mentions:
            writer.writerow({
                'date': mention.get('published_at', ''),
                'source': mention['source'],
                'keyword': '',  # À obtenir via l'ID
                'title': mention['title'],
                'author': mention['author'],
                'engagement': mention['engagement_score'],
                'url': mention['source_url']
            })
    
    print(f"✅ Export réalisé: {filename}")
    print(f"   {len(mentions)} mentions exportées")


# ============ Menu principal ============

def main():
    """Menu principal"""
    print("=" * 60)
    print("EXEMPLES D'UTILISATION - BRAND MONITOR")
    print("=" * 60)
    print()
    print("Choisissez un exemple:")
    print("1. Ajouter des mots-clés")
    print("2. Collecter et analyser")
    print("3. Analyser les mentions d'une marque")
    print("4. Monitoring continu (Ctrl+C pour arrêter)")
    print("5. Rapport quotidien")
    print("6. Export CSV")
    print("0. Quitter")
    print()
    
    choix = input("Votre choix: ")
    
    exemples = {
        "1": exemple_1_ajouter_mots_cles,
        "2": exemple_2_collecter_et_analyser,
        "3": exemple_3_analyser_mentions,
        "4": exemple_4_monitoring_continue,
        "5": exemple_5_rapport_quotidien,
        "6": exemple_6_export_csv,
    }
    
    if choix in exemples:
        exemples[choix]()
    elif choix == "0":
        print("Au revoir!")
    else:
        print("Choix invalide")


if __name__ == "__main__":
    main()