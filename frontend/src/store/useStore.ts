import { create } from 'zustand';
import type { Keyword, Mention, Stats, AdvancedStats, FilterOptions, Source } from '@/types/index';

interface AppState {
  // Data
  keywords: Keyword[];
  mentions: Mention[];
  stats: Stats | null;
  advancedStats: AdvancedStats | null;
  sources: Source[];

  // UI State
  sidebarOpen: boolean;
  darkMode: boolean;
  loading: boolean;
  filters: FilterOptions;

  // Actions
  setKeywords: (keywords: Keyword[]) => void;
  setMentions: (mentions: Mention[]) => void;
  setStats: (stats: Stats) => void;
  setAdvancedStats: (stats: AdvancedStats) => void;
  setSources: (sources: Source[]) => void;
  toggleSidebar: () => void;
  toggleDarkMode: () => void;
  setLoading: (loading: boolean) => void;
  setFilters: (filters: FilterOptions) => void;
  resetFilters: () => void;
}

const initialFilters: FilterOptions = {
  keyword: '',
  source: '',
  sentiment: '',
  search: '',
  language: '',
  content_type: 'all',
  country: '',
};

export const useStore = create<AppState>((set) => ({
  // Initial state
  keywords: [],
  mentions: [],
  stats: null,
  advancedStats: null,
  sources: [],
  sidebarOpen: true,
  darkMode: false,
  loading: false,
  filters: initialFilters,

  // Actions
  setKeywords: (keywords) => set({ keywords }),
  setMentions: (mentions) => set({ mentions }),
  setStats: (stats) => set({ stats }),
  setAdvancedStats: (advancedStats) => set({ advancedStats }),
  setSources: (sources) => set({ sources }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  toggleDarkMode: () => set((state) => {
    const newDarkMode = !state.darkMode;
    if (newDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('darkMode', String(newDarkMode));
    return { darkMode: newDarkMode };
  }),
  setLoading: (loading) => set({ loading }),
  setFilters: (filters) => set({ filters }),
  resetFilters: () => set({ filters: initialFilters }),
}));

// Initialize dark mode from localStorage
const storedDarkMode = localStorage.getItem('darkMode') === 'true';
if (storedDarkMode) {
  document.documentElement.classList.add('dark');
  useStore.setState({ darkMode: true });
}