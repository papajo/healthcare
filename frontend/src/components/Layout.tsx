import { useState } from 'react';
import type { ReactNode } from 'react';
import { NavLink } from 'react-router-dom';
import { useMediaQuery } from '../hooks/useMediaQuery';
import { navItems } from './NavItems';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import BottomNav from './BottomNav';

export default function Layout({ children }: { children: ReactNode }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const isDesktop = useMediaQuery('(min-width: 768px)');

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {isDesktop && (
        <Sidebar
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        />
      )}

      {/* Mobile slide-over menu */}
      {!isDesktop && mobileMenuOpen && (
        <div className="fixed inset-0 z-50">
          <div
            className="fixed inset-0 bg-black/50"
            onClick={() => setMobileMenuOpen(false)}
            aria-hidden="true"
          />
          <div className="fixed inset-y-0 left-0 w-72 bg-white dark:bg-gray-900 shadow-xl">
            <nav className="flex flex-col h-full" aria-label="Mobile navigation">
              <div className="flex items-center justify-between px-4 h-16 border-b border-gray-200 dark:border-gray-700">
                <span className="text-lg font-bold text-gray-900 dark:text-white">CCO</span>
                <button
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 min-w-[44px] min-h-[44px] flex items-center justify-center"
                  aria-label="Close menu"
                >
                  <svg className="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="flex-1 py-4 space-y-1 px-2">
                {navItems.map((item) => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    end={item.path === '/'}
                    onClick={() => setMobileMenuOpen(false)}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors min-h-[44px] ${
                        isActive
                          ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 font-medium'
                          : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'
                      }`
                    }
                  >
                    <item.icon className="h-5 w-5 shrink-0" aria-hidden="true" />
                    <span className="text-sm">{item.label}</span>
                  </NavLink>
                ))}
              </div>
            </nav>
          </div>
        </div>
      )}

      <div
        className={`transition-all duration-300 ${
          isDesktop
            ? sidebarCollapsed ? 'md:ml-16' : 'md:ml-64'
            : ''
        }`}
      >
        <TopBar
          onMenuToggle={() => setMobileMenuOpen(!mobileMenuOpen)}
          menuOpen={mobileMenuOpen}
        />
        <main
          className={`p-4 md:p-6 lg:p-8 ${isDesktop ? '' : 'pb-20'}`}
          role="main"
        >
          {children}
        </main>
      </div>

      {!isDesktop && <BottomNav />}
    </div>
  );
}
