import { useEffect, useState } from 'react';
import { useStore } from '@/store/useStore';
import { statsApi } from '@/services/api';
import {
  TrendingUp,
  TrendingDown,
  Calendar,
  Clock,
  BarChart3,
  PieChart as PieChartIcon,
  Activity,
} from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';
import { formatNumber } from '@/lib/utils';
import toast from 'react-hot-toast';

const SENTIMENT_COLORS = {
  positive: '#10b981',
  neutral: '#6b7280',
  negative: '#ef4444',
};

const SOURCE_COLORS = [
  '#667eea',
  '#764ba2',
  '#f093fb',
  '#4facfe',
  '#00f2fe',
  '#43e97b',
  '#fa709a',
  '#fee140',
];

export default function Analytics() {
  const { advancedStats, setAdvancedStats, setLoading } = useStore();
  const [timeRange, setTimeRange] = useState(7);
  const [activeTab, setActiveTab] = useState<'overview' | 'sentiment' | 'engagement' | 'temporal'>(
    'overview'
  );

  useEffect(() => {
    loadAnalytics();
  }, [timeRange]);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const response = await statsApi.getAdvanced(timeRange);
      setAdvancedStats(response.data);
    } catch (error) {
      console.error('Error loading analytics:', error);
      toast.error('Erreur de chargement des analyses');
    } finally {
      setLoading(false);
    }
  };

  if (!advancedStats) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">
            Chargement des analyses...
          </p>
        </div>
      </div>
    );
  }

  // Calculate trends
  const timeline = advancedStats.timeline;
  const trend =
    timeline.length >= 2
      ? ((timeline[timeline.length - 1].count - timeline[0].count) / timeline[0].count) * 100
      : 0;

  // Prepare data for charts
  const sentimentTotals = Object.entries(advancedStats.sentiment_by_source).reduce(
    (acc, [source, sentiments]) => {
      Object.entries(sentiments).forEach(([sentiment, count]) => {
        acc[sentiment] = (acc[sentiment] || 0) + count;
      });
      return acc;
    },
    {} as Record<string, number>
  );

  const sentimentData = [
    { name: 'Positif', value: sentimentTotals.positive || 0, color: SENTIMENT_COLORS.positive },
    { name: 'Neutre', value: sentimentTotals.neutral || 0, color: SENTIMENT_COLORS.neutral },
    { name: 'Négatif', value: sentimentTotals.negative || 0, color: SENTIMENT_COLORS.negative },
  ];

  const sourcesSentimentData = Object.entries(advancedStats.sentiment_by_source).map(
    ([source, sentiments]) => ({
      source,
      positive: sentiments.positive || 0,
      neutral: sentiments.neutral || 0,
      negative: sentiments.negative || 0,
    })
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Analytics Avancées
          </h1>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Analyses détaillées de vos mentions
          </p>
        </div>

        {/* Time Range Selector */}
        <div className="flex items-center space-x-2">
          {[7, 14, 30, 90].map((days) => (
            <button
              key={days}
              onClick={() => setTimeRange(days)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                timeRange === days
                  ? 'bg-primary-500 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              {days} jours
            </button>
          ))}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Total Mentions"
          value={timeline.reduce((sum, item) => sum + item.count, 0)}
          icon={Activity}
          color="blue"
        />
        <StatsCard
          title="Tendance"
          value={`${trend >= 0 ? '+' : ''}${trend.toFixed(1)}%`}
          icon={trend >= 0 ? TrendingUp : TrendingDown}
          color={trend >= 0 ? 'green' : 'red'}
          subtitle={trend >= 0 ? 'En hausse' : 'En baisse'}
        />
        <StatsCard
          title="Mentions/Jour"
          value={(timeline.reduce((sum, item) => sum + item.count, 0) / timeRange).toFixed(1)}
          icon={Calendar}
          color="purple"
        />
        <StatsCard
          title="Top Engagement"
          value={formatNumber(
            advancedStats.top_engaged[0]?.engagement || 0
          )}
          icon={TrendingUp}
          color="orange"
        />
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', label: 'Vue d\'ensemble', icon: BarChart3 },
            { id: 'sentiment', label: 'Sentiment', icon: Activity },
            { id: 'engagement', label: 'Engagement', icon: TrendingUp },
            { id: 'temporal', label: 'Temporel', icon: Clock },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              <tab.icon className="w-5 h-5" />
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="space-y-6">
        {activeTab === 'overview' && (
          <>
            {/* Timeline Chart */}
            <ChartCard title="Évolution des mentions">
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={timeline}>
                  <defs>
                    <linearGradient id="colorMentions" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#667eea" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#667eea" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Area
                    type="monotone"
                    dataKey="count"
                    stroke="#667eea"
                    fillOpacity={1}
                    fill="url(#colorMentions)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </ChartCard>

            {/* Sentiment Distribution */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ChartCard title="Distribution des sentiments">
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={sentimentData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) =>
                        `${name} ${(percent * 100).toFixed(0)}%`
                      }
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {sentimentData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard title="Sentiment par source">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={sourcesSentimentData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="source" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="positive" stackId="a" fill={SENTIMENT_COLORS.positive} />
                    <Bar dataKey="neutral" stackId="a" fill={SENTIMENT_COLORS.neutral} />
                    <Bar dataKey="negative" stackId="a" fill={SENTIMENT_COLORS.negative} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>
            </div>
          </>
        )}

        {activeTab === 'sentiment' && (
          <>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {sentimentData.map((sentiment) => (
                <div
                  key={sentiment.name}
                  className="card"
                  style={{
                    background: `linear-gradient(135deg, ${sentiment.color}15, ${sentiment.color}05)`,
                  }}
                >
                  <div className="text-center">
                    <div className="text-5xl mb-4">
                      {sentiment.name === 'Positif'
                        ? '😊'
                        : sentiment.name === 'Neutre'
                        ? '😐'
                        : '😞'}
                    </div>
                    <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                      {formatNumber(sentiment.value)}
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400">{sentiment.name}</p>
                    <div className="mt-4">
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div
                          className="h-2 rounded-full transition-all duration-500"
                          style={{
                            width: `${
                              (sentiment.value /
                                sentimentData.reduce((sum, s) => sum + s.value, 0)) *
                              100
                            }%`,
                            backgroundColor: sentiment.color,
                          }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <ChartCard title="Évolution du sentiment dans le temps">
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={timeline}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="count"
                    stroke="#667eea"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Sentiment par source (détaillé)">
              <div className="space-y-4">
                {sourcesSentimentData.map((source, index) => (
                  <div key={source.source} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-gray-900 dark:text-white capitalize">
                        {source.source}
                      </span>
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {source.positive + source.neutral + source.negative} mentions
                      </span>
                    </div>
                    <div className="flex h-4 rounded-full overflow-hidden">
                      <div
                        className="bg-green-500"
                        style={{
                          width: `${
                            (source.positive /
                              (source.positive + source.neutral + source.negative)) *
                            100
                          }%`,
                        }}
                      />
                      <div
                        className="bg-gray-500"
                        style={{
                          width: `${
                            (source.neutral /
                              (source.positive + source.neutral + source.negative)) *
                            100
                          }%`,
                        }}
                      />
                      <div
                        className="bg-red-500"
                        style={{
                          width: `${
                            (source.negative /
                              (source.positive + source.neutral + source.negative)) *
                            100
                          }%`,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </ChartCard>
          </>
        )}

        {activeTab === 'engagement' && (
          <>
            <ChartCard title="Top 10 mentions les plus engageantes">
              <div className="space-y-4">
                {advancedStats.top_engaged.slice(0, 10).map((mention, index) => (
                  <div
                    key={mention.id}
                    className="flex items-start space-x-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg hover:shadow-md transition-shadow"
                  >
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center text-white font-bold">
                      {index + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <a
                        href={mention.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-medium text-gray-900 dark:text-white hover:text-primary-500 transition-colors line-clamp-2"
                      >
                        {mention.title}
                      </a>
                      <div className="flex items-center space-x-3 mt-2 text-sm">
                        <span className="badge badge-primary">{mention.source}</span>
                        {mention.sentiment && (
                          <span className="text-gray-600 dark:text-gray-400">
                            {mention.sentiment === 'positive'
                              ? '😊'
                              : mention.sentiment === 'neutral'
                              ? '😐'
                              : '😞'}{' '}
                            {mention.sentiment}
                          </span>
                        )}
                        <span className="text-primary-500 font-semibold">
                          ⭐ {formatNumber(mention.engagement)}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </ChartCard>

            <ChartCard title="Distribution de l'engagement">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={advancedStats.top_engaged.slice(0, 10).map((m) => ({
                    title: m.title.substring(0, 30) + '...',
                    engagement: m.engagement,
                  }))}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="title" angle={-45} textAnchor="end" height={100} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="engagement" fill="#667eea" />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          </>
        )}

        {activeTab === 'temporal' && (
          <>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ChartCard title="Distribution horaire">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={advancedStats.hourly_distribution}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="hour" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#667eea" />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard title="Distribution par jour de la semaine">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={advancedStats.daily_distribution}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="day" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#764ba2" />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>
            </div>

            <ChartCard title="Activité sur 24h">
              <ResponsiveContainer width="100%" height={400}>
                <RadarChart data={advancedStats.hourly_distribution}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="hour" />
                  <PolarRadiusAxis />
                  <Radar
                    name="Mentions"
                    dataKey="count"
                    stroke="#667eea"
                    fill="#667eea"
                    fillOpacity={0.6}
                  />
                  <Tooltip />
                </RadarChart>
              </ResponsiveContainer>
            </ChartCard>
          </>
        )}
      </div>
    </div>
  );
}

// Helper Components
interface StatsCardProps {
  title: string;
  value: string | number;
  icon: React.ElementType;
  color: 'blue' | 'green' | 'red' | 'purple' | 'orange';
  subtitle?: string;
}

function StatsCard({ title, value, icon: Icon, color, subtitle }: StatsCardProps) {
  const colorClasses = {
    blue: 'from-blue-500 to-blue-600',
    green: 'from-green-500 to-green-600',
    red: 'from-red-500 to-red-600',
    purple: 'from-purple-500 to-purple-600',
    orange: 'from-orange-500 to-orange-600',
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">{value}</p>
          {subtitle && (
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{subtitle}</p>
          )}
        </div>
        <div
          className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colorClasses[color]} flex items-center justify-center`}
        >
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
    <div className="card">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{title}</h3>
      {children}
    </div>
  );
}