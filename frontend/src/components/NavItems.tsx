import {
  LayoutDashboard,
  Users,
  FileText,
  Shield,
  Settings,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

export interface NavItem {
  path: string;
  label: string;
  icon: LucideIcon;
}

export const navItems: NavItem[] = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/patients', label: 'Patients', icon: Users },
  { path: '/claims', label: 'Claims', icon: FileText },
  { path: '/audit', label: 'Audit', icon: Shield },
  { path: '/settings', label: 'Settings', icon: Settings },
];
