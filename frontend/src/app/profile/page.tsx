'use client';

import { useEffect, useState } from 'react';
import {
  HiOutlineUser,
  HiOutlineBriefcase,
  HiOutlineMapPin,
  HiOutlineCurrencyDollar,
  HiOutlineCodeBracket,
  HiOutlineAcademicCap,
  HiOutlineClock,
  HiOutlineArrowPath,
  HiOutlineCheck,
} from 'react-icons/hi2';
import { getProfile, updateProfile } from '@/lib/api';
import toast from 'react-hot-toast';

export default function ProfilePage() {
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editMode, setEditMode] = useState(false);

  // Form state
  const [form, setForm] = useState({
    name: '',
    email: '',
    phone: '',
    current_role: '',
    current_company: '',
    experience_years: 8,
    location: 'Hyderabad, India',
    skills: '',
    target_role: 'Senior AEM Developer / AEM Architect',
    target_companies: '',
    target_salary_min: 20,
    target_salary_max: 35,
    target_salary_currency: 'INR',
    preferred_remote: true,
    notice_period_days: 30,
    education: '',
    certifications: '',
    linkedin_url: '',
  });

  useEffect(() => {
    loadProfile();
  }, []);

  async function loadProfile() {
    try {
      const data = await getProfile();
      setProfile(data);
      if (data) {
        setForm({
          name: data.name || '',
          email: data.email || '',
          phone: data.phone || '',
          current_role: data.current_role || '',
          current_company: data.current_company || '',
          experience_years: data.experience_years || 8,
          location: data.location || 'Hyderabad, India',
          skills: data.skills || '',
          target_role: data.target_role || 'Senior AEM Developer / AEM Architect',
          target_companies: data.target_companies || '',
          target_salary_min: data.target_salary_min || 20,
          target_salary_max: data.target_salary_max || 35,
          target_salary_currency: data.target_salary_currency || 'INR',
          preferred_remote: data.preferred_remote ?? true,
          notice_period_days: data.notice_period_days || 30,
          education: data.education || '',
          certifications: data.certifications || '',
          linkedin_url: data.linkedin_url || '',
        });
      }
    } catch (e: any) {
      toast.error('Failed to load profile');
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    setSaving(true);
    try {
      await updateProfile(form);
      toast.success('Profile saved!');
      setEditMode(false);
      loadProfile();
    } catch (e: any) {
      toast.error(e.message || 'Failed to save profile');
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center h-[80vh]">
        <HiOutlineArrowPath className="w-8 h-8 text-brand-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-[900px]">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Profile</h1>
          <p className="text-sm text-slate-400 mt-0.5">Your profile drives AI scoring & resume tailoring</p>
        </div>
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

      {/* Profile Form */}
      <div className="space-y-6">
        {/* Personal Info */}
        <div className="glass-card p-5 space-y-4">
          <h2 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
            <HiOutlineUser className="w-4 h-4 text-brand-400" /> Personal Information
          </h2>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Full Name" value={form.name} editMode={editMode} onChange={(v) => setForm({ ...form, name: v })} />
            <Field label="Email" value={form.email} editMode={editMode} onChange={(v) => setForm({ ...form, email: v })} type="email" />
            <Field label="Phone" value={form.phone} editMode={editMode} onChange={(v) => setForm({ ...form, phone: v })} />
            <Field label="Location" value={form.location} editMode={editMode} onChange={(v) => setForm({ ...form, location: v })} icon={<HiOutlineMapPin className="w-4 h-4" />} />
          </div>
        </div>

        {/* Career */}
        <div className="glass-card p-5 space-y-4">
          <h2 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
            <HiOutlineBriefcase className="w-4 h-4 text-emerald-400" /> Career Details
          </h2>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Current Role" value={form.current_role} editMode={editMode} onChange={(v) => setForm({ ...form, current_role: v })} />
            <Field label="Current Company" value={form.current_company} editMode={editMode} onChange={(v) => setForm({ ...form, current_company: v })} />
            <Field label="Experience (years)" value={String(form.experience_years)} editMode={editMode} onChange={(v) => setForm({ ...form, experience_years: parseInt(v) || 0 })} type="number" />
            <Field label="Notice Period (days)" value={String(form.notice_period_days)} editMode={editMode} onChange={(v) => setForm({ ...form, notice_period_days: parseInt(v) || 0 })} type="number" icon={<HiOutlineClock className="w-4 h-4" />} />
          </div>
        </div>

        {/* Skills */}
        <div className="glass-card p-5 space-y-4">
          <h2 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
            <HiOutlineCodeBracket className="w-4 h-4 text-purple-400" /> Skills & Education
          </h2>
          <Field label="Skills (comma-separated)" value={form.skills} editMode={editMode} onChange={(v) => setForm({ ...form, skills: v })} multiline placeholder="AEM, EDS, Sling, OSGi, HTL, Java, Sightly, Dispatcher..." />
          <Field label="Education" value={form.education} editMode={editMode} onChange={(v) => setForm({ ...form, education: v })} />
          <Field label="Certifications" value={form.certifications} editMode={editMode} onChange={(v) => setForm({ ...form, certifications: v })} icon={<HiOutlineAcademicCap className="w-4 h-4" />} />
        </div>

        {/* Target */}
        <div className="glass-card p-5 space-y-4">
          <h2 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
            <HiOutlineCurrencyDollar className="w-4 h-4 text-amber-400" /> Job Targets
          </h2>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Target Role" value={form.target_role} editMode={editMode} onChange={(v) => setForm({ ...form, target_role: v })} />
            <Field label="Target Companies" value={form.target_companies} editMode={editMode} onChange={(v) => setForm({ ...form, target_companies: v })} placeholder="Comma-separated" />
            <Field label="Min Salary (LPA)" value={String(form.target_salary_min)} editMode={editMode} onChange={(v) => setForm({ ...form, target_salary_min: parseInt(v) || 0 })} type="number" />
            <Field label="Max Salary (LPA)" value={String(form.target_salary_max)} editMode={editMode} onChange={(v) => setForm({ ...form, target_salary_max: parseInt(v) || 0 })} type="number" />
          </div>
          <label className="flex items-center gap-3 cursor-pointer mt-2">
            <input
              type="checkbox"
              checked={form.preferred_remote}
              onChange={(e) => setForm({ ...form, preferred_remote: e.target.checked })}
              disabled={!editMode}
              className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-brand-500 focus:ring-brand-500"
            />
            <span className="text-sm text-slate-300">Open to remote roles</span>
          </label>
        </div>
      </div>
    </div>
  );
}

// ── Reusable Field Component ────────────────────────────────────────────────
function Field({ label, value, editMode, onChange, type = 'text', multiline = false, placeholder, icon }: {
  label: string;
  value: string;
  editMode: boolean;
  onChange: (v: string) => void;
  type?: string;
  multiline?: boolean;
  placeholder?: string;
  icon?: React.ReactNode;
}) {
  return (
    <div>
      <label className="text-xs text-slate-500 mb-1 flex items-center gap-1.5">
        {icon} {label}
      </label>
      {editMode ? (
        multiline ? (
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            rows={3}
            className="input-dark w-full resize-none"
          />
        ) : (
          <input
            type={type}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            className="input-dark w-full"
          />
        )
      ) : (
        <p className="text-sm text-slate-200 py-2 px-1 min-h-[36px]">{value || <span className="text-slate-600 italic">Not set</span>}</p>
      )}
    </div>
  );
}
