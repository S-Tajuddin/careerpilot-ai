'use client';

import { useEffect, useState } from 'react';
import {
  HiOutlineCog6Tooth,
  HiOutlineBell,
  HiOutlineClock,
  HiOutlineRocketLaunch,
  HiOutlineArrowPath,
  HiOutlinePlay,
  HiOutlineStop,
  HiOutlinePaperAirplane,
  HiOutlineCheck,
  HiOutlineExclamationTriangle,
} from 'react-icons/hi2';
import toast from 'react-hot-toast';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface SchedulerJob {
  id: string;
  name: string;
  next_run: string | null;
  trigger: string;
}

interface Settings {
  id: number;
  telegram_chat_id: string | null;
  telegram_bot_token: string | null;
  default_search_queries: string[] | null;
  default_location: string | null;
  min_salary: number | null;
  remote_only: boolean;
  job_alerts_enabled: boolean;
  alert_frequency: string | null;
  auto_score_jobs: boolean;
  llm_provider: string | null;
}

export default function SettingsPage() {
  const [schedulerRunning, setSchedulerRunning] = useState(false);
  const [schedulerJobs, setSchedulerJobs] = useState<SchedulerJob[]>([]);
  const [settings, setSettings] = useState<Settings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [telegramStatus, setTelegramStatus] = useState<any>(null);
  const [sendingTest, setSendingTest] = useState(false);

  // Editable fields (only scheduler/automation settings — search defaults moved to Profile)
  const [autoScore, setAutoScore] = useState(true);
  const [alertFrequency, setAlertFrequency] = useState('daily');

  useEffect(() => {
    loadAll();
  }, []);

  async function loadAll() {
    setLoading(true);
    try {
      const [schedRes, settingsRes, tgRes] = await Promise.allSettled([
        fetch(`${API_URL}/scheduler/status`).then(r => r.json()),
        fetch(`${API_URL}/scheduler/settings`).then(r => r.json()),
        fetch(`${API_URL}/telegram/test`).then(r => r.json()),
      ]);

      if (schedRes.status === 'fulfilled') {
        setSchedulerRunning(schedRes.value.running);
        setSchedulerJobs(schedRes.value.jobs || []);
      }
      if (settingsRes.status === 'fulfilled') {
        const s = settingsRes.value;
        setSettings(s);
        setAutoScore(s.auto_score_jobs);
        setAlertFrequency(s.alert_frequency || 'daily');
      }
      if (tgRes.status === 'fulfilled') setTelegramStatus(tgRes.value);
    } catch (e: any) {
      toast.error('Failed to load settings');
    } finally {
      setLoading(false);
    }
  }

  async function toggleScheduler(start: boolean) {
    try {
      const endpoint = start ? '/scheduler/start' : '/scheduler/stop';
      const res = await fetch(`${API_URL}${endpoint}`, { method: 'POST' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);
      setSchedulerRunning(start);
      setSchedulerJobs(data.jobs || []);
      toast.success(start ? 'Scheduler started' : 'Scheduler stopped');
    } catch (e: any) {
      toast.error(e.message);
    }
  }

  async function saveSettings() {
    setSaving(true);
    try {
      const res = await fetch(`${API_URL}/scheduler/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          auto_score_jobs: autoScore,
          alert_frequency: alertFrequency,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);
      toast.success('Settings saved!');
    } catch (e: any) {
      toast.error(e.message || 'Save failed');
    } finally {
      setSaving(false);
    }
  }

  async function triggerManual(action: string) {
    try {
      const res = await fetch(`${API_URL}/scheduler/trigger/${action}`, { method: 'POST' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);
      toast.success(data.message);
    } catch (e: any) {
      toast.error(e.message);
    }
  }

  async function sendTelegramTest() {
    setSendingTest(true);
    try {
      const res = await fetch(`${API_URL}/telegram/send-test`, { method: 'POST' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);
      toast.success('✅ Test message sent to Telegram!');
    } catch (e: any) {
      toast.error(e.message);
    } finally {
      setSendingTest(false);
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
      <div>
        <h1 className="text-2xl font-bold text-white">Settings & Automation</h1>
        <p className="text-sm text-slate-400 mt-0.5">Scheduler, Telegram alerts, automation preferences</p>
      </div>

      {/* Scheduler Control */}
      <div className="glass-card p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <HiOutlineClock className="w-5 h-5 text-brand-400" />
            <div>
              <h2 className="text-sm font-semibold text-white">Background Scheduler</h2>
              <p className="text-xs text-slate-500">Automated job search, digests, and reminders</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className={`flex items-center gap-1.5 text-xs ${schedulerRunning ? 'text-emerald-400' : 'text-slate-500'}`}>
              <div className={`w-2 h-2 rounded-full ${schedulerRunning ? 'bg-emerald-400 pulse-dot' : 'bg-slate-600'}`} />
              {schedulerRunning ? 'Running' : 'Stopped'}
            </div>
            <button
              onClick={() => toggleScheduler(!schedulerRunning)}
              className={schedulerRunning ? 'btn-secondary text-xs flex items-center gap-1.5' : 'btn-primary text-xs flex items-center gap-1.5'}
            >
              {schedulerRunning ? <><HiOutlineStop className="w-3.5 h-3.5" /> Stop</> : <><HiOutlinePlay className="w-3.5 h-3.5" /> Start</>}
            </button>
          </div>
        </div>

        {/* Scheduled Jobs */}
        {schedulerJobs.length > 0 && (
          <div className="space-y-2">
            {schedulerJobs.map((job) => (
              <div key={job.id} className="flex items-center justify-between py-2.5 px-3 rounded-lg bg-slate-900/40">
                <div>
                  <p className="text-xs font-medium text-slate-300">{job.name}</p>
                  <p className="text-[10px] text-slate-600">{job.trigger}</p>
                </div>
                <div className="text-right">
                  <p className="text-[10px] text-slate-500">Next run</p>
                  <p className="text-xs text-slate-400">
                    {job.next_run ? new Date(job.next_run).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'short' }) : 'Pending'}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Manual Triggers */}
        <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-700/50">
          <button onClick={() => triggerManual('search')} className="btn-secondary text-xs flex items-center gap-1.5">
            <HiOutlineRocketLaunch className="w-3.5 h-3.5" /> Run Search Now
          </button>
          <button onClick={() => triggerManual('digest')} className="btn-secondary text-xs flex items-center gap-1.5">
            <HiOutlineBell className="w-3.5 h-3.5" /> Send Digest Now
          </button>
        </div>
      </div>

      {/* Telegram Notifications */}
      <div className="glass-card p-5 space-y-4">
        <div className="flex items-center gap-3">
          <HiOutlineBell className="w-5 h-5 text-purple-400" />
          <div>
            <h2 className="text-sm font-semibold text-white">Telegram Notifications</h2>
            <p className="text-xs text-slate-500">Job alerts, daily digests, follow-up reminders</p>
          </div>
        </div>

        {telegramStatus && (
          <div className={`flex items-center gap-3 p-3 rounded-lg ${
            telegramStatus.status === 'ok' ? 'bg-emerald-400/5 border border-emerald-400/20' : 'bg-amber-400/5 border border-amber-400/20'
          }`}>
            {telegramStatus.status === 'ok' ? (
              <>
                <HiOutlineCheck className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <div>
                  <p className="text-xs text-emerald-400">Connected — @{telegramStatus.bot_name}</p>
                  <p className="text-[10px] text-slate-500">Chat ID: {telegramStatus.chat_id_configured ? 'Set ✅' : 'Not set ❌'}</p>
                </div>
              </>
            ) : (
              <>
                <HiOutlineExclamationTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
                <p className="text-xs text-amber-400">{telegramStatus.detail}</p>
              </>
            )}
          </div>
        )}

        <button onClick={sendTelegramTest} disabled={sendingTest} className="btn-secondary text-xs flex items-center gap-1.5">
          {sendingTest ? <HiOutlineArrowPath className="w-3.5 h-3.5 animate-spin" /> : <HiOutlinePaperAirplane className="w-3.5 h-3.5" />}
          {sendingTest ? 'Sending...' : 'Send Test Message'}
        </button>
      </div>

      {/* Automation Preferences (search defaults REMOVED — now on Profile page) */}
      <div className="glass-card p-5 space-y-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <HiOutlineCog6Tooth className="w-5 h-5 text-amber-400" /> Automation Preferences
        </h2>

        <div className="grid grid-cols-2 gap-4">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={autoScore}
              onChange={(e) => setAutoScore(e.target.checked)}
              className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-brand-500 focus:ring-brand-500"
            />
            <div>
              <span className="text-sm text-slate-300">Auto-score new jobs</span>
              <p className="text-[10px] text-slate-600">Quick-score every job found during search</p>
            </div>
          </label>
        </div>

        <div>
          <label className="text-xs text-slate-500 mb-1 block">Alert Frequency</label>
          <select
            value={alertFrequency}
            onChange={(e) => setAlertFrequency(e.target.value)}
            className="input-dark w-48"
          >
            <option value="daily">Daily</option>
            <option value="twice_daily">Twice Daily</option>
            <option value="weekly">Weekly</option>
          </select>
        </div>

        <div className="pt-2 border-t border-slate-700/50">
          <p className="text-xs text-slate-600">
            💡 Search defaults (queries, location, salary, remote preference) are now configured on the <a href="/profile" className="text-brand-400 hover:underline">Profile page</a> — auto-generated from your resume.
          </p>
        </div>

        <button onClick={saveSettings} disabled={saving} className="btn-primary flex items-center gap-2">
          {saving ? <HiOutlineArrowPath className="w-4 h-4 animate-spin" /> : <HiOutlineCheck className="w-4 h-4" />}
          {saving ? 'Saving...' : 'Save Settings'}
        </button>
      </div>
    </div>
  );
}
