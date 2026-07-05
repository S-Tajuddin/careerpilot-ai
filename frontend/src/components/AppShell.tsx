'use client';

import { useState } from 'react';
import Sidebar from '@/components/Sidebar';
import { HiOutlineBars3 } from 'react-icons/hi2';

export default function AppShell({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const mainMargin = collapsed ? 'md:ml-[72px]' : 'md:ml-64';

  return (
    <>
      <Sidebar
        collapsed={collapsed}
        onCollapsedChange={setCollapsed}
        mobileOpen={mobileOpen}
        onMobileOpenChange={setMobileOpen}
      />

      {mobileOpen && (
        <button
          type="button"
          aria-label="Close menu"
          className="fixed inset-0 z-40 bg-black/60 md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile top bar */}
      <header className="md:hidden sticky top-0 z-30 flex items-center gap-3 px-4 h-14 bg-slate-900/95 backdrop-blur border-b border-slate-800">
        <button
          type="button"
          aria-label="Open menu"
          onClick={() => setMobileOpen(true)}
          className="p-2 rounded-lg text-slate-300 hover:bg-slate-800"
        >
          <HiOutlineBars3 className="w-6 h-6" />
        </button>
        <span className="text-sm font-semibold gradient-text">CareerPilot</span>
      </header>

      <main className={`min-h-screen transition-all duration-300 ml-0 ${mainMargin}`}>
        {children}
      </main>
    </>
  );
}
