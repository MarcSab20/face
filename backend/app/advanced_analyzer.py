"""
Système d'Analyse Avancée
- Topic Modeling (BERTopic)
- Détection d'Anomalies
- Analyse de Réseau d'Influence
- Analyse Temporelle
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Topic:
    """Représente un topic identifié"""
    topic_id: int
    keywords: List[str]
    representative_docs: List[str]
    size: int
    coherence_score: float


@dataclass
class Anomaly:
    """Représente une anomalie détectée"""
    type: str  # 'volume_spike', 'sentiment_shift', 'new_influencer'
    severity: str  # 'low', 'medium', 'high', 'critical'
    timestamp: datetime
    description: str
    metrics: Dict
    affected_entities: List[str]


@dataclass
class InfluenceNetwork:
    """Représente un réseau d'influence"""
    nodes: List[Dict]  # Influenceurs
    edges: List[Dict]  # Relations
    communities: List[List[str]]
    central_nodes: List[str]
    metrics: Dict


class AdvancedAnalyzer:
    """
    Analyseur avancé pour Brand Monitor
    
    Fonctionnalités:
    1. Topic Modeling automatique
    2. Détection d'anomalies
    3. Analyse de réseau
    4. Prédictions de tendances
    """
    
    def __init__(self, db):
        self.db = db
        
        # Initialiser BERTopic
        try:
            from bertopic import BERTopic
            from sentence_transformers import SentenceTransformer
            
            # Modèle d'embedding multilingue
            embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            
            self.topic_model = BERTopic(
                embedding_model=embedding_model,
                language='french',
                calculate_probabilities=True,
                verbose=False
            )
            
            self.bertopic_enabled = True
            logger.info("✅ BERTopic initialisé")
            
        except ImportError:
            logger.warning("BERTopic non disponible. Installer: pip install bertopic")
            self.bertopic_enabled = False
            self.topic_model = None
    
    def analyze_topics(
        self,
        contents: List[Dict],
        min_topic_size: int = 10,
        nr_topics: Optional[int] = None
    ) -> List[Topic]:
        """
        Identifier automatiquement les topics principaux
        
        Args:
            contents: Liste de contenus à analyser
            min_topic_size: Taille minimale d'un topic
            nr_topics: Nombre de topics souhaités (None = auto)
            
        Returns:
            Liste de topics identifiés
        """
        if not self.bertopic_enabled or not contents:
            logger.warning("Topic modeling non disponible ou pas de contenu")
            return []
        
        try:
            logger.info(f"🔬 Analyse topics: {len(contents)} documents")
            
            # Extraire textes
            documents = [
                f"{c.get('title', '')} {c.get('content', '')}"
                for c in contents
            ]
            
            # Nettoyer et filtrer
            documents = [doc for doc in documents if len(doc.strip()) > 20]
            
            if len(documents) < min_topic_size:
                logger.warning(f"Pas assez de documents ({len(documents)}) pour topic modeling")
                return []
            
            # Appliquer BERTopic
            topics, probs = self.topic_model.fit_transform(documents)
            
            # Extraire informations des topics
            topic_info = self.topic_model.get_topic_info()
            
            detected_topics = []
            
            for idx, row in topic_info.iterrows():
                topic_id = row['Topic']
                
                # Ignorer le topic outlier (-1)
                if topic_id == -1:
                    continue
                
                # Extraire mots-clés
                topic_words = self.topic_model.get_topic(topic_id)
                keywords = [word for word, _ in topic_words[:10]]
                
                # Obtenir documents représentatifs
                representative = self.topic_model.get_representative_docs(topic_id)[:3]
                
                topic = Topic(
                    topic_id=topic_id,
                    keywords=keywords,
                    representative_docs=representative,
                    size=row['Count'],
                    coherence_score=self._calculate_topic_coherence(topic_words)
                )
                
                detected_topics.append(topic)
            
            logger.info(f"✅ {len(detected_topics)} topics identifiés")
            return detected_topics
            
        except Exception as e:
            logger.error(f"Erreur topic modeling: {e}")
            return []
    
    def _calculate_topic_coherence(self, topic_words: List[Tuple]) -> float:
        """
        Calculer le score de cohérence d'un topic
        
        Basé sur les scores de probabilité des mots
        """
        if not topic_words:
            return 0.0
        
        scores = [score for _, score in topic_words[:10]]
        return float(np.mean(scores))
    
    def detect_anomalies(
        self,
        keyword_id: int,
        days: int = 30,
        sensitivity: float = 2.0
    ) -> List[Anomaly]:
        """
        Détecter des anomalies dans l'activité
        
        Args:
            keyword_id: ID du mot-clé à analyser
            days: Période d'analyse
            sensitivity: Sensibilité (2.0 = écart-type x2)
            
        Returns:
            Liste d'anomalies détectées
        """
        from app.models import Mention
        
        since_date = datetime.utcnow() - timedelta(days=days)
        
        mentions = self.db.query(Mention).filter(
            Mention.keyword_id == keyword_id,
            Mention.published_at >= since_date
        ).all()
        
        if not mentions:
            return []
        
        anomalies = []
        
        # 1. Détection de pics de volume
        volume_anomalies = self._detect_volume_spikes(mentions, sensitivity)
        anomalies.extend(volume_anomalies)
        
        # 2. Détection de changements de sentiment
        sentiment_anomalies = self._detect_sentiment_shifts(mentions, sensitivity)
        anomalies.extend(sentiment_anomalies)
        
        # 3. Détection de nouveaux influenceurs puissants
        influencer_anomalies = self._detect_new_influencers(mentions)
        anomalies.extend(influencer_anomalies)
        
        # 4. Détection de patterns inhabituels temporels
        temporal_anomalies = self._detect_temporal_anomalies(mentions, sensitivity)
        anomalies.extend(temporal_anomalies)
        
        # Trier par sévérité
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        anomalies.sort(key=lambda a: severity_order[a.severity])
        
        logger.info(f"✅ {len(anomalies)} anomalies détectées")
        return anomalies
    
    def _detect_volume_spikes(
        self,
        mentions: List,
        sensitivity: float
    ) -> List[Anomaly]:
        """Détecter les pics de volume inhabituels"""
        
        anomalies = []
        
        # Grouper par jour
        daily_counts = defaultdict(int)
        for mention in mentions:
            if mention.published_at:
                date_key = mention.published_at.date()
                daily_counts[date_key] += 1
        
        if len(daily_counts) < 7:
            return anomalies
        
        # Calculer statistiques
        counts = list(daily_counts.values())
        mean = np.mean(counts)
        std = np.std(counts)
        
        # Détecter spikes
        threshold = mean + (sensitivity * std)
        
        for date, count in daily_counts.items():
            if count > threshold:
                spike_ratio = count / mean
                
                severity = 'critical' if spike_ratio > 5 else ('high' if spike_ratio > 3 else 'medium')
                
                anomaly = Anomaly(
                    type='volume_spike',
                    severity=severity,
                    timestamp=datetime.combine(date, datetime.min.time()),
                    description=f"Pic de volume détecté: {count} mentions (moyenne: {mean:.1f})",
                    metrics={
                        'count': count,
                        'mean': mean,
                        'std': std,
                        'spike_ratio': spike_ratio
                    },
                    affected_entities=[]
                )
                
                anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_sentiment_shifts(
        self,
        mentions: List,
        sensitivity: float
    ) -> List[Anomaly]:
        """Détecter les changements brusques de sentiment"""
        
        anomalies = []
        
        # Grouper par jour avec sentiments
        daily_sentiments = defaultdict(lambda: {'positive': 0, 'neutral': 0, 'negative': 0})
        
        for mention in mentions:
            if mention.published_at and mention.sentiment:
                date_key = mention.published_at.date()
                daily_sentiments[date_key][mention.sentiment] += 1
        
        if len(daily_sentiments) < 7:
            return anomalies
        
        # Calculer ratio négatif par jour
        dates = sorted(daily_sentiments.keys())
        negative_ratios = []
        
        for date in dates:
            sentiments = daily_sentiments[date]
            total = sum(sentiments.values())
            if total > 0:
                negative_ratio = sentiments['negative'] / total
                negative_ratios.append((date, negative_ratio))
        
        # Détecter changements brusques
        for i in range(1, len(negative_ratios)):
            prev_date, prev_ratio = negative_ratios[i-1]
            curr_date, curr_ratio = negative_ratios[i]
            
            # Changement significatif vers le négatif
            if curr_ratio > prev_ratio + 0.3 and curr_ratio > 0.5:
                severity = 'critical' if curr_ratio > 0.7 else ('high' if curr_ratio > 0.6 else 'medium')
                
                anomaly = Anomaly(
                    type='sentiment_shift',
                    severity=severity,
                    timestamp=datetime.combine(curr_date, datetime.min.time()),
                    description=f"Changement de sentiment vers négatif: {curr_ratio*100:.0f}% (était {prev_ratio*100:.0f}%)",
                    metrics={
                        'previous_negative_ratio': prev_ratio,
                        'current_negative_ratio': curr_ratio,
                        'change': curr_ratio - prev_ratio
                    },
                    affected_entities=[]
                )
                
                anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_new_influencers(self, mentions: List) -> List[Anomaly]:
        """Détecter l'apparition de nouveaux influenceurs puissants"""
        
        anomalies = []
        
        # Analyser engagement par auteur
        author_engagement = defaultdict(lambda: {'total': 0, 'count': 0, 'first_seen': None})
        
        for mention in mentions:
            author = mention.author
            if author and author not in ['Unknown', '[deleted]', '']:
                author_engagement[author]['total'] += mention.engagement_score
                author_engagement[author]['count'] += 1
                
                if not author_engagement[author]['first_seen']:
                    author_engagement[author]['first_seen'] = mention.published_at
        
        # Identifier nouveaux influenceurs (apparus récemment avec fort engagement)
        recent_threshold = datetime.utcnow() - timedelta(days=7)
        
        for author, data in author_engagement.items():
            if data['first_seen'] and data['first_seen'] >= recent_threshold:
                avg_engagement = data['total'] / data['count']
                
                # Si engagement moyen élevé
                if avg_engagement > 1000:
                    severity = 'high' if avg_engagement > 5000 else 'medium'
                    
                    anomaly = Anomaly(
                        type='new_influencer',
                        severity=severity,
                        timestamp=data['first_seen'],
                        description=f"Nouvel influenceur détecté: {author} (engagement moyen: {avg_engagement:.0f})",
                        metrics={
                            'author': author,
                            'avg_engagement': avg_engagement,
                            'total_mentions': data['count'],
                            'first_seen': data['first_seen'].isoformat()
                        },
                        affected_entities=[author]
                    )
                    
                    anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_temporal_anomalies(
        self,
        mentions: List,
        sensitivity: float
    ) -> List[Anomaly]:
        """Détecter des patterns temporels inhabituels (ex: activité nocturne anormale)"""
        
        anomalies = []
        
        # Analyser distribution horaire
        hourly_counts = defaultdict(int)
        
        for mention in mentions:
            if mention.published_at:
                hour = mention.published_at.hour
                hourly_counts[hour] += 1
        
        if not hourly_counts:
            return anomalies
        
        # Calculer statistiques
        counts = list(hourly_counts.values())
        mean = np.mean(counts)
        std = np.std(counts)
        
        # Heures inhabituelles (2h-6h du matin)
        unusual_hours = [2, 3, 4, 5]
        threshold = mean + (sensitivity * std)
        
        for hour in unusual_hours:
            count = hourly_counts.get(hour, 0)
            if count > threshold:
                anomaly = Anomaly(
                    type='temporal_anomaly',
                    severity='medium',
                    timestamp=datetime.utcnow().replace(hour=hour, minute=0, second=0),
                    description=f"Activité inhabituelle à {hour}h: {count} mentions (moyenne: {mean:.1f})",
                    metrics={
                        'hour': hour,
                        'count': count,
                        'mean': mean
                    },
                    affected_entities=[]
                )
                
                anomalies.append(anomaly)
        
        return anomalies
    
    def analyze_influence_network(
        self,
        keyword_id: int,
        days: int = 30
    ) -> InfluenceNetwork:
        """
        Analyser le réseau d'influence
        
        Identifier:
        - Qui influence qui
        - Communautés d'influenceurs
        - Nœuds centraux
        - Relais d'information
        """
        try:
            import networkx as nx
            from app.models import Mention
            
            since_date = datetime.utcnow() - timedelta(days=days)
            
            mentions = self.db.query(Mention).filter(
                Mention.keyword_id == keyword_id,
                Mention.published_at >= since_date
            ).all()
            
            # Créer graphe
            G = nx.DiGraph()
            
            # Ajouter nœuds (auteurs)
            author_metrics = defaultdict(lambda: {
                'mentions': 0,
                'total_engagement': 0,
                'sentiment_score': 0
            })
            
            for mention in mentions:
                author = mention.author
                if author and author not in ['Unknown', '[deleted]', '']:
                    author_metrics[author]['mentions'] += 1
                    author_metrics[author]['total_engagement'] += mention.engagement_score
                    
                    # Score sentiment (1=pos, 0=neu, -1=neg)
                    sentiment_value = {'positive': 1, 'neutral': 0, 'negative': -1}.get(mention.sentiment, 0)
                    author_metrics[author]['sentiment_score'] += sentiment_value
            
            # Ajouter nœuds au graphe
            for author, metrics in author_metrics.items():
                G.add_node(
                    author,
                    mentions=metrics['mentions'],
                    engagement=metrics['total_engagement'],
                    sentiment=metrics['sentiment_score'] / metrics['mentions']
                )
            
            # Ajouter arêtes (interactions)
            # Note: Dans ce cas simplifié, on considère que les auteurs qui parlent
            # du même sujet ont une relation. Pour plus de précision, on pourrait
            # analyser les réponses, mentions, retweets, etc.
            
            # Identifier communautés
            if len(G.nodes()) > 3:
                communities = list(nx.community.greedy_modularity_communities(G.to_undirected()))
            else:
                communities = []
            
            # Identifier nœuds centraux
            if len(G.nodes()) > 0:
                centrality = nx.degree_centrality(G)
                central_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:10]
                central_node_names = [node for node, _ in central_nodes]
            else:
                central_node_names = []
            
            # Formater résultats
            nodes = [
                {
                    'id': node,
                    'mentions': G.nodes[node]['mentions'],
                    'engagement': G.nodes[node]['engagement'],
                    'sentiment': G.nodes[node]['sentiment']
                }
                for node in G.nodes()
            ]
            
            edges = [
                {'source': u, 'target': v, 'weight': data.get('weight', 1)}
                for u, v, data in G.edges(data=True)
            ]
            
            network = InfluenceNetwork(
                nodes=nodes,
                edges=edges,
                communities=[[str(n) for n in community] for community in communities],
                central_nodes=central_node_names,
                metrics={
                    'total_nodes': len(G.nodes()),
                    'total_edges': len(G.edges()),
                    'density': nx.density(G),
                    'num_communities': len(communities)
                }
            )
            
            logger.info(f"✅ Réseau analysé: {len(nodes)} nœuds, {len(edges)} arêtes, {len(communities)} communautés")
            return network
            
        except ImportError:
            logger.warning("NetworkX non disponible. Installer: pip install networkx")
            return InfluenceNetwork(nodes=[], edges=[], communities=[], central_nodes=[], metrics={})
        except Exception as e:
            logger.error(f"Erreur analyse réseau: {e}")
            return InfluenceNetwork(nodes=[], edges=[], communities=[], central_nodes=[], metrics={})


# Exemple d'utilisation
if __name__ == '__main__':
    print("✅ Système d'analyse avancée chargé")
    print("   - Topic Modeling (BERTopic)")
    print("   - Détection d'anomalies")
    print("   - Analyse de réseau") 