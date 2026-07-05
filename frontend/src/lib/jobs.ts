import type { ApplicationView } from './applications';

export interface JobDetail {
  id: number;
  title?: string;
  company_name?: string;
  location?: string;
  description?: string;
  source_url?: string;
  apply_label?: string;
  source?: string;
  match_score?: number | null;
  match_strengths?: string[];
  match_weaknesses?: string[];
  match_recommendations?: string[];
  skills_required?: string[];
  is_remote?: boolean;
  job_type?: string;
  posted_date?: string;
  salary_display?: string;
}

export function jobDetailFromApplication(app: ApplicationView): JobDetail {
  const j = app.job || {};
  return {
    id: app.job_id,
    title: app.job_title,
    company_name: app.company_name,
    location: app.job_location,
    description: j.description as string | undefined,
    source_url: j.source_url as string | undefined,
    apply_label: j.apply_label as string | undefined,
    source: j.source as string | undefined,
    match_score: j.match_score as number | null | undefined,
    match_strengths: j.match_strengths as string[] | undefined,
    match_weaknesses: j.match_weaknesses as string[] | undefined,
    match_recommendations: j.match_recommendations as string[] | undefined,
    skills_required: j.skills_required as string[] | undefined,
    is_remote: j.is_remote as boolean | undefined,
    job_type: j.job_type as string | undefined,
    posted_date: j.posted_date as string | undefined,
    salary_display: j.salary_display as string | undefined,
  };
}

export function jobDetailFromRecord(job: Record<string, unknown>): JobDetail {
  return {
    id: job.id as number,
    title: job.title as string | undefined,
    company_name: job.company_name as string | undefined,
    location: job.location as string | undefined,
    description: job.description as string | undefined,
    source_url: job.source_url as string | undefined,
    apply_label: job.apply_label as string | undefined,
    source: job.source as string | undefined,
    match_score: job.match_score as number | null | undefined,
    match_strengths: job.match_strengths as string[] | undefined,
    match_weaknesses: job.match_weaknesses as string[] | undefined,
    match_recommendations: job.match_recommendations as string[] | undefined,
    skills_required: job.skills_required as string[] | undefined,
    is_remote: job.is_remote as boolean | undefined,
    job_type: job.job_type as string | undefined,
    posted_date: job.posted_date as string | undefined,
    salary_display: job.salary_display as string | undefined,
  };
}
