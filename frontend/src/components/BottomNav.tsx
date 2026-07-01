import { NavLink } from 'react-router-dom';
import { navItems } from './NavItems';

export default function BottomNav() {
  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-50 md:hidden bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 safe-area-bottom"
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="flex items-center justify-around h-16">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              `flex flex-col items-center justify-center min-w-[48px] min-h-[48px] px-2 py-1 rounded-lg transition-colors ${
                isActive
                  ? 'text-blue-600 dark:text-blue-400'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`
            }
            aria-label={item.label}
          >
            <item.icon className="h-5 w-5" aria-hidden="true" />
            <span className="text-[10px] mt-0.5 font-medium">{item.label}</span>
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
