import React from 'react';
import { Activity, Clock, ShieldAlert, Sparkles, CheckCircle2, ArrowRight } from 'lucide-react';

export function DecisionLog({ events = [] }) {
  const formatTime = (isoString) => {
    if (!isoString) return '';
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return '';
    }
  };

  const stepEvents = events.filter((e) =>
    [
      'run.started',
      'agent.step',
      'tool.completed',
      'decision.created',
      'approval.required',
      'approval.received',
      'approval.rejected',
      'action.completed',
      'verification.started',
      'exception.detected',
      'reconciliation.completed',
      'run.completed',
    ].includes(e.event_type)
  );

  return (
    <div className="glass-panel rounded-2xl p-5 border border-white/10 space-y-3.5">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
          <Activity className="w-4 h-4 text-brand-400" />
          Live Agentic Decision Timeline
        </h3>
        <span className="text-[11px] text-slate-400 font-mono">
          Dynamic Reasoning
        </span>
      </div>

      <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1">
        {stepEvents.map((ev, idx) => {
          const isLatest = idx === stepEvents.length - 1;
          const time = formatTime(ev.timestamp);

          let badgeStyle = 'bg-slate-800 text-slate-300 border-slate-700';
          let label = ev.step_name || ev.event_type.toUpperCase();

          if (ev.event_type === 'decision.created') {
            badgeStyle = 'bg-brand-500/20 text-brand-300 border-brand-500/40 font-bold';
            label = 'DECISION';
          } else if (ev.event_type === 'approval.required') {
            badgeStyle = 'bg-purple-500/20 text-purple-300 border-purple-500/40 font-bold';
            label = 'APPROVAL GATE';
          } else if (ev.event_type === 'exception.detected') {
            badgeStyle = 'bg-red-500/20 text-red-300 border-red-500/40 font-bold';
            label = 'EXCEPTION ENGINE';
          } else if (ev.event_type === 'reconciliation.completed') {
            badgeStyle = 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 font-bold';
            label = 'RECONCILIATION';
          }

          return (
            <div key={ev.event_id || idx} className="flex items-start gap-3 text-xs">
              <span className="text-[10px] font-mono text-slate-500 w-16 pt-0.5 flex-shrink-0">
                {time}
              </span>

              <div className="relative pl-3 border-l-2 border-white/10 flex-1 pb-1">
                <span className={`absolute -left-[5px] top-1.5 w-2 h-2 rounded-full ${isLatest ? 'bg-brand-400 ring-4 ring-brand-400/20 animate-ping' : 'bg-slate-600'}`} />

                <div className="flex items-center gap-2 mb-1">
                  <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-mono tracking-wider border ${badgeStyle}`}>
                    {label}
                  </span>
                  {ev.provider && (
                    <span className="text-[10px] text-slate-400 font-medium">
                      via {ev.provider}
                    </span>
                  )}
                </div>

                <p className="text-slate-200 text-xs font-medium leading-relaxed">
                  "{ev.output_summary || ev.input_summary}"
                </p>

                {ev.decision_effect && (
                  <p className="text-[11px] text-slate-400 mt-1 italic">
                    ↳ {ev.decision_effect}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
