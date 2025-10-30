import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Search,
  MessageSquare,
  BarChart3,
  Settings,
  X,
  Users,
  Globe,
  Menu,
  Moon,
  Sun,
} from 'lucide-react';
import { useStore } from '@/store/useStore';
import { cn } from '@/lib/utils';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Mots-clés', href: '/keywords', icon: Search },
  { name: 'Mentions', href: '/mentions', icon: MessageSquare },
  { name: 'Influenceurs', href: '/influencers', icon: Users },  // Nouveau
  { name: 'Géographie', href: '/geography', icon: Globe },  
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Paramètres', href: '/settings', icon: Settings },
];

export default function Sidebar() {
  const location = useLocation();
  const { sidebarOpen, toggleSidebar, darkMode, toggleDarkMode } = useStore();

  return (
    <>
      {/* Mobile backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={toggleSidebar}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 transform bg-white dark:bg-gray-900 shadow-xl transition-transform duration-300 lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex h-full flex-col">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center space-x-2">
              <div className="rounded-lg bg-gradient-to-br from-primary-500 to-secondary-500 p-2">
                <Search className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                  Brand Monitor
                </h1>
                <p className="text-xs text-gray-500 dark:text-gray-400">Pro v2.0</p>
              </div>
            </div>
            <button
              onClick={toggleSidebar}
              className="lg:hidden rounded-lg p-2 hover:bg-gray-100 dark:hover:bg-gray-800"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 p-4 overflow-y-auto">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    'flex items-center space-x-3 rounded-lg px-4 py-3 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-gradient-to-r from-primary-500 to-secondary-500 text-white shadow-lg'
                      : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800'
                  )}
                >
                  <item.icon className="h-5 w-5" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="border-t border-gray-200 dark:border-gray-700 p-4 space-y-2">
            {/* Dark Mode Toggle */}
            <button
              onClick={toggleDarkMode}
              className="flex w-full items-center space-x-3 rounded-lg px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
            >
              {darkMode ? (
                <>
                  <Sun className="h-5 w-5" />
                  <span>Mode Clair</span>
                </>
              ) : (
                <>
                  <Moon className="h-5 w-5" />
                  <span>Mode Sombre</span>
                </>
              )}
            </button>

            {/* User Info */}
            <div className="rounded-lg bg-gradient-to-br from-primary-50 to-secondary-50 dark:from-gray-800 dark:to-gray-700 p-4">
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                Compte Gratuit
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                Sources illimitées
              </p>
            </div>
          </div>
        </div>
      </aside>

      {/* Mobile header */}
      <header className="fixed top-0 left-0 right-0 z-30 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 lg:hidden">
        <div className="flex items-center justify-between p-4">
          <button
            onClick={toggleSidebar}
            className="rounded-lg p-2 hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            <Menu className="h-6 w-6" />
          </button>
          <h1 className="text-lg font-bold text-gray-900 dark:text-white">
            Brand Monitor
          </h1>
          <div className="w-10" /> {/* Spacer */}
        </div>
      </header>
    </>
  );
}