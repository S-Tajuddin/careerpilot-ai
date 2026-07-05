/** Map API profile response to Profile page form state */

export interface ProfileFormState {
  full_name: string;
  email: string;
  phone: string;
  current_role: string;
  location: string;
  skills: string[];
  experience_years: number;
  target_role: string;
  expected_salary_min: number;
  expected_salary_max: number;
  remote_preference: string;
  notice_period: string;
  summary: string;
}

export function profileToForm(p: Record<string, unknown>): ProfileFormState {
  return {
    full_name: (p.full_name as string) || '',
    email: (p.email as string) || '',
    phone: (p.phone as string) || '',
    current_role: (p.current_role as string) || '',
    location: (p.location as string) || 'Hyderabad, India',
    skills: (p.skills as string[]) || [],
    experience_years: (p.experience_years as number) || 8,
    target_role: (p.target_role as string) || 'Senior AEM Developer / AEM Architect',
    expected_salary_min: ((p.expected_salary_min as number) || 2_000_000) / 100_000,
    expected_salary_max: ((p.expected_salary_max as number) || 3_500_000) / 100_000,
    remote_preference: (p.remote_preference as string) || 'any',
    notice_period: (p.notice_period as string) || '60_days',
    summary: (p.summary as string) || '',
  };
}
