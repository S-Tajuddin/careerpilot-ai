'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  HiOutlineHome,
  HiOutlineBriefcase,
  HiOutlineClipboardDocumentList,
  HiOutlineUser,
  HiOutlineBuildingOffice2,
  HiOutlineRocketLaunch,
  HiOutlineCog6Tooth,
  HiOutlineXMark,
} from 'react-icons/hi2';

const navItems = [
  { href: '/', label: 'Dashboard', icon: HiOutlineHome },
  { href: '/jobs', label: 'Jobs', icon: HiOutlineBriefcase },
  { href: '/applications', label: 'Applications', icon: HiOutlineClipboardDocumentList },
  { href: '/company', label: 'Company Intel', icon: HiOutlineBuildingOffice2 },
  { href: '/profile', label: 'Profile', icon: HiOutlineUser },
  { href: '/settings', label: 'Settings', icon: HiOutlineCog6Tooth },
];

interface SidebarProps {
  collapsed: boolean;
  onCollapsedChange: (v: boolean) => void;
  mobileOpen: boolean;
  onMobileOpenChange: (v: boolean) => void;
}

export default function Sidebar({
  collapsed,
  onCollapsedChange,
  mobileOpen,
  onMobileOpenChange,
}: SidebarProps) {
  const pathname = usePathname();

  const widthClass = collapsed ? 'md:w-[72px]' : 'md:w-64';
  const mobileTransform = mobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0';

  return (
    <aside
      className={`fixed top-0 left-0 h-screen bg-slate-900 border-r border-slate-800
                  flex flex-col z-50 transition-all duration-300 w-64 ${widthClass} ${mobileTransform}`}
    >
      <div className="flex items-center justify-between gap-3 px-4 h-16 border-b border-slate-800">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-brand-500 to-purple-500 flex items-center justify-center flex-shrink-0">
            <HiOutlineRocketLaunch className="w-5 h-5 text-white" />
          </div>
          {(!collapsed || mobileOpen) && (
            <div className="overflow-hidden md:block">
              <h1 className="text-lg font-bold gradient-text whitespace-nowrap">CareerPilot</h1>
              <p className="text-[10px] text-slate-500 -mt-0.5 whitespace-nowrap">AI Career Assistant</p>
            </div>
          )}
        </div>
        <button
          type="button"
          aria-label="Close menu"
          onClick={() => onMobileOpenChange(false)}
          className="md:hidden p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800"
        >
          <HiOutlineXMark className="w-5 h-5" />
        </button>
      </div>

      <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
        {navItems.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href || (href !== '/' && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              onClick={() => onMobileOpenChange(false)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group ${
                isActive
                  ? 'bg-brand-600/15 text-brand-400 border border-brand-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent'
              }`}
            >
              <Icon className={`w-5 h-5 flex-shrink-0 ${isActive ? 'text-brand-400' : 'text-slate-500 group-hover:text-slate-300'}`} />
              <span className={`text-sm font-medium whitespace-nowrap ${collapsed ? 'md:hidden' : ''}`}>{label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-3 border-t border-slate-800 hidden md:block">
        <button
          type="button"
          onClick={() => onCollapsedChange(!collapsed)}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-slate-800/50 transition-colors text-xs"
        >
          <svg className={`w-4 h-4 transition-transform ${collapsed ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
          {!collapsed && <span>Collapse</span>}
        </button>
      </div>

      {!collapsed && (
        <div className="px-4 pb-4 hidden md:block">
          <div className="glass-card p-3">
            <div className="flex items-center gap-2 mb-1.5">
              <div className="w-2 h-2 rounded-full bg-emerald-400 pulse-dot" />
              <span className="text-xs text-slate-400">System Status</span>
            </div>
            <p className="text-[11px] text-slate-500">Ollama + Gemini Online</p>
          </div>
        </div>
      )}
    </aside>
  );
}
