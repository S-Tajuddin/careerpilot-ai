'use client';

import { useEffect, useState } from 'react';
import {
  HiOutlineBriefcase,
  HiOutlineMapPin,
  HiOutlineCurrencyDollar,
  HiOutlineFunnel,
  HiOutlineMagnifyingGlass,
  HiOutlineGlobeAlt,
  HiOutlineClock,
  HiOutlineArrowPath,
  HiOutlineChevronLeft,
  HiOutlineChevronRight,
  HiOutlineStar,
  HiOutlineBolt,
  HiOutlineBookmark,
  HiOutlineArrowTopRightOnSquare,
} from 'react-icons/hi2';
import { searchJobs, getJobs, getJobStats } from '@/lib/api';
import toast from 'react-hot-toast';

const QUICK_SEARCHES = [
  { label: 'AEM Developer', query: 'AEM developer', location: 'India' },
  { label: 'EDS Engineer', query: 'Experience Delivery Solution engineer', location: 'India' },
  { label: 'AEM Architect', query: 'AEM architect senior', location: 'India' },
  { label: 'Remote AEM', query: 'AEM developer remote', location: '' },
  { label: 'CQ5 Developer', query: 'CQ5 developer', location: 'India' },
  { label: 'Adobe Developer', query: 'Adobe developer', location: 'Hyderabad India' },
];

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function JobsPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [location, setLocation] = useState('India');
  const [remoteOnly, setRemoteOnly] = useState(false);
  const [datePosted, setDatePosted] = useState('');
  const [sortBy, setSortBy] = useState('created_at');
  const [selectedJob, setSelectedJob] = useState<any>(null);
  const [scoringAll, setScoringAll] = useState(false);
  const [scoreDetail, setScoreDetail] = useState<any>(null);

  useEffect(() => {
    loadSavedJobs();
  }, [page]);

  async function loadSavedJobs() {
    try {
      const data = await getJobs({ page, per_page: 15, sort_by: sortBy, sort_order: 'desc' });
      setJobs(data.jobs || []);
      setTotal(data.total || 0);
    } catch (e: any) {
      toast.error('Failed to load jobs');
    }
  }

  async function handleSearch() {
    if (!searchQuery.trim()) return;
    setLoading(true);
    try {
      const results = await searchJobs({
        query: searchQuery,
        location: location || undefined,
        remote_only: remoteOnly,
        date_posted: datePosted || undefined,
        max_results: 20,
      });
      setJobs(results.jobs || []);
      setTotal(results.total || 0);
      toast.success(`Found ${results.total} jobs for "${searchQuery}"`);
    } catch (e: any) {
      toast.error(e.message || 'Search failed');
    } finally {
      setLoading(false);
    }
  }

  async function handleQuickSearch(q: string, loc: string) {
    setSearchQuery(q);
    setLocation(loc);
    setLoading(true);
    try {
      const results = await searchJobs({
        query: q,
        location: loc || undefined,
        remote_only: remoteOnly,
        max_results: 20,
      });
      setJobs(results.jobs || []);
      setTotal(results.total || 0);
      toast.success(`Found ${results.total} jobs for "${q}"`);
    } catch (e: any) {
      toast.error(e.message || 'Search failed');
    } finally {
      setLoading(false);
    }
  }

  async function handleScoreAll(mode: 'quick' | 'deep' = 'quick') {
    setScoringAll(true);
    try {
      const res = await fetch(`${API_URL}/api/jobs/score/batch?mode=${mode}`, { method: 'POST' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Scoring failed');
      toast.success(data.message || 'Scoring complete');
      loadSavedJobs();
    } catch (e: any) {
      toast.error(e.message || 'Scoring failed');
    } finally {
      setScoringAll(false);
    }
  }

  async function handleScoreSingle(jobId: number) {
    try {
      const res = await fetch(`${API_URL}/api/jobs/score`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: jobId }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Scoring failed');
      toast.success(`Scored: ${data.match_score}%`);
      // Update job in list
      setJobs(prev => prev.map(j => j.id === jobId ? { ...j, match_score: data.match_score, match_strengths: data.match_strengths, match_weaknesses: data.match_weaknesses, match_recommendations: data.match_recommendations } : j));
    } catch (e: any) {
      toast.error(e.message || 'Scoring failed');
    }
  }

  async function handleViewScoreDetail(jobId: number) {
    try {
      const res = await fetch(`${API_URL}/api/jobs/${jobId}/score-detail`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to load score detail');
      setScoreDetail(data);
    } catch (e: any) {
      toast.error(e.message || 'Failed to load score detail');
    }
  }

  function scoreBadge(score: number | null) {
    if (score == null) return null;
    const cls = score >= 75 ? 'bg-emerald-400/10 text-emerald-400 ring-emerald-400/20' :
                score >= 50 ? 'bg-amber-400/10 text-amber-400 ring-amber-400/20' :
                'bg-slate-400/10 text-slate-400 ring-slate-400/20';
    return <span className={`text-xs font-bold px-2 py-1 rounded-md ring-1 ring-inset ${cls}`}>{score}%</span>;
  }

  const totalPages = Math.ceil(total / 15);

  return (
    <div className="p-6 space-y-6 max-w-[1400px]">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Job Search</h1>
          <p className="text-sm text-slate-400 mt-0.5">Search across JSearch + Adzuna for AEM/EDS roles</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleScoreAll('quick')}
            disabled={scoringAll}
            className="btn-secondary flex items-center gap-2 text-xs"
            title="Instant deterministic scoring — no AI calls"
          >
            {scoringAll ? (
              <><HiOutlineArrowPath className="w-4 h-4 animate-spin" /> Scoring...</>
            ) : (
              <><HiOutlineStar className="w-4 h-4" /> ⚡ Score All</>
            )}
          </button>
          <button
            onClick={() => handleScoreAll('deep')}
            disabled={scoringAll}
            className="btn-primary flex items-center gap-2 text-xs"
            title="Full AI analysis with recommendations — slower"
          >
            {scoringAll ? (
              <><HiOutlineArrowPath className="w-4 h-4 animate-spin" /> Scoring...</>
            ) : (
              <><HiOutlineBolt className="w-4 h-4" /> 🧠 Deep Score</>
            )}
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="glass-card p-5 space-y-4">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <HiOutlineMagnifyingGlass className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
            <input
              type="text"
              placeholder='e.g. "AEM developer", "Adobe Experience Manager architect"'
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="input-dark w-full pl-10"
            />
          </div>
          <div className="w-48 relative">
            <HiOutlineMapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              placeholder="Location"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="input-dark w-full pl-9"
            />
          </div>
          <button onClick={handleSearch} disabled={loading} className="btn-primary flex items-center gap-2 whitespace-nowrap">
            {loading ? <HiOutlineArrowPath className="w-4 h-4 animate-spin" /> : <HiOutlineMagnifyingGlass className="w-4 h-4" />}
            {loading ? 'Searching...' : 'Search APIs'}
          </button>
        </div>

        {/* Filters Row */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <HiOutlineFunnel className="w-4 h-4 text-slate-500" />
            <span className="text-xs text-slate-500">Filters:</span>
          </div>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={remoteOnly}
              onChange={(e) => setRemoteOnly(e.target.checked)}
              className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-brand-500 focus:ring-brand-500 focus:ring-offset-0"
            />
            <span className="text-xs text-slate-400 flex items-center gap-1">
              <HiOutlineGlobeAlt className="w-3.5 h-3.5" /> Remote only
            </span>
          </label>
          <select
            value={datePosted}
            onChange={(e) => setDatePosted(e.target.value)}
            className="input-dark text-xs py-1.5 px-2"
          >
            <option value="">Any time</option>
            <option value="today">Today</option>
            <option value="3days">Last 3 days</option>
            <option value="week">This week</option>
            <option value="month">This month</option>
          </select>
          <select
            value={sortBy}
            onChange={(e) => { setSortBy(e.target.value); loadSavedJobs(); }}
            className="input-dark text-xs py-1.5 px-2"
          >
            <option value="created_at">Newest first</option>
            <option value="match_score">Best match</option>
            <option value="posted_date">Posted date</option>
          </select>
        </div>

        {/* Quick Search Chips */}
        <div className="flex flex-wrap gap-2">
          {QUICK_SEARCHES.map((qs) => (
            <button
              key={qs.label}
              onClick={() => handleQuickSearch(qs.query, qs.location)}
              className="text-xs px-3 py-1.5 rounded-full bg-slate-800/80 text-slate-300 border border-slate-700/50 
                         hover:border-brand-500/30 hover:text-brand-300 transition-all duration-200"
            >
              {qs.label}
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-400">
          {total > 0 ? `${total} jobs found` : 'No jobs yet — search above to discover opportunities'}
        </p>
      </div>

      {jobs.length === 0 ? (
        <div className="glass-card p-12 text-center">
          <HiOutlineBriefcase className="w-16 h-16 mx-auto mb-4 text-slate-700" />
          <h3 className="text-lg font-medium text-slate-400 mb-2">No jobs to display</h3>
          <p className="text-sm text-slate-500 max-w-md mx-auto">
            Use the search bar above to find AEM/EDS roles across India and remote. 
            Try clicking one of the quick search chips!
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {jobs.map((job: any) => (
            <div
              key={job.id}
              onClick={() => setSelectedJob(selectedJob?.id === job.id ? null : job)}
              className={`glass-card-hover p-4 cursor-pointer ${
                selectedJob?.id === job.id ? 'border-brand-500/40 ring-1 ring-brand-500/20' : ''
              }`}
            >
              <div className="flex items-start gap-4">
                {/* Company initial */}
                <div className="w-10 h-10 rounded-lg bg-brand-500/10 flex items-center justify-center flex-shrink-0">
                  <span className="text-sm font-bold text-brand-400">
                    {(job.company_name || '?')[0].toUpperCase()}
                  </span>
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="text-sm font-semibold text-white hover:text-brand-300 transition-colors">
                        {job.title}
                      </h3>
                      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1">
                        <span className="text-xs text-slate-300">{job.company_name}</span>
                        {job.location && (
                          <span className="text-xs text-slate-500 flex items-center gap-1">
                            <HiOutlineMapPin className="w-3 h-3" /> {job.location}
                          </span>
                        )}
                        {job.is_remote && (
                          <span className="text-[10px] font-medium text-purple-400 bg-purple-400/10 px-1.5 py-0.5 rounded">
                            Remote
                          </span>
                        )}
                        {job.job_type && (
                          <span className="text-[10px] text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded capitalize">
                            {job.job_type}
                          </span>
                        )}
                        {job.posted_date && (
                          <span className="text-xs text-slate-600 flex items-center gap-1">
                            <HiOutlineClock className="w-3 h-3" /> {new Date(job.posted_date).toLocaleDateString('en-IN')}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {job.salary_display && (
                        <span className="text-xs text-emerald-400 flex items-center gap-1">
                          <HiOutlineCurrencyDollar className="w-3.5 h-3.5" /> {job.salary_display}
                        </span>
                      )}
                      {scoreBadge(job.match_score)}
                      <span className="text-[10px] text-slate-600 uppercase">{job.source}</span>
                    </div>
                  </div>

                  {/* Skills */}
                  {job.skills_required?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {job.skills_required.slice(0, 8).map((skill: string) => (
                        <span key={skill} className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700/50">
                          {skill}
                        </span>
                      ))}
                      {job.skills_required.length > 8 && (
                        <span className="text-[10px] px-2 py-0.5 text-slate-600">+{job.skills_required.length - 8} more</span>
                      )}
                    </div>
                  )}

                  {/* Expanded detail */}
                  {selectedJob?.id === job.id && (
                    <div className="mt-3 pt-3 border-t border-slate-700/50 space-y-3" onClick={(e) => e.stopPropagation()}>
                      {job.description && (
                        <div className="text-xs text-slate-400 leading-relaxed max-h-40 overflow-y-auto whitespace-pre-line">
                          {job.description.slice(0, 1500)}
                          {job.description.length > 1500 && '...'}
                        </div>
                      )}
                      {job.match_strengths?.length > 0 && (
                        <div>
                          <p className="text-xs font-medium text-emerald-400 mb-1">Strengths</p>
                          <div className="flex flex-wrap gap-1.5">
                            {job.match_strengths.map((s: string) => (
                              <span key={s} className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-400/10 text-emerald-400 border border-emerald-400/20">
                                {s}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      {job.match_weaknesses?.length > 0 && (
                        <div>
                          <p className="text-xs font-medium text-amber-400 mb-1">Gaps</p>
                          <div className="flex flex-wrap gap-1.5">
                            {job.match_weaknesses.map((w: string) => (
                              <span key={w} className="text-[10px] px-2 py-0.5 rounded-full bg-amber-400/10 text-amber-400 border border-amber-400/20">
                                {w}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      {job.match_recommendations?.length > 0 && (
                        <div>
                          <p className="text-xs font-medium text-brand-400 mb-1">AI Recommendations</p>
                          <ul className="space-y-1">
                            {job.match_recommendations.map((r: string, i: number) => (
                              <li key={i} className="text-[11px] text-slate-400 flex gap-2">
                                <span className="text-brand-500 mt-0.5">→</span>
                                <span>{r}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      <div className="flex gap-2">
                        {job.source_url && (
                          <a
                            href={job.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn-primary text-xs flex items-center gap-1"
                          >
                            <HiOutlineArrowTopRightOnSquare className="w-3.5 h-3.5" /> Apply on {job.source}
                          </a>
                        )}
                        {job.match_score == null ? (
                          <button
                            onClick={() => handleScoreSingle(job.id)}
                            className="btn-secondary text-xs flex items-center gap-1"
                          >
                            <HiOutlineStar className="w-3.5 h-3.5" /> 🧠 AI Analyze
                          </button>
                        ) : (
                          <button
                            onClick={() => handleViewScoreDetail(job.id)}
                            className="btn-secondary text-xs flex items-center gap-1"
                          >
                            <HiOutlineStar className="w-3.5 h-3.5" /> Score Detail
                          </button>
                        )}
                        <button className="btn-secondary text-xs flex items-center gap-1">
                          <HiOutlineBookmark className="w-3.5 h-3.5" /> Save
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-4">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="btn-secondary text-xs flex items-center gap-1 disabled:opacity-30"
          >
            <HiOutlineChevronLeft className="w-4 h-4" /> Prev
          </button>
          <span className="text-xs text-slate-500">Page {page} of {totalPages}</span>
          <button
            onClick={() => setPage(Math.min(totalPages, page + 1))}
            disabled={page === totalPages}
            className="btn-secondary text-xs flex items-center gap-1 disabled:opacity-30"
          >
            Next <HiOutlineChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Score Detail Modal */}
      {scoreDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setScoreDetail(null)}>
          <div className="glass-card p-6 w-full max-w-lg space-y-4" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-white">{scoreDetail.title}</h2>
                <p className="text-sm text-slate-400">{scoreDetail.company_name} · {scoreDetail.location || 'Remote'}</p>
              </div>
              <button onClick={() => setScoreDetail(null)} className="text-slate-500 hover:text-slate-300 text-xl">×</button>
            </div>

            {/* Overall Score */}
            <div className="flex items-center gap-4">
              <div className={`w-20 h-20 rounded-full flex items-center justify-center border-4 ${
                scoreDetail.overall_score >= 75 ? 'border-emerald-400 bg-emerald-400/10' :
                scoreDetail.overall_score >= 50 ? 'border-amber-400 bg-amber-400/10' :
                'border-slate-400 bg-slate-400/10'
              }`}>
                <span className={`text-2xl font-bold ${
                  scoreDetail.overall_score >= 75 ? 'text-emerald-400' :
                  scoreDetail.overall_score >= 50 ? 'text-amber-400' : 'text-slate-400'
                }`}>
                  {scoreDetail.overall_score}
                </span>
              </div>
              <div>
                <p className="text-sm font-medium text-white">Overall Match Score</p>
                <p className="text-xs text-slate-500 mt-0.5">Weighted across 6 dimensions</p>
              </div>
            </div>

            {/* Strengths */}
            {scoreDetail.strengths?.length > 0 && (
              <div>
                <p className="text-xs font-medium text-emerald-400 mb-2">✅ Strengths</p>
                <ul className="space-y-1">
                  {scoreDetail.strengths.map((s: string, i: number) => (
                    <li key={i} className="text-xs text-slate-300 flex gap-2"><span className="text-emerald-500">+</span>{s}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Weaknesses */}
            {scoreDetail.weaknesses?.length > 0 && (
              <div>
                <p className="text-xs font-medium text-amber-400 mb-2">⚠️ Gaps</p>
                <ul className="space-y-1">
                  {scoreDetail.weaknesses.map((w: string, i: number) => (
                    <li key={i} className="text-xs text-slate-300 flex gap-2"><span className="text-amber-500">-</span>{w}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Recommendations */}
            {scoreDetail.recommendations?.length > 0 && (
              <div>
                <p className="text-xs font-medium text-brand-400 mb-2">🎯 AI Recommendations</p>
                <ul className="space-y-1.5">
                  {scoreDetail.recommendations.map((r: string, i: number) => (
                    <li key={i} className="text-xs text-slate-300 flex gap-2"><span className="text-brand-500">→</span>{r}</li>
                  ))}
                </ul>
              </div>
            )}

            <button onClick={() => setScoreDetail(null)} className="btn-primary w-full text-sm">Close</button>
          </div>
        </div>
      )}
    </div>
  );
}
