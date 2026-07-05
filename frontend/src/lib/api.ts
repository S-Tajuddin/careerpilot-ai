/**
 * CareerPilot AI — API Client
 * All backend communication goes through here.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchAPI(path: string, options?: RequestInit) {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API Error: ${res.status}`);
  }
  return res.json();
}

async function uploadFileAPI(path: string, formData: FormData) {
  const res = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    body: formData,
    // Don't set Content-Type header — browser sets it with boundary for FormData
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `Upload Error: ${res.status}`);
  }
  return res.json();
}

// ── Health ──────────────────────────────────────────────────────────────────
export const healthCheck = () => fetchAPI('/health');

// ── Jobs ────────────────────────────────────────────────────────────────────
export const getJobs = (params?: Record<string, string | number | boolean>) => {
  const sp = new URLSearchParams();
  if (params) Object.entries(params).forEach(([k, v]) => sp.append(k, String(v)));
  return fetchAPI(`/api/jobs/?${sp.toString()}`);
};

export const searchJobs = (params: {
  query: string;
  location?: string;
  country?: string;
  remote_only?: boolean;
  date_posted?: string;
  max_results?: number;
}) => {
  const sp = new URLSearchParams();
  sp.append('query', params.query);
  if (params.location) sp.append('location', params.location);
  if (params.country) sp.append('country', params.country);
  if (params.remote_only) sp.append('remote_only', 'true');
  if (params.date_posted) sp.append('date_posted', params.date_posted);
  if (params.max_results) sp.append('max_results', String(params.max_results));
  return fetchAPI(`/api/jobs/search?${sp.toString()}`);
};

export const searchJobsByResume = (maxResultsPerQuery: number = 5) =>
  fetchAPI(`/api/jobs/search-by-resume?max_results_per_query=${maxResultsPerQuery}`);

export const getJob = (id: number) => fetchAPI(`/api/jobs/${id}`);

export const getJobStats = () => fetchAPI('/api/jobs/stats/summary');

// ── Applications ────────────────────────────────────────────────────────────
export const getApplications = (params?: Record<string, string | number>) => {
  const sp = new URLSearchParams();
  if (params) Object.entries(params).forEach(([k, v]) => sp.append(k, String(v)));
  return fetchAPI(`/api/applications/?${sp.toString()}`);
};

export const createApplication = (data: {
  job_id: number;
  status?: string;
  notes?: string;
}) => fetchAPI('/api/applications/', {
  method: 'POST',
  body: JSON.stringify(data),
});

export const updateApplication = (id: number, data: Record<string, unknown>) =>
  fetchAPI(`/api/applications/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });

export const getApplicationStats = () => fetchAPI('/api/applications/stats/summary');

// ── Profile ─────────────────────────────────────────────────────────────────
export const getProfile = () => fetchAPI('/api/profile/');

export const updateProfile = (data: Record<string, unknown>) =>
  fetchAPI('/api/profile/', {
    method: 'PUT',
    body: JSON.stringify(data),
  });

export const uploadResume = (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  return uploadFileAPI('/api/profile/resume-upload', formData);
};

export const getResumeStatus = () => fetchAPI('/api/profile/resume-status');

export const getResumeSearchQueries = () => fetchAPI('/api/profile/resume-search-queries');

export const deleteResume = () => fetchAPI('/api/profile/resume', { method: 'DELETE' });

// ── Company Research ────────────────────────────────────────────────────────
export const researchCompany = (companyName: string) =>
  fetchAPI(`/api/company/research?company_name=${encodeURIComponent(companyName)}`);

export const getInterviewTips = (companyName: string, role: string = 'AEM Developer') =>
  fetchAPI(`/api/company/interview-tips?company_name=${encodeURIComponent(companyName)}&role=${encodeURIComponent(role)}`);

export const getSalaryIntel = (companyName: string, role: string = 'AEM Developer', location: string = 'Hyderabad, India') =>
  fetchAPI(`/api/company/salary-intel?company_name=${encodeURIComponent(companyName)}&role=${encodeURIComponent(role)}&location=${encodeURIComponent(location)}`);
