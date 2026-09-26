import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  ArrowRight,
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Lock,
  Layers,
  FileText,
  Building,
  Landmark,
  CheckSquare,
  MessageSquare,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  ExternalLink,
} from 'lucide-react';
import { ApprovalModal } from './ApprovalModal';
import { ToolTimeline } from './ToolTimeline';

const EXAMPLE_COMMANDS = [
  {
    id: 'scenario_1_success',
    text: "Settle Zelar's approved March invoice for ₹2,40,000.",
    badge: 'Standard Payout',
  },
  {
    id: 'scenario_2_failure',
    text: "Find out why Zelar's payout failed and resolve the issue.",
    badge: 'Exception Recovery',
  },
  {
    id: 'scenario_3_unknown_timeout',
    text: "Check this vendor settlement and tell me what is blocking it.",
    badge: 'Timeout Reconcile',
  },
  {
    id: 'scenario_4_mismatch',
    text: "Pay this invoice, but stop if anything doesn't match the approved records.",
    badge: 'Safety Block',
  },
];

const BUSINESS_STAGES = [
  { id: 'understand', label: 'Understanding request' },
  { id: 'invoice', label: 'Verifying approved invoice' },
  { id: 'vendor', label: 'Checking vendor' },
  { id: 'history', label: 'Checking payment history' },
  { id: 'approval_internal', label: 'Confirming internal approval' },
  { id: 'prepare', label: 'Preparing vendor settlement' },
  { id: 'auth_gate', label: 'Authorization required' },
  { id: 'payout', label: 'Settlement initiated' },
  { id: 'records', label: 'Updating business records' },
  { id: 'notify', label: 'Notifying finance' },
  { id: 'remittance', label: 'Remittance prepared' },
  { id: 'complete', label: 'Completed' },
];

export function CommandView({
  runState,
  events = [],
  auditLogs = [],
  isLoading,
  error,
  activeScenario,
  setActiveScenario,
  demoMode,
  onRun,
  onApprove,
  onReject,
  onNavigateToAdmin,
}) {
  const [prompt, setPrompt] = useState("Settle Zelar's approved March invoice for ₹2,40,000.");
  const [submittedPrompt, setSubmittedPrompt] = useState('');

  const hasRunStarted = !!runState || events.length > 0 || isLoading;
  const isCompleted = runState && (runState.status === 'COMPLETED' || runState.status === 'BLOCKED' || runState.status === 'FAILED' || runState.payment_state === 'PAID' || runState.payment_state === 'BLOCKED');
  const isBlockedMismatch = runState && (runState.payment_state === 'BLOCKED' || runState.status === 'BLOCKED' || activeScenario === 'scenario_4_mismatch');
  const isFailureRecovery = runState && (runState.payment_state === 'FAILED' || (activeScenario === 'scenario_2_failure' && isCompleted));

  const handleExampleClick = (example) => {
    setPrompt(example.text);
    setActiveScenario(example.id);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!prompt.trim() || isLoading) return;

    // Detect scenario from prompt if changed
    let scenId = activeScenario;
    const lower = prompt.toLowerCase();
    if (lower.includes('2,80,000') || lower.includes('280000') || lower.includes("doesn't match") || lower.includes('mismatch') || lower.includes('stop if')) {
      scenId = 'scenario_4_mismatch';
    } else if (lower.includes('failed') || lower.includes('resolve the issue')) {
      scenId = 'scenario_2_failure';
    } else if (lower.includes('blocking') || lower.includes('timeout')) {
      scenId = 'scenario_3_unknown_timeout';
    }

    setSubmittedPrompt(prompt);
    setActiveScenario(scenId);
    onRun(prompt, scenId);
  };

  const getStageStatus = (stageId) => {
    if (!runState && events.length === 0) return 'idle';

    const pState = runState?.payment_state || '';
    const currentStatus = runState?.status || '';
    const eventTypes = events.map((e) => e.event_type);
    const providers = events.map((e) => e.provider || '');

    switch (stageId) {
      case 'understand':
        return eventTypes.includes('run.started') || hasRunStarted ? 'completed' : 'idle';
      case 'invoice':
        return providers.includes('Notion') ? 'completed' : hasRunStarted ? 'active' : 'idle';
      case 'vendor':
        return providers.includes('Stripe') ? 'completed' : 'idle';
      case 'history':
        return providers.includes('Stripe') ? 'completed' : 'idle';
      case 'approval_internal':
        return providers.includes('Slack') ? 'completed' : 'idle';
      case 'prepare':
        return eventTypes.includes('decision.created') ? 'completed' : 'idle';
      case 'auth_gate':
        if (['AWAITING_APPROVAL', 'APPROVAL_REQUIRED'].includes(pState) || currentStatus === 'APPROVAL_REQUIRED') return 'waiting';
        if (runState?.approval_status === 'APPROVED' || eventTypes.includes('approval.received')) return 'completed';
        if (pState === 'BLOCKED') return 'skipped';
        return 'idle';
      case 'payout':
        if (['PAID', 'SUCCEEDED', 'RECONCILING'].includes(pState)) return 'completed';
        if (['EXECUTING', 'PAYOUT_CREATING', 'EXECUTION_LOCKED', 'HUMAN_APPROVED'].includes(currentStatus)) return 'active';
        return 'idle';
      case 'records':
        return providers.includes('Jira') ? 'completed' : 'idle';
      case 'notify':
        return eventTypes.includes('action.completed') && events.some((e) => e.provider === 'Slack') ? 'completed' : 'idle';
      case 'remittance':
        return eventTypes.includes('action.completed') && events.some((e) => e.provider === 'Gmail') ? 'completed' : 'idle';
      case 'complete':
        return isCompleted ? 'completed' : 'idle';
      default:
        return 'idle';
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-300">
      {/* 1. HERO / LANDING COMMAND BOX */}
      {!hasRunStarted ? (
        <div className="space-y-8 py-8 text-center sm:text-left">
          {/* Hero Header */}
          <div className="space-y-3">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-brand-500/10 text-brand-300 border border-brand-500/30">
              <Sparkles className="w-3.5 h-3.5 text-brand-400" />
              <span>Autonomous AI Operator</span>
            </div>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-white tracking-tight leading-tight">
              Tell OpsPilot what needs to get done.
            </h1>
            <p className="text-base sm:text-lg text-slate-300 max-w-2xl leading-relaxed">
              Describe the outcome. OpsPilot handles the workflow, coordination and follow-through across all your enterprise systems.
            </p>
          </div>

          {/* Primary Command Input */}
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="relative group">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-brand-500 to-indigo-500 rounded-2xl blur opacity-30 group-hover:opacity-60 transition duration-300"></div>
              <div className="relative bg-dark-900 border border-white/15 rounded-2xl p-2.5 sm:p-3 shadow-2xl flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                <input
                  type="text"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="e.g. Settle Zelar's approved March invoice for ₹2,40,000."
                  disabled={isLoading}
                  className="flex-1 bg-transparent border-0 px-3 py-2.5 text-base sm:text-lg text-white placeholder-slate-500 focus:outline-none focus:ring-0"
                />
                <button
                  type="submit"
                  disabled={isLoading || !prompt.trim()}
                  className="flex items-center justify-center gap-2 bg-gradient-to-r from-brand-500 via-brand-600 to-indigo-600 hover:from-brand-600 hover:to-indigo-700 text-white font-bold text-sm sm:text-base px-6 py-3 rounded-xl shadow-lg shadow-brand-500/25 transition active:scale-[0.98] disabled:opacity-50 whitespace-nowrap cursor-pointer"
                >
                  <span>{isLoading ? 'Running Operator...' : 'Run with OpsPilot'}</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Empty State Tagline */}
            <div className="flex items-center justify-between text-xs text-slate-400 px-1 pt-1">
              <span className="italic font-medium text-slate-400">
                "One request in. One business outcome out."
              </span>
              <span className="font-mono text-[11px] text-slate-500">
                Connected: Notion • Stripe • Jira • Slack • Gmail
              </span>
            </div>
          </form>

          {/* 2. EXAMPLE COMMANDS */}
          <div className="space-y-3 pt-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block">
              Example Business Instructions:
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {EXAMPLE_COMMANDS.map((example) => (
                <button
                  key={example.id}
                  onClick={() => handleExampleClick(example)}
                  type="button"
                  className="text-left p-4 rounded-xl bg-dark-900/70 hover:bg-dark-800 border border-white/10 hover:border-brand-500/40 transition group cursor-pointer space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-brand-300 group-hover:text-brand-200">
                      {example.badge}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono group-hover:text-slate-400">
                      Click to fill ↵
                    </span>
                  </div>
                  <p className="text-xs text-slate-200 group-hover:text-white leading-snug">
                    "{example.text}"
                  </p>
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : (
        /* IN-FLIGHT / EXECUTION VIEW */
        <div className="space-y-6">
          {/* Active Request Banner */}
          <div className="glass-panel-glow rounded-2xl p-5 border border-brand-500/40 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <span className="text-[10px] font-mono font-bold tracking-widest uppercase text-brand-400">
                REQUEST
              </span>
              <h2 className="text-base sm:text-lg font-semibold text-white">
                "{submittedPrompt || prompt}"
              </h2>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <button
                onClick={onNavigateToAdmin}
                className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-xs font-medium text-slate-300 hover:text-white transition flex items-center gap-1.5"
              >
                <span>Admin Console</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Error Alert if any */}
          {error && (
            <div className="p-4 rounded-xl bg-red-950/50 border border-red-500/40 text-red-200 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Business Progression Flow (Horizontal Badge Stepper) */}
          <div className="glass-panel rounded-2xl p-4 border border-white/10 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-brand-400" /> Live Business Progression
              </span>
              <span className="text-[11px] font-mono text-slate-400">
                {isCompleted ? 'Finished' : isLoading ? 'In Progress' : 'Awaiting Action'}
              </span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
              {BUSINESS_STAGES.map((stg) => {
                const status = getStageStatus(stg.id);
                let badgeClass = 'bg-dark-950/40 text-slate-500 border-white/5';
                if (status === 'completed') {
                  badgeClass = 'bg-emerald-950/40 text-emerald-300 border-emerald-500/30';
                } else if (status === 'active') {
                  badgeClass = 'bg-brand-950/60 text-brand-300 border-brand-500/50 ring-1 ring-brand-500/40 animate-pulse';
                } else if (status === 'waiting') {
                  badgeClass = 'bg-purple-950/60 text-purple-300 border-purple-500/50 animate-bounce';
                } else if (status === 'skipped') {
                  badgeClass = 'bg-slate-900/40 text-slate-600 line-through border-slate-800';
                }

                return (
                  <div
                    key={stg.id}
                    className={`p-2 rounded-lg border text-[11px] font-medium flex items-center gap-1.5 transition-all ${badgeClass}`}
                  >
                    {status === 'completed' && <CheckCircle2 className="w-3 h-3 text-emerald-400 flex-shrink-0" />}
                    {status === 'active' && <RefreshCw className="w-3 h-3 text-brand-400 animate-spin flex-shrink-0" />}
                    {status === 'waiting' && <Lock className="w-3 h-3 text-purple-400 flex-shrink-0" />}
                    {status === 'idle' && <span className="w-1.5 h-1.5 rounded-full bg-slate-700 flex-shrink-0" />}
                    <span className="truncate">{stg.label}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Human Authorization Gate (Interactive Modal) */}
          <ApprovalModal
            runState={runState}
            onApprove={onApprove}
            onReject={onReject}
            isLoading={isLoading}
          />

          {/* 3. FINAL OUTCOME CARDS (When Completed / Blocked) */}
          {isCompleted && (
            <div>
              {isBlockedMismatch ? (
                /* Mismatch / Blocked Outcome */
                <div className="glass-panel-glow rounded-2xl p-6 border-2 border-purple-500/50 bg-gradient-to-br from-purple-950/40 via-dark-950 to-dark-900 space-y-4 animate-in fade-in zoom-in-95">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 rounded-xl bg-purple-500/20 text-purple-400 border border-purple-500/30">
                        <ShieldAlert className="w-6 h-6" />
                      </div>
                      <div>
                        <span className="text-[10px] font-bold uppercase tracking-wider text-purple-400 block">
                          Safety Block Enforced
                        </span>
                        <h3 className="font-bold text-lg text-white">
                          OpsPilot stopped the settlement.
                        </h3>
                      </div>
                    </div>
                    <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                      BLOCKED
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-dark-950/80 p-4 rounded-xl border border-white/5 text-xs">
                    <div>
                      <span className="text-slate-400 block mb-0.5">Requested Amount</span>
                      <span className="text-white font-mono font-bold text-sm">₹2,80,000.00</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block mb-0.5">Approved Amount</span>
                      <span className="text-emerald-400 font-mono font-bold text-sm">₹2,40,000.00</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block mb-0.5">Variance Detected</span>
                      <span className="text-red-400 font-mono font-bold text-sm">₹40,000.00</span>
                    </div>
                  </div>

                  <p className="text-xs text-slate-200 leading-relaxed font-medium">
                    Payment was not released because the request does not match the approved business record.
                  </p>

                  <div className="flex flex-wrap items-center gap-4 text-xs text-slate-300 pt-2 border-t border-white/10">
                    <span className="flex items-center gap-1.5 text-blue-300">
                      <CheckCircle2 className="w-4 h-4 text-blue-400" /> Jira reconciliation created (SCRUM-43)
                    </span>
                    <span className="flex items-center gap-1.5 text-amber-300">
                      <CheckCircle2 className="w-4 h-4 text-amber-400" /> Finance notified (#finance-ops)
                    </span>
                  </div>

                  <div className="pt-2 flex justify-end">
                    <button
                      onClick={onNavigateToAdmin}
                      className="text-xs font-semibold text-brand-400 hover:text-brand-300 flex items-center gap-1 cursor-pointer"
                    >
                      View operational details in Admin Console →
                    </button>
                  </div>
                </div>
              ) : isFailureRecovery ? (
                /* Failure Exception Outcome */
                <div className="glass-panel-glow rounded-2xl p-6 border-2 border-red-500/50 bg-gradient-to-br from-red-950/40 via-dark-950 to-dark-900 space-y-4 animate-in fade-in zoom-in-95">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 rounded-xl bg-red-500/20 text-red-400 border border-red-500/30">
                        <AlertTriangle className="w-6 h-6" />
                      </div>
                      <div>
                        <span className="text-[10px] font-bold uppercase tracking-wider text-red-400 block">
                          Exception Recovery
                        </span>
                        <h3 className="font-bold text-lg text-white">
                          OpsPilot flagged payout exception and initiated recovery.
                        </h3>
                      </div>
                    </div>
                    <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-red-500/20 text-red-300 border border-red-500/30">
                      RECOVERY ACTIVE
                    </span>
                  </div>

                  <p className="text-xs text-slate-200 leading-relaxed font-medium">
                    Destination bank rejected payout rails. OpsPilot halted automatic retries to prevent duplicate disbursement, created Jira incident ticket, and notified Finance Operations.
                  </p>

                  <div className="flex flex-wrap items-center gap-4 text-xs text-slate-300 pt-2 border-t border-white/10">
                    <span className="flex items-center gap-1.5 text-blue-300">
                      <CheckCircle2 className="w-4 h-4 text-blue-400" /> Jira incident updated
                    </span>
                    <span className="flex items-center gap-1.5 text-amber-300">
                      <CheckCircle2 className="w-4 h-4 text-amber-400" /> Finance alerted on Slack
                    </span>
                  </div>

                  <div className="pt-2 flex justify-end">
                    <button
                      onClick={onNavigateToAdmin}
                      className="text-xs font-semibold text-brand-400 hover:text-brand-300 flex items-center gap-1 cursor-pointer"
                    >
                      View operational details in Admin Console →
                    </button>
                  </div>
                </div>
              ) : (
                /* Successful Settlement Outcome */
                <div className="glass-panel-glow rounded-2xl p-6 border-2 border-emerald-500/50 bg-gradient-to-br from-emerald-950/40 via-dark-950 to-dark-900 space-y-4 animate-in fade-in zoom-in-95">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                        <CheckCircle2 className="w-6 h-6" />
                      </div>
                      <div>
                        <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 block">
                          Done
                        </span>
                        <h3 className="font-bold text-lg text-white">
                          Zelar's approved settlement has been processed.
                        </h3>
                      </div>
                    </div>
                    <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                      SETTLED (₹2,40,000)
                    </span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-dark-950/80 p-4 rounded-xl border border-white/5 text-xs">
                    <div className="flex items-center gap-2 text-emerald-300">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                      <span className="font-medium">Settlement completed</span>
                    </div>
                    <div className="flex items-center gap-2 text-emerald-300">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                      <span className="font-medium">Jira updated</span>
                    </div>
                    <div className="flex items-center gap-2 text-emerald-300">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                      <span className="font-medium">Finance notified</span>
                    </div>
                    <div className="flex items-center gap-2 text-emerald-300">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                      <span className="font-medium">Remittance prepared</span>
                    </div>
                  </div>

                  {runState?.final_response && (
                    <div className="text-xs text-slate-200 whitespace-pre-line leading-relaxed bg-black/40 p-4 rounded-xl border border-white/5">
                      {runState.final_response}
                    </div>
                  )}

                  <div className="pt-2 flex justify-end">
                    <button
                      onClick={onNavigateToAdmin}
                      className="text-xs font-semibold text-brand-400 hover:text-brand-300 flex items-center gap-1 cursor-pointer"
                    >
                      View operational details →
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 4. WHAT OPSPIOLOT HANDLED (Business Actions + Expandable Technical Details) */}
          <ToolTimeline events={events} />

          {/* 5. FOOTER SHORTCUT TO ADMIN CONSOLE */}
          <div className="p-4 rounded-xl bg-dark-900/60 border border-white/10 flex items-center justify-between text-xs">
            <span className="text-slate-400">
              Need full multi-system telemetry, audit trail & raw tool schemas?
            </span>
            <button
              onClick={onNavigateToAdmin}
              className="px-3.5 py-1.5 rounded-lg bg-brand-500/20 hover:bg-brand-500/30 border border-brand-500/40 text-brand-300 hover:text-brand-200 font-semibold transition flex items-center gap-1 cursor-pointer"
            >
              <span>Admin Console</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
