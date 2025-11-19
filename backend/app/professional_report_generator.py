"""
Générateur de Rapports Professionnel v2.0
Intègre tous les composants améliorés:
- Collecteurs avec commentaires
- Résumé hiérarchique
- IA externe pour synthèse
- Gestion influenceurs avancée
"""

import logging
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Imports des nouveaux composants
from youtube_collector_enhanced import YouTubeCollectorEnhanced
from reddit_collector_enhanced import RedditCollectorEnhanced
from hierarchical_summarizer import HierarchicalSummarizer
from external_ai_service import ExternalAIService
from influencer_manager import AdvancedInfluencerAnalyzer, get_influencer_report_prompt

logger = logging.getLogger(__name__)


class ProfessionalReportGenerator:
    """
    Générateur de rapports professionnel
    
    Fonctionnalités:
    - Collecte multi-sources avec commentaires
    - Résumé hiérarchique intelligent
    - Synthèse IA externe de qualité
    - Rapports d'influenceurs détaillés
    - Métriques avancées
    """
    
    def __init__(
        self,
        db: Session,
        llm_service,  # Service LLM local (Ollama)
        youtube_api_key: str,
        reddit_credentials: Dict,
        gemini_api_key: Optional[str] = None,
        groq_api_key: Optional[str] = None
    ):
        self.db = db
        
        # Collecteurs
        self.youtube_collector = YouTubeCollectorEnhanced(youtube_api_key)
        self.reddit_collector = RedditCollectorEnhanced(**reddit_credentials)
        
        # Analyse et résumé
        self.hierarchical_summarizer = HierarchicalSummarizer(
            llm_service=llm_service,
            batch_size=20,
            max_content_length=500
        )
        
        # IA externe (pour synthèse finale)
        self.external_ai = ExternalAIService(gemini_api_key, groq_api_key)
        
        # Gestion influenceurs
        self.influencer_analyzer = AdvancedInfluencerAnalyzer(db)
        
        logger.info("✅ ProfessionalReportGenerator initialisé")
    
    async def generate_comprehensive_report(
        self,
        keyword_ids: List[int],
        days: int = 30,
        include_web_analysis: bool = True,
        include_influencer_profiles: bool = True
    ) -> Dict:
        """
        Générer un rapport complet professionnel
        
        Args:
            keyword_ids: Liste des IDs de keywords à surveiller
            days: Période d'analyse en jours
            include_web_analysis: Inclure analyse web approfondie
            include_influencer_profiles: Inclure profils détaillés influenceurs
            
        Returns:
            Rapport complet avec toutes les sections
        """
        start_time = datetime.utcnow()
        
        logger.info(f"📊 Génération rapport complet: {len(keyword_ids)} keywords, {days} jours")
        
        # ===== ÉTAPE 1: COLLECTE DES DONNÉES =====
        logger.info("🔍 ÉTAPE 1/6: Collecte des données...")
        
        keywords = self._get_keywords(keyword_ids)
        all_contents = []
        
        for keyword in keywords:
            logger.info(f"   Collecte pour '{keyword.keyword}'...")
            
            # Collecter depuis la DB (données déjà collectées)
            db_contents = self._get_stored_mentions(keyword.id, days)
            all_contents.extend(db_contents)
        
        logger.info(f"   ✅ {len(all_contents)} contenus collectés")
        
        if not all_contents:
            return self._empty_report(keywords, days)
        
        # ===== ÉTAPE 2: ANALYSE DES INFLUENCEURS =====
        logger.info("👑 ÉTAPE 2/6: Analyse des influenceurs...")
        
        influencers_by_category = self.influencer_analyzer.analyze_all_influencers(
            days=days,
            keyword_ids=keyword_ids
        )
        
        logger.info(f"   ✅ {sum(len(v) for v in influencers_by_category.values())} influenceurs analysés")
        
        # ===== ÉTAPE 3: RÉSUMÉ HIÉRARCHIQUE =====
        logger.info("📝 ÉTAPE 3/6: Résumé hiérarchique...")
        
        hierarchical_summary = await self.hierarchical_summarizer.summarize_large_dataset(
            contents=all_contents,
            context=f"Surveillance keywords: {', '.join([k.keyword for k in keywords])}"
        )
        
        logger.info(f"   ✅ Résumé généré ({hierarchical_summary.processing_time:.1f}s)")
        
        # ===== ÉTAPE 4: SYNTHÈSE FINALE IA EXTERNE =====
        logger.info("🤖 ÉTAPE 4/6: Synthèse finale (IA externe)...")
        
        async with self.external_ai as ai_service:
            executive_summary = await ai_service.generate_executive_summary(
                batch_summaries=hierarchical_summary.batch_summaries,
                sentiment_data=hierarchical_summary.sentiment_analysis,
                themes=hierarchical_summary.themes,
                context=f"Rapport stratégique - {', '.join([k.keyword for k in keywords])}",
                total_contents=len(all_contents)
            )
        
        logger.info("   ✅ Synthèse exécutive générée")
        
        # ===== ÉTAPE 5: RAPPORTS D'INFLUENCEURS (optionnel) =====
        influencer_reports = []
        
        if include_influencer_profiles:
            logger.info("📋 ÉTAPE 5/6: Génération rapports influenceurs...")
            
            # Top 5 influenceurs critiques (activistes + émergents à risque)
            critical_influencers = (
                influencers_by_category['activists'][:3] +
                [inf for inf in influencers_by_category['emerging'][:5] if inf.risk_level in ['high', 'critical']]
            )[:5]
            
            for influencer in critical_influencers:
                # Rapport détaillé
                detailed_report = self.influencer_analyzer.get_influencer_detailed_report(
                    author_name=influencer.name,
                    source=influencer.source,
                    days=days
                )
                
                # Génération synthèse IA pour l'influenceur
                prompt = get_influencer_report_prompt(detailed_report)
                
                async with self.external_ai as ai_service:
                    ai_analysis = await ai_service.generate_smart_synthesis(
                        prompt=prompt,
                        context_data={},
                        max_tokens=600,
                        temperature=0.2
                    )
                
                influencer_reports.append({
                    'influencer': influencer.name,
                    'category': influencer.category,
                    'risk_level': influencer.risk_level,
                    'detailed_report': detailed_report,
                    'ai_analysis': ai_analysis.get('text', 'Analyse non disponible')
                })
            
            logger.info(f"   ✅ {len(influencer_reports)} rapports d'influenceurs générés")
        else:
            logger.info("⏭️  ÉTAPE 5/6: Rapports influenceurs désactivés")
        
        # ===== ÉTAPE 6: COMPILATION DU RAPPORT FINAL =====
        logger.info("📄 ÉTAPE 6/6: Compilation rapport final...")
        
        # Métriques avancées
        metrics = self._calculate_advanced_metrics(all_contents, days)
        
        # Analyse temporelle
        timeline = self._build_timeline(all_contents, days)
        
        # Distribution par source
        source_distribution = self._analyze_source_distribution(all_contents)
        
        # Recommandations
        recommendations = self._generate_recommendations(
            sentiment_analysis=hierarchical_summary.sentiment_analysis,
            influencers=influencers_by_category,
            metrics=metrics
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        report = {
            'metadata': {
                'title': f"Rapport Stratégique - {', '.join([k.keyword for k in keywords])}",
                'keywords': [k.keyword for k in keywords],
                'period_days': days,
                'generated_at': datetime.utcnow().isoformat(),
                'processing_time_seconds': round(processing_time, 1),
                'classification': 'CONFIDENTIEL - DIFFUSION RESTREINTE'
            },
            'executive_summary': {
                'text': executive_summary,
                'key_insights': hierarchical_summary.key_insights,
                'priority_level': self._determine_priority_level(
                    hierarchical_summary.sentiment_analysis,
                    influencers_by_category
                )
            },
            'metrics': metrics,
            'sentiment_analysis': hierarchical_summary.sentiment_analysis,
            'themes': hierarchical_summary.themes,
            'timeline': timeline,
            'source_distribution': source_distribution,
            'influencers': {
                'activists': self._format_influencers_for_report(influencers_by_category['activists'][:10]),
                'emerging': self._format_influencers_for_report(influencers_by_category['emerging'][:10]),
                'official_media': self._format_influencers_for_report(influencers_by_category['official_media'][:5])
            },
            'influencer_detailed_reports': influencer_reports,
            'recommendations': recommendations,
            'data_quality': {
                'total_contents_analyzed': len(all_contents),
                'hierarchical_batches': len(hierarchical_summary.batch_summaries),
                'ai_service_used': 'gemini' if self.external_ai.gemini_api_key else ('groq' if self.external_ai.groq_api_key else 'local'),
                'comments_included': sum(1 for c in all_contents if 'comment' in c.get('source', '').lower())
            }
        }
        
        logger.info(f"✅ Rapport complet généré en {processing_time:.1f}s")
        
        return report
    
    async def generate_influencer_focused_report(
        self,
        influencer_name: str,
        days: int = 30
    ) -> Dict:
        """
        Générer un rapport focalisé sur un influenceur spécifique
        
        Utile pour le suivi approfondi d'activistes ou personnes d'intérêt
        """
        logger.info(f"👤 Génération rapport influenceur: {influencer_name}")
        
        # Rapport détaillé
        detailed_report = self.influencer_analyzer.get_influencer_detailed_report(
            author_name=influencer_name,
            days=days
        )
        
        if 'error' in detailed_report:
            return detailed_report
        
        # Évolution dans le temps
        evolution = self.influencer_analyzer.track_influencer_evolution(
            author_name=influencer_name,
            periods=4,
            period_days=7
        )
        
        # Générer analyse IA
        prompt = get_influencer_report_prompt(detailed_report)
        
        async with self.external_ai as ai_service:
            ai_analysis = await ai_service.generate_smart_synthesis(
                prompt=prompt,
                context_data={},
                max_tokens=800,
                temperature=0.2
            )
        
        # Collecter activité récente détaillée
        recent_activity = self._get_recent_activity_detailed(
            influencer_name,
            days=7
        )
        
        return {
            'influencer': {
                'name': influencer_name,
                'category': detailed_report['influencer']['category'],
                'category_label': detailed_report['influencer']['category_label']
            },
            'period_analyzed': days,
            'detailed_analysis': detailed_report,
            'evolution': evolution,
            'ai_synthesis': ai_analysis.get('text', 'Analyse IA non disponible'),
            'recent_activity_detailed': recent_activity,
            'recommendations': self._generate_influencer_recommendations(
                detailed_report,
                evolution
            ),
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _get_keywords(self, keyword_ids: List[int]) -> List:
        """Récupérer les objets Keyword depuis la DB"""
        from app.models import Keyword
        return self.db.query(Keyword).filter(Keyword.id.in_(keyword_ids)).all()
    
    def _get_stored_mentions(self, keyword_id: int, days: int) -> List[Dict]:
        """Récupérer les mentions stockées depuis la DB"""
        from app.models import Mention
        
        since_date = datetime.utcnow() - timedelta(days=days)
        
        mentions = self.db.query(Mention).filter(
            Mention.keyword_id == keyword_id,
            Mention.published_at >= since_date
        ).all()
        
        # Convertir en format dict
        return [
            {
                'title': m.title,
                'content': m.content,
                'author': m.author,
                'source': m.source,
                'sentiment': m.sentiment,
                'engagement_score': m.engagement_score,
                'published_at': m.published_at,
                'url': m.source_url
            }
            for m in mentions
        ]
    
    def _calculate_advanced_metrics(self, contents: List[Dict], days: int) -> Dict:
        """Calculer des métriques avancées"""
        
        if not contents:
            return {}
        
        total_engagement = sum(c.get('engagement_score', 0) for c in contents)
        avg_engagement = total_engagement / len(contents)
        
        # Contenus très engageants
        high_engagement_threshold = avg_engagement * 2
        viral_content = [c for c in contents if c.get('engagement_score', 0) > high_engagement_threshold]
        
        # Distribution par auteur
        from collections import Counter
        author_dist = Counter(c.get('author') for c in contents)
        top_authors = author_dist.most_common(5)
        
        return {
            'total_contents': len(contents),
            'total_engagement': total_engagement,
            'avg_engagement': round(avg_engagement, 2),
            'viral_content_count': len(viral_content),
            'viral_percentage': round((len(viral_content) / len(contents)) * 100, 1),
            'unique_authors': len(author_dist),
            'top_authors': [
                {'name': author, 'mentions': count}
                for author, count in top_authors
            ],
            'period_days': days,
            'contents_per_day': round(len(contents) / days, 1)
        }
    
    def _build_timeline(self, contents: List[Dict], days: int) -> List[Dict]:
        """Construire une timeline d'activité"""
        from collections import defaultdict
        
        daily_data = defaultdict(lambda: {'count': 0, 'engagement': 0})
        
        for content in contents:
            pub_date = content.get('published_at')
            if pub_date:
                date_key = pub_date.strftime('%Y-%m-%d')
                daily_data[date_key]['count'] += 1
                daily_data[date_key]['engagement'] += content.get('engagement_score', 0)
        
        timeline = [
            {
                'date': date,
                'mentions': data['count'],
                'engagement': data['engagement']
            }
            for date, data in sorted(daily_data.items())
        ]
        
        return timeline
    
    def _analyze_source_distribution(self, contents: List[Dict]) -> Dict:
        """Analyser la distribution par source"""
        from collections import Counter
        
        source_counts = Counter(c.get('source') for c in contents)
        total = len(contents)
        
        return {
            'distribution': dict(source_counts),
            'percentages': {
                source: round((count / total) * 100, 1)
                for source, count in source_counts.items()
            },
            'top_source': source_counts.most_common(1)[0][0] if source_counts else None
        }
    
    def _determine_priority_level(
        self,
        sentiment_analysis: Dict,
        influencers: Dict
    ) -> str:
        """Déterminer le niveau de priorité global"""
        
        score = 0
        
        # Sentiment négatif
        neg_pct = sentiment_analysis['percentages']['negative']
        if neg_pct > 60:
            score += 3
        elif neg_pct > 40:
            score += 2
        
        # Influenceurs critiques
        critical_influencers = [
            inf for inf in influencers['activists']
            if inf.risk_level in ['high', 'critical']
        ]
        score += len(critical_influencers)
        
        # Niveau
        if score >= 5:
            return 'CRITIQUE'
        elif score >= 3:
            return 'ÉLEVÉ'
        elif score >= 1:
            return 'MODÉRÉ'
        else:
            return 'NORMAL'
    
    def _generate_recommendations(
        self,
        sentiment_analysis: Dict,
        influencers: Dict,
        metrics: Dict
    ) -> List[Dict]:
        """Générer des recommandations actionnables"""
        
        recommendations = []
        
        # Basé sur le sentiment
        neg_pct = sentiment_analysis['percentages']['negative']
        if neg_pct > 50:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Communication',
                'action': 'Stratégie de communication corrective nécessaire',
                'rationale': f'Sentiment négatif dominant ({neg_pct:.0f}%)'
            })
        
        # Basé sur les influenceurs critiques
        critical_activists = [
            inf for inf in influencers['activists']
            if inf.risk_level in ['high', 'critical']
        ]
        
        if critical_activists:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Influenceurs',
                'action': f'Engagement prioritaire avec {len(critical_activists)} activiste(s) critique(s)',
                'rationale': 'Activistes surveillés à forte influence négative'
            })
        
        # Basé sur le volume
        if metrics.get('contents_per_day', 0) > 100:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Surveillance',
                'action': 'Renforcer la capacité de surveillance',
                'rationale': f"Volume élevé ({metrics['contents_per_day']:.0f} contenus/jour)"
            })
        
        return recommendations
    
    def _format_influencers_for_report(self, influencers: List) -> List[Dict]:
        """Formater les influenceurs pour le rapport"""
        return [
            {
                'name': inf.name,
                'source': inf.source,
                'category': inf.category,
                'total_mentions': inf.total_mentions,
                'total_engagement': inf.total_engagement,
                'sentiment_score': inf.sentiment_score,
                'risk_level': inf.risk_level,
                'trending': inf.trending,
                'reach_estimate': inf.reach_estimate
            }
            for inf in influencers
        ]
    
    def _get_recent_activity_detailed(
        self,
        author_name: str,
        days: int
    ) -> List[Dict]:
        """Récupérer activité récente détaillée d'un influenceur"""
        from app.models import Mention
        
        since_date = datetime.utcnow() - timedelta(days=days)
        
        mentions = self.db.query(Mention).filter(
            Mention.author == author_name,
            Mention.published_at >= since_date
        ).order_by(Mention.published_at.desc()).limit(20).all()
        
        return [
            {
                'date': m.published_at.isoformat() if m.published_at else None,
                'title': m.title,
                'content_preview': m.content[:200] if m.content else '',
                'source': m.source,
                'url': m.source_url,
                'engagement': m.engagement_score,
                'sentiment': m.sentiment
            }
            for m in mentions
        ]
    
    def _generate_influencer_recommendations(
        self,
        detailed_report: Dict,
        evolution: Dict
    ) -> List[Dict]:
        """Générer recommandations pour un influenceur spécifique"""
        
        recommendations = []
        
        risk_level = detailed_report['risk_assessment']['level']
        trend = evolution['trend']
        
        if risk_level in ['high', 'critical']:
            recommendations.append({
                'priority': 'URGENT',
                'action': 'Contact et engagement immédiat',
                'rationale': f'Niveau de risque {risk_level}'
            })
        
        if trend == 'rising':
            recommendations.append({
                'priority': 'MEDIUM',
                'action': 'Surveillance renforcée',
                'rationale': f"Influence en croissance ({evolution['growth_rate_percentage']}%)"
            })
        
        return recommendations
    
    def _empty_report(self, keywords: List, days: int) -> Dict:
        """Rapport vide si pas de données"""
        return {
            'metadata': {
                'title': 'Rapport Vide',
                'keywords': [k.keyword for k in keywords],
                'period_days': days,
                'generated_at': datetime.utcnow().isoformat()
            },
            'error': 'Aucune donnée disponible pour cette période'
        }


# Exemple d'utilisation
async def example_usage():
    """Exemple d'utilisation du générateur"""
    
    # Configuration (à adapter selon votre setup)
    from app.database import SessionLocal
    from app.ai_service import SovereignLLMService
    
    db = SessionLocal()
    llm_service = SovereignLLMService()
    
    generator = ProfessionalReportGenerator(
        db=db,
        llm_service=llm_service,
        youtube_api_key="votre_cle",
        reddit_credentials={
            'client_id': 'votre_client_id',
            'client_secret': 'votre_secret',
            'user_agent': 'BrandMonitor/1.0'
        },
        gemini_api_key="votre_gemini_key",  # Optionnel mais recommandé
        groq_api_key="votre_groq_key"  # Optionnel
    )
    
    # Générer rapport complet
    report = await generator.generate_comprehensive_report(
        keyword_ids=[1, 2, 3],
        days=30,
        include_web_analysis=True,
        include_influencer_profiles=True
    )
    
    print(f"✅ Rapport généré: {report['metadata']['title']}")
    print(f"📊 {report['data_quality']['total_contents_analyzed']} contenus analysés")
    print(f"\n📝 Synthèse:\n{report['executive_summary']['text']}")
    
    # Rapport influenceur spécifique
    influencer_report = await generator.generate_influencer_focused_report(
        influencer_name="Maurice Kamto",
        days=30
    )
    
    print(f"\n👤 Rapport influenceur: {influencer_report['influencer']['name']}")
    print(f"📈 Tendance: {influencer_report['evolution']['trend']}")
    print(f"\n🤖 Analyse IA:\n{influencer_report['ai_synthesis']}")


if __name__ == '__main__':
    asyncio.run(example_usage())