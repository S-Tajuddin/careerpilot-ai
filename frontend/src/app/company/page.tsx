'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import {
  HiOutlineBuildingOffice2,
  HiOutlineChatBubbleLeftRight,
  HiOutlineCurrencyDollar,
  HiOutlineLightBulb,
  HiOutlineMagnifyingGlass,
  HiOutlineArrowPath,
} from 'react-icons/hi2';
import { researchCompany, getInterviewTips, getSalaryIntel } from '@/lib/api';
import toast from 'react-hot-toast';

const KNOWN_AEM_COMPANIES = [
  'Accenture', 'Infosys', 'Wipro', 'TCS', 'Cognizant', 'Capgemini',
  'IBM', 'Deloitte', 'Adobe', 'Publicis Sapient', 'HCL', 'Tech Mahindra',
];

function CompanyPageInner() {
  const [companyName, setCompanyName] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'research' | 'interview' | 'salary'>('research');
  const [research, setResearch] = useState<any>(null);
  const [interviewTips, setInterviewTips] = useState<any>(null);
  const [salaryIntel, setSalaryIntel] = useState<any>(null);
  const searchParams = useSearchParams();

  useEffect(() => {
    const name = searchParams.get('name');
    if (name) {
      setCompanyName(name);
      handleResearchWithName(name);
    }
  }, []);

  async function handleResearch() {
    if (!companyName.trim()) return;
    setLoading(true);
    try {
      const data = await researchCompany(companyName);
      setResearch(data);
      setActiveTab('research');
      toast.success(`Research loaded for ${companyName}`);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Research failed');
    } finally {
      setLoading(false);
    }
  }

  async function handleInterviewTips() {
    if (!companyName.trim()) return;
    setLoading(true);
    try {
      const data = await getInterviewTips(companyName);
      setInterviewTips(data);
      setActiveTab('interview');
      toast.success('Interview tips loaded');
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to get tips');
    } finally {
      setLoading(false);
    }
  }

  async function handleSalaryIntel() {
    if (!companyName.trim()) return;
    setLoading(true);
    try {
      const data = await getSalaryIntel(companyName);
      setSalaryIntel(data);
      setActiveTab('salary');
      toast.success('Salary intel loaded');
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to get salary info');
    } finally {
      setLoading(false);
    }
  }

  async function handleResearchWithName(name: string) {
    setLoading(true);
    try {
      const data = await researchCompany(name);
      setResearch(data);
      setActiveTab('research');
      toast.success(`Research loaded for ${name}`);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Research failed');
    } finally {
      setLoading(false);
    }
  }

  const hasResults = research || interviewTips || salaryIntel;

  return (
    <div className="p-6 space-y-6 max-w-[1400px]">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Company Intel</h1>
        <p className="text-sm text-slate-400 mt-0.5">AI-powered company research, interview tips & salary insights via Gemini Flash</p>
      </div>

      {/* Search */}
      <div className="glass-card p-5 space-y-4">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <HiOutlineBuildingOffice2 className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
            <input
              type="text"
              placeholder="Enter company name — e.g. Accenture, Adobe, Infosys..."
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleResearch()}
              className="input-dark w-full pl-10"
            />
          </div>
          <button onClick={handleResearch} disabled={loading} className="btn-primary flex items-center gap-2">
            {loading ? <HiOutlineArrowPath className="w-4 h-4 animate-spin" /> : <HiOutlineMagnifyingGlass className="w-4 h-4" />}
            Research
          </button>
        </div>

        {/* Quick company chips */}
        <div className="flex flex-wrap gap-2">
          <span className="text-xs text-slate-500 py-1">Known AEM hirers:</span>
          {KNOWN_AEM_COMPANIES.map((c) => (
            <button
              key={c}
              onClick={() => { setCompanyName(c); }}
              className="text-xs px-3 py-1.5 rounded-full bg-slate-800/80 text-slate-300 border border-slate-700/50 
                         hover:border-brand-500/30 hover:text-brand-300 transition-all"
            >
              {c}
            </button>
          ))}
        </div>

        {/* Action buttons */}
        {companyName && (
          <div className="flex gap-2">
            <button onClick={handleInterviewTips} disabled={loading} className="btn-secondary text-xs flex items-center gap-1.5">
              <HiOutlineChatBubbleLeftRight className="w-4 h-4" /> Interview Tips
            </button>
            <button onClick={handleSalaryIntel} disabled={loading} className="btn-secondary text-xs flex items-center gap-1.5">
              <HiOutlineCurrencyDollar className="w-4 h-4" /> Salary Intel
            </button>
          </div>
        )}
      </div>

      {/* Results */}
      {hasResults && (
        <div className="space-y-4">
          {/* Tabs */}
          <div className="flex gap-1 bg-slate-800/50 p-1 rounded-lg w-fit">
            {[
              { key: 'research' as const, label: 'Research', icon: HiOutlineBuildingOffice2, data: research },
              { key: 'interview' as const, label: 'Interview Tips', icon: HiOutlineChatBubbleLeftRight, data: interviewTips },
              { key: 'salary' as const, label: 'Salary Intel', icon: HiOutlineCurrencyDollar, data: salaryIntel },
            ].map(({ key, label, icon: Icon, data }) => (
              <button
                key={key}
                onClick={() => data && setActiveTab(key)}
                disabled={!data}
                className={`flex items-center gap-1.5 px-4 py-2 rounded-md text-xs font-medium transition-all ${
                  activeTab === key && data
                    ? 'bg-brand-600 text-white'
                    : data
                    ? 'text-slate-400 hover:text-slate-200'
                    : 'text-slate-600 cursor-not-allowed'
                }`}
              >
                <Icon className="w-4 h-4" /> {label}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div className="glass-card p-6">
            {activeTab === 'research' && research && (
              <div className="prose prose-invert prose-sm max-w-none">
                <h2 className="text-lg font-bold text-white mb-3">{research.company_name || companyName}</h2>
                <div className="text-sm text-slate-300 leading-relaxed whitespace-pre-line">
                  {research.research || research.content || JSON.stringify(research, null, 2)}
                </div>
              </div>
            )}

            {activeTab === 'interview' && interviewTips && (
              <div className="prose prose-invert prose-sm max-w-none">
                <h2 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
                  <HiOutlineLightBulb className="w-5 h-5 text-amber-400" />
                  Interview Tips for {companyName}
                </h2>
                <div className="text-sm text-slate-300 leading-relaxed whitespace-pre-line">
                  {interviewTips.tips || interviewTips.content || JSON.stringify(interviewTips, null, 2)}
                </div>
              </div>
            )}

            {activeTab === 'salary' && salaryIntel && (
              <div className="prose prose-invert prose-sm max-w-none">
                <h2 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
                  <HiOutlineCurrencyDollar className="w-5 h-5 text-emerald-400" />
                  Salary Intel for {companyName}
                </h2>
                <div className="text-sm text-slate-300 leading-relaxed whitespace-pre-line">
                  {salaryIntel.salary_info || salaryIntel.content || JSON.stringify(salaryIntel, null, 2)}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!hasResults && !loading && (
        <div className="glass-card p-12 text-center">
          <HiOutlineBuildingOffice2 className="w-16 h-16 mx-auto mb-4 text-slate-700" />
          <h3 className="text-lg font-medium text-slate-400 mb-2">Company Intelligence</h3>
          <p className="text-sm text-slate-500 max-w-md mx-auto">
            Enter a company name above to get AI-powered research, interview tips, and salary insights. 
            Powered by Gemini Flash.
          </p>
        </div>
      )}
    </div>
  );
}

export default function CompanyPage() {
  return (
    <Suspense fallback={<div className="p-6 flex items-center justify-center h-[80vh]"><div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" /></div>}>
      <CompanyPageInner />
    </Suspense>
  );
}
