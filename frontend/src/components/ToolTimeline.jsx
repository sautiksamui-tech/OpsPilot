import React, { useState } from 'react';
import {
  Code,
  ChevronDown,
  ChevronUp,
  Clock,
  CheckCircle2,
  AlertCircle,
  Layers,
  Sparkles,
  ExternalLink,
  ShieldCheck,
  Check,
} from 'lucide-react';

const PROVIDER_COLORS = {
  Notion: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
  Stripe: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30',
  Jira: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  Slack: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
  Gmail: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
};

const STANDARD_BUSINESS_ACTIONS = [
  { id: 'notion', label: 'Verified approved invoice', provider: 'Notion', icon: 'Check' },
  { id: 'vendor', label: 'Verified vendor profile & bank rails', provider: 'Stripe', icon: 'Check' },
  { id: 'history', label: 'Checked prior settlement activity (zero collisions)', provider: 'Stripe', icon: 'Check' },
  { id: 'approval_internal', label: 'Confirmed internal approval (#finance-ops)', provider: 'Slack', icon: 'Check' },
  { id: 'gate', label: 'Secured human authorization', provider: 'OpsPilot', icon: 'Check' },
  { id: 'payout', label: 'Executed vendor payout (stripe.payout.create)', provider: 'Stripe', icon: 'Check' },
  { id: 'jira', label: 'Updated Jira tracking ticket (SCRUM-42)', provider: 'Jira', icon: 'Check' },
  { id: 'slack_notify', label: 'Notified finance operations team', provider: 'Slack', icon: 'Check' },
  { id: 'gmail_draft', label: 'Prepared vendor remittance notification', provider: 'Gmail', icon: 'Check' },
];

export function ToolTimeline({ events = [] }) {
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);
  const [expandedEvents, setExpandedEvents] = useState({});

  const toggleExpand = (eventId) => {
    setExpandedEvents((prev) => ({ ...prev, [eventId]: !prev[eventId] }));
  };

  const toolEvents = events.filter(
    (e) =>
      e.canonical_tool_id ||
      e.provider ||
      ['tool.completed', 'action.completed', 'evidence.added'].includes(e.event_type)
  );

  if (toolEvents.length === 0) {
    return (
      <div className="glass-panel rounded-2xl p-6 border border-white/10 text-center py-8">
        <Layers className="w-7 h-7 text-slate-600 mx-auto mb-2" />
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">WHAT OPSPIOLOT HANDLED</h4>
        <p className="text-xs text-slate-500 mt-1">
          Business actions and Swytchcode tool executions will appear here in real time.
        </p>
      </div>
    );
  }

  return (
    <div className="glass-panel rounded-2xl p-5 border border-white/10 space-y-4">
      {/* 1. Primary Header: WHAT OPSPIOLOT HANDLED */}
      <div className="flex items-center justify-between border-b border-white/10 pb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-brand-500/20 text-brand-400">
            <CheckCircle2 className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-white">
              WHAT OPSPIOLOT HANDLED
            </h3>
            <p className="text-[11px] text-slate-400">
              Verified business outcomes across 5 enterprise platforms
            </p>
          </div>
        </div>
        <span className="text-[11px] font-mono px-2.5 py-0.5 rounded-full bg-emerald-950/60 text-emerald-300 border border-emerald-500/20 font-semibold">
          {toolEvents.length} Actions Completed
        </span>
      </div>

      {/* 2. Business-Level Actions Checklist */}
      <div className="space-y-2">
        {toolEvents.map((ev, idx) => {
          const provider = ev.provider || 'Swytchcode';
          const badgeColor = PROVIDER_COLORS[provider] || 'bg-slate-800 text-slate-300 border-slate-700';

          return (
            <div
              key={ev.event_id || idx}
              className="flex items-start justify-between p-2.5 rounded-xl bg-dark-950/60 border border-white/5 text-xs text-slate-200"
            >
              <div className="flex items-start gap-2.5">
                <Check className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-white block">
                    {ev.output_summary || ev.input_summary || ev.step_name}
                  </span>
                  {ev.decision_effect && (
                    <span className="text-[11px] text-brand-300 italic block mt-0.5">
                      ↳ {ev.decision_effect}
                    </span>
                  )}
                </div>
              </div>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border flex-shrink-0 ml-2 ${badgeColor}`}>
                {provider}
              </span>
            </div>
          );
        })}
      </div>

      {/* 3. Secondary Expandable Control: View Swytchcode execution details */}
      <div className="pt-2 border-t border-white/5">
        <button
          type="button"
          onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
          className="w-full flex items-center justify-between p-2.5 rounded-xl bg-dark-900/80 hover:bg-dark-900 border border-white/10 text-xs font-semibold text-slate-300 hover:text-white transition cursor-pointer"
        >
          <div className="flex items-center gap-2">
            <Code className="w-3.5 h-3.5 text-brand-400" />
            <span>View Swytchcode execution details ({toolEvents.length} Canonical Tools)</span>
          </div>
          {showTechnicalDetails ? (
            <ChevronUp className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          )}
        </button>

        {/* 4. Full Swytchcode Technical Provenance */}
        {showTechnicalDetails && (
          <div className="mt-3 space-y-2.5 max-h-[420px] overflow-y-auto pr-1 animate-in fade-in duration-200">
            {toolEvents.map((ev, index) => {
              const provider = ev.provider || 'Swytchcode';
              const badgeColor = PROVIDER_COLORS[provider] || 'bg-slate-800 text-slate-300 border-slate-700';
              const isExpanded = expandedEvents[ev.event_id];

              return (
                <div
                  key={ev.event_id || index}
                  className="bg-dark-950/90 rounded-xl border border-white/5 p-3 text-xs"
                >
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase border ${badgeColor}`}>
                        {provider}
                      </span>
                      <span className="font-mono text-[11px] text-brand-300 font-semibold bg-brand-950/50 px-2 py-0.5 rounded border border-brand-500/20">
                        {ev.canonical_tool_id || ev.step_name}
                      </span>
                      {ev.duration_ms !== undefined && ev.duration_ms !== null && (
                        <span className="text-[10px] text-slate-400 flex items-center gap-0.5 font-mono">
                          <Clock className="w-3 h-3 text-slate-500" />
                          {ev.duration_ms}ms
                        </span>
                      )}
                    </div>

                    <button
                      type="button"
                      onClick={() => toggleExpand(ev.event_id)}
                      className="p-1 rounded hover:bg-white/5 text-slate-400 hover:text-slate-200 transition cursor-pointer"
                      title="Toggle Raw JSON Payload"
                    >
                      {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    </button>
                  </div>

                  <p className="text-slate-200 text-xs mb-1.5 font-medium leading-relaxed">
                    {ev.output_summary || ev.input_summary}
                  </p>

                  {/* Expandable JSON Payload */}
                  {isExpanded && ev.payload && (
                    <div className="mt-2.5 pt-2.5 border-t border-white/5 animate-in fade-in duration-200">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[10px] font-mono text-slate-400 uppercase">
                          Raw Swytchcode Schema Payload
                        </span>
                      </div>
                      <pre className="p-2.5 rounded-lg bg-black/80 text-[10px] font-mono text-emerald-300 overflow-x-auto max-h-44 border border-white/5">
                        {JSON.stringify(ev.payload, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
