import React, { useState } from 'react';
import { Play, Sparkles, AlertCircle, Clock, ShieldCheck, ArrowRight } from 'lucide-react';

const SCENARIO_BUTTONS = [
  {
    id: 'scenario_1_success',
    title: 'Scenario 1: Approved Settlement',
    badge: 'Standard Payout',
    badgeColor: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
    prompt: 'Handle the Zelar payment.',
    subtitle: 'Thoughtworks pays Zelar ₹2.4L via stripe.payout.create to verified bank ba_zelar_corp_hdfc_0981.',
  },
  {
    id: 'scenario_2_failure',
    title: 'Scenario 2: Payout Failure',
    badge: 'Exception Recovery',
    badgeColor: 'bg-red-500/20 text-red-300 border-red-500/30',
    prompt: 'Handle the Zelar payment.',
    subtitle: 'Destination bank error on payout rails. OpsPilot updates Jira, alerts Finance in Slack, and records exception.',
  },
  {
    id: 'scenario_3_unknown_timeout',
    title: 'Scenario 3: Gateway Timeout',
    badge: 'Uncertain State',
    badgeColor: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
    prompt: 'Handle the Zelar payment.',
    subtitle: 'Gateway drops connection. OpsPilot prevents duplicate payout and queries stripe.payout.get for reconciliation.',
  },
  {
    id: 'scenario_4_mismatch',
    title: 'Scenario 4: Amount Mismatch',
    badge: 'Safety Block',
    badgeColor: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
    prompt: 'Pay ₹2,80,000 to vendor Zelar for March infrastructure services.',
    subtitle: 'User asks for ₹2.8L but approved invoice is ₹2.4L. OpsPilot blocks payout & logs Jira reconciliation ticket.',
  },
];

export function ScenarioBar({ activeScenario, setActiveScenario, onRun, isRunning }) {
  const [customPrompt, setCustomPrompt] = useState('Handle the Zelar payment.');

  const handleSelectScenario = (scen) => {
    setActiveScenario(scen.id);
    setCustomPrompt(scen.prompt);
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    if (!customPrompt.trim() || isRunning) return;
    onRun(customPrompt, activeScenario);
  };

  return (
    <div className="bg-dark-900 border-b border-white/10 px-6 py-4">
      <div className="max-w-7xl mx-auto space-y-3.5">
        {/* Scenario Carousel */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider whitespace-nowrap mr-1 flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5 text-brand-400" /> Scenarios:
          </span>
          {SCENARIO_BUTTONS.map((scen) => {
            const isSelected = activeScenario === scen.id;
            return (
              <button
                key={scen.id}
                onClick={() => handleSelectScenario(scen)}
                disabled={isRunning}
                className={`text-left px-3.5 py-2 rounded-lg border transition-all flex-shrink-0 flex flex-col gap-0.5 ${
                  isSelected
                    ? 'bg-dark-800 border-brand-500/60 shadow-sm shadow-brand-500/20 ring-1 ring-brand-500/40'
                    : 'bg-dark-950/60 border-white/5 hover:border-white/20 text-slate-400 hover:text-slate-200'
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className={`text-xs font-semibold ${isSelected ? 'text-white' : 'text-slate-300'}`}>
                    {scen.title}
                  </span>
                  <span className={`px-1.5 py-0.2 rounded text-[10px] font-semibold uppercase border ${scen.badgeColor}`}>
                    {scen.badge}
                  </span>
                </div>
                <span className="text-[11px] text-slate-400 truncate max-w-[280px]">
                  {scen.subtitle}
                </span>
              </button>
            );
          })}
        </div>

        {/* Input Bar */}
        <form onSubmit={handleFormSubmit} className="flex items-center gap-2">
          <div className="relative flex-1">
            <input
              type="text"
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              placeholder="e.g. Handle the Zelar payment."
              disabled={isRunning}
              className="w-full bg-dark-950 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-brand-500/80 focus:ring-2 focus:ring-brand-500/20 transition disabled:opacity-50"
            />
          </div>
          <button
            type="submit"
            disabled={isRunning || !customPrompt.trim()}
            className="flex items-center gap-2 bg-gradient-to-r from-brand-500 to-brand-600 hover:from-brand-600 hover:to-brand-700 text-white font-medium px-5 py-2.5 rounded-xl shadow-md shadow-brand-500/20 hover:shadow-brand-500/30 transition disabled:opacity-50 disabled:cursor-not-allowed text-sm"
          >
            <Play className={`w-4 h-4 fill-white ${isRunning ? 'animate-spin' : ''}`} />
            <span>{isRunning ? 'Operator Executing...' : 'Run Agent Operator'}</span>
          </button>
        </form>
      </div>
    </div>
  );
}
