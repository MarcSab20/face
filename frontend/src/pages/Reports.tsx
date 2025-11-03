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
  AlertTriangle,
  TrendingUp,
  Users,
  MapPin,
  Target,
  BarChart3,
  MessageSquare,
  Shield
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

interface EnhancedReportPreview {
  keywords: string[];
  keyword_ids: number[];
  period_days: number;
  total_mentions: number;
  has_analysis: boolean;
  has_risk_assessment: boolean;
  has_trends: boolean;
  has_influencers: boolean;
  has_geography: boolean;
  risk_level?: string;
}

interface ReportSection {
  id: string;
  name: string;
  description: string;
  icon: string;
  required: boolean;
}

interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  sections: string[];
  duration: string;
  audience: string;
}

export default function EnhancedReports() {
  const [selectedKeywords, setSelectedKeywords] = useState<number[]>([]);
  const [periodDays, setPeriodDays] = useState(30);
  const [reportObject, setReportObject] = useState('');
  const [selectedSections, setSelectedSections] = useState<string[]>([
    'analysis',
    'risk_assessment',
    'trends',
    'detailed_influencers',
    'geography',
    'comparison',
    'recommendations'
  ]);
  const [format, setFormat] = useState<'pdf' | 'html'>('pdf');
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [previewData, setPreviewData] = useState<EnhancedReportPreview | null>(null);
  const [activeTab, setActiveTab] = useState<'config' | 'templates' | 'methodology'>('config');

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

  // Charger les sections disponibles
  const { data: sectionsData } = useQuery({
    queryKey: ['reportSections'],
    queryFn: async () => {
      const response = await axios.get<{ sections: ReportSection[]; default_sections: string[] }>(
        `${API_BASE_URL}/api/reports/sections-available`
      );
      return response.data;
    },
  });

  // Charger les templates
  const { data: templatesData } = useQuery({
    queryKey: ['reportTemplates'],
    queryFn: async () => {
      const response = await axios.get<{ templates: ReportTemplate[] }>(
        `${API_BASE_URL}/api/reports/templates`
      );
      return response.data;
    },
  });

  // Charger la méthodologie de risque
  const { data: methodologyData } = useQuery({
    queryKey: ['riskMethodology'],
    queryFn: async () => {
      const response = await axios.get(
        `${API_BASE_URL}/api/reports/risk-methodology`
      );
      return response.data;
    },
  });

  const sections = sectionsData?.sections || [];
  const templates = templatesData?.templates || [];

  const toggleKeyword = (keywordId: number) => {
    setSelectedKeywords((prev) =>
      prev.includes(keywordId)
        ? prev.filter((id) => id !== keywordId)
        : [...prev, keywordId]
    );
  };

  const toggleSection = (sectionId: string) => {
    const section = sections.find(s => s.id === sectionId);
    if (section?.required) return; // Ne pas permettre de désélectionner les sections requises
    
    setSelectedSections((prev) =>
      prev.includes(sectionId)
        ? prev.filter((s) => s !== sectionId)
        : [...prev, sectionId]
    );
  };

  const applyTemplate = (template: ReportTemplate) => {
    setSelectedSections(template.sections);
    setShowTemplateModal(false);
    toast.success(`Template "${template.name}" appliqué !`);
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
        `${API_BASE_URL}/api/reports/generate-enhanced`,
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
        // Télécharger le PDF enrichi
        const blob = new Blob([response.data], { type: 'application/pdf' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `rapport_enrichi_${reportObject.substring(0, 30)}_${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);

        toast.success('Rapport enrichi PDF généré avec succès !');
      } else {
        // Ouvrir HTML dans nouvel onglet
        const blob = new Blob([response.data], { type: 'text/html' });
        const url = window.URL.createObjectURL(blob);
        window.open(url, '_blank');
        toast.success('Rapport enrichi HTML généré !');
      }
    } catch (error) {
      console.error('Erreur génération rapport enrichi:', error);
      toast.error('Erreur lors de la génération du rapport enrichi');
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
      const response = await axios.post<EnhancedReportPreview>(
        `${API_BASE_URL}/api/reports/preview-enhanced`,
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

  const getRiskColor = (riskLevel?: string) => {
    switch (riskLevel) {
      case 'ÉLEVÉ': return 'text-red-600';
      case 'MODÉRÉ': return 'text-yellow-600';
      case 'FAIBLE': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  const getSectionIcon = (sectionId: string) => {
    const icons: Record<string, any> = {
      analysis: BarChart3,
      risk_assessment: Shield,
      trends: TrendingUp,
      key_content: MessageSquare,
      detailed_influencers: Users,
      geography: MapPin,
      comparison: BarChart3,
      recommendations: Target
    };
    return icons[sectionId] || FileText;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          📊 Génération de Rapports Enrichis
        </h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Rapports analytiques avancés avec évaluation de risque et recommandations opérationnelles
        </p>
      </div>

      {/* Tabs */}
      <Tabs
        tabs={[
          { id: 'config', label: 'Configuration', icon: Settings },
          { id: 'templates', label: 'Templates', icon: FileText },
          { id: 'methodology', label: 'Méthodologie', icon: Shield },
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

            {/* Sélection mots-clés */}
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

            {/* Sections enrichies */}
            <Card>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <FileText className="w-6 h-6 text-primary-500" />
                  <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                    Sections du rapport enrichi
                  </h2>
                </div>
                <button
                  onClick={() => setShowTemplateModal(true)}
                  className="btn btn-secondary"
                >
                  <FileText className="w-4 h-4 mr-2" />
                  Templates
                </button>
              </div>

              <div className="space-y-3">
                {sections.map((section) => {
                  const IconComponent = getSectionIcon(section.id);
                  const isSelected = selectedSections.includes(section.id);
                  const isRequired = section.required;
                  
                  return (
                    <button
                      key={section.id}
                      onClick={() => toggleSection(section.id)}
                      disabled={isRequired}
                      className={`w-full p-4 rounded-xl border-2 text-left transition-all ${
                        isSelected
                          ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                      } ${isRequired ? 'opacity-75' : ''}`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <span className="text-2xl">{section.icon}</span>
                          <span className="font-semibold text-gray-900 dark:text-white">
                            {section.name}
                          </span>
                          {isRequired && (
                            <Badge variant="warning" size="sm">Requis</Badge>
                          )}
                        </div>
                        {isSelected ? (
                          <Check className="w-5 h-5 text-primary-500" />
                        ) : (
                          <X className="w-5 h-5 text-gray-400" />
                        )}
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {section.description}
                      </p>
                    </button>
                  );
                })}
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
                  <div className="font-semibold text-gray-900 dark:text-white">PDF Enrichi</div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Format professionnel, 4-5 pages avec analyses avancées
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
                    Prévisualisation web enrichie
                  </p>
                </button>
              </div>
            </Card>
          </div>

          {/* Résumé et actions */}
          <div className="space-y-6">
            <Card className="sticky top-6">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
                📋 Résumé du Rapport Enrichi
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
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                    Sections ({selectedSections.length})
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {selectedSections.map((sectionId) => {
                      const section = sections.find((s) => s.id === sectionId);
                      return (
                        <Badge key={sectionId} variant="primary" size="sm">
                          {section?.icon} {section?.name.split(' ')[0]}
                        </Badge>
                      );
                    })}
                  </div>
                </div>

                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Format</p>
                  <p className="font-semibold text-gray-900 dark:text-white uppercase">
                    {format} {format === 'pdf' ? 'Enrichi' : 'Interactif'}
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
                      <span>Générer Rapport Enrichi</span>
                    </>
                  )}
                </button>
              </div>
            </Card>

            {/* Aide enrichie */}
            <Card className="bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-200 dark:border-blue-800">
              <div className="flex items-start space-x-3">
                <div className="text-2xl">🎯</div>
                <div>
                  <h4 className="font-semibold text-blue-900 dark:text-blue-200 mb-2">
                    Fonctionnalités enrichies
                  </h4>
                  <ul className="text-sm text-blue-800 dark:text-blue-300 space-y-1">
                    <li><strong>🚨 Évaluation de gravité:</strong> Note de risque automatique</li>
                    <li><strong>📈 Détection de pics:</strong> Analyse des variations inhabituelles</li>
                    <li><strong>👑 Profils influenceurs:</strong> Métriques avancées et évolution</li>
                    <li><strong>🌍 Géographie:</strong> Répartition mondiale des mentions</li>
                    <li><strong>📊 Comparaisons:</strong> Évolution vs période précédente</li>
                    <li><strong>🎯 Recommandations:</strong> Actions concrètes prioritaires</li>
                  </ul>
                </div>
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* Tab Templates */}
      {activeTab === 'templates' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {templates.map((template) => (
            <Card key={template.id} hoverable>
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                    {template.name}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    {template.description}
                  </p>
                </div>
                <button
                  onClick={() => applyTemplate(template)}
                  className="btn btn-primary"
                >
                  Appliquer
                </button>
              </div>
              
              <div className="space-y-3">
                <div>
                  <Badge variant="info" size="sm">{template.audience}</Badge>
                  <Badge variant="primary" size="sm" >{template.duration}</Badge>
                </div>
                
                <div>
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Sections incluses:
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {template.sections.map((sectionId) => {
                      const section = sections.find(s => s.id === sectionId);
                      return (
                        <Badge key={sectionId} variant="primary" size="sm">
                          {section?.icon} {section?.name.split(' ')[0]}
                        </Badge>
                      );
                    })}
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Tab Méthodologie */}
      {activeTab === 'methodology' && methodologyData && (
        <div className="space-y-6">
          <Card>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
              {methodologyData.methodology.title}
            </h2>
            <p className="text-gray-700 dark:text-gray-300 mb-6">
              {methodologyData.methodology.description}
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
              {methodologyData.methodology.factors.map((factor: any, index: number) => (
                <div key={index} className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                    {factor.name} ({factor.weight})
                  </h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                    {factor.description}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500">
                    {factor.calculation}
                  </p>
                </div>
              ))}
            </div>

            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Échelle de Risque
            </h3>
            <div className="space-y-3">
              {methodologyData.methodology.scale.map((level: any, index: number) => (
                <div key={index} className="flex items-center space-x-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div 
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: level.color }}
                  />
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-gray-900 dark:text-white">
                        {level.level}
                      </span>
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        ({level.range})
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {level.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Modal Templates */}
      {showTemplateModal && (
        <Modal
          isOpen={showTemplateModal}
          onClose={() => setShowTemplateModal(false)}
          title="Choisir un template de rapport"
          size="lg"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {templates.map((template) => (
              <button
                key={template.id}
                onClick={() => applyTemplate(template)}
                className="p-4 border-2 border-gray-200 dark:border-gray-700 rounded-lg hover:border-primary-500 transition-colors text-left"
              >
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                  {template.name}
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  {template.description}
                </p>
                <div className="flex flex-wrap gap-1">
                  {template.sections.map((sectionId) => {
                    const section = sections.find(s => s.id === sectionId);
                    return (
                      <Badge key={sectionId} variant="primary" size="sm">
                        {section?.icon}
                      </Badge>
                    );
                  })}
                </div>
              </button>
            ))}
          </div>
        </Modal>
      )}

      {/* Modal de prévisualisation enrichie */}
      {showPreviewModal && previewData && (
        <Modal
          isOpen={showPreviewModal}
          onClose={() => setShowPreviewModal(false)}
          title="Prévisualisation du rapport enrichi"
          size="lg"
        >
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Mots-clés</p>
                <div className="flex flex-wrap gap-1">
                  {previewData.keywords.map((kw) => (
                    <Badge key={kw} variant="primary" size="sm">
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

            {previewData.risk_level && (
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                  Niveau de risque estimé
                </p>
                <p className={`text-lg font-bold ${getRiskColor(previewData.risk_level)}`}>
                  <Shield className="w-5 h-5 inline mr-2" />
                  {previewData.risk_level}
                </p>
              </div>
            )}

            <div>
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Sections disponibles
              </p>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { key: 'has_analysis', label: 'Analyse Détaillée', icon: '📊' },
                  { key: 'has_risk_assessment', label: 'Évaluation Risque', icon: '🚨' },
                  { key: 'has_trends', label: 'Analyse Tendances', icon: '📈' },
                  { key: 'has_influencers', label: 'Profils Influenceurs', icon: '👑' },
                  { key: 'has_geography', label: 'Répartition Géo', icon: '🌍' },
                ].map((item) => (
                  <div
                    key={item.key}
                    className={`p-3 rounded-lg ${
                      previewData[item.key as keyof EnhancedReportPreview]
                        ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
                        : 'bg-gray-50 dark:bg-gray-700'
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">{item.icon}</span>
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {item.label}
                      </span>
                      {previewData[item.key as keyof EnhancedReportPreview] ? (
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