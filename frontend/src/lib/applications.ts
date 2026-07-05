/** Flatten application + nested job for UI display */

export interface ApplicationView {
  id: number;
  job_id: number;
  status: string;
  notes?: string | null;
  rating?: number | null;
  created_at?: string;
  updated_at?: string;
  job_title: string;
  company_name: string;
  job_location: string;
  job?: Record<string, unknown>;
}

export function normalizeApplication(app: Record<string, unknown>): ApplicationView {
  const job = (app.job as Record<string, unknown>) || {};
  return {
    id: app.id as number,
    job_id: app.job_id as number,
    status: app.status as string,
    notes: app.notes as string | null | undefined,
    rating: app.rating as number | null | undefined,
    created_at: app.created_at as string | undefined,
    updated_at: app.updated_at as string | undefined,
    job_title: (job.title as string) || (app.job_title as string) || 'Untitled',
    company_name: (job.company_name as string) || (app.company_name as string) || 'Unknown',
    job_location: (job.location as string) || (app.job_location as string) || 'Remote',
    job,
  };
}

export function normalizeApplications(raw: unknown): ApplicationView[] {
  const list = Array.isArray(raw) ? raw : [];
  return list.map((app) => normalizeApplication(app as Record<string, unknown>));
}
