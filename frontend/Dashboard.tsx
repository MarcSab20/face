import { useEffect } from 'react';
import { useStore } from '@/store/useStore';
import { statsApi, advancedStatsApi } from '@/services/api';
import { TrendingUp, MessageSquare, Search as SearchIcon, Activity } from 'lucide-react';
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
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { formatNumber, getSentimentEmoji, getSourceIcon } from '@/lib/utils';
import toast from 'react-hot-toast';

const SENTIMENT_COLORS = {
  positive: '#10b981',
  neutral: '#6b7280',
  negative: '#ef4444',
};

export default function Dashboard() {
  const { stats, advancedStats, setStats, setAdvancedStats, setLoading } = useStore();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [statsRes, advancedStatsRes] = await Promise.all([
        statsApi.getBasic(),
        statsApi.getAdvanced(7),
      ]);
      setStats(statsRes.data);
      setAdvancedStats(advancedStatsRes.data);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      toast.error('Erreur de chargement des données');
    } finally {
      setLoading(false);
    }
  };

  if (!stats || !advancedStats) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Chargement...</p>
        </div>
      </div>
    );
  }

  const sentimentData = stats.sentiment_distribution
    ? [
        { name: 'Positif', value: stats.sentiment_distribution.positive },
        { name: 'Neutre', value: stats.sentiment_distribution.neutral },
        { name: 'Négatif', value: stats.sentiment_distribution.negative },
      ]
    : [];

  const sourcesData = Object.entries(stats.mentions_by_source).map(([source, count]) => ({
    source,
    count,
  }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Dashboard
          </h1>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Vue d'ensemble de vos surveillances
          </p>
        </div>
        <button
          onClick={loadData}
          className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
        >
          Actualiser
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Mots-clés"
          value={stats.total_keywords}
          icon={SearchIcon}
          color="blue"
        />
        <StatsCard
          title="Mentions totales"
          value={stats.total_mentions}
          icon={MessageSquare}
          color="purple"
        />
        <StatsCard
          title="Aujourd'hui"
          value={stats.mentions_today}
          icon={TrendingUp}
          color="green"
        />
        <StatsCard
          title="Sources actives"
          value={Object.keys(stats.mentions_by_source).length}
          icon={Activity}
          color="orange"
        />
      </div>

      {/* Sentiment Overview */}
      {stats.sentiment_distribution && (
        <div className="bg-gradient-to-br from-primary-500 to-secondary-500 rounded-2xl p-6 text-white shadow-xl">
          <h3 className="text-lg font-semibold mb-4">Analyse de Sentiment</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-4xl mb-2">😊</div>
              <div className="text-3xl font-bold">{stats.sentiment_distribution.positive}</div>
              <div className="text-sm opacity-90">Positif</div>
            </div>
            <div className="text-center">
              <div className="text-4xl mb-2">😐</div>
              <div className="text-3xl font-bold">{stats.sentiment_distribution.neutral}</div>
              <div className="text-sm opacity-90">Neutre</div>
            </div>
            <div className="text-center">
              <div className="text-4xl mb-2">😞</div>
              <div className="text-3xl font-bold">{stats.sentiment_distribution.negative}</div>
              <div className="text-sm opacity-90">Négatif</div>
            </div>
          </div>
        </div>
      )}

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Timeline Chart */}
        <ChartCard title="Évolution temporelle (7 derniers jours)">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={advancedStats.timeline}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="count"
                stroke="#667eea"
                strokeWidth={2}
                dot={{ fill: '#667eea' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Sentiment Distribution Chart */}
        <ChartCard title="Répartition des sentiments">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={sentimentData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {sentimentData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={Object.values(SENTIMENT_COLORS)[index]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Sources Chart */}
        <ChartCard title="Mentions par source">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={sourcesData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="source" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#667eea" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Top Keywords */}
        <ChartCard title="Top Mots-clés">
          <div className="space-y-3">
            {stats.top_keywords.slice(0, 5).map((kw, index) => (
              <div
                key={kw.keyword}
                className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center text-white font-bold">
                    {index + 1}
                  </div>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {kw.keyword}
                  </span>
                </div>
                <span className="text-sm font-semibold text-primary-500">
                  {kw.mentions} mentions
                </span>
              </div>
            ))}
          </div>
        </ChartCard>
      </div>

      {/* Top Engaged Mentions */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
          🔥 Top Mentions Engageantes
        </h3>
        <div className="space-y-3">
          {advancedStats.top_engaged.slice(0, 5).map((mention, index) => (
            <div
              key={mention.id}
              className="flex items-start space-x-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg hover:shadow-md transition-shadow"
            >
              <div className="text-2xl font-bold text-primary-500">#{index + 1}</div>
              <div className="flex-1">
                <a
                  href={mention.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-medium text-gray-900 dark:text-white hover:text-primary-500 transition-colors line-clamp-2"
                >
                  {mention.title}
                </a>
                <div className="flex items-center space-x-3 mt-2 text-sm">
                  <span className="inline-flex items-center px-2 py-1 rounded-full bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300">
                    {getSourceIcon(mention.source)} {mention.source}
                  </span>
                  {mention.sentiment && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full bg-gray-200 dark:bg-gray-600">
                      {getSentimentEmoji(mention.sentiment)} {mention.sentiment}
                    </span>
                  )}
                  <span className="text-gray-600 dark:text-gray-400">
                    ⭐ {formatNumber(mention.engagement)}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Helper Components

interface StatsCardProps {
  title: string;
  value: number;
  icon: React.ElementType;
  color: 'blue' | 'purple' | 'green' | 'orange';
}

function StatsCard({ title, value, icon: Icon, color }: StatsCardProps) {
  const colorClasses = {
    blue: 'from-blue-500 to-blue-600',
    purple: 'from-purple-500 to-purple-600',
    green: 'from-green-500 to-green-600',
    orange: 'from-orange-500 to-orange-600',
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
            {formatNumber(value)}
          </p>
        </div>
        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colorClasses[color]} flex items-center justify-center`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </div>
  );
}

interface ChartCardProps {
  title: string;
  children: React.ReactNode;
}

function ChartCard({ title, children }: ChartCardProps) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{title}</h3>
      {children}
    </div>
  );
}