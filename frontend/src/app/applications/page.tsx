'use client';

import { useEffect, useState } from 'react';
import {
  HiOutlineClipboardDocumentList,
  HiOutlinePaperAirplane,
  HiOutlineChatBubbleLeftRight,
  HiOutlineCheckBadge,
  HiOutlineXMark,
  HiOutlineClock,
  HiOutlineFunnel,
} from 'react-icons/hi2';
import { getApplications, getApplicationStats } from '@/lib/api';
import toast from 'react-hot-toast';

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string; icon: any }> = {
  saved: { label: 'Saved', color: 'text-slate-400', bg: 'bg-slate-400/10 border-slate-400/20', icon: HiOutlineClipboardDocumentList },
  applied: { label: 'Applied', color: 'text-blue-400', bg: 'bg-blue-400/10 border-blue-400/20', icon: HiOutlinePaperAirplane },
  interview_scheduled: { label: 'Interview', color: 'text-amber-400', bg: 'bg-amber-400/10 border-amber-400/20', icon: HiOutlineChatBubbleLeftRight },
  interview_done: { label: 'Interviewed', color: 'text-purple-400', bg: 'bg-purple-400/10 border-purple-400/20', icon: HiOutlineChatBubbleLeftRight },
  offer: { label: 'Offer', color: 'text-emerald-400', bg: 'bg-emerald-400/10 border-emerald-400/20', icon: HiOutlineCheckBadge },
  rejected: { label: 'Rejected', color: 'text-red-400', bg: 'bg-red-400/10 border-red-400/20', icon: HiOutlineXMark },
  withdrawn: { label: 'Withdrawn', color: 'text-slate-500', bg: 'bg-slate-500/10 border-slate-500/20', icon: HiOutlineXMark },
};

const PIPELINE_ORDER = ['saved', 'applied', 'interview_scheduled', 'interview_done', 'offer', 'rejected', 'withdrawn'];

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('');
  const [viewMode, setViewMode] = useState<'list' | 'kanban'>('kanban');

  useEffect(() => {
    loadData();
  }, [filterStatus]);

  async function loadData() {
    setLoading(true);
    try {
      const params: any = { per_page: 100 };
      if (filterStatus) params.status = filterStatus;
      const [apps, s] = await Promise.allSettled([
        getApplications(params),
        getApplicationStats(),
      ]);
      if (apps.status === 'fulfilled') setApplications(apps.value.applications || []);
      if (s.status === 'fulfilled') setStats(s.value);
    } catch (e: any) {
      toast.error('Failed to load applications');
    } finally {
      setLoading(false);
    }
  }

  const byStatus = PIPELINE_ORDER.reduce((acc, status) => {
    acc[status] = applications.filter((a: any) => a.status === status);
    return acc;
  }, {} as Record<string, any[]>);

  const statusCount = (status: string) => byStatus[status]?.length || 0;

  return (
    <div className="p-6 space-y-6 max-w-[1400px]">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Applications</h1>
          <p className="text-sm text-slate-400 mt-0.5">Track your job applications pipeline</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setViewMode('kanban')}
            className={`px-3 py-1.5 text-xs rounded-lg transition-colors ${
              viewMode === 'kanban' ? 'bg-brand-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            Kanban
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`px-3 py-1.5 text-xs rounded-lg transition-colors ${
              viewMode === 'list' ? 'bg-brand-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            List
          </button>
        </div>
      </div>

      {/* Pipeline Stats */}
      {stats && (
        <div className="grid grid-cols-7 gap-2">
          {PIPELINE_ORDER.map((status) => {
            const cfg = STATUS_CONFIG[status];
            const count = stats.by_status?.[status] || 0;
            return (
              <div key={status} className="glass-card p-3 text-center">
                <p className={`text-lg font-bold ${cfg.color}`}>{count}</p>
                <p className="text-[10px] text-slate-500 mt-0.5">{cfg.label}</p>
              </div>
            );
          })}
        </div>
      )}

      {/* Filter */}
      <div className="flex items-center gap-2">
        <HiOutlineFunnel className="w-4 h-4 text-slate-500" />
        <span className="text-xs text-slate-500">Filter:</span>
        {PIPELINE_ORDER.map((status) => {
          const cfg = STATUS_CONFIG[status];
          const isActive = filterStatus === status;
          return (
            <button
              key={status}
              onClick={() => setFilterStatus(isActive ? '' : status)}
              className={`text-xs px-2.5 py-1 rounded-full border transition-all ${
                isActive ? `${cfg.bg} ${cfg.color}` : 'border-slate-700 text-slate-500 hover:border-slate-600'
              }`}
            >
              {cfg.label} ({statusCount(status)})
            </button>
          );
        })}
      </div>

      {/* Kanban View */}
      {viewMode === 'kanban' ? (
        <div className="grid grid-cols-5 gap-4 overflow-x-auto">
          {['saved', 'applied', 'interview_scheduled', 'interview_done', 'offer'].map((status) => {
            const cfg = STATUS_CONFIG[status];
            const apps = byStatus[status] || [];
            return (
              <div key={status} className="min-w-[220px]">
                <div className="flex items-center gap-2 mb-3">
                  <div className={`w-2 h-2 rounded-full ${cfg.bg.includes('blue') ? 'bg-blue-400' : cfg.bg.includes('amber') ? 'bg-amber-400' : cfg.bg.includes('purple') ? 'bg-purple-400' : cfg.bg.includes('emerald') ? 'bg-emerald-400' : 'bg-slate-400'}`} />
                  <h3 className={`text-xs font-semibold ${cfg.color}`}>{cfg.label}</h3>
                  <span className="text-[10px] text-slate-600 bg-slate-800 px-1.5 rounded">{apps.length}</span>
                </div>
                <div className="space-y-2 max-h-[calc(100vh-300px)] overflow-y-auto">
                  {apps.map((app: any) => (
                    <div key={app.id} className="glass-card p-3 hover:border-slate-600 transition-colors cursor-pointer">
                      <h4 className="text-xs font-medium text-slate-200 line-clamp-2">{app.job_title || 'Untitled'}</h4>
                      <p className="text-[10px] text-slate-500 mt-1">{app.company_name || 'Unknown'}</p>
                      {app.notes && (
                        <p className="text-[10px] text-slate-600 mt-1.5 line-clamp-2">{app.notes}</p>
                      )}
                      <div className="flex items-center gap-1 mt-2">
                        <HiOutlineClock className="w-3 h-3 text-slate-600" />
                        <span className="text-[10px] text-slate-600">
                          {new Date(app.created_at).toLocaleDateString('en-IN')}
                        </span>
                      </div>
                    </div>
                  ))}
                  {apps.length === 0 && (
                    <div className="text-center py-6 text-slate-700 text-xs">No items</div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* List View */
        <div className="space-y-2">
          {applications.length === 0 ? (
            <div className="glass-card p-12 text-center">
              <HiOutlineClipboardDocumentList className="w-16 h-16 mx-auto mb-4 text-slate-700" />
              <h3 className="text-lg font-medium text-slate-400 mb-2">No applications yet</h3>
              <p className="text-sm text-slate-500">
                Apply to jobs from the Jobs page — they&apos;ll appear here automatically.
              </p>
            </div>
          ) : (
            applications.map((app: any) => {
              const cfg = STATUS_CONFIG[app.status] || STATUS_CONFIG.saved;
              return (
                <div key={app.id} className="glass-card-hover p-4 flex items-center gap-4">
                  <div className={`w-10 h-10 rounded-lg ${cfg.bg} border flex items-center justify-center`}>
                    <cfg.icon className={`w-5 h-5 ${cfg.color}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium text-white truncate">{app.job_title || 'Untitled'}</h3>
                    <p className="text-xs text-slate-400">{app.company_name} · {app.job_location || 'Remote'}</p>
                  </div>
                  <span className={`text-[10px] font-medium px-2.5 py-1 rounded-full ${cfg.bg} ${cfg.color} border`}>
                    {cfg.label}
                  </span>
                  <span className="text-[10px] text-slate-600">{new Date(app.created_at).toLocaleDateString('en-IN')}</span>
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}
