import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  FileText,
  Download,
  Eye,
  Settings,
  Calendar,
  Check,
  X,
  Loader2,
} from 'lucide-react';
import { Card, Badge, PageLoading, Modal, Alert } from '@/components/ui/index';
import toast from 'react-hot-toast';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface KeywordOption {
  id: number;
  keyword: string;
  mentions_30d: number;
  last_collected: string | null;
}

interface ReportPreview {
  keyword: string;
  keyword_id: number;
  period_days: number;
  total_mentions: number;
  has_stats: boolean;
  has_influencers: boolean;
  has_geography: boolean;
}

export default function Reports() {
  const [selectedKeyword, setSelectedKeyword] = useState<number | null>(null);
  const [periodDays, setPeriodDays] = useState(30);
  const [selectedSections, setSelectedSections] = useState<string[]>([
    'stats',
    'influencers',
    'mentions',
    'geography',
  ]);
  const [format, setFormat] = useState<'pdf' | 'html'>('pdf');
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  // Charger les mots-clés disponibles
  const { data: keywordsData, isLoading: loadingKeywords } = useQuery({
    queryKey: ['availableKeywords'],
    queryFn: async () => {
      const response = await axios.get<{ keywords: KeywordOption[] }>(
        `${API_BASE_URL}/api/reports/keywords-available`
      );
      return response.data;
    },
  });

  // Prévisualisation du rapport
  const { data: previewData, refetch: refetchPreview } = useQuery<ReportPreview>({
    queryKey: ['reportPreview', selectedKeyword, periodDays],
    queryFn: async () => {
      if (!selectedKeyword) return null;
      const response = await axios.get(
        `${API_BASE_URL}/api/reports/preview/${selectedKeyword}?days=${periodDays}`
      );
      return response.data;
    },
    enabled: !!selectedKeyword,
  });

  const sections = [
    {
      id: 'stats',
      name: 'Statistiques',
      description: 'Vue d\'ensemble, sentiment, sources',
      icon: '📊',
    },
    {
      id: 'influencers',
      name: 'Influenceurs',
      description: 'Top influenceurs et leur impact',
      icon: '👑',
    },
    {
      id: 'mentions',
      name: 'Mentions',
      description: 'Détails des mentions et auteurs',
      icon: '💬',
    },
    {
      id: 'geography',
      name: 'Géographie',
      description: 'Distribution géographique',
      icon: '🌍',
    },
  ];

  const toggleSection = (sectionId: string) => {
    setSelectedSections((prev) =>
      prev.includes(sectionId)
        ? prev.filter((s) => s !== sectionId)
        : [...prev, sectionId]
    );
  };

  const handleGenerateReport = async () => {
    if (!selectedKeyword) {
      toast.error('Veuillez sélectionner un mot-clé');
      return;
    }

    if (selectedSections.length === 0) {
      toast.error('Veuillez sélectionner au moins une section');
      return;
    }

    setIsGenerating(true);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/reports/generate`,
        {
          keyword_id: selectedKeyword,
          days: periodDays,
          include_sections: selectedSections,
          format: format,
        },
        {
          responseType: format === 'pdf' ? 'blob' : 'text',
        }
      );

      if (format === 'pdf') {
        // Télécharger le PDF
        const blob = new Blob([response.data], { type: 'application/pdf' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        const keyword = keywordsData?.keywords.find((k) => k.id === selectedKeyword);
        link.download = `rapport_${keyword?.keyword}_${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);

        toast.success('Rapport PDF généré avec succès !');
      } else {
        // Ouvrir HTML dans nouvel onglet
        const blob = new Blob([response.data], { type: 'text/html' });
        const url = window.URL.createObjectURL(blob);
        window.open(url, '_blank');
        toast.success('Rapport HTML généré !');
      }
    } catch (error) {
      console.error('Erreur génération rapport:', error);
      toast.error('Erreur lors de la génération du rapport');
    } finally {
      setIsGenerating(false);
    }
  };

  const handlePreview = () => {
    if (!selectedKeyword) {
      toast.error('Veuillez sélectionner un mot-clé');
      return;
    }
    setShowPreviewModal(true);
    refetchPreview();
  };

  if (loadingKeywords) {
    return <PageLoading message="Chargement des mots-clés..." />;
  }

  const keywords = keywordsData?.keywords || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          📄 Génération de Rapports
        </h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Créez des rapports PDF professionnels pour vos mots-clés
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Configuration */}
        <div className="lg:col-span-2 space-y-6">
          {/* Sélection mot-clé */}
          <Card>
            <div className="flex items-center space-x-3 mb-4">
              <FileText className="w-6 h-6 text-primary-500" />
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                Sélection du mot-clé
              </h2>
            </div>

            {keywords.length === 0 ? (
              <Alert type="info">
                Aucun mot-clé disponible. Ajoutez des mots-clés dans la section dédiée.
              </Alert>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {keywords.map((keyword) => (
                  <button
                    key={keyword.id}
                    onClick={() => setSelectedKeyword(keyword.id)}
                    className={`p-4 rounded-xl border-2 text-left transition-all ${
                      selectedKeyword === keyword.id
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <span className="font-semibold text-gray-900 dark:text-white">
                        {keyword.keyword}
                      </span>
                      {selectedKeyword === keyword.id && (
                        <Check className="w-5 h-5 text-primary-500" />
                      )}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      {keyword.mentions_30d} mentions (30j)
                    </div>
                  </button>
                ))}
              </div>
            )}
          </Card>

          {/* Période */}
          <Card>
            <div className="flex items-center space-x-3 mb-4">
              <Calendar className="w-6 h-6 text-primary-500" />
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                Période d'analyse
              </h2>
            </div>

            <div className="grid grid-cols-4 gap-3">
              {[7, 14, 30, 90].map((days) => (
                <button
                  key={days}
                  onClick={() => setPeriodDays(days)}
                  className={`px-4 py-3 rounded-lg font-medium transition-colors ${
                    periodDays === days
                      ? 'bg-primary-500 text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                >
                  {days} jours
                </button>
              ))}
            </div>
          </Card>

          {/* Sections à inclure */}
          <Card>
            <div className="flex items-center space-x-3 mb-4">
              <Settings className="w-6 h-6 text-primary-500" />
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                Sections à inclure
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {sections.map((section) => (
                <button
                  key={section.id}
                  onClick={() => toggleSection(section.id)}
                  className={`p-4 rounded-xl border-2 text-left transition-all ${
                    selectedSections.includes(section.id)
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-2xl">{section.icon}</span>
                      <span className="font-semibold text-gray-900 dark:text-white">
                        {section.name}
                      </span>
                    </div>
                    {selectedSections.includes(section.id) ? (
                      <Check className="w-5 h-5 text-primary-500" />
                    ) : (
                      <X className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {section.description}
                  </p>
                </button>
              ))}
            </div>
          </Card>

          {/* Format */}
          <Card>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              Format de sortie
            </h2>

            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => setFormat('pdf')}
                className={`p-4 rounded-xl border-2 text-left transition-all ${
                  format === 'pdf'
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-2xl">📄</span>
                  {format === 'pdf' && <Check className="w-5 h-5 text-primary-500" />}
                </div>
                <div className="font-semibold text-gray-900 dark:text-white">PDF</div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Format professionnel, prêt à imprimer
                </p>
              </button>

              <button
                onClick={() => setFormat('html')}
                className={`p-4 rounded-xl border-2 text-left transition-all ${
                  format === 'html'
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-2xl">🌐</span>
                  {format === 'html' && <Check className="w-5 h-5 text-primary-500" />}
                </div>
                <div className="font-semibold text-gray-900 dark:text-white">HTML</div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Prévisualisation web interactive
                </p>
              </button>
            </div>
          </Card>
        </div>

        {/* Résumé et actions */}
        <div className="space-y-6">
          <Card className="sticky top-6">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
              📋 Résumé
            </h3>

            <div className="space-y-4">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Mot-clé</p>
                <p className="font-semibold text-gray-900 dark:text-white">
                  {selectedKeyword
                    ? keywords.find((k) => k.id === selectedKeyword)?.keyword
                    : 'Non sélectionné'}
                </p>
              </div>

              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Période</p>
                <p className="font-semibold text-gray-900 dark:text-white">
                  {periodDays} derniers jours
                </p>
              </div>

              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Sections</p>
                <div className="flex flex-wrap gap-2">
                  {selectedSections.map((sectionId) => {
                    const section = sections.find((s) => s.id === sectionId);
                    return (
                      <Badge key={sectionId} variant="primary">
                        {section?.icon} {section?.name}
                      </Badge>
                    );
                  })}
                </div>
              </div>

              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Format</p>
                <p className="font-semibold text-gray-900 dark:text-white uppercase">
                  {format}
                </p>
              </div>

              {previewData && (
                <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                    Mentions trouvées
                  </p>
                  <p className="text-3xl font-bold text-primary-500">
                    {previewData.total_mentions}
                  </p>
                </div>
              )}
            </div>

            <div className="mt-6 space-y-3">
              <button
                onClick={handlePreview}
                disabled={!selectedKeyword}
                className="btn btn-secondary w-full flex items-center justify-center space-x-2"
              >
                <Eye className="w-4 h-4" />
                <span>Prévisualiser</span>
              </button>

              <button
                onClick={handleGenerateReport}
                disabled={!selectedKeyword || selectedSections.length === 0 || isGenerating}
                className="btn btn-primary w-full flex items-center justify-center space-x-2"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Génération...</span>
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4" />
                    <span>Générer le rapport</span>
                  </>
                )}
              </button>
            </div>
          </Card>

          {/* Conseils */}
          <Card className="bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-200 dark:border-blue-800">
            <div className="flex items-start space-x-3">
              <div className="text-2xl">💡</div>
              <div>
                <h4 className="font-semibold text-blue-900 dark:text-blue-200 mb-2">
                  Conseils
                </h4>
                <ul className="text-sm text-blue-800 dark:text-blue-300 space-y-1">
                  <li>• Sélectionnez une période pertinente (30 jours recommandé)</li>
                  <li>• Incluez toutes les sections pour un rapport complet</li>
                  <li>• Le format PDF est idéal pour l'impression et le partage</li>
                  <li>• Les rapports peuvent prendre quelques secondes à générer</li>
                </ul>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Modal de prévisualisation */}
      {showPreviewModal && previewData && (
        <Modal
          isOpen={showPreviewModal}
          onClose={() => setShowPreviewModal(false)}
          title="Prévisualisation du rapport"
          size="lg"
        >
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Mot-clé</p>
                <p className="text-xl font-bold text-gray-900 dark:text-white">
                  {previewData.keyword}
                </p>
              </div>

              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                  Total mentions
                </p>
                <p className="text-xl font-bold text-gray-900 dark:text-white">
                  {previewData.total_mentions}
                </p>
              </div>
            </div>

            <div>
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Sections disponibles
              </p>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { key: 'has_stats', label: 'Statistiques', icon: '📊' },
                  { key: 'has_influencers', label: 'Influenceurs', icon: '👑' },
                  { key: 'has_geography', label: 'Géographie', icon: '🌍' },
                ].map((item) => (
                  <div
                    key={item.key}
                    className={`p-3 rounded-lg ${
                      previewData[item.key as keyof ReportPreview]
                        ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
                        : 'bg-gray-50 dark:bg-gray-700'
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">{item.icon}</span>
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {item.label}
                      </span>
                      {previewData[item.key as keyof ReportPreview] ? (
                        <Check className="w-4 h-4 text-green-500 ml-auto" />
                      ) : (
                        <X className="w-4 h-4 text-gray-400 ml-auto" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {previewData.total_mentions === 0 && (
              <Alert type="warning">
                Aucune mention trouvée pour cette période. Le rapport sera vide.
              </Alert>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
}