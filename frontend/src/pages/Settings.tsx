import { useEffect, useState } from 'react';
import { useStore } from '@/store/useStore';
import { sourcesApi } from '@/services/api';
import {
  Settings as SettingsIcon,
  Bell,
  Database,
  Shield,
  Palette,
  Key,
  Mail,
  Globe,
  Check,
  X,
  AlertCircle,
  Info,
} from 'lucide-react';
import type { Source } from '@/types/index';
import toast from 'react-hot-toast';

export default function Settings() {
  const { sources, setSources, darkMode, toggleDarkMode } = useStore();
  const [activeTab, setActiveTab] = useState<
    'general' | 'sources' | 'notifications' | 'security' | 'advanced'
  >('general');
  const [loading, setLoading] = useState(false);

  // Settings state
  const [settings, setSettingState] = useState({
    // General
    language: 'fr',
    timezone: 'Europe/Paris',
    dateFormat: 'DD/MM/YYYY',

    // Notifications
    emailNotifications: true,
    emailAddress: '',
    notifyNewMention: true,
    notifyNegativeSentiment: true,
    notifyVolumeSpike: false,
    dailyDigest: true,

    // API Keys (masked for security)
    googleApiKey: '',
    redditClientId: '',
    youtubeApiKey: '',

    // Advanced
    collectionInterval: 3600,
    maxResultsPerSource: 50,
    retentionDays: 90,
  });

  useEffect(() => {
    loadSources();
    loadSettings();
  }, []);

  const loadSources = async () => {
    try {
      const response = await sourcesApi.getAll();
      setSources(response.data.sources);
    } catch (error) {
      console.error('Error loading sources:', error);
    }
  };

  const loadSettings = () => {
    // Load settings from localStorage or API
    const savedSettings = localStorage.getItem('appSettings');
    if (savedSettings) {
      setSettingState(JSON.parse(savedSettings));
    }
  };

  const handleSaveSettings = () => {
    setLoading(true);
    try {
      // Save to localStorage
      localStorage.setItem('appSettings', JSON.stringify(settings));
      toast.success('Paramètres sauvegardés avec succès !');
    } catch (error) {
      toast.error('Erreur lors de la sauvegarde');
    } finally {
      setLoading(false);
    }
  };

  const handleSettingChange = (key: string, value: any) => {
    setSettingState((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Paramètres</h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Configurez votre application Superviseur
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-1">
          <nav className="space-y-1">
            {[
              { id: 'general', label: 'Général', icon: SettingsIcon },
              { id: 'sources', label: 'Sources', icon: Globe },
              { id: 'notifications', label: 'Notifications', icon: Bell },
              { id: 'security', label: 'Sécurité', icon: Shield },
              { id: 'advanced', label: 'Avancé', icon: Database },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-primary-500 text-white'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
              >
                <tab.icon className="w-5 h-5" />
                <span>{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="lg:col-span-3">
          <div className="card">
            {activeTab === 'general' && (
              <GeneralSettings
                settings={settings}
                darkMode={darkMode}
                onSettingChange={handleSettingChange}
                onToggleDarkMode={toggleDarkMode}
              />
            )}

            {activeTab === 'sources' && <SourcesSettings sources={sources} />}

            {activeTab === 'notifications' && (
              <NotificationSettings
                settings={settings}
                onSettingChange={handleSettingChange}
              />
            )}

            {activeTab === 'security' && (
              <SecuritySettings settings={settings} onSettingChange={handleSettingChange} />
            )}

            {activeTab === 'advanced' && (
              <AdvancedSettings settings={settings} onSettingChange={handleSettingChange} />
            )}

            {/* Save Button */}
            <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700 flex justify-end space-x-3">
              <button
                onClick={handleSaveSettings}
                disabled={loading}
                className="btn btn-primary"
              >
                {loading ? 'Sauvegarde...' : 'Sauvegarder les modifications'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// General Settings Component
interface GeneralSettingsProps {
  settings: any;
  darkMode: boolean;
  onSettingChange: (key: string, value: any) => void;
  onToggleDarkMode: () => void;
}

function GeneralSettings({
  settings,
  darkMode,
  onSettingChange,
  onToggleDarkMode,
}: GeneralSettingsProps) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Paramètres généraux
        </h3>
      </div>

      {/* Language */}
      <SettingItem
        label="Langue"
        description="Choisissez la langue de l'interface"
        icon={Globe}
      >
        <select
          value={settings.language}
          onChange={(e) => onSettingChange('language', e.target.value)}
          className="input max-w-xs"
        >
          <option value="fr">Français</option>
          <option value="en">English</option>
          <option value="es">Español</option>
        </select>
      </SettingItem>

      {/* Timezone */}
      <SettingItem
        label="Fuseau horaire"
        description="Votre fuseau horaire local"
        icon={Globe}
      >
        <select
          value={settings.timezone}
          onChange={(e) => onSettingChange('timezone', e.target.value)}
          className="input max-w-xs"
        >
          <option value="Europe/Paris">Paris (GMT+1)</option>
          <option value="Europe/London">Londres (GMT+0)</option>
          <option value="America/New_York">New York (GMT-5)</option>
          <option value="America/Los_Angeles">Los Angeles (GMT-8)</option>
          <option value="Asia/Tokyo">Tokyo (GMT+9)</option>
        </select>
      </SettingItem>

      {/* Date Format */}
      <SettingItem
        label="Format de date"
        description="Comment afficher les dates"
        icon={Globe}
      >
        <select
          value={settings.dateFormat}
          onChange={(e) => onSettingChange('dateFormat', e.target.value)}
          className="input max-w-xs"
        >
          <option value="DD/MM/YYYY">DD/MM/YYYY</option>
          <option value="MM/DD/YYYY">MM/DD/YYYY</option>
          <option value="YYYY-MM-DD">YYYY-MM-DD</option>
        </select>
      </SettingItem>

      {/* Dark Mode */}
      <SettingItem
        label="Mode sombre"
        description="Activer le thème sombre"
        icon={Palette}
      >
        <button
          onClick={onToggleDarkMode}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
            darkMode ? 'bg-primary-500' : 'bg-gray-200'
          }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
              darkMode ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
      </SettingItem>
    </div>
  );
}

// Sources Settings Component
interface SourcesSettingsProps {
  sources: Source[];
}

function SourcesSettings({ sources }: SourcesSettingsProps) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Sources de données
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Gérez les sources de collecte disponibles
        </p>
      </div>

      <div className="space-y-4">
        {sources.map((source) => (
          <div
            key={source.id}
            className="flex items-start justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg"
          >
            <div className="flex items-start space-x-4 flex-1">
              <div className="text-3xl">{source.icon}</div>
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-1">
                  <h4 className="font-semibold text-gray-900 dark:text-white">
                    {source.name}
                  </h4>
                  {source.free && (
                    <span className="badge badge-success text-xs">Activée</span>
                  )}
                  {source.requiresAuth && (
                    <span className="badge badge-warning text-xs">API Required</span>
                  )}
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                  {source.description}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-500">
                  Limite actuelle: {source.limit}
                </p>
              </div>
            </div>
            <div className="ml-4">
              {source.enabled ? (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                  <Check className="w-3 h-3 mr-1" />
                  Activée
                </span>
              ) : (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-200">
                  <X className="w-3 h-3 mr-1" />
                  Désactivée
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

    </div>
  );
}

// Notification Settings Component
interface NotificationSettingsProps {
  settings: any;
  onSettingChange: (key: string, value: any) => void;
}

function NotificationSettings({ settings, onSettingChange }: NotificationSettingsProps) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Notifications
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Configurez comment vous souhaitez être notifié
        </p>
      </div>

      {/* Email Notifications */}
      <SettingItem
        label="Notifications par email"
        description="Recevoir des notifications par email"
        icon={Mail}
      >
        <button
          onClick={() =>
            onSettingChange('emailNotifications', !settings.emailNotifications)
          }
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
            settings.emailNotifications ? 'bg-primary-500' : 'bg-gray-200'
          }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
              settings.emailNotifications ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
      </SettingItem>

      {settings.emailNotifications && (
        <>
          {/* Email Address */}
          <SettingItem label="Adresse email" description="Où envoyer les notifications">
            <input
              type="email"
              value={settings.emailAddress}
              onChange={(e) => onSettingChange('emailAddress', e.target.value)}
              placeholder="votre@email.com"
              className="input max-w-md"
            />
          </SettingItem>

          {/* Notification Types */}
          <div className="space-y-3">
            <h4 className="font-medium text-gray-900 dark:text-white">
              Types de notifications
            </h4>

            <ToggleOption
              label="Nouvelle mention"
              description="À chaque nouvelle mention trouvée"
              checked={settings.notifyNewMention}
              onChange={(checked) => onSettingChange('notifyNewMention', checked)}
            />

            <ToggleOption
              label="Sentiment négatif"
              description="Quand une mention négative est détectée"
              checked={settings.notifyNegativeSentiment}
              onChange={(checked) => onSettingChange('notifyNegativeSentiment', checked)}
            />

            <ToggleOption
              label="Pic de volume"
              description="Augmentation inhabituelle du nombre de mentions"
              checked={settings.notifyVolumeSpike}
              onChange={(checked) => onSettingChange('notifyVolumeSpike', checked)}
            />

            <ToggleOption
              label="Résumé quotidien"
              description="Rapport quotidien par email"
              checked={settings.dailyDigest}
              onChange={(checked) => onSettingChange('dailyDigest', checked)}
            />
          </div>
        </>
      )}
    </div>
  );
}

// Security Settings Component
interface SecuritySettingsProps {
  settings: any;
  onSettingChange: (key: string, value: any) => void;
}

function SecuritySettings({ settings, onSettingChange }: SecuritySettingsProps) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Sécurité & API
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Configurez vos clés API (stockées localement)
        </p>
      </div>

      <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-yellow-900 dark:text-yellow-200">
            <p className="font-medium mb-1">Attention</p>
            <p>
              Les clés API sont stockées localement dans votre navigateur. Ne partagez
              jamais vos clés API avec quiconque.
            </p>
          </div>
        </div>
      </div>

      {/* API Keys */}
      <SettingItem
        label="Google API Key"
        description="Pour Google Custom Search et YouTube"
        icon={Key}
      >
        <input
          type="password"
          value={settings.googleApiKey}
          onChange={(e) => onSettingChange('googleApiKey', e.target.value)}
          placeholder="Entrez votre clé API"
          className="input max-w-md"
        />
      </SettingItem>

      <SettingItem
        label="Reddit Client ID"
        description="Pour l'API Reddit"
        icon={Key}
      >
        <input
          type="password"
          value={settings.redditClientId}
          onChange={(e) => onSettingChange('redditClientId', e.target.value)}
          placeholder="Entrez votre Client ID"
          className="input max-w-md"
        />
      </SettingItem>

      <SettingItem
        label="YouTube API Key"
        description="Pour l'API YouTube Data"
        icon={Key}
      >
        <input
          type="password"
          value={settings.youtubeApiKey}
          onChange={(e) => onSettingChange('youtubeApiKey', e.target.value)}
          placeholder="Entrez votre clé API"
          className="input max-w-md"
        />
      </SettingItem>
    </div>
  );
}

// Advanced Settings Component
interface AdvancedSettingsProps {
  settings: any;
  onSettingChange: (key: string, value: any) => void;
}

function AdvancedSettings({ settings, onSettingChange }: AdvancedSettingsProps) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Paramètres avancés
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Configuration technique de la collecte
        </p>
      </div>

      <SettingItem
        label="Intervalle de collecte"
        description="Fréquence de collecte automatique (en secondes)"
        icon={Database}
      >
        <input
          type="number"
          value={settings.collectionInterval}
          onChange={(e) =>
            onSettingChange('collectionInterval', parseInt(e.target.value))
          }
          min="300"
          max="86400"
          className="input max-w-xs"
        />
        <p className="text-xs text-gray-500 mt-1">
          Minimum: 300 (5 min), Maximum: 86400 (24h)
        </p>
      </SettingItem>

      <SettingItem
        label="Résultats max par source"
        description="Nombre maximum de mentions à collecter par source"
        icon={Database}
      >
        <input
          type="number"
          value={settings.maxResultsPerSource}
          onChange={(e) =>
            onSettingChange('maxResultsPerSource', parseInt(e.target.value))
          }
          min="10"
          max="200"
          className="input max-w-xs"
        />
      </SettingItem>

      <SettingItem
        label="Rétention des données"
        description="Durée de conservation des mentions (en jours)"
        icon={Database}
      >
        <input
          type="number"
          value={settings.retentionDays}
          onChange={(e) => onSettingChange('retentionDays', parseInt(e.target.value))}
          min="7"
          max="365"
          className="input max-w-xs"
        />
      </SettingItem>

      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-red-900 dark:text-red-200">
            <p className="font-medium mb-1">Zone dangereuse</p>
            <p className="mb-3">
              Ces actions sont irréversibles. Procédez avec prudence.
            </p>
            <button className="btn btn-danger text-sm">
              Supprimer toutes les données
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Helper Components
interface SettingItemProps {
  label: string;
  description?: string;
  icon?: React.ElementType;
  children: React.ReactNode;
}

function SettingItem({ label, description, icon: Icon, children }: SettingItemProps) {
  return (
    <div className="flex items-start justify-between py-4 border-b border-gray-200 dark:border-gray-700 last:border-0">
      <div className="flex items-start space-x-3 flex-1">
        {Icon && (
          <div className="mt-1">
            <Icon className="w-5 h-5 text-gray-400" />
          </div>
        )}
        <div className="flex-1">
          <label className="block font-medium text-gray-900 dark:text-white mb-1">
            {label}
          </label>
          {description && (
            <p className="text-sm text-gray-600 dark:text-gray-400">{description}</p>
          )}
        </div>
      </div>
      <div className="ml-4">{children}</div>
    </div>
  );
}

interface ToggleOptionProps {
  label: string;
  description: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}

function ToggleOption({ label, description, checked, onChange }: ToggleOptionProps) {
  return (
    <div className="flex items-center justify-between py-3 px-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
      <div>
        <p className="font-medium text-gray-900 dark:text-white">{label}</p>
        <p className="text-sm text-gray-600 dark:text-gray-400">{description}</p>
      </div>
      <button
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
          checked ? 'bg-primary-500' : 'bg-gray-200'
        }`}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
            checked ? 'translate-x-6' : 'translate-x-1'
          }`}
        />
      </button>
    </div>
  );
}