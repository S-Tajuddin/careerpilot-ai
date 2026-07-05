'use client';

import type { ReactNode } from 'react';
import {
  HiOutlineArrowPath,
  HiOutlineArrowTopRightOnSquare,
  HiOutlineBookmark,
  HiOutlineEnvelope,
  HiOutlinePencilSquare,
  HiOutlineStar,
} from 'react-icons/hi2';
import { isAEMSkill, isGenuineUrl } from '@/lib/utils';
import type { JobDetail } from '@/lib/jobs';

interface JobDetailPanelProps {
  job: JobDetail;
  hasResume?: boolean;
  showSave?: boolean;
  generatingDoc?: { type: 'cover_letter' | 'tailored_resume' | null; jobId: number | null };
  onScore?: (jobId: number) => void;
  onScoreDetail?: (jobId: number) => void;
  onCoverLetter?: (jobId: number) => void;
  onTailorResume?: (jobId: number) => void;
  onSave?: (jobId: number) => void;
  headerExtra?: ReactNode;
}

export function JobDetailPanel({
  job,
  hasResume = false,
  showSave = true,
  generatingDoc = { type: null, jobId: null },
  onScore,
  onScoreDetail,
  onCoverLetter,
  onTailorResume,
  onSave,
  headerExtra,
}: JobDetailPanelProps) {
  const coverLoading = generatingDoc.type === 'cover_letter' && generatingDoc.jobId === job.id;
  const resumeLoading = generatingDoc.type === 'tailored_resume' && generatingDoc.jobId === job.id;

  return (
    <div className="mt-3 pt-3 border-t border-slate-700/50 space-y-3" onClick={(e) => e.stopPropagation()}>
      {headerExtra}
      {job.description && (
        <div className="text-xs text-slate-400 leading-relaxed max-h-40 overflow-y-auto whitespace-pre-line">
          {job.description.slice(0, 1500)}
          {job.description.length > 1500 && '...'}
        </div>
      )}
      {job.match_strengths && job.match_strengths.length > 0 && (
        <div>
          <p className="text-xs font-medium text-emerald-400 mb-1">Strengths</p>
          <div className="flex flex-wrap gap-1.5">
            {job.match_strengths.map((s) => (
              <span key={s} className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-400/10 text-emerald-400 border border-emerald-400/20">
                {s}
              </span>
            ))}
          </div>
        </div>
      )}
      {job.match_weaknesses && job.match_weaknesses.length > 0 && (
        <div>
          <p className="text-xs font-medium text-amber-400 mb-1">Gaps</p>
          <div className="flex flex-wrap gap-1.5">
            {job.match_weaknesses.map((w) => (
              <span key={w} className="text-[10px] px-2 py-0.5 rounded-full bg-amber-400/10 text-amber-400 border border-amber-400/20">
                {w}
              </span>
            ))}
          </div>
        </div>
      )}
      {job.match_recommendations && job.match_recommendations.length > 0 && (
        <div>
          <p className="text-xs font-medium text-brand-400 mb-1">AI Recommendations</p>
          <ul className="space-y-1">
            {job.match_recommendations.map((r, i) => (
              <li key={i} className="text-[11px] text-slate-400 flex gap-2">
                <span className="text-brand-500 mt-0.5">→</span>
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      <div className="flex flex-wrap gap-2">
        {job.source_url && isGenuineUrl(job.source_url) && (
          <a
            href={job.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary text-xs flex items-center gap-1"
          >
            <HiOutlineArrowTopRightOnSquare className="w-3.5 h-3.5" />
            {job.apply_label || `Apply on ${job.source}`}
          </a>
        )}
        {job.match_score == null
          ? onScore && (
              <button onClick={() => onScore(job.id)} className="btn-secondary text-xs flex items-center gap-1">
                <HiOutlineStar className="w-3.5 h-3.5" /> AI Analyze
              </button>
            )
          : onScoreDetail && (
              <button onClick={() => onScoreDetail(job.id)} className="btn-secondary text-xs flex items-center gap-1">
                <HiOutlineStar className="w-3.5 h-3.5" /> Score Detail
              </button>
            )}
        {onCoverLetter && (
          <button
            onClick={() => onCoverLetter(job.id)}
            disabled={coverLoading}
            className="btn-secondary text-xs flex items-center gap-1"
          >
            {coverLoading ? (
              <HiOutlineArrowPath className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <HiOutlineEnvelope className="w-3.5 h-3.5" />
            )}
            {coverLoading ? 'Generating...' : 'Cover Letter'}
          </button>
        )}
        {hasResume && onTailorResume && (
          <button
            onClick={() => onTailorResume(job.id)}
            disabled={resumeLoading}
            className="btn-secondary text-xs flex items-center gap-1"
          >
            {resumeLoading ? (
              <HiOutlineArrowPath className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <HiOutlinePencilSquare className="w-3.5 h-3.5" />
            )}
            {resumeLoading ? 'Tailoring...' : 'Tailor Resume'}
          </button>
        )}
        {showSave && onSave && (
          <button onClick={() => onSave(job.id)} className="btn-secondary text-xs flex items-center gap-1">
            <HiOutlineBookmark className="w-3.5 h-3.5" /> Save
          </button>
        )}
      </div>
    </div>
  );
}
