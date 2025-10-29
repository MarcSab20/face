import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return Math.round(num).toString();
}

export function formatDate(date: string | null): string {
  if (!date) return 'Date inconnue';
  return new Date(date).toLocaleString('fr-FR');
}

export function getSentimentEmoji(sentiment: string | null): string {
  const emojis: Record<string, string> = {
    positive: '😊',
    neutral: '😐',
    negative: '😞',
  };
  return emojis[sentiment || ''] || '😐';
}

export function getSentimentColor(sentiment: string | null): string {
  const colors: Record<string, string> = {
    positive: 'bg-green-500',
    neutral: 'bg-gray-500',
    negative: 'bg-red-500',
  };
  return colors[sentiment || ''] || 'bg-gray-500';
}

export function getSourceIcon(source: string): string {
  const icons: Record<string, string> = {
    rss: '📰',
    reddit: '🔴',
    youtube: '📺',
    tiktok: '🎵',
    google_search: '🔍',
    google_alerts: '📧',
    twitter: '🐦',
    instagram: '📷',
    facebook: '👍',
    linkedin: '💼',
    telegram: '✈️',
    discord: '💬',
    medium: '📝',
  };
  return icons[source] || '📄';
}

export function getSourceColor(source: string): string {
  const colors: Record<string, string> = {
    rss: 'bg-orange-500',
    reddit: 'bg-red-500',
    youtube: 'bg-red-600',
    tiktok: 'bg-black',
    google_search: 'bg-blue-500',
    google_alerts: 'bg-green-500',
    twitter: 'bg-blue-400',
    instagram: 'bg-pink-500',
    facebook: 'bg-blue-600',
    linkedin: 'bg-blue-700',
    telegram: 'bg-blue-400',
    discord: 'bg-indigo-600',
    medium: 'bg-gray-800',
  };
  return colors[source] || 'bg-gray-500';
}