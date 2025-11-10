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

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';;
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 600000, // 5 minutes pour l'IA
  headers: {
    'Content-Type': 'application/json',
  },
});

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
  sources_distribution: Record<string, number>;
  sentiment_preview: {
    distribution: Record<string, number>;
    negative_ratio: number;
    dominant: string;
  };
  processing_time_estimate: string;
  confidence_score: number;
  risk_indicators: string[];
}

interface AIServiceStatus {
  ai_available: boolean;
  ollama_status: string;
  transformers_status: string;
  models_available: string[];
  recommendation: string;
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
  const [reportTitle, setReportTitle] = useState('');
  const [includeWebAnalysis, setIncludeWebAnalysis] = useState(true);
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
        `${API_BASE_URL}/api/intelligent-reports/keywords-available`
      );
      return response.data;
    },
  });

  // Charger le statut de l'IA
  const { data: aiStatusData } = useQuery({
    queryKey: ['aiStatus'],
    queryFn: async () => {
      const response = await axios.get<AIServiceStatus>(
        `${API_BASE_URL}/api/intelligent-reports/ai-status`
      );
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

    if (!reportTitle.trim()) {
      toast.error('Veuillez saisir le titre du rapport');
      return;
    }

    if (!aiStatusData?.ai_available) {
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
          report_title: reportTitle,
          include_web_analysis: includeWebAnalysis,
          format: format,
        },
        {
          responseType: 'blob', // Important pour recevoir les fichiers binaires
        }
      );

      // Télécharger le fichier
      const blob = new Blob([response.data], { 
        type: format === 'pdf' ? 'application/pdf' : 'text/html' 
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const timestamp = new Date().toISOString().split('T')[0];
      link.download = `rapport_intelligent_${timestamp}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      toast.success('🤖 Rapport intelligent généré avec succès !');
    } catch (error: any) {
      console.error('Erreur génération rapport intelligent:', error);
      const errorMsg = error.response?.data?.detail || 'Erreur lors de la génération du rapport intelligent';
      toast.error(errorMsg);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleGenerateExecutiveReport = async () => {
  if (selectedKeywords.length === 0 || !reportTitle.trim()) {
    toast.error('Veuillez sélectionner des mots-clés et saisir un titre');
    return;
  }

  if (!aiStatusData?.ai_available) {
    toast.error('Service IA non disponible. Vérifiez la configuration.');
    return;
  }

  setIsGenerating(true);
  
  // Toast avec progression
  const loadingToast = toast.loading(
    '🤖 Analyse IA en cours... Lecture des contenus, classification, synthèse... Patientez 2-5 min',
    { duration: 600000 }
  );

  try {
    console.log('🚀 Début génération rapport exécutif');
    console.log('Mots-clés:', selectedKeywords);
    console.log('Période:', periodDays);
    
    const response = await apiClient.post(
      '/api/intelligent-reports/generate-executive',
      {
        keyword_ids: selectedKeywords,
        days: periodDays,
        report_title: reportTitle,
        format: format,
      },
      {
        responseType: 'blob',
        onDownloadProgress: (progressEvent) => {
          if (progressEvent.loaded > 0) {
            toast.loading('📥 Réception du rapport...', { id: loadingToast });
          }
        }
      }
    );

    console.log('✅ Rapport reçu, taille:', response.data.size);
    
    toast.dismiss(loadingToast);

    // Vérifier que le blob n'est pas vide
    if (response.data.size === 0) {
      throw new Error('Le rapport généré est vide');
    }

    // Télécharger le fichier
    const blob = new Blob([response.data], { 
      type: format === 'pdf' ? 'application/pdf' : 'text/html' 
    });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `rapport_executif_${new Date().toISOString().split('T')[0]}.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);

    toast.success('🎯 Rapport exécutif généré avec succès !', { duration: 5000 });
    
  } catch (error: any) {
    console.error('❌ Erreur génération rapport:', error);
    toast.dismiss(loadingToast);
    
    let errorMsg = 'Erreur lors de la génération du rapport exécutif';
    
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      errorMsg = '⏱️ Timeout: Le rapport prend trop de temps. Essayez avec moins de données ou une période plus courte.';
    } else if (error.code === 'ERR_NETWORK') {
      errorMsg = '🔌 Erreur réseau: Vérifiez que le backend est accessible et qu\'Ollama fonctionne.';
    } else if (error.response?.status === 500) {
      errorMsg = '🤖 Erreur serveur: ' + (error.response?.data?.detail || 'Problème avec l\'analyse IA');
    } else if (error.response?.status === 400) {
      errorMsg = error.response?.data?.detail || 'Données invalides';
    }
    
    toast.error(errorMsg, { duration: 7000 });
    
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
        {
          keyword_ids: selectedKeywords,
          days: periodDays
        }
      );
      setPreviewData(response.data);
      setShowPreviewModal(true);
    } catch (error: any) {
      console.error('Erreur prévisualisation:', error);
      const errorMsg = error.response?.data?.detail || 'Erreur lors de la prévisualisation';
      toast.error(errorMsg);
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
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
          🤖 Rapports Intelligents IA
          <Badge variant="primary">
            <Sparkles className="w-4 h-4 mr-1" />
            IA Souveraine
          </Badge>
        </h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Génération automatique de rapports avec analyse IA avancée et lecture web
        </p>
      </div>

      {/* Alerte statut IA */}
      {aiStatusData && !aiStatusData.ai_available && (
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
            {/* Titre du rapport */}
            <Card>
              <div className="flex items-center space-x-3 mb-4">
                <Target className="w-6 h-6 text-primary-500" />
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                  Titre du rapport intelligent
                </h2>
              </div>
              
              <input
                type="text"
                value={reportTitle}
                onChange={(e) => setReportTitle(e.target.value)}
                placeholder="Ex: Analyse IA de l'opinion publique Q4 2024"
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
              <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                🤖 Résumé Rapport IA
                {aiStatusData?.ai_available && (
                  <Badge variant="success" size="sm">
                    <Activity className="w-3 h-3 mr-1" />
                    IA Active
                  </Badge>
                )}
              </h3>

              <div className="space-y-4">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Titre</p>
                  <p className="font-semibold text-gray-900 dark:text-white text-sm">
                    {reportTitle || 'Non renseigné'}
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
                  onClick={handleGenerateExecutiveReport}
                  disabled={
                    selectedKeywords.length === 0 ||
                    !reportTitle.trim() ||
                    isGenerating ||
                    !aiStatusData?.ai_available
                  }
                  className="btn w-full flex items-center justify-center space-x-2"
                  style={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    color: 'white'
                  }}
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Génération...</span>
                    </>
                  ) : (
                    <>
                      <Target className="w-4 h-4" />
                      <span>Rapport Exécutif (DG)</span>
                    </>
                  )}
                </button>

                <button
                  onClick={handleGenerateReport}
                  disabled={
                    selectedKeywords.length === 0 ||
                    !reportTitle.trim() ||
                    isGenerating ||
                    !aiStatusData?.ai_available
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

            <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
              <p className="text-sm text-purple-600 dark:text-purple-400 mb-1">
                Temps de traitement estimé
              </p>
              <p className="text-lg font-bold text-purple-900 dark:text-purple-200">
                ⏱️ {previewData.processing_time_estimate}
              </p>
              <p className="text-sm text-purple-700 dark:text-purple-300 mt-2">
                Confiance: {(previewData.confidence_score * 100).toFixed(0)}%
              </p>
            </div>

            {previewData.risk_indicators && previewData.risk_indicators.length > 0 && (
              <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                <p className="text-sm font-medium text-yellow-900 dark:text-yellow-200 mb-2">
                  <AlertTriangle className="w-4 h-4 inline mr-1" />
                  Indicateurs de risque
                </p>
                <ul className="text-sm text-yellow-800 dark:text-yellow-300 space-y-1">
                  {previewData.risk_indicators.map((indicator, idx) => (
                    <li key={idx}>• {indicator}</li>
                  ))}
                </ul>
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