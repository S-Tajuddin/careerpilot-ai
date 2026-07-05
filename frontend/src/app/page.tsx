'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  HiOutlineBriefcase,
  HiOutlineClipboardDocumentList,
  HiOutlineMapPin,
  HiOutlineCurrencyDollar,
  HiOutlineArrowTrendingUp,
  HiOutlineGlobeAlt,
  HiOutlineBolt,
  HiOutlineClock,
  HiOutlineArrowPath,
  HiOutlineDocumentText,
} from 'react-icons/hi2';
import { healthCheck, getJobStats, getApplicationStats, getResumeStatus, searchJobsByResume } from '@/lib/api';
import toast from 'react-hot-toast';

interface HealthData {
  status: string;
  database: string;
  ollama: string;
  gemini: string;
}

interface JobStatsData {
  total_active_jobs: number;
  total_scored: number;
  avg_match_score: number;
  remote_jobs: number;
  onsite_jobs: number;
  applications_count: number;
  by_source: Record<string, number>;
  top_companies: { company: string; count: number }[];
}

interface AppStatsData {
  total_applications: number;
  by_status: Record<string, number>;
}

export default function Dashboard() {
  const router = useRouter();
  const [health, setHealth] = useState<HealthData | null>(null);
  const [jobStats, setJobStats] = useState<JobStatsData | null>(null);
  const [appStats, setAppStats] = useState<AppStatsData | null>(null);
  const [recentJobs, setRecentJobs] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [hasResume, setHasResume] = useState(false);
  const [resumeSearching, setResumeSearching] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [h, js, as, rs] = await Promise.allSettled([
        healthCheck(),
        getJobStats(),
        getApplicationStats(),
        getResumeStatus(),
      ]);
      if (h.status === 'fulfilled') setHealth(h.value);
      if (js.status === 'fulfilled') setJobStats(js.value);
      if (as.status === 'fulfilled') setAppStats(as.value);
      if (rs.status === 'fulfilled') setHasResume(rs.value.has_resume);
    } catch (e: any) {
      toast.error('Failed to load dashboard data');
    }
  }

  function handleQuickSearch() {
    if (!searchQuery.trim()) return;
    router.push(`/jobs?q=${encodeURIComponent(searchQuery)}`);
  }

  async function handleResumeSearch() {
    if (!hasResume) {
      router.push('/profile');
      return;
    }
    setResumeSearching(true);
    try {
      const result = await searchJobsByResume(5);
      if (!result.has_resume) {
        router.push('/profile');
        return;
      }
      router.push('/jobs');
      toast.success(`Resume search found ${result.total} jobs!`);
    } catch (e: any) {
      toast.error(e.message || 'Resume search failed');
    } finally {
      setResumeSearching(false);
    }
  }

  const statusColor = (s: string) => {
    if (s === 'ok' || s === 'ready' || s === 'connected') return 'text-emerald-400';
    if (s === 'error' || s === 'unavailable') return 'text-red-400';
    return 'text-amber-400';
  };

  const statusDot = (s: string) => {
    if (s === 'ok' || s === 'ready' || s === 'connected') return 'bg-emerald-400';
    if (s === 'error' || s === 'unavailable') return 'bg-red-400';
    return 'bg-amber-400';
  };

  return (
    <div className="p-6 space-y-6 max-w-[1400px]">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-sm text-slate-400 mt-0.5">Your AEM/EDS career command center</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <HiOutlineClock className="w-3.5 h-3.5" />
          {new Date().toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
        </div>
      </div>

      {/* System Health Strip */}
      {health && (
        <div className="flex gap-3">
          {(['database', 'ollama', 'gemini'] as const).map((service) => (
            <div key={service} className="glass-card px-3 py-2 flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${statusDot(health[service as keyof HealthData] as string)} pulse-dot`} />
              <span className="text-xs text-slate-400 capitalize">{service}</span>
              <span className={`text-xs font-medium ${statusColor(health[service as keyof HealthData] as string)}`}>
                {health[service as keyof HealthData] as string}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Quick Search */}
      <div className="glass-card p-4">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <HiOutlineBriefcase className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
            <input
              type="text"
              placeholder='Search jobs — try "AEM developer" or "EDS architect"'
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleQuickSearch()}
              className="input-dark w-full pl-10"
            />
          </div>
          <button onClick={handleQuickSearch} className="btn-primary flex items-center gap-2">
            <HiOutlineBolt className="w-4 h-4" />
            Search
          </button>
          {hasResume && (
            <button
              onClick={handleResumeSearch}
              disabled={resumeSearching}
              className="bg-gradient-to-r from-brand-500 to-purple-500 hover:from-brand-400 hover:to-purple-400 
                         text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 
                         transition-all disabled:opacity-50 whitespace-nowrap"
            >
              {resumeSearching ? (
                <><HiOutlineArrowPath className="w-4 h-4 animate-spin" /> Searching...</>
              ) : (
                <><HiOutlineDocumentText className="w-4 h-4" /> 🔍 Resume Match</>
              )}
            </button>
          )}
          {!hasResume && (
            <button
              onClick={() => router.push('/profile')}
              className="btn-secondary flex items-center gap-2 whitespace-nowrap"
            >
              <HiOutlineDocumentText className="w-4 h-4" /> Upload Resume
            </button>
          )}
        </div>
      </div>

      {/* Stats Grid — CLICKABLE CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div onClick={() => router.push('/jobs')} className="cursor-pointer">
          <StatsCard
            icon={<HiOutlineBriefcase className="w-6 h-6" />}
            label="Active Jobs"
            value={jobStats?.total_active_jobs ?? 0}
            accent="brand"
            subtitle={`${jobStats?.total_scored ?? 0} scored`}
          />
        </div>
        <div onClick={() => router.push('/applications')} className="cursor-pointer">
          <StatsCard
            icon={<HiOutlineClipboardDocumentList className="w-6 h-6" />}
            label="Applications"
            value={appStats?.total_applications ?? 0}
            accent="emerald"
            subtitle={`${appStats?.by_status?.applied ?? 0} in progress`}
          />
        </div>
        <div onClick={() => router.push('/jobs?remote=true')} className="cursor-pointer">
          <StatsCard
            icon={<HiOutlineGlobeAlt className="w-6 h-6" />}
            label="Remote Jobs"
            value={jobStats?.remote_jobs ?? 0}
            accent="purple"
            subtitle={`${jobStats?.onsite_jobs ?? 0} onsite`}
          />
        </div>
        <div onClick={() => router.push('/jobs?sort=match_score')} className="cursor-pointer">
          <StatsCard
            icon={<HiOutlineArrowTrendingUp className="w-6 h-6" />}
            label="Avg Match"
            value={jobStats?.avg_match_score ? `${jobStats.avg_match_score}%` : '—'}
            accent="amber"
            subtitle="across scored jobs"
          />
        </div>
      </div>

      {/* Two-column: Quick Actions + Top Companies */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quick Actions */}
        <div className="lg:col-span-2 glass-card p-5">
          <h2 className="text-lg font-semibold text-white mb-4">Get Started</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Search Jobs */}
            <div
              onClick={() => router.push('/jobs')}
              className="p-4 rounded-xl bg-brand-500/5 border border-brand-500/20 hover:border-brand-500/40 cursor-pointer transition-all group"
            >
              <HiOutlineBriefcase className="w-8 h-8 text-brand-400 mb-2" />
              <p className="text-sm font-medium text-white group-hover:text-brand-300">Search Jobs</p>
              <p className="text-xs text-slate-500 mt-1">Find AEM/EDS roles across India & Remote</p>
            </div>
            {/* Resume Search */}
            <div
              onClick={() => hasResume ? handleResumeSearch() : router.push('/profile')}
              className="p-4 rounded-xl bg-purple-500/5 border border-purple-500/20 hover:border-purple-500/40 cursor-pointer transition-all group"
            >
              <HiOutlineDocumentText className="w-8 h-8 text-purple-400 mb-2" />
              <p className="text-sm font-medium text-white group-hover:text-purple-300">
                {hasResume ? 'Resume Match' : 'Upload Resume'}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                {hasResume ? 'AI-matched jobs from your resume' : 'Get personalized job matches'}
              </p>
            </div>
            {/* Company Research */}
            <div
              onClick={() => router.push('/company')}
              className="p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/20 hover:border-emerald-500/40 cursor-pointer transition-all group"
            >
              <HiOutlineGlobeAlt className="w-8 h-8 text-emerald-400 mb-2" />
              <p className="text-sm font-medium text-white group-hover:text-emerald-300">Company Intel</p>
              <p className="text-xs text-slate-500 mt-1">Research companies, salary intel, interview tips</p>
            </div>
            {/* Profile */}
            <div
              onClick={() => router.push('/profile')}
              className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/20 hover:border-amber-500/40 cursor-pointer transition-all group"
            >
              <HiOutlineClipboardDocumentList className="w-8 h-8 text-amber-400 mb-2" />
              <p className="text-sm font-medium text-white group-hover:text-amber-300">Update Profile</p>
              <p className="text-xs text-slate-500 mt-1">Skills, salary targets, search preferences</p>
            </div>
          </div>
        </div>

        {/* Top Companies + Source Breakdown */}
        <div className="space-y-6">
          {/* Top Companies */}
          <div className="glass-card p-5">
            <h2 className="text-lg font-semibold text-white mb-4">Top Companies</h2>
            {(!jobStats?.top_companies || jobStats.top_companies.length === 0) ? (
              <p className="text-sm text-slate-500">No company data yet — search for jobs to see stats</p>
            ) : (
              <div className="space-y-2.5">
                {jobStats.top_companies.slice(0, 6).map((c, i) => (
                  <div
                    key={c.company}
                    onClick={() => router.push(`/company?name=${encodeURIComponent(c.company)}`)}
                    className="flex items-center gap-3 cursor-pointer group"
                  >
                    <span className="text-xs text-slate-600 w-4">{i + 1}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-300 truncate group-hover:text-white transition-colors">{c.company}</p>
                      <div className="mt-1 h-1 bg-slate-800 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-brand-500 to-purple-500 rounded-full transition-all duration-500"
                          style={{ width: `${Math.min((c.count / (jobStats.top_companies[0]?.count || 1)) * 100, 100)}%` }}
                        />
                      </div>
                    </div>
                    <span className="text-xs text-slate-500">{c.count}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Source Breakdown */}
          <div className="glass-card p-5">
            <h2 className="text-lg font-semibold text-white mb-4">By Source</h2>
            {(!jobStats?.by_source || Object.keys(jobStats.by_source).length === 0) ? (
              <p className="text-sm text-slate-500">No data yet</p>
            ) : (
              <div className="space-y-2">
                {Object.entries(jobStats.by_source).map(([source, count]) => (
                  <div key={source} className="flex items-center justify-between">
                    <span className="text-sm text-slate-400 capitalize">{source}</span>
                    <span className="text-sm font-medium text-slate-200">{count as number}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Stats Card Component ────────────────────────────────────────────────────
function StatsCard({ icon, label, value, accent, subtitle }: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  accent: 'brand' | 'emerald' | 'purple' | 'amber';
  subtitle?: string;
}) {
  const accentMap = {
    brand: 'from-brand-500/20 to-brand-600/5 text-brand-400 border-brand-500/20',
    emerald: 'from-emerald-500/20 to-emerald-600/5 text-emerald-400 border-emerald-500/20',
    purple: 'from-purple-500/20 to-purple-600/5 text-purple-400 border-purple-500/20',
    amber: 'from-amber-500/20 to-amber-600/5 text-amber-400 border-amber-500/20',
  };
  const iconBgMap = {
    brand: 'bg-brand-500/10 text-brand-400',
    emerald: 'bg-emerald-500/10 text-emerald-400',
    purple: 'bg-purple-500/10 text-purple-400',
    amber: 'bg-amber-500/10 text-amber-400',
  };

  return (
    <div className={`glass-card-hover p-5 bg-gradient-to-br ${accentMap[accent]} active:scale-[0.98] transition-transform`}>
      <div className="flex items-center justify-between mb-3">
        <div className={`w-10 h-10 rounded-lg ${iconBgMap[accent]} flex items-center justify-center`}>
          {icon}
        </div>
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
      <p className="text-sm text-slate-400 mt-0.5">{label}</p>
      {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
    </div>
  );
}
