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
import { healthCheck, getJobStats, getApplicationStats, getJobs, getResumeStatus, searchJobsByResume } from '@/lib/api';
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
      const [h, js, as, jobs, rs] = await Promise.allSettled([
        healthCheck(),
        getJobStats(),
        getApplicationStats(),
        getJobs({ per_page: 5, sort_by: 'created_at' }),
        getResumeStatus(),
      ]);
      if (h.status === 'fulfilled') setHealth(h.value);
      if (js.status === 'fulfilled') setJobStats(js.value);
      if (as.status === 'fulfilled') setAppStats(as.value);
      if (jobs.status === 'fulfilled') setRecentJobs(jobs.value.jobs || []);
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

      {/* Two-column: Recent Jobs + Top Companies */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Jobs */}
        <div className="lg:col-span-2 glass-card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Recent Jobs</h2>
            <button
              onClick={() => router.push('/jobs')}
              className="text-xs text-brand-400 hover:text-brand-300 transition-colors"
            >
              View all →
            </button>
          </div>
          {recentJobs.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              <HiOutlineBriefcase className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p className="text-sm">No jobs yet. Search for &quot;AEM developer&quot; to get started!</p>
            </div>
          ) : (
            <div className="space-y-2">
              {recentJobs.map((job: any) => (
                <div
                  key={job.id}
                  onClick={() => router.push('/jobs')}
                  className="flex items-center gap-4 p-3 rounded-lg bg-slate-900/40 hover:bg-slate-900/70 transition-all cursor-pointer group"
                >
                  <div className="w-9 h-9 rounded-lg bg-brand-500/10 flex items-center justify-center flex-shrink-0">
                    <span className="text-xs font-bold text-brand-400">
                      {(job.company_name || '?')[0].toUpperCase()}
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium text-slate-200 truncate group-hover:text-white transition-colors">
                      {job.title}
                    </h3>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-xs text-slate-400">{job.company_name}</span>
                      {job.location && (
                        <>
                          <span className="text-slate-700">·</span>
                          <span className="text-xs text-slate-500 flex items-center gap-0.5">
                            <HiOutlineMapPin className="w-3 h-3" /> {job.location}
                          </span>
                        </>
                      )}
                      {job.is_remote && (
                        <span className="text-[10px] font-medium text-purple-400 bg-purple-400/10 px-1.5 py-0.5 rounded">
                          Remote
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {job.salary_display && job.salary_display !== 'Not disclosed' && (
                      <span className="text-xs text-emerald-400 flex items-center gap-0.5">
                        <HiOutlineCurrencyDollar className="w-3.5 h-3.5" /> {job.salary_display}
                      </span>
                    )}
                    {job.match_score != null && (
                      <span className={`text-xs font-bold px-2 py-1 rounded-md ${
                        job.match_score >= 75 ? 'bg-emerald-400/10 text-emerald-400' :
                        job.match_score >= 50 ? 'bg-amber-400/10 text-amber-400' :
                        'bg-slate-400/10 text-slate-400'
                      }`}>
                        {Math.round(job.match_score)}%
                      </span>
                    )}
                    <span className="text-[10px] text-slate-600 uppercase bg-slate-800 px-1.5 py-0.5 rounded">
                      {job.source}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Top Companies + Source Breakdown */}
        <div className="space-y-6">
          {/* Top Companies */}
          <div className="glass-card p-5">
            <h2 className="text-lg font-semibold text-white mb-4">Top Companies</h2>
            {(!jobStats?.top_companies || jobStats.top_companies.length === 0) ? (
              <p className="text-sm text-slate-500">No company data yet</p>
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
