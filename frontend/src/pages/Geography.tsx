import { useEffect, useState, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Globe, TrendingUp, MapPin } from 'lucide-react';
import { Card, Badge, PageLoading, ErrorState } from '@/components/ui/index';
import { formatNumber } from '@/lib/utils';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ============ INTERFACES TYPESCRIPT ============

interface CountryData {
  country_code: string;
  country_name: string;
  latitude: number;
  longitude: number;
  mention_count: number;
  percentage: number;
}

interface HeatmapPoint {
  lat: number;
  lon: number;
  intensity: number;
  count: number;
  country: string;
  country_code: string;
}

interface SentimentDistribution {
  positive: number;
  neutral: number;
  negative: number;
}

interface CountryTrends {
  country_code: string;
  country_name: string;
  total_mentions: number;
  sentiment_distribution: SentimentDistribution;
  top_sources: Record<string, number>;
  avg_engagement: number;
}

interface GeoDistributionResponse {
  period_days: number;
  keyword: string | null;
  total_countries: number;
  distribution: CountryData[];
}

interface HeatmapDataResponse {
  period_days: number;
  points: HeatmapPoint[];
  total_points: number;
}

// ============ COMPOSANT PRINCIPAL ============

export default function Geography() {
  const [days, setDays] = useState(30);
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null);
  const mapRef = useRef<HTMLDivElement>(null);
  const leafletMapRef = useRef<any>(null);

  // Charger les données géographiques
  const { data: geoData, isLoading, error } = useQuery<GeoDistributionResponse>({
    queryKey: ['geography', days],
    queryFn: async () => {
      const response = await axios.get<GeoDistributionResponse>(
        `${API_BASE_URL}/api/geography/distribution?days=${days}`
      );
      return response.data;
    },
  });

  // Charger les données heatmap
  const { data: heatmapData } = useQuery<HeatmapDataResponse>({
    queryKey: ['heatmap', days],
    queryFn: async () => {
      const response = await axios.get<HeatmapDataResponse>(
        `${API_BASE_URL}/api/geography/heatmap?days=${days}`
      );
      return response.data;
    },
  });

  // Charger les données d'un pays spécifique
  const { data: countryTrends } = useQuery<CountryTrends | null>({
    queryKey: ['countryTrends', selectedCountry, days],
    queryFn: async () => {
      if (!selectedCountry) return null;
      const response = await axios.get<CountryTrends>(
        `${API_BASE_URL}/api/geography/country/${selectedCountry}?days=${days}`
      );
      return response.data;
    },
    enabled: !!selectedCountry,
  });

    // Initialiser la carte Leaflet
        
    useEffect(() => {
    if (!heatmapData) return;

    const initMap = async () => {
        // ✅ Vérification à l'intérieur de initMap
        if (!mapRef.current) return;

        try {
        // Import Leaflet CSS
        if (!document.querySelector('link[href*="leaflet.css"]')) {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
            document.head.appendChild(link);
        }

        // Charger Leaflet dynamiquement
        const L = (await import('leaflet')).default;
        
        // Détruire la carte existante
        if (leafletMapRef.current) {
            leafletMapRef.current.remove();
        }

        // ✅ Maintenant TypeScript sait que mapRef.current n'est pas null
        const map = L.map(mapRef.current).setView([20, 0], 2);

        // Ajouter le fond de carte
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 18,
        }).addTo(map);

        // Ajouter les markers pour chaque pays
        heatmapData.points.forEach((point: HeatmapPoint) => {
            const radius = 10 + (point.intensity * 30);
            const opacity = 0.5 + (point.intensity * 0.5);

            const circle = L.circleMarker([point.lat, point.lon], {
            radius: radius,
            fillColor: point.intensity > 0.7 ? '#ef4444' : point.intensity > 0.4 ? '#f59e0b' : '#10b981',
            color: '#fff',
            weight: 2,
            opacity: 1,
            fillOpacity: opacity,
            }).addTo(map);

            circle.bindPopup(`
            <div style="font-family: sans-serif;">
                <h3 style="margin: 0 0 8px 0; font-size: 16px; font-weight: bold;">${point.country}</h3>
                <p style="margin: 0; font-size: 14px;"><strong>${point.count}</strong> mentions</p>
                <button 
                onclick="window.selectCountry('${point.country_code}')"
                style="margin-top: 8px; padding: 6px 12px; background: #667eea; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 12px;"
                >
                Voir détails →
                </button>
            </div>
            `);
        });

        leafletMapRef.current = map;
        } catch (err) {
        console.error('Erreur initialisation carte:', err);
        }
    };

    initMap();

    // Fonction globale pour sélectionner un pays depuis le popup
    (window as any).selectCountry = (countryCode: string) => {
        setSelectedCountry(countryCode);
    };
    return () => {
        if (leafletMapRef.current) {
        leafletMapRef.current.remove();
        }
    };
    }, [heatmapData]);

  if (error) {
    return <ErrorState message="Erreur de chargement des données géographiques" />;
  }

  if (isLoading) {
    return <PageLoading message="Chargement de la carte..." />;
  }

  const distribution: CountryData[] = geoData?.distribution || [];
  const totalMentions = distribution.reduce((sum, c) => sum + c.mention_count, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            🌍 Carte Géographique
          </h1>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Distribution mondiale des mentions
          </p>
        </div>

        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="input max-w-xs"
        >
          <option value="7">7 derniers jours</option>
          <option value="14">14 derniers jours</option>
          <option value="30">30 derniers jours</option>
          <option value="90">90 derniers jours</option>
        </select>
      </div>

      {/* Stats globales */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Pays Actifs</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {distribution.length}
              </p>
            </div>
            <Globe className="w-10 h-10 text-primary-500" />
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Mentions</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {formatNumber(totalMentions)}
              </p>
            </div>
            <TrendingUp className="w-10 h-10 text-green-500" />
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Pays Principal</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {distribution[0]?.country_name || 'N/A'}
              </p>
            </div>
            <MapPin className="w-10 h-10 text-orange-500" />
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Carte interactive */}
        <div className="lg:col-span-2">
          <Card>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Heatmap Interactive
            </h3>
            <div
              ref={mapRef}
              className="w-full h-[500px] rounded-lg overflow-hidden border-2 border-gray-200 dark:border-gray-700"
            />
            <div className="mt-4 flex items-center justify-between text-sm">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 rounded-full bg-green-500" />
                  <span className="text-gray-600 dark:text-gray-400">Faible</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 rounded-full bg-yellow-500" />
                  <span className="text-gray-600 dark:text-gray-400">Moyen</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 rounded-full bg-red-500" />
                  <span className="text-gray-600 dark:text-gray-400">Élevé</span>
                </div>
              </div>
              <p className="text-gray-500 dark:text-gray-400">
                Cliquez sur un marqueur pour plus de détails
              </p>
            </div>
          </Card>
        </div>

        {/* Classement des pays */}
        <div>
          <Card>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              🏆 Top Pays
            </h3>
            <div className="space-y-3">
              {distribution.slice(0, 10).map((country, index) => (
                <button
                  key={country.country_code}
                  onClick={() => setSelectedCountry(country.country_code)}
                  className={`w-full text-left p-3 rounded-lg transition-colors ${
                    selectedCountry === country.country_code
                      ? 'bg-primary-100 dark:bg-primary-900/30 border-2 border-primary-500'
                      : 'bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-gray-900 dark:text-white">
                        #{index + 1}
                      </span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {country.country_name}
                      </span>
                    </div>
                    <Badge variant="primary">{country.mention_count}</Badge>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-primary-500 to-secondary-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${country.percentage}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    {country.percentage.toFixed(1)}% du total
                  </p>
                </button>
              ))}
            </div>
          </Card>
        </div>
      </div>

      {/* Détails du pays sélectionné - CORRECTION ICI */}
      {selectedCountry && countryTrends && (
        <Card className="animate-fade-in">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white">
              📊 Détails - {countryTrends.country_name}
            </h3>
            <button
              onClick={() => setSelectedCountry(null)}
              className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            >
              ✕ Fermer
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Total mentions */}
            <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                Total Mentions
              </p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white">
                {countryTrends.total_mentions}
              </p>
            </div>

            {/* Engagement moyen */}
            <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                Engagement Moyen
              </p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white">
                {formatNumber(countryTrends.avg_engagement)}
              </p>
            </div>

            {/* Sentiment dominant */}
            <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                Sentiment Dominant
              </p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white">
                {countryTrends.sentiment_distribution.positive >
                countryTrends.sentiment_distribution.negative
                  ? '😊 Positif'
                  : '😞 Négatif'}
              </p>
            </div>
          </div>

          {/* Distribution sentiment */}
          <div className="mt-6">
            <h4 className="font-semibold text-gray-900 dark:text-white mb-3">
              Distribution du Sentiment
            </h4>
            <div className="flex h-10 rounded-lg overflow-hidden">
              <div
                className="bg-green-500 flex items-center justify-center text-white text-sm font-semibold"
                style={{
                  width: `${
                    (countryTrends.sentiment_distribution.positive /
                      countryTrends.total_mentions) *
                    100
                  }%`,
                }}
              >
                {countryTrends.sentiment_distribution.positive}
              </div>
              <div
                className="bg-gray-500 flex items-center justify-center text-white text-sm font-semibold"
                style={{
                  width: `${
                    (countryTrends.sentiment_distribution.neutral /
                      countryTrends.total_mentions) *
                    100
                  }%`,
                }}
              >
                {countryTrends.sentiment_distribution.neutral}
              </div>
              <div
                className="bg-red-500 flex items-center justify-center text-white text-sm font-semibold"
                style={{
                  width: `${
                    (countryTrends.sentiment_distribution.negative /
                      countryTrends.total_mentions) *
                    100
                  }%`,
                }}
              >
                {countryTrends.sentiment_distribution.negative}
              </div>
            </div>
          </div>

          {/* Top sources - CORRECTION DU TYPAGE ICI */}
          <div className="mt-6">
            <h4 className="font-semibold text-gray-900 dark:text-white mb-3">
              Top Sources
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {Object.entries(countryTrends.top_sources).map(([source, count]) => (
                <div
                  key={source}
                  className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg text-center"
                >
                  <p className="text-sm text-gray-600 dark:text-gray-400 capitalize">
                    {source}
                  </p>
                  <p className="text-xl font-bold text-gray-900 dark:text-white mt-1">
                    {count as number}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}