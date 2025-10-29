import { memo, useMemo } from 'react';
import { useQuery, useQueries } from '@tanstack/react-query';
import { statsApi } from '@/services/api';
import {
  TrendingUp,
  MessageSquare,
  Search as SearchIcon,
  Activity,
  RefreshCw,
  Download,
} from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import {
  PageLoading,
  ErrorState,
  Card,
  Badge,
  Skeleton,
} from '@/components/ui/index';
import { formatNumber, getSentimentEmoji, getSourceIcon } from '@/lib/utils';
import { useMediaQuery } from '@/hooks';
import toast from 'react-hot-toast';
import type { Stats, AdvancedStats } from '@/types/index';

const SENTIMENT_COLORS = {
  positive: '#10b981',
  neutral: '#6b7280',
  negative: '#ef4444',
};

type ColorKey = 'blue' | 'purple' | 'green' | 'orange';

export default function Dashboard() {
  const isMobile = useMediaQuery('(max-width: 768px)');

  const [statsQuery, advancedStatsQuery] = useQueries({
    queries: [
      {
        queryKey: ['stats'],
        queryFn: async () => {
          const response = await statsApi.getBasic();
          return response.data as Stats;
        },
        staleTime: 2 * 60 * 1000,
        refetchInterval: 5 * 60 * 1000,
      },
      {
        queryKey: ['advancedStats', 7],
        queryFn: async () => {
          const response = await statsApi.getAdvanced(7);
          return response.data as AdvancedStats;
        },
        staleTime: 5 * 60 * 1000,
      },
    ],
  });

  const { data: stats, isLoading: statsLoading, error: statsError, refetch } = statsQuery;
  const { data: advancedStats, isLoading: advancedLoading, error: advancedError } = advancedStatsQuery;

  if (statsError || advancedError) {
    return (
      <ErrorState
        message="Impossible de charger les données du dashboard"
        retry={() => {
          statsQuery.refetch();
          advancedStatsQuery.refetch();
        }}
      />
    );
  }

  if (statsLoading || advancedLoading || !stats || !advancedStats) {
    return <DashboardSkeleton />;
  }

  const handleRefresh = () => {
    refetch();
    toast.success('Données actualisées !');
  };

  return (
    <div className="space-y-6">
      <DashboardHeader onRefresh={handleRefresh} isRefreshing={statsQuery.isFetching} />
      <StatsCardsSection stats={stats} />
      {stats.sentiment_distribution && <SentimentOverviewCard distribution={stats.sentiment_distribution} />}
      
      <div className={`grid gap-6 ${isMobile ? 'grid-cols-1' : 'lg:grid-cols-2'}`}>
        <TimelineChart data={advancedStats.timeline} />
        <SentimentPieChart distribution={stats.sentiment_distribution} />
        <SourcesBarChart data={stats.mentions_by_source} />
        <TopKeywordsCard keywords={stats.top_keywords} />
      </div>

      <TopEngagedSection mentions={advancedStats.top_engaged} />
    </div>
  );
}

const DashboardHeader = memo(({ onRefresh, isRefreshing }: { onRefresh: () => void; isRefreshing: boolean }) => (
  <div className="flex items-center justify-between flex-wrap gap-4">
    <div>
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
      <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">Vue d'ensemble de vos surveillances</p>
    </div>
    <button onClick={onRefresh} disabled={isRefreshing} className="btn btn-primary">
      <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
    </button>
  </div>
));

const StatsCardsSection = memo(({ stats }: { stats: Stats }) => {
  const cardsData = useMemo(() => [
    { title: 'Mots-clés', value: stats.total_keywords, icon: SearchIcon, color: 'blue' as ColorKey },
    { title: 'Mentions totales', value: stats.total_mentions, icon: MessageSquare, color: 'purple' as ColorKey },
    { title: 'Aujourd\'hui', value: stats.mentions_today, icon: TrendingUp, color: 'green' as ColorKey },
    { title: 'Sources actives', value: Object.keys(stats.mentions_by_source).length, icon: Activity, color: 'orange' as ColorKey },
  ], [stats]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {cardsData.map((card) => <StatsCard key={card.title} {...card} />)}
    </div>
  );
});

const StatsCard = memo(({ title, value, icon: Icon, color }: { title: string; value: number; icon: any; color: ColorKey }) => {
  const colorClasses: Record<ColorKey, string> = {
    blue: 'from-blue-500 to-blue-600',
    purple: 'from-purple-500 to-purple-600',
    green: 'from-green-500 to-green-600',
    orange: 'from-orange-500 to-orange-600',
  };

  return (
    <Card hoverable>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">{formatNumber(value)}</p>
        </div>
        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colorClasses[color]} flex items-center justify-center shadow-lg`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </Card>
  );
});

const SentimentOverviewCard = memo(({ distribution }: { distribution: { positive: number; neutral: number; negative: number } }) => {
  const total = distribution.positive + distribution.neutral + distribution.negative;
  return (
    <Card className="bg-gradient-to-br from-primary-500 to-secondary-500 text-white shadow-xl">
      <h3 className="text-lg font-semibold mb-4">Analyse de Sentiment</h3>
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Positif', value: distribution.positive, emoji: '😊' },
          { label: 'Neutre', value: distribution.neutral, emoji: '😐' },
          { label: 'Négatif', value: distribution.negative, emoji: '😞' },
        ].map((item) => (
          <div key={item.label} className="text-center">
            <div className="text-4xl mb-2">{item.emoji}</div>
            <div className="text-3xl font-bold">{item.value}</div>
            <div className="text-sm opacity-90">{item.label}</div>
            <div className="text-xs opacity-75 mt-1">{((item.value / total) * 100).toFixed(1)}%</div>
          </div>
        ))}
      </div>
    </Card>
  );
});

const TimelineChart = memo(({ data }: { data: Array<{ date: string; count: number }> }) => (
  <ChartCard title="Évolution temporelle">
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="count" stroke="#667eea" strokeWidth={2} />
      </LineChart>
    </ResponsiveContainer>
  </ChartCard>
));

const SentimentPieChart = memo(({ distribution }: { distribution: { positive: number; neutral: number; negative: number } | undefined }) => {
  const data = useMemo(() => [
    { name: 'Positif', value: distribution?.positive || 0 },
    { name: 'Neutre', value: distribution?.neutral || 0 },
    { name: 'Négatif', value: distribution?.negative || 0 },
  ], [distribution]);

  return (
    <ChartCard title="Répartition des sentiments">
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie data={data} cx="50%" cy="50%" labelLine={false} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} outerRadius={80} dataKey="value">
            {data.map((_, index) => <Cell key={`cell-${index}`} fill={Object.values(SENTIMENT_COLORS)[index]} />)}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    </ChartCard>
  );
});

const SourcesBarChart = memo(({ data }: { data: Record<string, number> }) => {
  const chartData = useMemo(() => Object.entries(data).map(([source, count]) => ({ source, count })), [data]);
  return (
    <ChartCard title="Mentions par source">
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="source" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="count" fill="#667eea" radius={[8, 8, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
});

const TopKeywordsCard = memo(({ keywords }: { keywords: Array<{ keyword: string; mentions: number }> }) => (
  <ChartCard title="Top Mots-clés">
    <div className="space-y-3">
      {keywords.slice(0, 5).map((kw, index) => (
        <div key={kw.keyword} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center text-white font-bold">{index + 1}</div>
            <span className="font-medium text-gray-900 dark:text-white">{kw.keyword}</span>
          </div>
          <Badge variant="primary">{kw.mentions} mentions</Badge>
        </div>
      ))}
    </div>
  </ChartCard>
));

const TopEngagedSection = memo(({ mentions }: { mentions: Array<{ id: number; title: string; source: string; engagement: number; sentiment: string | null; url: string }> }) => (
  <Card>
    <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">🔥 Top Mentions Engageantes</h3>
    <div className="space-y-3">
      {mentions.slice(0, 5).map((mention, index) => (
        <div key={mention.id} className="flex items-start space-x-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <div className="text-2xl font-bold text-primary-500">#{index + 1}</div>
          <div className="flex-1">
            <a href={mention.url} target="_blank" rel="noopener noreferrer" className="font-medium text-gray-900 dark:text-white hover:text-primary-500 line-clamp-2">{mention.title}</a>
            <div className="flex items-center space-x-3 mt-2 text-sm">
              <Badge>{getSourceIcon(mention.source)} {mention.source}</Badge>
              {mention.sentiment && <span>{getSentimentEmoji(mention.sentiment)} {mention.sentiment}</span>}
              <span className="text-primary-500 font-semibold">⭐ {formatNumber(mention.engagement)}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  </Card>
));

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Card>
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{title}</h3>
      {children}
    </Card>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><Skeleton className="h-8 w-48 mb-2" /><Skeleton className="h-4 w-64" /></div>
        <Skeleton className="h-10 w-32" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <div className="flex items-center justify-between">
              <div className="flex-1"><Skeleton className="h-4 w-24 mb-2" /><Skeleton className="h-8 w-16" /></div>
              <Skeleton className="w-12 h-12 rounded-xl" />
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

DashboardHeader.displayName = 'DashboardHeader';
StatsCardsSection.displayName = 'StatsCardsSection';
StatsCard.displayName = 'StatsCard';
SentimentOverviewCard.displayName = 'SentimentOverviewCard';
TimelineChart.displayName = 'TimelineChart';
SentimentPieChart.displayName = 'SentimentPieChart';
SourcesBarChart.displayName = 'SourcesBarChart';
TopKeywordsCard.displayName = 'TopKeywordsCard';
TopEngagedSection.displayName = 'TopEngagedSection';