import axios from 'axios';
import type {
  Keyword,
  Mention,
  Stats,
  AdvancedStats,
  FilterOptions,
  CollectionRequest,
  Source,
} from '@/types/index';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteurs pour gérer les erreurs
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// ===== Keywords =====
export const keywordsApi = {
  getAll: (activeOnly = true) =>
    api.get<Keyword[]>('/api/keywords', { params: { active_only: activeOnly } }),

  getOne: (id: number) =>
    api.get<Keyword>(`/api/keywords/${id}`),

  create: (keyword: string, sources: string[]) =>
    api.post<Keyword>('/api/keywords', { keyword, sources }),

  delete: (id: number) =>
    api.delete(`/api/keywords/${id}`),
};

// ===== Mentions =====
export const mentionsApi = {
  getAll: (filters: FilterOptions = {}, limit = 50, offset = 0) => {
    const params = new URLSearchParams();
    
    if (filters.keyword) params.append('keyword', filters.keyword);
    if (filters.source) params.append('source', filters.source);
    if (filters.sentiment) params.append('sentiment', filters.sentiment);
    if (filters.min_engagement) params.append('min_engagement', filters.min_engagement.toString());
    if (filters.date_from) params.append('date_from', filters.date_from);
    if (filters.date_to) params.append('date_to', filters.date_to);
    if (filters.search) params.append('search', filters.search);
    if (filters.language) params.append('language', filters.language);
    if (filters.content_type && filters.content_type !== 'all') params.append('content_type', filters.content_type);
    if (filters.min_followers) params.append('min_followers', filters.min_followers.toString());
    if (filters.hashtag) params.append('hashtag', filters.hashtag);
    if (filters.country) params.append('country', filters.country);
    
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());
    
    return api.get<Mention[]>(`/api/mentions?${params.toString()}`);
  },

  getOne: (id: number) =>
    api.get<Mention>(`/api/mentions/${id}`),
};

// ===== Stats =====
export const statsApi = {
  getBasic: () =>
    api.get<Stats>('/api/stats'),

  getAdvanced: (days = 7) =>
    api.get<AdvancedStats>('/api/stats/advanced', { params: { days } }),
};

// ===== Collection =====
export const collectionApi = {
  start: (request: CollectionRequest = {}) =>
    api.post('/api/collect', request),

  startForKeyword: (keywordId: number) =>
    api.post('/api/collect', { keyword_id: keywordId }),
};

// ===== Sentiment =====
export const sentimentApi = {
  analyzeMention: (mentionId: number) =>
    api.post(`/api/analyze-sentiment/${mentionId}`),

  analyzeAll: () =>
    api.post('/api/analyze-all-sentiments'),
};

// ===== Sources =====
export const sourcesApi = {
  getAll: () =>
    api.get<{ sources: Source[] }>('/api/sources'),
};

// ===== Export =====
export const exportApi = {
  toCSV: async (filters: FilterOptions = {}) => {
    const response = await mentionsApi.getAll(filters, 1000, 0);
    const mentions = response.data;

    const csv = [
      ['Date', 'Source', 'Titre', 'Auteur', 'Sentiment', 'Engagement', 'URL'].join(','),
      ...mentions.map(m => [
        m.published_at || '',
        m.source,
        `"${m.title.replace(/"/g, '""')}"`,
        `"${m.author.replace(/"/g, '""')}"`,
        m.sentiment || 'inconnu',
        m.engagement_score,
        m.source_url,
      ].join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `mentions_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  },

  toJSON: async (filters: FilterOptions = {}) => {
    const response = await mentionsApi.getAll(filters, 1000, 0);
    const json = JSON.stringify(response.data, null, 2);

    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `mentions_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  },
};

export default api;