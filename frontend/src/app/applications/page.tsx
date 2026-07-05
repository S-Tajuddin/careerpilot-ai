'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  HiOutlineClipboardDocumentList,
  HiOutlinePaperAirplane,
  HiOutlineChatBubbleLeftRight,
  HiOutlineCheckBadge,
  HiOutlineXMark,
  HiOutlineClock,
  HiOutlineArrowPath,
  HiOutlineMapPin,
  HiOutlineCurrencyDollar,
  HiOutlineArrowDownTray,
  HiOutlineEnvelope,
} from 'react-icons/hi2';
import {
  getApplications,
  getApplicationStats,
  getResumeStatus,
  scoreJob,
  getJobScoreDetail,
  generateCoverLetter,
  tailorResume,
  downloadCoverLetterUrl,
} from '@/lib/api';
import { normalizeApplications, type ApplicationView } from '@/lib/applications';
import { jobDetailFromApplication } from '@/lib/jobs';
import { JobDetailPanel } from '@/components/JobDetailPanel';
import { ScoreBadge } from '@/components/ScoreBadge';
import { isAEMSkill } from '@/lib/utils';
import toast from 'react-hot-toast';

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string; icon: typeof HiOutlineClipboardDocumentList }> = {
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
  const router = useRouter();
  const [applications, setApplications] = useState<ApplicationView[]>([]);
  const [stats, setStats] = useState<{ by_status?: Record<string, number> } | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('');
  const [viewMode, setViewMode] = useState<'list' | 'kanban'>('kanban');
  const [selectedAppId, setSelectedAppId] = useState<number | null>(null);
  const [hasResume, setHasResume] = useState(false);
  const [scoreDetail, setScoreDetail] = useState<Record<string, unknown> | null>(null);
  const [generatingDoc, setGeneratingDoc] = useState<{ type: 'cover_letter' | 'tailored_resume' | null; jobId: number | null }>({ type: null, jobId: null });
  const [coverLetterModal, setCoverLetterModal] = useState<{ content: string; id: number; jobId: number } | null>(null);

  useEffect(() => {
    loadData();
    getResumeStatus()
      .then((rs) => setHasResume(rs.has_resume))
      .catch(() => {});
  }, [filterStatus]);

  async function loadData() {
    setLoading(true);
    try {
      const params: { limit: number; status?: string } = { limit: 100 };
      if (filterStatus) params.status = filterStatus;
      const [apps, s] = await Promise.allSettled([
        getApplications(params),
        getApplicationStats(),
      ]);
      if (apps.status === 'fulfilled') {
        setApplications(normalizeApplications(apps.value));
      }
      if (s.status === 'fulfilled') setStats(s.value);
    } catch {
      toast.error('Failed to load applications');
    } finally {
      setLoading(false);
    }
  }

  function toggleApp(appId: number) {
    setSelectedAppId((prev) => (prev === appId ? null : appId));
  }

  function updateAppJob(jobId: number, patch: Record<string, unknown>) {
    setApplications((prev) =>
      prev.map((app) =>
        app.job_id === jobId
          ? { ...app, job: { ...(app.job || {}), ...patch } }
          : app,
      ),
    );
  }

  async function handleScoreSingle(jobId: number) {
    try {
      const data = await scoreJob(jobId);
      toast.success(`Scored: ${data.match_score}%`);
      updateAppJob(jobId, {
        match_score: data.match_score,
        match_strengths: data.match_strengths,
        match_weaknesses: data.match_weaknesses,
        match_recommendations: data.match_recommendations,
      });
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

  async function handleGenerateCoverLetter(jobId: number) {
    setGeneratingDoc({ type: 'cover_letter', jobId });
    try {
      const result = await generateCoverLetter({ job_id: jobId, tone: 'professional' });
      toast.success('Cover letter generated!');
      setCoverLetterModal({ content: result.content, id: result.id, jobId });
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Cover letter generation failed');
    } finally {
      setGeneratingDoc({ type: null, jobId: null });
    }
  }

  async function handleTailorResume(jobId: number) {
    if (!hasResume) {
      toast.error('Upload your resume first in the Profile page');
      router.push('/profile');
      return;
    }
    setGeneratingDoc({ type: 'tailored_resume', jobId });
    try {
      await tailorResume(jobId);
      toast.success('Tailored resume generated!');
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Resume tailoring failed');
    } finally {
      setGeneratingDoc({ type: null, jobId: null });
    }
  }

  function renderApplicationCard(app: ApplicationView, compact = false) {
    const cfg = STATUS_CONFIG[app.status] || STATUS_CONFIG.saved;
    const job = jobDetailFromApplication(app);
    const isSelected = selectedAppId === app.id;
    const skills = job.skills_required || [];

    return (
      <div
        key={app.id}
        onClick={() => toggleApp(app.id)}
        className={`${compact ? 'p-3' : 'p-4'} glass-card-hover cursor-pointer ${
          isSelected ? 'border-brand-500/40 ring-1 ring-brand-500/20' : ''
        }`}
      >
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-lg bg-brand-500/10 flex items-center justify-center flex-shrink-0">
            <span className="text-sm font-bold text-brand-400">
              {(app.company_name || '?')[0].toUpperCase()}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <div className={`flex ${compact ? 'flex-col' : 'flex-col sm:flex-row sm:items-start sm:justify-between'} gap-2`}>
              <div>
                <h3 className={`${compact ? 'text-xs' : 'text-sm'} font-semibold text-white hover:text-brand-300 transition-colors line-clamp-2`}>
                  {app.job_title}
                </h3>
                <div className="flex flex-wrap items-center gap-x-2 gap-y-1 mt-1">
                  <span className={`${compact ? 'text-[10px]' : 'text-xs'} text-slate-300`}>{app.company_name}</span>
                  {app.job_location && (
                    <span className={`${compact ? 'text-[10px]' : 'text-xs'} text-slate-500 flex items-center gap-1`}>
                      <HiOutlineMapPin className="w-3 h-3" /> {app.job_location}
                    </span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0 flex-wrap">
                {job.salary_display && (
                  <span className="text-xs text-emerald-400 flex items-center gap-1">
                    <HiOutlineCurrencyDollar className="w-3.5 h-3.5" /> {job.salary_display}
                  </span>
                )}
                <ScoreBadge score={job.match_score} />
                <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${cfg.bg} ${cfg.color} border`}>
                  {cfg.label}
                </span>
              </div>
            </div>
            {!compact && skills.length > 0 && !isSelected && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {skills.slice(0, 6).map((skill) => (
                  <span
                    key={skill}
                    className={`text-[10px] px-2 py-0.5 rounded-full border ${
                      isAEMSkill(skill)
                        ? 'bg-brand-500/10 text-brand-300 border-brand-500/20'
                        : 'bg-slate-800 text-slate-400 border-slate-700/50'
                    }`}
                  >
                    {skill}
                  </span>
                ))}
              </div>
            )}
            {compact && (
              <div className="flex items-center gap-1 mt-2">
                <HiOutlineClock className="w-3 h-3 text-slate-600" />
                <span className="text-[10px] text-slate-600">
                  {app.created_at ? new Date(app.created_at).toLocaleDateString('en-IN') : '—'}
                </span>
              </div>
            )}
            {isSelected && (
              <JobDetailPanel
                job={job}
                hasResume={hasResume}
                showSave={false}
                generatingDoc={generatingDoc}
                onScore={handleScoreSingle}
                onScoreDetail={handleViewScoreDetail}
                onCoverLetter={handleGenerateCoverLetter}
                onTailorResume={handleTailorResume}
                headerExtra={
                  app.notes ? (
                    <div>
                      <p className="text-xs font-medium text-slate-400 mb-1">Notes</p>
                      <p className="text-xs text-slate-500">{app.notes}</p>
                    </div>
                  ) : undefined
                }
              />
            )}
          </div>
        </div>
        {!compact && !isSelected && (
          <div className="flex items-center justify-end gap-3 mt-2 pt-2 border-t border-slate-800/50">
            <span className="text-[10px] text-slate-600">
              {app.created_at ? new Date(app.created_at).toLocaleDateString('en-IN') : '—'}
            </span>
          </div>
        )}
      </div>
    );
  }

  const byStatus = PIPELINE_ORDER.reduce((acc, status) => {
    acc[status] = applications.filter((a) => a.status === status);
    return acc;
  }, {} as Record<string, ApplicationView[]>);

  const statusCount = (status: string) => byStatus[status]?.length || 0;

  if (loading) {
    return (
      <div className="page-shell flex items-center justify-center min-h-[60vh]">
        <HiOutlineArrowPath className="w-8 h-8 text-brand-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="page-shell">
      <div className="page-header">
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

      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
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

      <div className="flex flex-wrap items-center gap-2">
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

      {viewMode === 'kanban' ? (
        <div className="flex flex-wrap gap-4 lg:grid lg:grid-cols-5">
          {['saved', 'applied', 'interview_scheduled', 'interview_done', 'offer'].map((status) => {
            const cfg = STATUS_CONFIG[status];
            const apps = byStatus[status] || [];
            return (
              <div key={status} className="w-full sm:min-w-[220px] sm:flex-1 lg:min-w-0">
                <div className="flex items-center gap-2 mb-3">
                  <div className={`w-2 h-2 rounded-full ${cfg.bg.includes('blue') ? 'bg-blue-400' : cfg.bg.includes('amber') ? 'bg-amber-400' : cfg.bg.includes('purple') ? 'bg-purple-400' : cfg.bg.includes('emerald') ? 'bg-emerald-400' : 'bg-slate-400'}`} />
                  <h3 className={`text-xs font-semibold ${cfg.color}`}>{cfg.label}</h3>
                  <span className="text-[10px] text-slate-600 bg-slate-800 px-1.5 rounded">{apps.length}</span>
                </div>
                <div className="space-y-2 max-h-[calc(100vh-300px)] overflow-y-auto">
                  {apps.map((app) => renderApplicationCard(app, true))}
                  {apps.length === 0 && (
                    <div className="text-center py-6 text-slate-700 text-xs">No items</div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="space-y-3">
          {applications.length === 0 ? (
            <div className="glass-card p-12 text-center">
              <HiOutlineClipboardDocumentList className="w-16 h-16 mx-auto mb-4 text-slate-700" />
              <h3 className="text-lg font-medium text-slate-400 mb-2">No applications yet</h3>
              <p className="text-sm text-slate-500">
                Apply to jobs from the Jobs page — they&apos;ll appear here automatically.
              </p>
            </div>
          ) : (
            applications.map((app) => renderApplicationCard(app, false))
          )}
        </div>
      )}

      {scoreDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setScoreDetail(null)}>
          <div className="glass-card p-6 w-full max-w-lg space-y-4 mx-4" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-white">{String(scoreDetail.title)}</h2>
                <p className="text-sm text-slate-400">
                  {String(scoreDetail.company_name)} · {String(scoreDetail.location || 'Remote')}
                </p>
              </div>
              <button onClick={() => setScoreDetail(null)} className="text-slate-500 hover:text-slate-300 text-xl">×</button>
            </div>
            <div className="flex items-center gap-4">
              <div className={`w-20 h-20 rounded-full flex items-center justify-center border-4 ${
                Number(scoreDetail.overall_score) >= 75 ? 'border-emerald-400 bg-emerald-400/10'
                  : Number(scoreDetail.overall_score) >= 50 ? 'border-amber-400 bg-amber-400/10'
                  : 'border-slate-400 bg-slate-400/10'
              }`}>
                <span className={`text-2xl font-bold ${
                  Number(scoreDetail.overall_score) >= 75 ? 'text-emerald-400'
                    : Number(scoreDetail.overall_score) >= 50 ? 'text-amber-400'
                    : 'text-slate-400'
                }`}>{String(scoreDetail.overall_score)}</span>
              </div>
              <div>
                <p className="text-sm font-medium text-white">Overall Match Score</p>
                <p className="text-xs text-slate-500 mt-0.5">Weighted across 6 dimensions</p>
              </div>
            </div>
            {(scoreDetail.strengths as string[])?.length > 0 && (
              <div>
                <p className="text-xs font-medium text-emerald-400 mb-2">Strengths</p>
                <ul className="space-y-1">
                  {(scoreDetail.strengths as string[]).map((s, i) => (
                    <li key={i} className="text-xs text-slate-300 flex gap-2"><span className="text-emerald-500">+</span>{s}</li>
                  ))}
                </ul>
              </div>
            )}
            {(scoreDetail.weaknesses as string[])?.length > 0 && (
              <div>
                <p className="text-xs font-medium text-amber-400 mb-2">Gaps</p>
                <ul className="space-y-1">
                  {(scoreDetail.weaknesses as string[]).map((w, i) => (
                    <li key={i} className="text-xs text-slate-300 flex gap-2"><span className="text-amber-500">-</span>{w}</li>
                  ))}
                </ul>
              </div>
            )}
            {(scoreDetail.recommendations as string[])?.length > 0 && (
              <div>
                <p className="text-xs font-medium text-brand-400 mb-2">AI Recommendations</p>
                <ul className="space-y-1.5">
                  {(scoreDetail.recommendations as string[]).map((r, i) => (
                    <li key={i} className="text-xs text-slate-300 flex gap-2"><span className="text-brand-500">→</span>{r}</li>
                  ))}
                </ul>
              </div>
            )}
            <button onClick={() => setScoreDetail(null)} className="btn-primary w-full text-sm">Close</button>
          </div>
        </div>
      )}

      {coverLetterModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setCoverLetterModal(null)}>
          <div className="glass-card p-6 w-full max-w-2xl max-h-[85vh] flex flex-col mx-4" onClick={(e) => e.stopPropagation()}>
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
          </div>
        </div>
      )}
    </div>
  );
}
