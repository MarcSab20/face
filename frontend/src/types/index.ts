export interface Keyword {
  id: number;
  keyword: string;
  active: boolean;
  sources: string;
  created_at: string;
  last_collected: string | null;
}

export interface Mention {
  id: number;
  keyword_id: number;
  source: string;
  source_url: string;
  title: string;
  content: string;
  author: string;
  engagement_score: number;
  sentiment: string | null;
  published_at: string | null;
  collected_at: string;
  mention_metadata?: string;
}

export interface Stats {
  total_keywords: number;
  total_mentions: number;
  mentions_today: number;
  mentions_by_source: Record<string, number>;
  top_keywords: Array<{
    keyword: string;
    mentions: number;
  }>;
  sentiment_distribution: {
    positive: number;
    neutral: number;
    negative: number;
  };
}

export interface AdvancedStats {
  timeline: Array<{
    date: string;
    count: number;
  }>;
  sentiment_by_source: Record<string, Record<string, number>>;
  top_engaged: Array<{
    id: number;
    title: string;
    source: string;
    engagement: number;
    sentiment: string | null;
    url: string;
  }>;
  hourly_distribution: Array<{
    hour: number;
    count: number;
  }>;
  daily_distribution: Array<{
    day: string;
    count: number;
  }>;
}

export interface FilterOptions {
  keyword?: string;
  source?: string;
  sentiment?: 'positive' | 'negative' | 'neutral' | '';
  min_engagement?: number;
  date_from?: string;
  date_to?: string;
  search?: string;
  language?: string;
  content_type?: 'all' | 'video' | 'image' | 'text';
  min_followers?: number;
  hashtag?: string;
  country?: string;
}

export interface CollectionRequest {
  keyword_id?: number;
  sources?: string[];
}

export interface Source {
  id: string;
  name: string;
  description: string;
  icon?: string;
  free: boolean;
  limit: string;
  enabled?: boolean;
  requiresAuth?: boolean;
}