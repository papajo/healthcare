import { Moon, Sun, Bell, Menu, X } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

interface TopBarProps {
  onMenuToggle: () => void;
  menuOpen: boolean;
}

export default function TopBar({ onMenuToggle, menuOpen }: TopBarProps) {
  const { theme, toggleTheme } = useTheme();

  return (
    <header
      className="sticky top-0 z-30 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm border-b border-gray-200 dark:border-gray-700"
      role="banner"
    >
      <div className="flex items-center justify-between h-16 px-4 md:px-6">
        <div className="flex items-center gap-3">
          <button
            onClick={onMenuToggle}
            className="md:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400 min-w-[44px] min-h-[44px] flex items-center justify-center"
            aria-label={menuOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={menuOpen}
          >
            {menuOpen ? <X className="h-5 w-5" aria-hidden="true" /> : <Menu className="h-5 w-5" aria-hidden="true" />}
          </button>
          <h1 className="text-lg font-bold text-gray-900 dark:text-white md:hidden">
            CCO
          </h1>
        </div>

        <div className="hidden md:flex items-center gap-4">
          <div className="relative">
            <input
              type="search"
              placeholder="Search patients, claims..."
              className="w-64 lg:w-80 px-4 py-2 pl-10 text-sm rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              aria-label="Search"
            />
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400 min-w-[44px] min-h-[44px] flex items-center justify-center"
            aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
          >
            {theme === 'light' ? (
              <Moon className="h-5 w-5" aria-hidden="true" />
            ) : (
              <Sun className="h-5 w-5" aria-hidden="true" />
            )}
          </button>
          <button
            className="relative p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400 min-w-[44px] min-h-[44px] flex items-center justify-center"
            aria-label="Notifications"
          >
            <Bell className="h-5 w-5" aria-hidden="true" />
            <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-red-500" aria-hidden="true" />
          </button>
          <div className="hidden md:flex items-center gap-3 ml-2 pl-4 border-l border-gray-200 dark:border-gray-700">
            <div className="h-8 w-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center text-blue-600 dark:text-blue-400 text-sm font-bold">
              A
            </div>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Admin</span>
          </div>
        </div>
      </div>
    </header>
  );
}
