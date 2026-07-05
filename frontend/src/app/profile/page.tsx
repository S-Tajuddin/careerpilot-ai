'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import {
  HiOutlineUser,
  HiOutlineBriefcase,
  HiOutlineMapPin,
  HiOutlineCurrencyDollar,
  HiOutlineCodeBracket,
  HiOutlineClock,
  HiOutlineArrowPath,
  HiOutlineCheck,
  HiOutlineCloudArrowUp,
  HiOutlineDocumentText,
  HiOutlineTrash,
  HiOutlineSparkles,
  HiOutlineMagnifyingGlass,
  HiOutlinePlusCircle,
  HiOutlineXMark,
  HiOutlineRocketLaunch,
  HiOutlineFunnel,
} from 'react-icons/hi2';
import {
  getProfile, updateProfile, uploadResume, reparseResume, getResumeStatus, deleteResume,
  getResumeSearchQueries, searchJobsByResume,
} from '@/lib/api';
import toast from 'react-hot-toast';

export default function ProfilePage() {
  const router = useRouter();
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [resumeStatus, setResumeStatus] = useState<any>(null);
  const [uploadingResume, setUploadingResume] = useState(false);
  const [parsedPreview, setParsedPreview] = useState<any>(null);
  const [dragOver, setDragOver] = useState(false);
  const [resumeSearchQueries, setResumeSearchQueries] = useState<any[]>([]);
  const [resumeSearching, setResumeSearching] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Form state
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    phone: '',
    current_role: '',
    location: 'Hyderabad, India',
    skills: [] as string[],
    experience_years: 8,
    target_role: 'Senior AEM Developer / AEM Architect',
    expected_salary_min: 20,
    expected_salary_max: 35,
    remote_preference: 'any',
    notice_period: '60_days',
    summary: '',
  });

  const [skillsText, setSkillsText] = useState('');

  useEffect(() => {
    loadProfile();
  }, []);

  async function loadProfile() {
    try {
      const [data, status, queries] = await Promise.allSettled([
        getProfile(),
        getResumeStatus(),
        getResumeSearchQueries(),
      ]);

      let profileData = data.status === 'fulfilled' ? data.value : null;
      const hasStoredResume = status.status === 'fulfilled' && status.value.has_resume;

      // Re-sync profile from stored resume when key fields are missing
      if (
        profileData &&
        hasStoredResume &&
        (!profileData.full_name || !profileData.email || !profileData.skills?.length)
      ) {
        try {
          const reparsed = await reparseResume();
          profileData = reparsed.profile || profileData;
          if (reparsed.details?.parsed_data) {
            setParsedPreview(reparsed.details.parsed_data);
          }
          toast.success('Profile updated from your resume', { duration: 4000 });
        } catch {
          // Non-fatal — show whatever profile data we have
        }
      }

      if (profileData) {
        const p = profileData;
        setProfile(p);
        setForm({
          full_name: p.full_name || '',
          email: p.email || '',
          phone: p.phone || '',
          current_role: p.current_role || '',
          location: p.location || 'Hyderabad, India',
          skills: p.skills || [],
          experience_years: p.experience_years || 8,
          target_role: p.target_role || 'Senior AEM Developer / AEM Architect',
          expected_salary_min: (p.expected_salary_min || 2000000) / 100000,
          expected_salary_max: (p.expected_salary_max || 3500000) / 100000,
          remote_preference: p.remote_preference || 'any',
          notice_period: p.notice_period || '60_days',
          summary: p.summary || '',
        });
        setSkillsText((p.skills || []).join(', '));

        if (p.summary && p.summary.includes('[PARSED_DATA]')) {
          try {
            const start = p.summary.indexOf('[PARSED_DATA]') + '[PARSED_DATA]'.length;
            const end = p.summary.indexOf('[/PARSED_DATA]');
            const jsonStr = p.summary.substring(start, end);
            setParsedPreview((prev) => prev || JSON.parse(jsonStr));
          } catch { /* ignore */ }
        }
      }
      if (status.status === 'fulfilled') {
        setResumeStatus(status.value);
      }
      if (queries.status === 'fulfilled' && queries.value.has_resume) {
        setResumeSearchQueries(queries.value.queries || []);
      }
    } catch (err: unknown) {
      toast.error('Failed to load profile');
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    setSaving(true);
    try {
      const payload: Record<string, unknown> = {
        full_name: form.full_name || null,
        email: form.email || null,
        phone: form.phone || null,
        current_role: form.current_role || null,
        location: form.location || null,
        skills: form.skills.length > 0 ? form.skills : null,
        experience_years: form.experience_years,
        target_role: form.target_role || null,
        expected_salary_min: form.expected_salary_min * 100000,
        expected_salary_max: form.expected_salary_max * 100000,
        remote_preference: form.remote_preference,
        notice_period: form.notice_period,
        summary: form.summary || null,
      };
      await updateProfile(payload);
      toast.success('Profile saved!');
      setEditMode(false);
      loadProfile();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to save profile');
    } finally {
      setSaving(false);
    }
  }

  async function handleResumeUpload(file: File) {
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!ext || !['pdf', 'docx', 'doc', 'txt'].includes(ext)) {
      toast.error('Please upload a PDF, DOCX, or TXT file');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      toast.error('File too large. Maximum 10MB.');
      return;
    }

    setUploadingResume(true);
    try {
      const result = await uploadResume(file);
      toast.success(result.message || 'Resume uploaded and parsed!');

      // Show parsed data preview from the upload response
      if (result.details?.parsed_data) {
        setParsedPreview(result.details.parsed_data);
      }

      // Show which fields were updated from resume
      if (result.details?.updated_fields) {
        const fields = result.details.updated_fields
          .filter((f: string) => !['resume_text', 'resume_file_path'].includes(f))
          .map((f: string) => f.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase()));
        if (fields.length > 0) {
          toast.success(`✨ Profile updated: ${fields.join(', ')}`, { duration: 5000 });
        }
      }

      // Re-load profile to refresh all form fields with updated data
      if (result.profile) {
        const p = result.profile;
        setProfile(p);
        setForm({
          full_name: p.full_name || '',
          email: p.email || '',
          phone: p.phone || '',
          current_role: p.current_role || '',
          location: p.location || 'Hyderabad, India',
          skills: p.skills || [],
          experience_years: p.experience_years || 8,
          target_role: p.target_role || 'Senior AEM Developer / AEM Architect',
          expected_salary_min: (p.expected_salary_min || 2000000) / 100000,
          expected_salary_max: (p.expected_salary_max || 3500000) / 100000,
          remote_preference: p.remote_preference || 'any',
          notice_period: p.notice_period || '60_days',
          summary: p.summary || '',
        });
        setSkillsText((p.skills || []).join(', '));
        setResumeStatus({ has_resume: true, has_file: true });
      } else {
        await loadProfile();
      }
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Resume upload failed');
    } finally {
      setUploadingResume(false);
    }
  }

  async function handleDeleteResume() {
    if (!confirm('Remove your uploaded resume? Profile fields will be kept.')) return;
    try {
      await deleteResume();
      toast.success('Resume removed');
      setParsedPreview(null);
      setResumeSearchQueries([]);
      loadProfile();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to remove resume');
    }
  }

  async function handleResumeSearch() {
    if (!hasResume) return;
    setResumeSearching(true);
    try {
      const result = await searchJobsByResume(5);
      if (!result.has_resume) {
        toast.error('Upload your resume first');
        return;
      }
      router.push('/jobs');
      toast.success(`Resume search found ${result.total} jobs!`);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setResumeSearching(false);
    }
  }

  function handleFileDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleResumeUpload(file);
  }

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleResumeUpload(file);
    if (fileInputRef.current) fileInputRef.current.value = '';
  }

  function handleSkillsChange(text: string) {
    setSkillsText(text);
    const skills = text.split(',').map(s => s.trim()).filter(s => s.length > 0);
    setForm({ ...form, skills });
  }

  function handleChipSearch(query: string, location: string) {
    router.push(`/jobs?q=${encodeURIComponent(query)}${location ? `&loc=${encodeURIComponent(location)}` : ''}`);
  }

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center h-[80vh]">
        <HiOutlineArrowPath className="w-8 h-8 text-brand-400 animate-spin" />
      </div>
    );
  }

  const hasResume = resumeStatus?.has_resume || profile?.resume_text;

  // Resume-generated search queries only (no hardcoded defaults)
  const allSearchChips = (() => {
    const seen = new Set<string>();
    const chips: { label: string; query: string; location: string; source: 'resume' }[] = [];
    for (const q of resumeSearchQueries) {
      const key = q.query?.toLowerCase();
      if (key && !seen.has(key)) {
        seen.add(key);
        chips.push({ label: q.label || q.query, query: q.query, location: q.location || 'India', source: 'resume' });
      }
    }
    return chips;
  })();

  return (
    <div className="p-6 space-y-6 max-w-[960px]">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Profile & Search Setup</h1>
          <p className="text-sm text-slate-400 mt-0.5">Your resume drives AI scoring. Search defaults are auto-generated from it.</p>
        </div>
        <div className="flex items-center gap-2">
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
                <><HiOutlineRocketLaunch className="w-4 h-4" /> 🔍 Resume Search</>
              )}
            </button>
          )}
          <button
            onClick={() => editMode ? handleSave() : setEditMode(true)}
            disabled={saving}
            className={editMode ? 'btn-primary flex items-center gap-2' : 'btn-secondary flex items-center gap-2'}
          >
            {saving ? (
              <><HiOutlineArrowPath className="w-4 h-4 animate-spin" /> Saving...</>
            ) : editMode ? (
              <><HiOutlineCheck className="w-4 h-4" /> Save Profile</>
            ) : (
              'Edit Profile'
            )}
          </button>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════ */}
      {/* SECTION 1: RESUME UPLOAD + SEARCH DEFAULTS (UNIFIED)             */}
      {/* ═══════════════════════════════════════════════════════════════════ */}
      <div className="glass-card p-5 space-y-5">
        <h2 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
          <HiOutlineSparkles className="w-4 h-4 text-brand-400" /> Resume & Search Configuration
        </h2>

        {/* Resume Upload Area */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-xs text-slate-500 flex items-center gap-1.5">
              <HiOutlineDocumentText className="w-3.5 h-3.5" /> Resume
              {hasResume && (
                <span className="text-[10px] font-medium text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded-full flex items-center gap-1 ml-1">
                  <HiOutlineCheck className="w-3 h-3" /> Uploaded
                </span>
              )}
            </p>
            {hasResume && (
              <button
                onClick={handleDeleteResume}
                className="text-[10px] text-red-400 hover:text-red-300 flex items-center gap-1 transition-colors"
              >
                <HiOutlineTrash className="w-3 h-3" /> Remove
              </button>
            )}
          </div>

          {hasResume ? (
            <div className="flex items-center gap-3 p-3 rounded-lg bg-emerald-400/5 border border-emerald-400/20">
              <HiOutlineDocumentText className="w-8 h-8 text-emerald-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-200 truncate">
                  {profile?.resume_file_path ? profile.resume_file_path.split('/').pop() : 'Resume on file'}
                </p>
                <p className="text-xs text-slate-500">
                  {resumeStatus?.resume_text_length || profile?.resume_text?.length || 0} chars parsed
                  {resumeStatus?.last_updated && ` · Updated ${new Date(resumeStatus.last_updated).toLocaleDateString('en-IN')}`}
                </p>
              </div>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="btn-secondary text-xs flex items-center gap-1 flex-shrink-0"
              >
                <HiOutlineCloudArrowUp className="w-3.5 h-3.5" /> Replace
              </button>
            </div>
          ) : (
            <div
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleFileDrop}
              className={`border-2 border-dashed rounded-xl p-6 text-center transition-all duration-200 ${
                dragOver
                  ? 'border-brand-400 bg-brand-400/5'
                  : 'border-slate-700 bg-slate-900/20 hover:border-slate-600'
              }`}
            >
              {uploadingResume ? (
                <div className="space-y-2">
                  <HiOutlineArrowPath className="w-8 h-8 mx-auto text-brand-400 animate-spin" />
                  <p className="text-sm text-brand-300 font-medium">Parsing your resume with AI...</p>
                  <p className="text-xs text-slate-500">Extracting skills, experience & search queries</p>
                </div>
              ) : (
                <div className="space-y-2">
                  <HiOutlineCloudArrowUp className="w-8 h-8 mx-auto text-slate-600" />
                  <p className="text-sm text-slate-300 font-medium">Drop your resume here or click to upload</p>
                  <p className="text-xs text-slate-500">PDF, DOCX, or TXT · Max 10MB</p>
                  <button onClick={() => fileInputRef.current?.click()} className="btn-primary text-xs mt-1">
                    <HiOutlineCloudArrowUp className="w-3.5 h-3.5 inline mr-1" /> Choose File
                  </button>
                </div>
              )}
            </div>
          )}

          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.doc,.txt"
            onChange={handleFileSelect}
            className="hidden"
          />

          {/* Parsed Data Preview */}
          {parsedPreview && (
            <div className="p-3 rounded-lg bg-brand-500/5 border border-brand-500/20 space-y-2">
              <p className="text-xs font-medium text-brand-400 flex items-center gap-1.5">
                <HiOutlineSparkles className="w-3.5 h-3.5" /> AI Extracted From Resume
              </p>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                {parsedPreview.education && (
                  <div className="text-slate-400"><span className="text-slate-500">Education:</span> {parsedPreview.education}</div>
                )}
                {parsedPreview.current_company && (
                  <div className="text-slate-400"><span className="text-slate-500">Company:</span> {parsedPreview.current_company}</div>
                )}
                {parsedPreview.target_roles?.length > 0 && (
                  <div className="text-slate-400"><span className="text-slate-500">Targets:</span> {parsedPreview.target_roles.join(', ')}</div>
                )}
                {parsedPreview.certifications?.length > 0 && (
                  <div className="text-slate-400"><span className="text-slate-500">Certs:</span> {parsedPreview.certifications.join(', ')}</div>
                )}
              </div>
              {parsedPreview.companies_worked?.length > 0 && (
                <div className="text-xs text-slate-400">
                  <span className="text-slate-500">Past:</span> {parsedPreview.companies_worked.join(' → ')}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Divider */}
        <div className="border-t border-slate-700/50" />

        {/* Search Queries — generated from resume */}
        <div className="space-y-3">
          <p className="text-xs text-slate-500 flex items-center gap-1.5">
            <HiOutlineMagnifyingGlass className="w-3.5 h-3.5" /> Search Queries
            {hasResume && resumeSearchQueries.length > 0 && <span className="text-emerald-400">(AI-generated from your resume)</span>}
            {!hasResume && <span className="text-amber-400">(Upload your resume to generate personalized search queries)</span>}
          </p>

          {allSearchChips.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {allSearchChips.map((chip) => (
              <button
                key={chip.query + chip.location}
                onClick={() => handleChipSearch(chip.query, chip.location)}
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
          ) : (
            <p className="text-xs text-slate-600 italic">No search queries yet — upload your resume to auto-generate them.</p>
          )}

          {hasResume && resumeSearchQueries.length > 0 && (
            <p className="text-[10px] text-slate-600 flex items-center gap-1">
              <HiOutlineSparkles className="w-3 h-3 text-brand-400" /> Purple chips are AI-generated from your resume.
              Click any chip to search immediately.
            </p>
          )}
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════ */}
      {/* SECTION 2: PERSONAL INFO                                         */}
      {/* ═══════════════════════════════════════════════════════════════════ */}
      <div className="glass-card p-5 space-y-4">
        <h2 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
          <HiOutlineUser className="w-4 h-4 text-brand-400" /> Personal Information
          {hasResume && <span className="text-[10px] text-emerald-400 font-normal flex items-center gap-0.5"><HiOutlineSparkles className="w-3 h-3" /> from resume</span>}
        </h2>
        <div className="grid grid-cols-2 gap-4">
          <Field label="Full Name" value={form.full_name} editMode={editMode} onChange={(v) => setForm({ ...form, full_name: v })} />
          <Field label="Email" value={form.email} editMode={editMode} onChange={(v) => setForm({ ...form, email: v })} type="email" />
          <Field label="Phone" value={form.phone} editMode={editMode} onChange={(v) => setForm({ ...form, phone: v })} />
          <Field label="Location" value={form.location} editMode={editMode} onChange={(v) => setForm({ ...form, location: v })} icon={<HiOutlineMapPin className="w-4 h-4" />} />
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════ */}
      {/* SECTION 3: CAREER DETAILS                                        */}
      {/* ═══════════════════════════════════════════════════════════════════ */}
      <div className="glass-card p-5 space-y-4">
        <h2 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
          <HiOutlineBriefcase className="w-4 h-4 text-emerald-400" /> Career Details
          {hasResume && <span className="text-[10px] text-emerald-400 font-normal flex items-center gap-0.5"><HiOutlineSparkles className="w-3 h-3" /> from resume</span>}
        </h2>
        <div className="grid grid-cols-2 gap-4">
          <Field label="Current Role" value={form.current_role} editMode={editMode} onChange={(v) => setForm({ ...form, current_role: v })} />
          <Field label="Target Role" value={form.target_role} editMode={editMode} onChange={(v) => setForm({ ...form, target_role: v })} />
          <Field label="Experience (years)" value={String(form.experience_years)} editMode={editMode} onChange={(v) => setForm({ ...form, experience_years: parseFloat(v) || 0 })} type="number" />
          <div>
            <label className="text-xs text-slate-500 mb-1 flex items-center gap-1.5">
              <HiOutlineClock className="w-4 h-4" /> Notice Period
            </label>
            {editMode ? (
              <select value={form.notice_period} onChange={(e) => setForm({ ...form, notice_period: e.target.value })} className="input-dark w-full">
                <option value="immediate">Immediate</option>
                <option value="15_days">15 Days</option>
                <option value="30_days">30 Days</option>
                <option value="60_days">60 Days</option>
                <option value="90_days">90 Days</option>
              </select>
            ) : (
              <p className="text-sm text-slate-200 py-2 px-1 min-h-[36px]">{form.notice_period.replace('_', ' ')}</p>
            )}
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════ */}
      {/* SECTION 4: SKILLS                                                */}
      {/* ═══════════════════════════════════════════════════════════════════ */}
      <div className="glass-card p-5 space-y-4">
        <h2 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
          <HiOutlineCodeBracket className="w-4 h-4 text-purple-400" /> Skills
          {hasResume && <span className="text-[10px] text-emerald-400 font-normal">(from resume)</span>}
        </h2>
        <Field
          label="Skills (comma-separated)"
          value={skillsText}
          editMode={editMode}
          onChange={handleSkillsChange}
          multiline
          placeholder="AEM, EDS, Sling, OSGi, HTL, Java, Sightly, Dispatcher..."
        />
        {form.skills.length > 0 && !editMode && (
          <div className="flex flex-wrap gap-1.5">
            {form.skills.map((skill: string) => (
              <span
                key={skill}
                className={`text-[10px] px-2 py-0.5 rounded-full border ${
                  isAEMSkill(skill) ? 'bg-brand-500/10 text-brand-300 border-brand-500/20' : 'bg-slate-800 text-slate-400 border-slate-700/50'
                }`}
              >
                {skill}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* ═══════════════════════════════════════════════════════════════════ */}
      {/* SECTION 5: JOB TARGETS                                           */}
      {/* ═══════════════════════════════════════════════════════════════════ */}
      <div className="glass-card p-5 space-y-4">
        <h2 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
          <HiOutlineCurrencyDollar className="w-4 h-4 text-amber-400" /> Job Targets
        </h2>
        <div className="grid grid-cols-2 gap-4">
          <Field label="Min Salary (LPA)" value={String(form.expected_salary_min)} editMode={editMode} onChange={(v) => setForm({ ...form, expected_salary_min: parseInt(v) || 0 })} type="number" />
          <Field label="Max Salary (LPA)" value={String(form.expected_salary_max)} editMode={editMode} onChange={(v) => setForm({ ...form, expected_salary_max: parseInt(v) || 0 })} type="number" />
        </div>
        <div>
          <label className="text-xs text-slate-500 mb-1 block">Work Preference</label>
          {editMode ? (
            <select value={form.remote_preference} onChange={(e) => setForm({ ...form, remote_preference: e.target.value })} className="input-dark w-full">
              <option value="any">Open to all (Remote + Onsite + Hybrid)</option>
              <option value="remote">Remote only</option>
              <option value="hybrid">Hybrid preferred</option>
              <option value="onsite">Onsite only</option>
            </select>
          ) : (
            <p className="text-sm text-slate-200 py-2 px-1">
              {{any: 'Open to all', remote: 'Remote only', hybrid: 'Hybrid preferred', onsite: 'Onsite only'}[form.remote_preference] || 'Open to all'}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function isAEMSkill(skill: string): boolean {
  const aemKeywords = ['aem', 'eds', 'adobe experience', 'sling', 'osgi', 'htl', 'sightly', 'cq5', 'dispatcher', 'edge delivery', 'franklin'];
  return aemKeywords.some(kw => skill.toLowerCase().includes(kw));
}

function Field({ label, value, editMode, onChange, type = 'text', multiline = false, placeholder, icon }: {
  label: string; value: string; editMode: boolean; onChange: (v: string) => void;
  type?: string; multiline?: boolean; placeholder?: string; icon?: React.ReactNode;
}) {
  return (
    <div>
      <label className="text-xs text-slate-500 mb-1 flex items-center gap-1.5">{icon} {label}</label>
      {editMode ? (
        multiline ? (
          <textarea value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} rows={3} className="input-dark w-full resize-none" />
        ) : (
          <input type={type} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} className="input-dark w-full" />
        )
      ) : (
        <p className="text-sm text-slate-200 py-2 px-1 min-h-[36px]">{value || <span className="text-slate-600 italic">Not set</span>}</p>
      )}
    </div>
  );
}
