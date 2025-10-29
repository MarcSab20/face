import { useState, useEffect, useCallback, useRef } from 'react';
import { useStore } from '@/store/useStore';
import type { FilterOptions } from '@/types';

// Hook pour la pagination
export function usePagination<T>(items: T[], itemsPerPage: number = 20) {
  const [currentPage, setCurrentPage] = useState(1);
  
  const totalPages = Math.ceil(items.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentItems = items.slice(startIndex, endIndex);
  
  const goToPage = (page: number) => {
    setCurrentPage(Math.min(Math.max(1, page), totalPages));
  };
  
  const nextPage = () => goToPage(currentPage + 1);
  const prevPage = () => goToPage(currentPage - 1);
  
  return {
    currentPage,
    totalPages,
    currentItems,
    goToPage,
    nextPage,
    prevPage,
    hasNextPage: currentPage < totalPages,
    hasPrevPage: currentPage > 1,
  };
}

// Hook pour le debounce (optimise les recherches)
export function useDebounce<T>(value: T, delay: number = 500): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

// Hook pour les requêtes API avec loading et erreurs
interface UseApiOptions<T> {
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
}

export function useApi<T, Args extends any[]>(
  apiFunction: (...args: Args) => Promise<{ data: T }>,
  options?: UseApiOptions<T>
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const execute = useCallback(
    async (...args: Args) => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await apiFunction(...args);
        setData(response.data);
        options?.onSuccess?.(response.data);
        return response.data;
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Unknown error');
        setError(error);
        options?.onError?.(error);
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [apiFunction, options]
  );

  return { data, loading, error, execute };
}

// Hook pour la sélection d'éléments multiples
export function useSelection<T extends { id: number }>(items: T[]) {
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  
  const toggleSelection = useCallback((id: number) => {
    setSelectedIds((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  }, []);
  
  const selectAll = useCallback(() => {
    setSelectedIds(new Set(items.map((item) => item.id)));
  }, [items]);
  
  const deselectAll = useCallback(() => {
    setSelectedIds(new Set());
  }, []);
  
  const isSelected = useCallback(
    (id: number) => selectedIds.has(id),
    [selectedIds]
  );
  
  const isAllSelected = items.length > 0 && selectedIds.size === items.length;
  const selectedItems = items.filter((item) => selectedIds.has(item.id));
  
  return {
    selectedIds: Array.from(selectedIds),
    selectedItems,
    isSelected,
    isAllSelected,
    toggleSelection,
    selectAll,
    deselectAll,
    selectedCount: selectedIds.size,
  };
}

// Hook pour le stockage local
export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error('Error reading from localStorage:', error);
      return initialValue;
    }
  });

  const setValue = (value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error('Error writing to localStorage:', error);
    }
  };

  return [storedValue, setValue] as const;
}

// Hook pour les filtres avec synchronisation URL
export function useFilters(initialFilters: FilterOptions = {}) {
  const { filters, setFilters, resetFilters } = useStore();
  const debouncedFilters = useDebounce(filters, 300);

  const updateFilter = useCallback(
    (key: keyof FilterOptions, value: any) => {
      setFilters({ ...filters, [key]: value });
    },
    [filters, setFilters]
  );

  const clearFilters = useCallback(() => {
    resetFilters();
  }, [resetFilters]);

  return {
    filters: debouncedFilters,
    updateFilter,
    clearFilters,
    hasActiveFilters: Object.values(filters).some((v) => v !== '' && v !== undefined),
  };
}

// Hook pour le copier-coller
export function useCopyToClipboard() {
  const [copiedText, setCopiedText] = useState<string | null>(null);

  const copy = async (text: string) => {
    if (!navigator?.clipboard) {
      console.warn('Clipboard not supported');
      return false;
    }

    try {
      await navigator.clipboard.writeText(text);
      setCopiedText(text);
      setTimeout(() => setCopiedText(null), 2000);
      return true;
    } catch (error) {
      console.warn('Copy failed', error);
      setCopiedText(null);
      return false;
    }
  };

  return { copiedText, copy };
}

// Hook pour l'intersection observer (infinite scroll, lazy loading)
export function useIntersectionObserver(
  callback: () => void,
  options: IntersectionObserverInit = {}
) {
  const targetRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const target = targetRef.current;
    if (!target) return;

    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        callback();
      }
    }, options);

    observer.observe(target);

    return () => {
      observer.disconnect();
    };
  }, [callback, options]);

  return targetRef;
}

// Hook pour l'état de la fenêtre (resize, scroll)
export function useWindowSize() {
  const [windowSize, setWindowSize] = useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 0,
    height: typeof window !== 'undefined' ? window.innerHeight : 0,
  });

  useEffect(() => {
    function handleResize() {
      setWindowSize({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    }

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return windowSize;
}

// Hook pour détecter le scroll
export function useScrollPosition() {
  const [scrollPosition, setScrollPosition] = useState(0);

  useEffect(() => {
    function handleScroll() {
      setScrollPosition(window.pageYOffset);
    }

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return scrollPosition;
}

// Hook pour le mode hors ligne
export function useOnlineStatus() {
  const [isOnline, setIsOnline] = useState(
    typeof navigator !== 'undefined' ? navigator.onLine : true
  );

  useEffect(() => {
    function handleOnline() {
      setIsOnline(true);
    }

    function handleOffline() {
      setIsOnline(false);
    }

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
}

// Hook pour le previous value
export function usePrevious<T>(value: T): T | undefined {
  const ref = useRef<T>();

  useEffect(() => {
    ref.current = value;
  }, [value]);

  return ref.current;
}

// Hook pour le toggle
export function useToggle(initialValue: boolean = false) {
  const [value, setValue] = useState(initialValue);

  const toggle = useCallback(() => {
    setValue((v) => !v);
  }, []);

  const setTrue = useCallback(() => {
    setValue(true);
  }, []);

  const setFalse = useCallback(() => {
    setValue(false);
  }, []);

  return { value, toggle, setTrue, setFalse, setValue };
}

// Hook pour le countdown
export function useCountdown(initialSeconds: number) {
  const [seconds, setSeconds] = useState(initialSeconds);
  const [isActive, setIsActive] = useState(false);

  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;

    if (isActive && seconds > 0) {
      interval = setInterval(() => {
        setSeconds((s) => s - 1);
      }, 1000);
    } else if (seconds === 0) {
      setIsActive(false);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isActive, seconds]);

  const start = () => setIsActive(true);
  const pause = () => setIsActive(false);
  const reset = () => {
    setSeconds(initialSeconds);
    setIsActive(false);
  };

  return { seconds, isActive, start, pause, reset };
}

// Hook pour les médias queries
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const media = window.matchMedia(query);
    if (media.matches !== matches) {
      setMatches(media.matches);
    }

    const listener = () => setMatches(media.matches);
    media.addEventListener('change', listener);

    return () => media.removeEventListener('change', listener);
  }, [matches, query]);

  return matches;
}

// Hook pour l'impression
export function usePrint() {
  const print = useCallback(() => {
    window.print();
  }, []);

  return print;
}

// Hook pour le téléchargement de fichier
export function useDownload() {
  const download = useCallback((url: string, filename?: string) => {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || 'download';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, []);

  return download;
}