import React from 'react';
import { ShieldCheck, UserCheck, Cpu, HardDrive, Key } from 'lucide-react';

export function AuditTrail({ logs = [] }) {
  if (!logs || logs.length === 0) {
    return (
      <div className="glass-panel rounded-2xl p-6 border border-white/10 text-center py-10">
        <ShieldCheck className="w-8 h-8 text-slate-600 mx-auto mb-2.5" />
        <h4 className="text-sm font-semibold text-slate-300">Audit Trail Vault</h4>
        <p className="text-xs text-slate-500 mt-1">
          Cryptographically timestamped audit events will be sealed here.
        </p>
      </div>
    );
  }

  const getActorIcon = (actor) => {
    switch (actor) {
      case 'HUMAN_APPROVER':
        return <UserCheck className="w-3.5 h-3.5 text-brand-400" />;
      case 'AGENT':
        return <Cpu className="w-3.5 h-3.5 text-indigo-400" />;
      default:
        return <HardDrive className="w-3.5 h-3.5 text-emerald-400" />;
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-5 border border-white/10 space-y-3.5">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          Tamper-Evident Audit Trail ({logs.length} entries)
        </h3>
        <span className="text-[11px] text-emerald-400 font-mono bg-emerald-950/50 px-2 py-0.5 rounded border border-emerald-500/20">
          SEALED
        </span>
      </div>

      <div className="space-y-2.5 max-h-[360px] overflow-y-auto pr-1">
        {logs.map((log, idx) => {
          return (
            <div
              key={log.id || idx}
              className="bg-dark-950/80 rounded-xl p-3 border border-white/5 space-y-1.5 text-xs"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="p-1 rounded bg-black/40 border border-white/10">
                    {getActorIcon(log.actor)}
                  </span>
                  <span className="font-bold text-white text-[11px] font-mono">
                    {log.event_type}
                  </span>
                  <span className="px-1.5 py-0.2 rounded text-[10px] bg-white/5 text-slate-400 font-medium">
                    {log.actor}
                  </span>
                </div>
                <span className="text-[10px] font-mono text-slate-500">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </span>
              </div>

              {log.details && (
                <pre className="p-2 rounded-lg bg-black/50 text-[10px] font-mono text-slate-300 overflow-x-auto max-h-28 border border-white/5">
                  {JSON.stringify(log.details, null, 2)}
                </pre>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
