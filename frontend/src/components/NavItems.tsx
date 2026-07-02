import {
  LayoutDashboard,
  Users,
  FileText,
  Shield,
  Settings,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import type { UserRole } from '../contexts/AuthContext';

export interface NavItem {
  path: string;
  label: string;
  icon: LucideIcon;
  minRole?: UserRole[]; // if set, only these roles see this item
}

const ALL_NAV_ITEMS: NavItem[] = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/patients', label: 'Patients', icon: Users, minRole: ['ADMIN', 'CLINICIAN', 'NURSE'] },
  { path: '/claims', label: 'Claims', icon: FileText, minRole: ['ADMIN', 'CLINICIAN', 'NURSE'] },
  {
    path: '/audit',
    label: 'Audit',
    icon: Shield,
    minRole: ['ADMIN', 'SYSTEM'],
  },
  { path: '/settings', label: 'Settings', icon: Settings, minRole: ['ADMIN'] },
];

export function getNavItems(userRole: UserRole): NavItem[] {
  return ALL_NAV_ITEMS.filter((item) => {
    if (!item.minRole) return true;
    return item.minRole.includes(userRole);
  });
}

/** Legacy export for backwards compat — returns all items unfiltered */
export const navItems = ALL_NAV_ITEMS;
