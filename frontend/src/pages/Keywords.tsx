import { useEffect, useState } from 'react';
import { useStore } from '@/store/useStore';
import { keywordsApi, collectionApi } from '@/services/api';
import { Plus, Trash2, Play, Clock, CheckCircle } from 'lucide-react';
import { formatDate, getSourceIcon } from '@/lib/utils';
import toast from 'react-hot-toast';

const AVAILABLE_SOURCES = [
  { id: 'rss', name: 'RSS Feeds', icon: '📰', color: 'bg-orange-500' },
  { id: 'reddit', name: 'Reddit', icon: '🔴', color: 'bg-red-500' },
  { id: 'youtube', name: 'YouTube', icon: '📺', color: 'bg-red-600' },
  { id: 'tiktok', name: 'TikTok', icon: '🎵', color: 'bg-black' },
  { id: 'google_search', name: 'Google Search', icon: '🔍', color: 'bg-blue-500' },
  { id: 'twitter', name: 'Twitter/X', icon: '🐦', color: 'bg-blue-400' },
  { id: 'instagram', name: 'Instagram', icon: '📷', color: 'bg-pink-500' },
  { id: 'facebook', name: 'Facebook', icon: '👍', color: 'bg-blue-600' },
  { id: 'linkedin', name: 'LinkedIn', icon: '💼', color: 'bg-blue-700' },
  { id: 'telegram', name: 'Telegram', icon: '✈️', color: 'bg-blue-400' },
  { id: 'discord', name: 'Discord', icon: '💬', color: 'bg-indigo-600' },
  { id: 'medium', name: 'Medium', icon: '📝', color: 'bg-gray-800' },
];

export default function Keywords() {
  const { keywords, setKeywords, setLoading } = useStore();
  const [showAddModal, setShowAddModal] = useState(false);
  const [newKeyword, setNewKeyword] = useState('');
  const [selectedSources, setSelectedSources] = useState<string[]>(['rss', 'reddit', 'youtube']);
  const [collectingId, setCollectingId] = useState<number | null>(null);

  useEffect(() => {
    loadKeywords();
  }, []);

  const loadKeywords = async () => {
    setLoading(true);
    try {
      const response = await keywordsApi.getAll();
      setKeywords(response.data);
    } catch (error) {
      console.error('Error loading keywords:', error);
      toast.error('Erreur de chargement des mots-clés');
    } finally {
      setLoading(false);
    }
  };

  const handleAddKeyword = async () => {
    if (!newKeyword.trim()) {
      toast.error('Veuillez entrer un mot-clé');
      return;
    }

    if (selectedSources.length === 0) {
      toast.error('Veuillez sélectionner au moins une source');
      return;
    }

    try {
      await keywordsApi.create(newKeyword.trim(), selectedSources);
      toast.success('Mot-clé ajouté avec succès !');
      setNewKeyword('');
      setSelectedSources(['rss', 'reddit', 'youtube']);
      setShowAddModal(false);
      loadKeywords();
    } catch (error: any) {
      console.error('Error adding keyword:', error);
      toast.error(error.response?.data?.detail || 'Erreur lors de l\'ajout');
    }
  };

  const handleDeleteKeyword = async (id: number, keyword: string) => {
    if (!confirm(`Êtes-vous sûr de vouloir supprimer "${keyword}" ?`)) {
      return;
    }

    try {
      await keywordsApi.delete(id);
      toast.success('Mot-clé supprimé');
      loadKeywords();
    } catch (error) {
      console.error('Error deleting keyword:', error);
      toast.error('Erreur lors de la suppression');
    }
  };

  const handleCollect = async (id: number) => {
    setCollectingId(id);
    try {
      await collectionApi.startForKeyword(id);
      toast.success('Collecte lancée ! Les résultats apparaîtront dans quelques instants.');
      setTimeout(() => {
        loadKeywords();
      }, 3000);
    } catch (error) {
      console.error('Error collecting:', error);
      toast.error('Erreur lors du lancement de la collecte');
    } finally {
      setCollectingId(null);
    }
  };

  const toggleSource = (sourceId: string) => {
    setSelectedSources((prev) =>
      prev.includes(sourceId)
        ? prev.filter((s) => s !== sourceId)
        : [...prev, sourceId]
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Mots-clés Surveillés
          </h1>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Gérez vos mots-clés et sources de collecte
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="btn btn-primary flex items-center space-x-2"
        >
          <Plus className="w-5 h-5" />
          <span>Ajouter un mot-clé</span>
        </button>
      </div>

      {/* Keywords List */}
      <div className="grid grid-cols-1 gap-6">
        {keywords.length === 0 ? (
          <div className="card text-center py-12">
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              Aucun mot-clé configuré
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Ajoutez votre premier mot-clé pour commencer la surveillance
            </p>
            <button
              onClick={() => setShowAddModal(true)}
              className="btn btn-primary"
            >
              Ajouter un mot-clé
            </button>
          </div>
        ) : (
          keywords.map((keyword) => (
            <KeywordCard
              key={keyword.id}
              keyword={keyword}
              onDelete={handleDeleteKeyword}
              onCollect={handleCollect}
              isCollecting={collectingId === keyword.id}
            />
          ))
        )}
      </div>

      {/* Add Keyword Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Ajouter un mot-clé
              </h2>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                Entrez le mot-clé à surveiller et sélectionnez les sources
              </p>
            </div>

            <div className="p-6 space-y-6">
              {/* Keyword Input */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Mot-clé ou expression
                </label>
                <input
                  type="text"
                  value={newKeyword}
                  onChange={(e) => setNewKeyword(e.target.value)}
                  placeholder="Ex: Tesla, iPhone 15, React tutorial..."
                  className="input"
                  autoFocus
                />
              </div>

              {/* Sources Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Sources de collecte ({selectedSources.length} sélectionnées)
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {AVAILABLE_SOURCES.map((source) => (
                    <button
                      key={source.id}
                      onClick={() => toggleSource(source.id)}
                      className={`p-4 rounded-xl border-2 transition-all ${
                        selectedSources.includes(source.id)
                          ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                      }`}
                    >
                      <div className="text-3xl mb-2">{source.icon}</div>
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {source.name}
                      </div>
                      {selectedSources.includes(source.id) && (
                        <CheckCircle className="w-5 h-5 text-primary-500 mx-auto mt-2" />
                      )}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Modal Actions */}
            <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowAddModal(false);
                  setNewKeyword('');
                  setSelectedSources(['rss', 'reddit', 'youtube']);
                }}
                className="btn btn-secondary"
              >
                Annuler
              </button>
              <button onClick={handleAddKeyword} className="btn btn-primary">
                Ajouter
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Keyword Card Component
interface KeywordCardProps {
  keyword: any;
  onDelete: (id: number, keyword: string) => void;
  onCollect: (id: number) => void;
  isCollecting: boolean;
}

function KeywordCard({ keyword, onDelete, onCollect, isCollecting }: KeywordCardProps) {
  const sources = JSON.parse(keyword.sources);

  return (
    <div className="card hover:shadow-xl transition-shadow">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-3 mb-3">
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
              {keyword.keyword}
            </h3>
            <span className="badge badge-primary">{sources.length} sources</span>
          </div>

          {/* Sources */}
          <div className="flex flex-wrap gap-2 mb-3">
            {sources.map((source: string) => {
              const sourceInfo = AVAILABLE_SOURCES.find((s) => s.id === source);
              return (
                <span
                  key={source}
                  className={`inline-flex items-center space-x-1 px-3 py-1 rounded-full text-white text-sm font-medium ${
                    sourceInfo?.color || 'bg-gray-500'
                  }`}
                >
                  <span>{sourceInfo?.icon || '📄'}</span>
                  <span>{sourceInfo?.name || source}</span>
                </span>
              );
            })}
          </div>

          {/* Metadata */}
          <div className="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
            <span className="flex items-center space-x-1">
              <Clock className="w-4 h-4" />
              <span>
                Dernière collecte:{' '}
                {keyword.last_collected ? formatDate(keyword.last_collected) : 'Jamais'}
              </span>
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center space-x-2 ml-4">
          <button
            onClick={() => onCollect(keyword.id)}
            disabled={isCollecting}
            className="btn btn-primary flex items-center space-x-2"
          >
            <Play className="w-4 h-4" />
            <span>{isCollecting ? 'Collecte...' : 'Collecter'}</span>
          </button>
          <button
            onClick={() => onDelete(keyword.id, keyword.keyword)}
            className="btn btn-danger"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}