'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  HiOutlineBriefcase,
  HiOutlineMapPin,
  HiOutlineCurrencyDollar,
  HiOutlineFunnel,
  HiOutlineMagnifyingGlass,
  HiOutlineGlobeAlt,
  HiOutlineClock,
  HiOutlineArrowPath,
  HiOutlineDocumentText,
  HiOutlineSparkles,
  HiOutlineEnvelope,
  HiOutlineArrowDownTray,
} from 'react-icons/hi2';
import { getJobs, searchJobs, searchJobsByResume, getResumeStatus, getResumeSearchQueries, generateCoverLetter, tailorResume, downloadCoverLetterUrl, scoreJob, getJobScoreDetail, createApplication } from '@/lib/api';
import { JobDetailPanel } from '@/components/JobDetailPanel';
import { ScoreBadge } from '@/components/ScoreBadge';
import { isAEMSkill } from '@/lib/utils';
import { jobDetailFromRecord } from '@/lib/jobs';
import toast from 'react-hot-toast';

function JobsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [jobs, setJobs] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [hasSearched, setHasSearched] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [location, setLocation] = useState('India');
  const [remoteOnly, setRemoteOnly] = useState(false);
  const [datePosted, setDatePosted] = useState('');
  const [selectedJob, setSelectedJob] = useState<any>(null);
  const [scoreDetail, setScoreDetail] = useState<any>(null);
  const [hasResume, setHasResume] = useState(false);
  const [resumeSearching, setResumeSearching] = useState(false);
  const [resumeQueries, setResumeQueries] = useState<any[]>([]);
  const [searchMode, setSearchMode] = useState<'manual' | 'resume' | 'saved'>('saved');
  const [searchChips, setSearchChips] = useState<Array<{label: string; query: string; location: string; source: 'resume'}>>([]);
  const [generatingDoc, setGeneratingDoc] = useState<{type: 'cover_letter' | 'tailored_resume' | null; jobId: number | null}>({type: null, jobId: null});
  const [coverLetterModal, setCoverLetterModal] = useState<{content: string; id: number; jobId: number} | null>(null);

  useEffect(() => {
    const q = searchParams.get('q');
    const loc = searchParams.get('loc');
    const remote = searchParams.get('remote') === 'true';
    const sortBy = searchParams.get('sort_by') || searchParams.get('sort') || 'match_score';

    if (q) {
      setSearchQuery(q);
      setLocation(loc || 'India');
      if (remote) setRemoteOnly(true);
      handleSearchWithQuery(q, loc || 'India', remote);
    } else {
      if (remote) setRemoteOnly(true);
      loadSavedJobs({ remoteOnly: remote, sortBy });
    }
    loadSearchConfig();
  }, []);

  async function loadSearchConfig() {
    const [rs, rq] = await Promise.allSettled([
      getResumeStatus(),
      getResumeSearchQueries(),
    ]);
    if (rs.status === 'fulfilled') setHasResume(rs.value.has_resume);

    type Chip = { label: string; query: string; location: string; source: 'resume' };

    const resumeChips: Chip[] = [];
    if (rq.status === 'fulfilled' && rq.value.has_resume && rq.value.queries) {
      for (const q of rq.value.queries) {
        resumeChips.push({ label: q.label || q.query, query: q.query, location: q.location || 'India', source: 'resume' });
      }
    }

    // Deduplicate by query text
    const seen = new Set<string>();
    const merged: Chip[] = [];
    for (const c of resumeChips) {
      const key = c.query.toLowerCase();
      if (!seen.has(key)) { seen.add(key); merged.push(c); }
    }
    setSearchChips(merged);
  }

  async function loadSavedJobs(options?: { remoteOnly?: boolean; sortBy?: string }) {
    setLoading(true);
    setHasSearched(true);
    setSearchMode('saved');
    try {
      const params: Record<string, string | number | boolean> = {
        per_page: 50,
        sort_by: options?.sortBy || 'match_score',
        sort_order: 'desc',
      };
      if (options?.remoteOnly) params.is_remote = true;

      const results = await getJobs(params);
      setJobs(results.jobs || []);
      setTotal(results.total || 0);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to load saved jobs');
    } finally {
      setLoading(false);
    }
  }

  async function handleSearchWithQuery(q: string, loc: string, remote: boolean) {
    setLoading(true);
    setHasSearched(true);
    setSearchMode('manual');
    try {
      const results = await searchJobs({ query: q, location: loc || undefined, remote_only: remote, max_results: 20 });
      setJobs(results.jobs || []);
      setTotal(results.total || 0);
      if (results.total > 0) toast.success(`Found ${results.total} jobs for "${q}"`);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  }

  async function handleSearch() {
    if (!searchQuery.trim()) return;
    setLoading(true);
    setHasSearched(true);
    setSearchMode('manual');
    try {
      const results = await searchJobs({ query: searchQuery, location: location || undefined, remote_only: remoteOnly, date_posted: datePosted || undefined, max_results: 20 });
      setJobs(results.jobs || []);
      setTotal(results.total || 0);
      toast.success(`Found ${results.total} jobs for "${searchQuery}"`);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  }

  async function handleQuickSearch(q: string, loc: string) {
    setSearchQuery(q);
    setLocation(loc);
    setLoading(true);
    setHasSearched(true);
    setSearchMode('manual');
    try {
      const results = await searchJobs({ query: q, location: loc || undefined, remote_only: remoteOnly, max_results: 20 });
      setJobs(results.jobs || []);
      setTotal(results.total || 0);
      toast.success(`Found ${results.total} jobs for "${q}"`);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  }

  async function handleResumeSearch() {
    if (!hasResume) {
      toast.error('Upload your resume first in the Profile page');
      router.push('/profile');
      return;
    }
    setResumeSearching(true);
    setHasSearched(true);
    setSearchMode('resume');
    setLoading(true);
    try {
      const result = await searchJobsByResume(5);
      if (!result.has_resume) {
        toast.error('Upload your resume first in the Profile page');
        router.push('/profile');
        return;
      }
      setJobs(result.jobs || []);
      setTotal(result.total || 0);
      setResumeQueries(result.queries_used || []);
      toast.success(`Resume search complete! Found ${result.total} jobs across ${result.queries_used?.length || 0} queries`);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Resume search failed');
    } finally {
      setLoading(false);
      setResumeSearching(false);
    }
  }

  async function handleScoreSingle(jobId: number) {
    try {
      const data = await scoreJob(jobId);
      toast.success(`Scored: ${data.match_score}%`);
      setJobs(prev => prev.map(j => j.id === jobId ? { ...j, match_score: data.match_score, match_strengths: data.match_strengths, match_weaknesses: data.match_weaknesses, match_recommendations: data.match_recommendations } : j));
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Scoring failed');
    }
  }

  async function handleViewScoreDetail(jobId: number) {
    try {
      setScoreDetail(await getJobScoreDetail(jobId));
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to load score detail');
    }
  }

  async function handleSaveJob(jobId: number) {
    try {
      await createApplication({ job_id: jobId, status: 'saved' });
      toast.success('Job saved to applications');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to save job';
      if (msg.toLowerCase().includes('already exists') || msg.includes('409')) {
        toast.success('Job already in applications');
      } else {
        toast.error(msg);
      }
    }
  }

  async function handleGenerateCoverLetter(jobId: number) {
    setGeneratingDoc({type: 'cover_letter', jobId});
    try {
      const result = await generateCoverLetter({job_id: jobId, tone: 'professional'});
      toast.success('Cover letter generated!');
      setCoverLetterModal({content: result.content, id: result.id, jobId});
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Cover letter generation failed');
    } finally {
      setGeneratingDoc({type: null, jobId: null});
    }
  }

  async function handleTailorResume(jobId: number) {
    if (!hasResume) {
      toast.error('Upload your resume first in the Profile page');
      router.push('/profile');
      return;
    }
    setGeneratingDoc({type: 'tailored_resume', jobId});
    try {
      const result = await tailorResume(jobId);
      toast.success('Tailored resume generated! Click to download.');
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Resume tailoring failed');
    } finally {
      setGeneratingDoc({type: null, jobId: null});
    }
  }

  return (
    <div className="page-shell">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Job Search</h1>
        <p className="text-sm text-slate-400 mt-0.5">
          {searchMode === 'resume' && hasResume
            ? '🔍 Resume-matched jobs — sorted by your profile relevance'
            : 'Search across JSearch + Adzuna for AEM/EDS roles'}
        </p>
      </div>

      {/* Resume search banner */}
      {hasResume && (
        <div className="glass-card p-4 border-brand-500/20 bg-gradient-to-r from-brand-500/5 to-purple-500/5">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-brand-500/10 flex items-center justify-center flex-shrink-0">
                <HiOutlineDocumentText className="w-5 h-5 text-brand-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-white flex items-center gap-2">
                  <HiOutlineSparkles className="w-4 h-4 text-brand-400" /> Search by Resume
                </p>
                <p className="text-xs text-slate-400 mt-0.5">Auto-generates search queries from your skills & experience</p>
              </div>
            </div>
            <button onClick={handleResumeSearch} disabled={resumeSearching || loading} className="btn-primary flex items-center justify-center gap-2 w-full sm:w-auto">
              {resumeSearching ? <><HiOutlineArrowPath className="w-4 h-4 animate-spin" /> Searching...</> : <><HiOutlineSparkles className="w-4 h-4" /> Find Jobs for Me</>}
            </button>
          </div>
          {resumeQueries.length > 0 && searchMode === 'resume' && (
            <div className="mt-3 pt-3 border-t border-slate-700/50">
              <p className="text-xs text-slate-500 mb-2">Queries generated from your resume:</p>
              <div className="flex flex-wrap gap-2">
                {resumeQueries.map((q: any, i: number) => (
                  <span key={i} className={`text-[10px] px-2 py-1 rounded-full border ${q.results > 0 ? 'bg-emerald-400/5 text-emerald-400 border-emerald-400/20' : 'bg-slate-800 text-slate-500 border-slate-700/50'}`}>
                    {q.label || q.query} {q.results > 0 && `(${q.results})`}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* No resume prompt */}
      {!hasResume && (
        <div className="glass-card p-4 border-amber-500/20 bg-amber-400/5">
          <div className="flex flex-col sm:flex-row sm:items-center gap-3">
            <div className="flex-1">
              <p className="text-sm font-medium text-slate-200">Upload your resume for personalized job matching</p>
              <p className="text-xs text-slate-400 mt-0.5">AI will extract your skills and auto-generate targeted search queries</p>
            </div>
            <button onClick={() => router.push('/profile')} className="btn-primary text-xs">Upload Resume</button>
          </div>
        </div>
      )}

      {/* Search Bar */}
      <div className="glass-card p-5 space-y-4">
        <div className="search-row">
          <div className="flex-1 relative min-w-0">
            <HiOutlineMagnifyingGlass className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
            <input type="text" placeholder={hasResume ? 'Search specific roles (resume match always prioritized)' : 'e.g. "AEM developer", "Adobe Experience Manager architect"'} value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleSearch()} className="input-dark w-full pl-10" />
          </div>
          <div className="w-full sm:w-48 relative">
            <HiOutlineMapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input type="text" placeholder="Location" value={location} onChange={(e) => setLocation(e.target.value)} className="input-dark w-full pl-9" />
          </div>
          <button onClick={handleSearch} disabled={loading} className="btn-primary flex items-center justify-center gap-2 whitespace-nowrap w-full sm:w-auto">
            {loading ? <HiOutlineArrowPath className="w-4 h-4 animate-spin" /> : <HiOutlineMagnifyingGlass className="w-4 h-4" />}
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>

        {/* Filters Row */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <HiOutlineFunnel className="w-4 h-4 text-slate-500" />
            <span className="text-xs text-slate-500">Filters:</span>
          </div>
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={remoteOnly} onChange={(e) => setRemoteOnly(e.target.checked)} className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-brand-500 focus:ring-brand-500 focus:ring-offset-0" />
            <span className="text-xs text-slate-400 flex items-center gap-1"><HiOutlineGlobeAlt className="w-3.5 h-3.5" /> Remote only</span>
          </label>
          <select value={datePosted} onChange={(e) => setDatePosted(e.target.value)} className="input-dark text-xs py-1.5 px-2">
            <option value="">Any time</option>
            <option value="today">Today</option>
            <option value="3days">Last 3 days</option>
            <option value="week">This week</option>
            <option value="month">This month</option>
          </select>
        </div>

        {/* Search Chips */}
        {searchChips.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {searchChips.map((chip) => (
              <button
                key={chip.query + chip.location}
                onClick={() => handleQuickSearch(chip.query, chip.location)}
                className={`text-xs px-3 py-1.5 rounded-full border transition-all duration-200
                  hover:border-brand-500/30 hover:text-brand-300 flex items-center gap-1.5 ${
                  chip.source === 'resume'
                    ? 'bg-brand-500/10 text-brand-300 border-brand-500/20'
                    : 'bg-slate-800/80 text-slate-300 border-slate-700/50'
                }`}
              >
                {chip.source === 'resume' && <HiOutlineSparkles className="w-3 h-3 text-brand-400" />}
                {chip.label}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* ═══════════════════════════════════════════════════════════════════ */}
      {/* RESULTS — only shown AFTER user clicks a search button            */}
      {/* ═══════════════════════════════════════════════════════════════════ */}

      {loading ? (
        /* ── Loading state ── */
        <div className="glass-card p-12 text-center">
          <HiOutlineArrowPath className="w-12 h-12 mx-auto mb-4 text-brand-400 animate-spin" />
          <p className="text-sm text-brand-300 font-medium">
            {searchMode === 'saved' ? 'Loading saved jobs...' : 'Searching across JSearch + Adzuna...'}
          </p>
          {searchMode !== 'saved' && (
            <p className="text-xs text-slate-500 mt-1">This may take a few seconds</p>
          )}
        </div>
      ) : !hasSearched ? (
        /* ── Empty state: user hasn't searched yet ── */
        <div className="glass-card p-16 text-center">
          <HiOutlineMagnifyingGlass className="w-20 h-20 mx-auto mb-5 text-slate-700" />
          <h3 className="text-xl font-medium text-slate-300 mb-2">Ready to find your next role</h3>
          <p className="text-sm text-slate-500 max-w-md mx-auto mb-4">
            {hasResume
              ? 'Use the search bar above, click a resume-matched chip, or hit "Find Jobs for Me" to discover AEM/EDS roles matched to your resume.'
              : 'Type a search query above to discover AEM/EDS roles. Upload your resume for personalized results and AI-generated search queries.'}
          </p>
          <div className="flex justify-center gap-3">
            {hasResume && (
              <button onClick={handleResumeSearch} disabled={resumeSearching} className="bg-gradient-to-r from-brand-500 to-purple-500 hover:from-brand-400 hover:to-purple-400 text-white px-5 py-2.5 rounded-lg text-sm font-medium flex items-center gap-2 transition-all disabled:opacity-50">
                <HiOutlineSparkles className="w-4 h-4" /> Find Jobs for Me
              </button>
            )}
            {searchChips.length > 0 && (
              <button onClick={() => handleQuickSearch(searchChips[0].query, searchChips[0].location)} className="btn-secondary text-sm flex items-center gap-2">
                <HiOutlineBriefcase className="w-4 h-4" /> Try: {searchChips[0].label}
              </button>
            )}
          </div>
        </div>
      ) : jobs.length === 0 ? (
        /* ── No results state ── */
        <div className="glass-card p-12 text-center">
          <HiOutlineBriefcase className="w-16 h-16 mx-auto mb-4 text-slate-700" />
          <h3 className="text-lg font-medium text-slate-400 mb-2">No jobs found</h3>
          <p className="text-sm text-slate-500 max-w-md mx-auto">
            Try a different search query, change the location, or remove filters.
          </p>
        </div>
      ) : (
        /* ── Results list ── */
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-400">
              {total} {searchMode === 'saved' ? 'saved job' : 'job'}{total !== 1 ? 's' : ''}{searchMode === 'saved' ? '' : ' found'}
              {searchMode === 'resume' && <span className="text-brand-400 ml-1">· Resume-prioritized</span>}
              {searchMode === 'saved' && remoteOnly && <span className="text-purple-400 ml-1">· Remote only</span>}
            </p>
          </div>

          {jobs.map((job: any) => (
            <div key={job.id} onClick={() => setSelectedJob(selectedJob?.id === job.id ? null : job)} className={`glass-card-hover p-4 cursor-pointer ${selectedJob?.id === job.id ? 'border-brand-500/40 ring-1 ring-brand-500/20' : ''}`}>
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-lg bg-brand-500/10 flex items-center justify-center flex-shrink-0">
                  <span className="text-sm font-bold text-brand-400">{(job.company_name || '?')[0].toUpperCase()}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                    <div>
                      <h3 className="text-sm font-semibold text-white hover:text-brand-300 transition-colors">{job.title}</h3>
                      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1">
                        <span className="text-xs text-slate-300">{job.company_name}</span>
                        {job.location && <span className="text-xs text-slate-500 flex items-center gap-1"><HiOutlineMapPin className="w-3 h-3" /> {job.location}</span>}
                        {job.is_remote && <span className="text-[10px] font-medium text-purple-400 bg-purple-400/10 px-1.5 py-0.5 rounded">Remote</span>}
                        {job.job_type && <span className="text-[10px] text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded capitalize">{job.job_type.replace(/_/g, ' ')}</span>}
                        {job.posted_date && <span className="text-xs text-slate-600 flex items-center gap-1"><HiOutlineClock className="w-3 h-3" /> {new Date(job.posted_date).toLocaleDateString('en-IN')}</span>}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {job.salary_display && <span className="text-xs text-emerald-400 flex items-center gap-1"><HiOutlineCurrencyDollar className="w-3.5 h-3.5" /> {job.salary_display}</span>}
                      <ScoreBadge score={job.match_score} />
                      <span className="text-[10px] text-slate-600 uppercase">{job.source}</span>
                    </div>
                  </div>
                  {job.skills_required?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {job.skills_required.slice(0, 8).map((skill: string) => (
                        <span key={skill} className={`text-[10px] px-2 py-0.5 rounded-full border ${isAEMSkill(skill) ? 'bg-brand-500/10 text-brand-300 border-brand-500/20' : 'bg-slate-800 text-slate-400 border-slate-700/50'}`}>{skill}</span>
                      ))}
                      {job.skills_required.length > 8 && <span className="text-[10px] px-2 py-0.5 text-slate-600">+{job.skills_required.length - 8} more</span>}
                    </div>
                  )}
                  {selectedJob?.id === job.id && (
                    <JobDetailPanel
                      job={jobDetailFromRecord(job)}
                      hasResume={hasResume}
                      generatingDoc={generatingDoc}
                      onScore={handleScoreSingle}
                      onScoreDetail={handleViewScoreDetail}
                      onCoverLetter={handleGenerateCoverLetter}
                      onTailorResume={handleTailorResume}
                      onSave={handleSaveJob}
                    />
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Score Detail Modal */}
      {scoreDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setScoreDetail(null)}>
          <div className="glass-card p-6 w-full max-w-lg space-y-4" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <div><h2 className="text-lg font-bold text-white">{scoreDetail.title}</h2><p className="text-sm text-slate-400">{scoreDetail.company_name} · {scoreDetail.location || 'Remote'}</p></div>
              <button onClick={() => setScoreDetail(null)} className="text-slate-500 hover:text-slate-300 text-xl">×</button>
            </div>
            <div className="flex items-center gap-4">
              <div className={`w-20 h-20 rounded-full flex items-center justify-center border-4 ${scoreDetail.overall_score >= 75 ? 'border-emerald-400 bg-emerald-400/10' : scoreDetail.overall_score >= 50 ? 'border-amber-400 bg-amber-400/10' : 'border-slate-400 bg-slate-400/10'}`}>
                <span className={`text-2xl font-bold ${scoreDetail.overall_score >= 75 ? 'text-emerald-400' : scoreDetail.overall_score >= 50 ? 'text-amber-400' : 'text-slate-400'}`}>{scoreDetail.overall_score}</span>
              </div>
              <div><p className="text-sm font-medium text-white">Overall Match Score</p><p className="text-xs text-slate-500 mt-0.5">Weighted across 6 dimensions</p></div>
            </div>
            {scoreDetail.strengths?.length > 0 && (<div><p className="text-xs font-medium text-emerald-400 mb-2">✅ Strengths</p><ul className="space-y-1">{scoreDetail.strengths.map((s: string, i: number) => (<li key={i} className="text-xs text-slate-300 flex gap-2"><span className="text-emerald-500">+</span>{s}</li>))}</ul></div>)}
            {scoreDetail.weaknesses?.length > 0 && (<div><p className="text-xs font-medium text-amber-400 mb-2">⚠️ Gaps</p><ul className="space-y-1">{scoreDetail.weaknesses.map((w: string, i: number) => (<li key={i} className="text-xs text-slate-300 flex gap-2"><span className="text-amber-500">-</span>{w}</li>))}</ul></div>)}
            {scoreDetail.recommendations?.length > 0 && (<div><p className="text-xs font-medium text-brand-400 mb-2">🎯 AI Recommendations</p><ul className="space-y-1.5">{scoreDetail.recommendations.map((r: string, i: number) => (<li key={i} className="text-xs text-slate-300 flex gap-2"><span className="text-brand-500">→</span>{r}</li>))}</ul></div>)}
            <button onClick={() => setScoreDetail(null)} className="btn-primary w-full text-sm">Close</button>
          </div>
        </div>
      )}

      {/* Cover Letter Modal */}
      {coverLetterModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setCoverLetterModal(null)}>
          <div className="glass-card p-6 w-full max-w-2xl max-h-[85vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <HiOutlineEnvelope className="w-5 h-5 text-brand-400" /> Cover Letter
                </h2>
                <p className="text-sm text-slate-400 mt-0.5">AI-generated for this position</p>
              </div>
              <div className="flex items-center gap-2">
                <a
                  href={downloadCoverLetterUrl(coverLetterModal.id)}
                  download
                  className="btn-secondary text-xs flex items-center gap-1"
                >
                  <HiOutlineArrowDownTray className="w-3.5 h-3.5" /> Download
                </a>
                <button onClick={() => setCoverLetterModal(null)} className="text-slate-500 hover:text-slate-300 text-xl">×</button>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto text-sm text-slate-300 leading-relaxed whitespace-pre-line bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
              {coverLetterModal.content}
            </div>
            <div className="mt-4 flex gap-2">
              <button
                onClick={() => { navigator.clipboard.writeText(coverLetterModal.content); toast.success('Copied to clipboard!'); }}
                className="btn-primary text-sm flex items-center gap-2"
              >
                Copy to Clipboard
              </button>
              <button onClick={() => setCoverLetterModal(null)} className="btn-secondary text-sm">Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function JobsPageWithSuspense() {
  return (
    <Suspense fallback={<div className="p-6 flex items-center justify-center h-[80vh]"><HiOutlineArrowPath className="w-8 h-8 text-brand-400 animate-spin" /></div>}>
      <JobsPage />
    </Suspense>
  );
}
