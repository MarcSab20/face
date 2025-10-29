import { useEffect, useState } from 'react';
import { useStore } from '@/store/useStore';
import { mentionsApi, exportApi, sentimentApi } from '@/services/api';
import {
  Filter,
  Download,
  ExternalLink,
  RefreshCw,
  Search as SearchIcon,
  Calendar,
  TrendingUp,
  Heart,
  MessageCircle,
  Eye,
} from 'lucide-react';
import {
  formatDate,
  formatNumber,
  getSentimentEmoji,
  getSentimentColor,
  getSourceIcon,
  getSourceColor,
} from '@/lib/utils';
import type { Mention, FilterOptions } from '@/types/index';
import toast from 'react-hot-toast';

const SENTIMENT_OPTIONS = [
  { value: '', label: 'Tous les sentiments' },
  { value: 'positive', label: '😊 Positif' },
  { value: 'neutral', label: '😐 Neutre' },
  { value: 'negative', label: '😞 Négatif' },
];

const SOURCES = ['rss', 'reddit', 'youtube', 'tiktok', 'google_search', 'google_alerts'];

export default function Mentions() {
  const { mentions, setMentions, keywords, filters, setFilters, resetFilters, setLoading } =
    useStore();
  const [showFilters, setShowFilters] = useState(false);
  const [selectedMentions, setSelectedMentions] = useState<number[]>([]);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('list');
  const [analyzingAll, setAnalyzingAll] = useState(false);

  useEffect(() => {
    loadMentions();
  }, [filters]);

  const loadMentions = async () => {
    setLoading(true);
    try {
      const response = await mentionsApi.getAll(filters, 100, 0);
      setMentions(response.data);
    } catch (error) {
      console.error('Error loading mentions:', error);
      toast.error('Erreur de chargement des mentions');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key: keyof FilterOptions, value: any) => {
    setFilters({ ...filters, [key]: value });
  };

  const handleExport = async (format: 'csv' | 'json') => {
    try {
      toast.loading(`Export ${format.toUpperCase()} en cours...`);
      if (format === 'csv') {
        await exportApi.toCSV(filters);
      } else {
        await exportApi.toJSON(filters);
      }
      toast.dismiss();
      toast.success(`Export ${format.toUpperCase()} réussi !`);
    } catch (error) {
      toast.dismiss();
      toast.error('Erreur lors de l\'export');
    }
  };

  const handleAnalyzeAll = async () => {
    setAnalyzingAll(true);
    try {
      await sentimentApi.analyzeAll();
      toast.success('Analyse de sentiment lancée en arrière-plan');
      setTimeout(() => {
        loadMentions();
      }, 5000);
    } catch (error) {
      toast.error('Erreur lors de l\'analyse');
    } finally {
      setAnalyzingAll(false);
    }
  };

  const handleSelectMention = (id: number) => {
    setSelectedMentions((prev) =>
      prev.includes(id) ? prev.filter((m) => m !== id) : [...prev, id]
    );
  };

  const handleSelectAll = () => {
    if (selectedMentions.length === mentions.length) {
      setSelectedMentions([]);
    } else {
      setSelectedMentions(mentions.map((m) => m.id));
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Mentions
          </h1>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            {mentions.length} mention{mentions.length !== 1 ? 's' : ''} trouvée
            {mentions.length !== 1 ? 's' : ''}
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`btn ${showFilters ? 'btn-primary' : 'btn-secondary'}`}
          >
            <Filter className="w-4 h-4 mr-2" />
            Filtres
          </button>

          <div className="relative group">
            <button className="btn btn-secondary">
              <Download className="w-4 h-4 mr-2" />
              Export
            </button>
            <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
              <button
                onClick={() => handleExport('csv')}
                className="block w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-t-lg"
              >
                Export CSV
              </button>
              <button
                onClick={() => handleExport('json')}
                className="block w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-b-lg"
              >
                Export JSON
              </button>
            </div>
          </div>

          <button onClick={loadMentions} className="btn btn-secondary">
            <RefreshCw className="w-4 h-4" />
          </button>

          {mentions.some((m) => !m.sentiment) && (
            <button
              onClick={handleAnalyzeAll}
              disabled={analyzingAll}
              className="btn btn-primary"
            >
              {analyzingAll ? 'Analyse...' : 'Analyser sentiments'}
            </button>
          )}
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="card animate-fade-in">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Search */}
            <div className="lg:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Recherche
              </label>
              <div className="relative">
                <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  value={filters.search || ''}
                  onChange={(e) => handleFilterChange('search', e.target.value)}
                  placeholder="Rechercher dans les titres et contenus..."
                  className="input pl-10"
                />
              </div>
            </div>

            {/* Keyword */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Mot-clé
              </label>
              <select
                value={filters.keyword || ''}
                onChange={(e) => handleFilterChange('keyword', e.target.value)}
                className="input"
              >
                <option value="">Tous les mots-clés</option>
                {keywords.map((kw) => (
                  <option key={kw.id} value={kw.keyword}>
                    {kw.keyword}
                  </option>
                ))}
              </select>
            </div>

            {/* Source */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Source
              </label>
              <select
                value={filters.source || ''}
                onChange={(e) => handleFilterChange('source', e.target.value)}
                className="input"
              >
                <option value="">Toutes les sources</option>
                {SOURCES.map((source) => (
                  <option key={source} value={source}>
                    {getSourceIcon(source)} {source}
                  </option>
                ))}
              </select>
            </div>

            {/* Sentiment */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Sentiment
              </label>
              <select
                value={filters.sentiment || ''}
                onChange={(e) => handleFilterChange('sentiment', e.target.value as any)}
                className="input"
              >
                {SENTIMENT_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Date From */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Date de début
              </label>
              <input
                type="date"
                value={filters.date_from || ''}
                onChange={(e) => handleFilterChange('date_from', e.target.value)}
                className="input"
              />
            </div>

            {/* Date To */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Date de fin
              </label>
              <input
                type="date"
                value={filters.date_to || ''}
                onChange={(e) => handleFilterChange('date_to', e.target.value)}
                className="input"
              />
            </div>

            {/* Min Engagement */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Engagement minimum
              </label>
              <input
                type="number"
                value={filters.min_engagement || ''}
                onChange={(e) =>
                  handleFilterChange('min_engagement', parseFloat(e.target.value) || undefined)
                }
                placeholder="0"
                className="input"
              />
            </div>
          </div>

          <div className="mt-4 flex justify-end space-x-2">
            <button onClick={resetFilters} className="btn btn-secondary">
              Réinitialiser
            </button>
          </div>
        </div>
      )}

      {/* Bulk Actions */}
      {selectedMentions.length > 0 && (
        <div className="card bg-primary-50 dark:bg-primary-900/20 border-2 border-primary-500">
          <div className="flex items-center justify-between">
            <span className="font-medium text-gray-900 dark:text-white">
              {selectedMentions.length} mention{selectedMentions.length !== 1 ? 's' : ''}{' '}
              sélectionnée{selectedMentions.length !== 1 ? 's' : ''}
            </span>
            <div className="flex space-x-2">
              <button onClick={handleSelectAll} className="btn btn-secondary">
                {selectedMentions.length === mentions.length
                  ? 'Tout désélectionner'
                  : 'Tout sélectionner'}
              </button>
              <button
                onClick={() => setSelectedMentions([])}
                className="btn btn-secondary"
              >
                Annuler
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Mentions List */}
      {mentions.length === 0 ? (
        <div className="card text-center py-12">
          <div className="text-6xl mb-4">🔍</div>
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            Aucune mention trouvée
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            {Object.values(filters).some((v) => v)
              ? 'Essayez de modifier vos filtres'
              : 'Lancez une collecte pour commencer'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {mentions.map((mention) => (
            <MentionCard
              key={mention.id}
              mention={mention}
              selected={selectedMentions.includes(mention.id)}
              onSelect={() => handleSelectMention(mention.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// Mention Card Component
interface MentionCardProps {
  mention: Mention;
  selected: boolean;
  onSelect: () => void;
}

function MentionCard({ mention, selected, onSelect }: MentionCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className={`card hover:shadow-xl transition-all cursor-pointer ${
        selected ? 'ring-2 ring-primary-500' : ''
      }`}
    >
      <div className="flex items-start space-x-4">
        {/* Checkbox */}
        <input
          type="checkbox"
          checked={selected}
          onChange={onSelect}
          className="mt-1 w-5 h-5 text-primary-500 rounded focus:ring-primary-500"
        />

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-start justify-between mb-3">
            <div className="flex-1 min-w-0">
              <a
                href={mention.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-lg font-semibold text-gray-900 dark:text-white hover:text-primary-500 transition-colors flex items-center space-x-2 group"
              >
                <span className="line-clamp-2">{mention.title}</span>
                <ExternalLink className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
              </a>
            </div>
          </div>

          {/* Metadata */}
          <div className="flex flex-wrap items-center gap-3 mb-3 text-sm">
            {/* Source */}
            <span
              className={`inline-flex items-center space-x-1 px-3 py-1 rounded-full text-white font-medium ${getSourceColor(
                mention.source
              )}`}
            >
              <span>{getSourceIcon(mention.source)}</span>
              <span>{mention.source}</span>
            </span>

            {/* Sentiment */}
            {mention.sentiment && (
              <span
                className={`inline-flex items-center space-x-1 px-3 py-1 rounded-full text-white font-medium ${getSentimentColor(
                  mention.sentiment
                )}`}
              >
                <span>{getSentimentEmoji(mention.sentiment)}</span>
                <span className="capitalize">{mention.sentiment}</span>
              </span>
            )}

            {/* Author */}
            <span className="text-gray-600 dark:text-gray-400">
              par <strong>{mention.author}</strong>
            </span>

            {/* Date */}
            <span className="flex items-center space-x-1 text-gray-600 dark:text-gray-400">
              <Calendar className="w-4 h-4" />
              <span>{formatDate(mention.published_at)}</span>
            </span>

            {/* Engagement */}
            <span className="flex items-center space-x-1 text-gray-600 dark:text-gray-400">
              <TrendingUp className="w-4 h-4" />
              <span>{formatNumber(mention.engagement_score)}</span>
            </span>
          </div>

          {/* Content Preview */}
          <p
            className={`text-gray-700 dark:text-gray-300 ${
              expanded ? '' : 'line-clamp-3'
            }`}
          >
            {mention.content}
          </p>

          {/* Expand Button */}
          {mention.content.length > 200 && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="mt-2 text-sm text-primary-500 hover:text-primary-600 font-medium"
            >
              {expanded ? 'Voir moins' : 'Voir plus'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}