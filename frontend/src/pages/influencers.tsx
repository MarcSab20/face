import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  TrendingUp,
  TrendingDown,
  Users,
  Award,
  ExternalLink,
  Filter,
  Calendar,
} from 'lucide-react';
import { formatNumber } from '@/lib/utils';
import { Card, Badge, PageLoading, ErrorState, Tabs } from '@/components/ui/index';
import toast from 'react-hot-toast';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Influencer {
  author: string;
  source: string;
  mention_count: number;
  total_engagement: number;
  avg_engagement: number;
  sentiment_score: number;
  positive_mentions: number;
  negative_mentions: number;
  profile_url: string;
  recent_mentions: Array<{
    title: string;
    url: string;
    engagement: number;
    sentiment: string | null;
    published_at: string | null;
  }>;
}

const SOURCE_COLORS: Record<string, string> = {
  youtube: 'bg-red-600',
  tiktok: 'bg-black',
  twitter: 'bg-blue-400',
  instagram: 'bg-pink-500',
  reddit: 'bg-red-500',
  telegram: 'bg-blue-400',
};

const SOURCE_ICONS: Record<string, string> = {
  youtube: '📺',
  tiktok: '🎵',
  twitter: '🐦',
  instagram: '📷',
  reddit: '🔴',
  telegram: '✈️',
};

export default function Influencers() {
  const [days, setDays] = useState(30);
  const [selectedSource, setSelectedSource] = useState<string>('all');
  const [activeTab, setActiveTab] = useState<'all' | 'by-source' | 'stats'>('all');

  // Charger les top influenceurs
  const { data: influencersData, isLoading, error, refetch } = useQuery({
    queryKey: ['topInfluencers', days, selectedSource],
    queryFn: async () => {
      const params = new URLSearchParams({
        days: days.toString(),
        limit: '20',
      });
      
      if (selectedSource !== 'all') {
        params.append('source', selectedSource);
      }
      
      const response = await axios.get(
        `${API_BASE_URL}/api/influencers/top?${params.toString()}`
      );
      return response.data;
    },
  });

  // Charger influenceurs par source
  const { data: bySourceData } = useQuery({
    queryKey: ['influencersBySource', days],
    queryFn: async () => {
      const response = await axios.get(
        `${API_BASE_URL}/api/influencers/by-source?days=${days}`
      );
      return response.data;
    },
    enabled: activeTab === 'by-source',
  });

  // Charger statistiques
  const { data: statsData } = useQuery({
    queryKey: ['influencerStats', days],
    queryFn: async () => {
      const response = await axios.get(
        `${API_BASE_URL}/api/influencers/stats?days=${days}`
      );
      return response.data;
    },
    enabled: activeTab === 'stats',
  });

  if (error) {
    return (
      <ErrorState
        message="Erreur de chargement des influenceurs"
        retry={() => refetch()}
      />
    );
  }

  if (isLoading) {
    return <PageLoading message="Chargement des influenceurs..." />;
  }

  const influencers = influencersData?.influencers || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            👑 Top Influenceurs
          </h1>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Les comptes qui génèrent le plus d'engagement
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {/* Filtre période */}
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="input max-w-xs"
          >
            <option value="7">7 derniers jours</option>
            <option value="14">14 derniers jours</option>
            <option value="30">30 derniers jours</option>
            <option value="90">90 derniers jours</option>
          </select>

          {/* Filtre source */}
          {activeTab === 'all' && (
            <select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              className="input max-w-xs"
            >
              <option value="all">Toutes les sources</option>
              <option value="youtube">YouTube</option>
              <option value="tiktok">TikTok</option>
              <option value="twitter">Twitter</option>
              <option value="instagram">Instagram</option>
              <option value="reddit">Reddit</option>
            </select>
          )}
        </div>
      </div>

      {/* Statistiques rapides */}
      {statsData && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Influenceurs</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                  {statsData.total_influencers}
                </p>
              </div>
              <Users className="w-10 h-10 text-primary-500" />
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Engagement Total</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                  {formatNumber(statsData.total_engagement)}
                </p>
              </div>
              <TrendingUp className="w-10 h-10 text-green-500" />
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Engagement Moyen</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                  {formatNumber(statsData.avg_engagement_per_influencer)}
                </p>
              </div>
              <Award className="w-10 h-10 text-orange-500" />
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Source Dominante</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1 capitalize">
                  {SOURCE_ICONS[statsData.top_source] || ''} {statsData.top_source}
                </p>
              </div>
              <Filter className="w-10 h-10 text-purple-500" />
            </div>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <Tabs
        tabs={[
          { id: 'all', label: 'Tous', icon: Users },
          { id: 'by-source', label: 'Par Source', icon: Filter },
          { id: 'stats', label: 'Statistiques', icon: TrendingUp },
        ]}
        activeTab={activeTab}
        onChange={(id) => setActiveTab(id as any)}
      />

      {/* Tab Content */}
      {activeTab === 'all' && (
        <div className="grid grid-cols-1 gap-6">
          {influencers.length === 0 ? (
            <Card>
              <div className="text-center py-12">
                <Users className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 dark:text-gray-400">
                  Aucun influenceur trouvé pour cette période
                </p>
              </div>
            </Card>
          ) : (
            influencers.map((influencer: Influencer, index: number) => (
              <InfluencerCard
                key={`${influencer.author}-${influencer.source}`}
                influencer={influencer}
                rank={index + 1}
              />
            ))
          )}
        </div>
      )}

      {activeTab === 'by-source' && bySourceData && (
        <div className="space-y-8">
          {Object.entries(bySourceData.sources).map(([source, influencers]: [string, any]) => (
            <div key={source}>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center space-x-2">
                <span className="text-3xl">{SOURCE_ICONS[source]}</span>
                <span className="capitalize">{source}</span>
                <Badge variant="primary">{influencers.length}</Badge>
              </h3>
              <div className="grid grid-cols-1 gap-4">
                {influencers.map((influencer: Influencer, index: number) => (
                  <InfluencerCard
                    key={`${influencer.author}-${source}`}
                    influencer={influencer}
                    rank={index + 1}
                    compact
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Composant carte influenceur
interface InfluencerCardProps {
  influencer: Influencer;
  rank: number;
  compact?: boolean;
}

function InfluencerCard({ influencer, rank, compact = false }: InfluencerCardProps) {
  const sourceColor = SOURCE_COLORS[influencer.source] || 'bg-gray-500';
  const sourceIcon = SOURCE_ICONS[influencer.source] || '📄';

  return (
    <Card hoverable>
      <div className="flex items-start space-x-4">
        {/* Rank */}
        <div className="flex-shrink-0">
          <div
            className={`w-12 h-12 rounded-full flex items-center justify-center text-white font-bold text-xl ${
              rank <= 3
                ? 'bg-gradient-to-br from-yellow-400 to-orange-500'
                : 'bg-gradient-to-br from-primary-500 to-secondary-500'
            }`}
          >
            {rank <= 3 ? '🏆' : rank}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-start justify-between mb-3">
            <div className="flex-1 min-w-0">
              <a
                href={influencer.profile_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xl font-bold text-gray-900 dark:text-white hover:text-primary-500 transition-colors flex items-center space-x-2 group"
              >
                <span className="truncate">{influencer.author}</span>
                <ExternalLink className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
              </a>
              <div className="flex items-center space-x-2 mt-1">
                <span
                  className={`inline-flex items-center space-x-1 px-3 py-1 rounded-full text-white font-medium text-sm ${sourceColor}`}
                >
                  <span>{sourceIcon}</span>
                  <span className="capitalize">{influencer.source}</span>
                </span>
                <Badge variant={influencer.sentiment_score >= 70 ? 'success' : influencer.sentiment_score >= 40 ? 'info' : 'warning'}>
                  {influencer.sentiment_score >= 70 ? '😊' : influencer.sentiment_score >= 40 ? '😐' : '😞'}{' '}
                  {influencer.sentiment_score.toFixed(0)}% positif
                </Badge>
              </div>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <StatItem
              label="Mentions"
              value={influencer.mention_count}
              icon="💬"
            />
            <StatItem
              label="Engagement Total"
              value={formatNumber(influencer.total_engagement)}
              icon="⭐"
            />
            <StatItem
              label="Engagement Moyen"
              value={formatNumber(influencer.avg_engagement)}
              icon="📊"
            />
            <StatItem
              label="Positives"
              value={influencer.positive_mentions}
              icon="👍"
              color="text-green-600"
            />
          </div>

          {/* Mentions récentes */}
          {!compact && influencer.recent_mentions.length > 0 && (
            <div>
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Mentions récentes :
              </p>
              <div className="space-y-2">
                {influencer.recent_mentions.slice(0, 2).map((mention, idx) => (
                  <a
                    key={idx}
                    href={mention.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block p-3 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
                  >
                    <p className="text-sm text-gray-900 dark:text-white line-clamp-2 mb-1">
                      {mention.title}
                    </p>
                    <div className="flex items-center space-x-3 text-xs text-gray-600 dark:text-gray-400">
                      <span>⭐ {formatNumber(mention.engagement)}</span>
                      {mention.sentiment && (
                        <span>
                          {mention.sentiment === 'positive'
                            ? '😊'
                            : mention.sentiment === 'neutral'
                            ? '😐'
                            : '😞'}{' '}
                          {mention.sentiment}
                        </span>
                      )}
                    </div>
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}

// Composant stat
interface StatItemProps {
  label: string;
  value: string | number;
  icon: string;
  color?: string;
}

function StatItem({ label, value, icon, color = 'text-gray-900 dark:text-white' }: StatItemProps) {
  return (
    <div className="text-center">
      <div className="text-2xl mb-1">{icon}</div>
      <p className={`text-lg font-bold ${color}`}>{value}</p>
      <p className="text-xs text-gray-600 dark:text-gray-400">{label}</p>
    </div>
  );
}