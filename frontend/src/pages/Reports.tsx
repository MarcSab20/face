import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Brain,
  Download,
  Eye,
  Settings,
  Calendar,
  Check,
  X,
  Loader2,
  Plus,
  Zap,
  AlertTriangle,
  TrendingUp,
  Users,
  MapPin,
  Target,
  BarChart3,
  MessageSquare,
  Shield,
  Globe,
  Sparkles,
  Cpu,
  Activity
} from 'lucide-react';
import { Card, Badge, PageLoading, Modal, Alert, Tabs } from '@/components/ui/index';
import toast from 'react-hot-toast';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface KeywordOption {
  id: number;
  keyword: string;
  mentions_30d: number;
  last_collected: string | null;
}

interface IntelligentReportPreview {
  keywords: string[];
  keyword_ids: number[];
  period_days: number;
  total_mentions: number;
  estimated_web_sources: number;
  ai_models_available: string[];
  processing_time_estimate: string;
  risk_level_preview?: string;
}

interface AIModelStatus {
  name: string;
  available: boolean;
  description: string;
  performance: string;
}

interface AICapability {
  name: string;
  description: string;
  agent: string;
  features: string[];
}

export default function IntelligentReports() {
  const [selectedKeywords, setSelectedKeywords] = useState<number[]>([]);
  const [periodDays, setPeriodDays] = useState(30);
  const [reportObject, setReportObject] = useState('');
  const [includeWebAnalysis, setIncludeWebAnalysis] = useState(true);
  const [aiModel, setAiModel] = useState('mistral:7b');
  const [format, setFormat] = useState<'pdf' | 'html'>('pdf');
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [showAIStatusModal, setShowAIStatusModal] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [previewData, setPreviewData] = useState<IntelligentReportPreview | null>(null);
  const [activeTab, setActiveTab] = useState<'config' | 'ai-status' | 'capabilities' | 'examples'>('config');

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

  // Charger le statut de l'IA
  const { data: aiStatusData } = useQuery({
    queryKey: ['aiStatus'],
    queryFn: async () => {
      const response = await axios.get<{
        ai_service_available: boolean;
        models: AIModelStatus[];
        recommendation: string;
      }>(`${API_BASE_URL}/api/intelligent-reports/ai-status`);
      return response.data;
    },
  });

  // Charger les capacités IA
  const { data: capabilitiesData } = useQuery({
    queryKey: ['aiCapabilities'],
    queryFn: async () => {
      const response = await axios.get(
        `${API_BASE_URL}/api/intelligent-reports/capabilities`
      );
      return response.data;
    },
  });

  // Charger les exemples
  const { data: examplesData } = useQuery({
    queryKey: ['aiExamples'],
    queryFn: async () => {
      const response = await axios.get(
        `${API_BASE_URL}/api/intelligent-reports/examples`
      );
      return response.data;
    },
  });

  const keywords = keywordsData?.keywords || [];

  const toggleKeyword = (keywordId: number) => {
    setSelectedKeywords((prev) =>
      prev.includes(keywordId)
        ? prev.filter((id) => id !== keywordId)
        : [...prev, keywordId]
    );
  };

  const handleGenerateReport = async () => {
    if (selectedKeywords.length === 0) {
      toast.error('Veuillez sélectionner au moins un mot-clé');
      return;
    }

    if (!reportObject.trim()) {
      toast.error('Veuillez saisir l\'objet du rapport');
      return;
    }

    if (!aiStatusData?.ai_service_available) {
      toast.error('Service IA non disponible. Vérifiez la configuration.');
      return;
    }

    setIsGenerating(true);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/intelligent-reports/generate`,
        {
          keyword_ids: selectedKeywords,
          days: periodDays,
          report_object: reportObject,
          include_web_analysis: includeWebAnalysis,
          ai_model: aiModel,
          format: format,
        },
        {
          responseType: format === 'pdf' ? 'blob' : 'text',
        }
      );

      if (format === 'pdf') {
        // Télécharger le PDF intelligent
        const blob = new Blob([response.data], { type: 'application/pdf' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `rapport_intelligent_${reportObject.substring(0, 30)}_${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);

        toast.success('🤖 Rapport intelligent généré avec succès !');
      } else {
        // Ouvrir HTML dans nouvel onglet
        const blob = new Blob([response.data], { type: 'text/html' });
        const url = window.URL.createObjectURL(blob);
        window.open(url, '_blank');
        toast.success('🤖 Rapport intelligent HTML généré !');
      }
    } catch (error) {
      console.error('Erreur génération rapport intelligent:', error);
      toast.error('Erreur lors de la génération du rapport intelligent');
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
      const response = await axios.post<IntelligentReportPreview>(
        `${API_BASE_URL}/api/intelligent-reports/preview`,
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

  const getRiskColor = (riskLevel?: string) => {
    switch (riskLevel) {
      case 'ÉLEVÉ': return 'text-red-600';
      case 'MODÉRÉ': return 'text-yellow-600';
      case 'FAIBLE': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  if (loadingKeywords) {
    return <PageLoading message="Chargement de l'interface IA..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center">
          🤖 Rapports Intelligents IA
          <Badge variant="primary" >
            <Sparkles className="w-4 h-4 mr-1" />
            IA Souveraine
          </Badge>
        </h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Génération automatique de rapports avec analyse IA avancée et lecture web
        </p>
      </div>

      {/* Alerte statut IA */}
      {aiStatusData && !aiStatusData.ai_service_available && (
        <Alert type="warning">
          <Brain className="w-4 h-4" />
          <span>Service IA non disponible. {aiStatusData.recommendation}</span>
        </Alert>
      )}

      {/* Tabs */}
      <Tabs
        tabs={[
          { id: 'config', label: 'Configuration', icon: Settings },
          { id: 'ai-status', label: 'Statut IA', icon: Brain },
          { id: 'capabilities', label: 'Capacités', icon: Zap },
          { id: 'examples', label: 'Exemples', icon: Eye },
        ]}
        activeTab={activeTab}
        onChange={(id) => setActiveTab(id as any)}
      />

      {/* Tab Content */}
      {activeTab === 'config' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Configuration */}
          <div className="lg:col-span-2 space-y-6">
            {/* Objet du rapport */}
            <Card>
              <div className="flex items-center space-x-3 mb-4">
                <Target className="w-6 h-6 text-primary-500" />
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                  Objet du rapport intelligent
                </h2>
              </div>
              
              <input
                type="text"
                value={reportObject}
                onChange={(e) => setReportObject(e.target.value)}
                placeholder="Ex: Analyse IA de l'opinion publique sur le projet X..."
                className="input"
                maxLength={200}
              />
              <p className="text-xs text-gray-500 mt-1">
                Décrivez l'objectif de votre analyse IA (max 200 caractères)
              </p>
            </Card>

            {/* Sélection mots-clés */}
            <Card>
              <div className="flex items-center space-x-3 mb-4">
                <MessageSquare className="w-6 h-6 text-primary-500" />
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                  Mots-clés pour l'analyse IA
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
                    🤖 L'IA analysera automatiquement le contenu de ces mots-clés
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

            {/* Configuration IA */}
            <Card>
              <div className="flex items-center space-x-3 mb-4">
                <Brain className="w-6 h-6 text-primary-500" />
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                  Configuration IA
                </h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Période */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    <Calendar className="w-4 h-4 inline mr-1" />
                    Période d'analyse
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    {[7, 14, 30, 90].map((days) => (
                      <button
                        key={days}
                        onClick={() => setPeriodDays(days)}
                        className={`px-3 py-2 rounded-lg font-medium transition-colors text-sm ${
                          periodDays === days
                            ? 'bg-primary-500 text-white'
                            : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                        }`}
                      >
                        {days}j
                      </button>
                    ))}
                  </div>
                </div>

                {/* Modèle IA */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    <Cpu className="w-4 h-4 inline mr-1" />
                    Modèle IA
                  </label>
                  <select
                    value={aiModel}
                    onChange={(e) => setAiModel(e.target.value)}
                    className="input"
                  >
                    <option value="mistral:7b">Mistral 7B (Recommandé)</option>
                    <option value="llama2:7b">Llama 2 7B</option>
                    <option value="codellama:7b">CodeLlama 7B</option>
                    <option value="neural-chat:7b">Neural Chat 7B</option>
                  </select>
                </div>
              </div>

              {/* Options avancées */}
              <div className="mt-4 space-y-3">
                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={includeWebAnalysis}
                    onChange={(e) => setIncludeWebAnalysis(e.target.checked)}
                    className="w-5 h-5 text-primary-500 rounded focus:ring-primary-500"
                  />
                  <div>
                    <span className="font-medium text-gray-900 dark:text-white">
                      <Globe className="w-4 h-4 inline mr-1" />
                      Analyse web approfondie
                    </span>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      L'IA lira et analysera le contenu des articles et commentaires
                    </p>
                  </div>
                </label>
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
                  <div className="font-semibold text-gray-900 dark:text-white">PDF Intelligent</div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Rapport professionnel avec analyses IA complètes
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
                  <div className="font-semibold text-gray-900 dark:text-white">HTML Interactif</div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Prévisualisation web avec insights IA
                  </p>
                </button>
              </div>
            </Card>
          </div>

          {/* Résumé et actions */}
          <div className="space-y-6">
            <Card className="sticky top-6">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center">
                🤖 Résumé Rapport IA
                {aiStatusData?.ai_service_available && (
                  <Badge variant="success" size="sm" >
                    <Activity className="w-3 h-3 mr-1" />
                    IA Active
                  </Badge>
                )}
              </h3>

              <div className="space-y-4">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Objet</p>
                  <p className="font-semibold text-gray-900 dark:text-white text-sm">
                    {reportObject || 'Non renseigné'}
                  </p>
                </div>

                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Mots-clés IA</p>
                  <div className="flex flex-wrap gap-2">
                    {selectedKeywords.length === 0 ? (
                      <span className="text-gray-500 text-sm">Aucun sélectionné</span>
                    ) : (
                      selectedKeywords.map((id) => {
                        const kw = keywords.find((k) => k.id === id);
                        return kw ? (
                          <Badge key={id} variant="primary" size="sm">
                            🤖 {kw.keyword}
                          </Badge>
                        ) : null;
                      })
                    )}
                  </div>
                </div>

                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Configuration</p>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span>Période:</span>
                      <span className="font-medium">{periodDays} jours</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Modèle IA:</span>
                      <span className="font-medium">{aiModel}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Web Analysis:</span>
                      <span className="font-medium">{includeWebAnalysis ? '✅ Oui' : '❌ Non'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Format:</span>
                      <span className="font-medium uppercase">{format}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-6 space-y-3">
                <button
                  onClick={handlePreview}
                  disabled={selectedKeywords.length === 0}
                  className="btn btn-secondary w-full flex items-center justify-center space-x-2"
                >
                  <Eye className="w-4 h-4" />
                  <span>Prévisualiser IA</span>
                </button>

                <button
                  onClick={handleGenerateReport}
                  disabled={
                    selectedKeywords.length === 0 ||
                    !reportObject.trim() ||
                    isGenerating ||
                    !aiStatusData?.ai_service_available
                  }
                  className="btn btn-primary w-full flex items-center justify-center space-x-2"
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>IA en cours...</span>
                    </>
                  ) : (
                    <>
                      <Brain className="w-4 h-4" />
                      <span>Générer avec IA</span>
                    </>
                  )}
                </button>
              </div>
            </Card>

            {/* Aide IA */}
            <Card className="bg-gradient-to-br from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 border-2 border-purple-200 dark:border-purple-800">
              <div className="flex items-start space-x-3">
                <div className="text-2xl">🧠</div>
                <div>
                  <h4 className="font-semibold text-purple-900 dark:text-purple-200 mb-2">
                    Intelligence Artificielle Souveraine
                  </h4>
                  <ul className="text-sm text-purple-800 dark:text-purple-300 space-y-1">
                    <li><strong>🔍 Analyse web:</strong> Lecture automatique des sources</li>
                    <li><strong>💭 Sentiment IA:</strong> Nuances émotionnelles avancées</li>
                    <li><strong>📈 Tendances:</strong> Détection de signaux faibles</li>
                    <li><strong>👑 Influenceurs:</strong> Évaluation de risque intelligente</li>
                    <li><strong>🎯 Recommandations:</strong> Actions basées sur l'IA</li>
                    <li><strong>🔒 Authenticité:</strong> Détection de contenu suspect</li>
                  </ul>
                </div>
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* Tab Statut IA */}
      {activeTab === 'ai-status' && aiStatusData && (
        <div className="space-y-6">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Statut du Service IA
              </h2>
              <Badge variant={aiStatusData.ai_service_available ? 'success' : 'danger'}>
                {aiStatusData.ai_service_available ? '🟢 Actif' : '🔴 Inactif'}
              </Badge>
            </div>

            <p className="text-gray-700 dark:text-gray-300 mb-6">
              {aiStatusData.recommendation}
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {aiStatusData.models.map((model, index) => (
                <div key={index} className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-gray-900 dark:text-white">
                      {model.name}
                    </h4>
                    <Badge variant={model.available ? 'success' : 'danger'} size="sm">
                      {model.available ? '✅' : '❌'}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                    {model.description}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500">
                    Performance: {model.performance}
                  </p>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Tab Capacités */}
      {activeTab === 'capabilities' && capabilitiesData && (
        <div className="space-y-6">
          <Card>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
              Capacités d'Analyse IA
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              {capabilitiesData.analysis_types?.map((capability: AICapability, index: number) => (
                <div key={index} className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                    {capability.name}
                  </h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                    {capability.description}
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {capability.features.map((feature, fIndex) => (
                      <Badge key={fIndex} variant="primary" size="sm">
                        {feature}
                      </Badge>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <h3 className="font-semibold text-blue-900 dark:text-blue-200 mb-2">
                🌐 Analyse Web Avancée
              </h3>
              <p className="text-sm text-blue-800 dark:text-blue-300 mb-3">
                {capabilitiesData.web_analysis?.description}
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="font-medium text-blue-900 dark:text-blue-200 mb-2">Fonctionnalités:</h4>
                  <ul className="text-sm text-blue-800 dark:text-blue-300 space-y-1">
                    {capabilitiesData.web_analysis?.features?.map((feature: string, index: number) => (
                      <li key={index}>• {feature}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4 className="font-medium text-blue-900 dark:text-blue-200 mb-2">Limitations:</h4>
                  <ul className="text-sm text-blue-800 dark:text-blue-300 space-y-1">
                    {capabilitiesData.web_analysis?.limitations?.map((limitation: string, index: number) => (
                      <li key={index}>• {limitation}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Tab Exemples */}
      {activeTab === 'examples' && examplesData && (
        <div className="space-y-6">
          <Card>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
              Exemples d'Analyses IA
            </h2>

            <div className="space-y-6">
              {Object.entries(examplesData.sample_analyses || {}).map(([type, example]: [string, any]) => (
                <div key={type} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-2 capitalize">
                    {type.replace('_', ' ')}
                  </h4>
                  <div className="space-y-2">
                    <div>
                      <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Input:</span>
                      <p className="text-sm text-gray-700 dark:text-gray-300 italic">
                        "{example.input}"
                      </p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Analyse IA:</span>
                      <p className="text-sm text-gray-900 dark:text-white">
                        {example.output}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 mt-6">
              <h3 className="font-semibold text-green-900 dark:text-green-200 mb-2">
                💡 Insights IA Avancés
              </h3>
              <ul className="text-sm text-green-800 dark:text-green-300 space-y-1">
                {examplesData.ai_insights_examples?.map((insight: string, index: number) => (
                  <li key={index}>• {insight}</li>
                ))}
              </ul>
            </div>
          </Card>
        </div>
      )}

      {/* Modal de prévisualisation intelligent */}
      {showPreviewModal && previewData && (
        <Modal
          isOpen={showPreviewModal}
          onClose={() => setShowPreviewModal(false)}
          title="🤖 Prévisualisation Rapport Intelligent"
          size="lg"
        >
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Mots-clés IA</p>
                <div className="flex flex-wrap gap-1">
                  {previewData.keywords.map((kw) => (
                    <Badge key={kw} variant="primary" size="sm">
                      🤖 {kw}
                    </Badge>
                  ))}
                </div>
              </div>

              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                  Données à analyser
                </p>
                <p className="text-xl font-bold text-gray-900 dark:text-white">
                  {previewData.total_mentions} mentions
                </p>
                <p className="text-xs text-gray-500">
                  + {previewData.estimated_web_sources} sources web
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <p className="text-sm text-blue-600 dark:text-blue-400 mb-1">
                  Modèles IA disponibles
                </p>
                <div className="space-y-1">
                  {previewData.ai_models_available.map((model, index) => (
                    <div key={index} className="text-sm text-blue-800 dark:text-blue-300">
                      ✓ {model}
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                <p className="text-sm text-purple-600 dark:text-purple-400 mb-1">
                  Temps de traitement estimé
                </p>
                <p className="text-lg font-bold text-purple-900 dark:text-purple-200">
                  ⏱️ {previewData.processing_time_estimate}
                </p>
              </div>
            </div>

            {previewData.risk_level_preview && (
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                  Niveau de risque préliminaire (IA)
                </p>
                <p className={`text-lg font-bold ${getRiskColor(previewData.risk_level_preview)}`}>
                  <Shield className="w-5 h-5 inline mr-2" />
                  {previewData.risk_level_preview}
                </p>
              </div>
            )}

            {previewData.total_mentions === 0 && (
              <Alert type="warning">
                Aucune mention trouvée pour cette période. Le rapport IA sera limité.
              </Alert>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
}