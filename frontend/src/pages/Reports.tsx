import { useState } from 'react';
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
  Plus,
  Trash2,
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
  keywords: string[];
  keyword_ids: number[];
  period_days: number;
  total_mentions: number;
  has_analysis: boolean;
  has_influencers: boolean;
}

export default function ReportsV2() {
  const [selectedKeywords, setSelectedKeywords] = useState<number[]>([]);
  const [periodDays, setPeriodDays] = useState(30);
  const [reportObject, setReportObject] = useState('');
  const [selectedSections, setSelectedSections] = useState<string[]>([
    'analysis',
    'influencers',
  ]);
  const [format, setFormat] = useState<'pdf' | 'html'>('pdf');
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [previewData, setPreviewData] = useState<ReportPreview | null>(null);

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

  const sections = [
    {
      id: 'analysis',
      name: 'Analyse Détaillée',
      description: 'Réponses aux questions stratégiques',
      icon: '📊',
    },
    {
      id: 'influencers',
      name: 'Top Influenceurs',
      description: 'Tableau des comptes les plus engagés',
      icon: '👑',
    },
  ];

  const toggleKeyword = (keywordId: number) => {
    setSelectedKeywords((prev) =>
      prev.includes(keywordId)
        ? prev.filter((id) => id !== keywordId)
        : [...prev, keywordId]
    );
  };

  const toggleSection = (sectionId: string) => {
    setSelectedSections((prev) =>
      prev.includes(sectionId)
        ? prev.filter((s) => s !== sectionId)
        : [...prev, sectionId]
    );
  };

  const handleGenerateReport = async () => {
    if (selectedKeywords.length === 0) {
      toast.error('Veuillez sélectionner au moins un mot-clé');
      return;
    }

    if (selectedSections.length === 0) {
      toast.error('Veuillez sélectionner au moins une section');
      return;
    }

    if (!reportObject.trim()) {
      toast.error('Veuillez saisir l\'objet du rapport');
      return;
    }

    setIsGenerating(true);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/reports/generate`,
        {
          keyword_ids: selectedKeywords,
          days: periodDays,
          report_object: reportObject,
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
        link.download = `rapport_${reportObject.substring(0, 30)}_${new Date().toISOString().split('T')[0]}.pdf`;
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

  const handlePreview = async () => {
    if (selectedKeywords.length === 0) {
      toast.error('Veuillez sélectionner au moins un mot-clé');
      return;
    }

    try {
      const response = await axios.post<ReportPreview>(
        `${API_BASE_URL}/api/reports/preview`,
        selectedKeywords,
        {
          params: { days: periodDays }
        }
      );
      setPreviewData(response.data);
      setShowPreviewModal(true);
    } catch (error) {
      toast.error('Erreur lors de la prévisualisation');
    }
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
          📄 Génération de Rapports Avancés
        </h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Rapports analytiques sur 2 pages avec analyse détaillée
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Configuration */}
        <div className="lg:col-span-2 space-y-6">
          {/* Objet du rapport */}
          <Card>
            <div className="flex items-center space-x-3 mb-4">
              <FileText className="w-6 h-6 text-primary-500" />
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                Objet du rapport
              </h2>
            </div>
            
            <input
              type="text"
              value={reportObject}
              onChange={(e) => setReportObject(e.target.value)}
              placeholder="Ex: Évaluation de la réception du projet X, Analyse sentiment campagne Y..."
              className="input"
              maxLength={200}
            />
            <p className="text-xs text-gray-500 mt-1">
              Cet objet apparaîtra en en-tête du rapport (max 200 caractères)
            </p>
          </Card>

          {/* Sélection mots-clés (MULTI) */}
          <Card>
            <div className="flex items-center space-x-3 mb-4">
              <Settings className="w-6 h-6 text-primary-500" />
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                Sélection des mots-clés
              </h2>
              <Badge variant="primary">
                {selectedKeywords.length} sélectionné{selectedKeywords.length > 1 ? 's' : ''}
              </Badge>
            </div>

            {keywords.length === 0 ? (
              <Alert type="info">
                Aucun mot-clé disponible. Ajoutez des mots-clés dans la section dédiée.
              </Alert>
            ) : (
              <>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  💡 Sélectionnez un ou plusieurs mots-clés pour combiner l'analyse
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {keywords.map((keyword) => (
                    <button
                      key={keyword.id}
                      onClick={() => toggleKeyword(keyword.id)}
                      className={`p-4 rounded-xl border-2 text-left transition-all ${
                        selectedKeywords.includes(keyword.id)
                          ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <span className="font-semibold text-gray-900 dark:text-white">
                          {keyword.keyword}
                        </span>
                        {selectedKeywords.includes(keyword.id) ? (
                          <Check className="w-5 h-5 text-primary-500" />
                        ) : (
                          <Plus className="w-5 h-5 text-gray-400" />
                        )}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        {keyword.mentions_30d} mentions (30j)
                      </div>
                    </button>
                  ))}
                </div>
              </>
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

          {/* Sections */}
          <Card>
            <div className="flex items-center space-x-3 mb-4">
              <FileText className="w-6 h-6 text-primary-500" />
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                Sections à inclure
              </h2>
            </div>

            <div className="space-y-3">
              {sections.map((section) => (
                <button
                  key={section.id}
                  onClick={() => toggleSection(section.id)}
                  className={`w-full p-4 rounded-xl border-2 text-left transition-all ${
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
                  Format professionnel, 2 pages
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
                  Prévisualisation web
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
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Objet</p>
                <p className="font-semibold text-gray-900 dark:text-white text-sm">
                  {reportObject || 'Non renseigné'}
                </p>
              </div>

              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Mots-clés</p>
                <div className="flex flex-wrap gap-2">
                  {selectedKeywords.length === 0 ? (
                    <span className="text-gray-500 text-sm">Aucun sélectionné</span>
                  ) : (
                    selectedKeywords.map((id) => {
                      const kw = keywords.find((k) => k.id === id);
                      return kw ? (
                        <Badge key={id} variant="primary">
                          {kw.keyword}
                        </Badge>
                      ) : null;
                    })
                  )}
                </div>
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
            </div>

            <div className="mt-6 space-y-3">
              <button
                onClick={handlePreview}
                disabled={selectedKeywords.length === 0}
                className="btn btn-secondary w-full flex items-center justify-center space-x-2"
              >
                <Eye className="w-4 h-4" />
                <span>Prévisualiser</span>
              </button>

              <button
                onClick={handleGenerateReport}
                disabled={
                  selectedKeywords.length === 0 ||
                  selectedSections.length === 0 ||
                  !reportObject.trim() ||
                  isGenerating
                }
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

          {/* Aide */}
          <Card className="bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-200 dark:border-blue-800">
            <div className="flex items-start space-x-3">
              <div className="text-2xl">💡</div>
              <div>
                <h4 className="font-semibold text-blue-900 dark:text-blue-200 mb-2">
                  Structure du rapport
                </h4>
                <ul className="text-sm text-blue-800 dark:text-blue-300 space-y-1">
                  <li><strong>Page 1:</strong> Analyse détaillée avec réponses aux questions stratégiques et synthèse</li>
                  <li><strong>Page 2:</strong> Tableau des top influenceurs les plus engagés</li>
                  <li>• Combinez plusieurs mots-clés pour une analyse groupée</li>
                  <li>• L'objet du rapport apparaît en en-tête</li>
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
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Mots-clés</p>
                <div className="flex flex-wrap gap-1">
                  {previewData.keywords.map((kw) => (
                    <Badge key={kw} variant="primary">
                      {kw}
                    </Badge>
                  ))}
                </div>
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
                  { key: 'has_analysis', label: 'Analyse Détaillée', icon: '📊' },
                  { key: 'has_influencers', label: 'Top Influenceurs', icon: '👑' },
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