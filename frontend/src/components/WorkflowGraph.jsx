import React from 'react';
import {
  CheckCircle2,
  Clock,
  AlertTriangle,
  Lock,
  ArrowRight,
  Shield,
  FileText,
  CreditCard,
  MessageSquare,
  CheckSquare,
  Sparkles,
  RefreshCw,
  Landmark,
} from 'lucide-react';

const WORKFLOW_STAGES = [
  { id: 'understand', label: 'Understand Request', icon: Sparkles },
  { id: 'notion', label: 'Notion PO & Bank Check', icon: FileText, provider: 'Notion' },
  { id: 'stripe_investigate', label: 'Stripe Verification', icon: CreditCard, provider: 'Stripe' },
  { id: 'slack', label: 'Slack Finance Comms', icon: MessageSquare, provider: 'Slack' },
  { id: 'jira', label: 'Jira Task Linkage', icon: CheckSquare, provider: 'Jira' },
  { id: 'decision', label: 'Evidence Synthesis & Decision', icon: Shield },
  { id: 'approval', label: 'Human Authorization Gate', icon: Lock },
  { id: 'execution', label: 'Stripe Payout Execution', icon: Landmark, provider: 'Stripe' },
  { id: 'reconciliation', label: 'Multi-System Reconciliation', icon: RefreshCw },
  { id: 'audit', label: 'Knowledge & Audit Record', icon: CheckCircle2 },
];

export function WorkflowGraph({ runState, events = [] }) {
  const getStageStatus = (stageId) => {
    if (!runState) return 'idle';

    const pState = runState.payment_state;
    const currentStatus = runState.status;

    // Check by events present
    const eventTypes = events.map((e) => e.event_type);
    const stepNames = events.map((e) => e.step_name || '');
    const providers = events.map((e) => e.provider || '');

    switch (stageId) {
      case 'understand':
        return eventTypes.includes('run.started') ? 'completed' : 'idle';
      case 'notion':
        return providers.includes('Notion') ? 'completed' : currentStatus === 'INVESTIGATING' ? 'active' : 'idle';
      case 'stripe_investigate':
        return providers.includes('Stripe') && events.some(e => e.step_name && e.step_name.includes('STRIPE_ACCOUNT')) ? 'completed' : 'idle';
      case 'slack':
        return providers.includes('Slack') ? 'completed' : 'idle';
      case 'jira':
        return providers.includes('Jira') ? 'completed' : 'idle';
      case 'decision':
        return eventTypes.includes('decision.created') ? 'completed' : 'idle';
      case 'approval':
        if (['AWAITING_APPROVAL', 'APPROVAL_REQUIRED'].includes(pState) || currentStatus === 'AWAITING_APPROVAL' || currentStatus === 'APPROVAL_REQUIRED') return 'pending_approval';
        if (runState.approval_status === 'APPROVED' || eventTypes.includes('approval.received')) return 'completed';
        if (runState.approval_status === 'REJECTED' || eventTypes.includes('approval.rejected')) return 'rejected';
        if (pState === 'BLOCKED') return 'skipped';
        return 'idle';
      case 'execution':
        if (['PAID', 'SUCCEEDED', 'FAILED', 'UNKNOWN', 'RECONCILING'].includes(pState)) return 'completed';
        if (['EXECUTING', 'PAYOUT_CREATING', 'EXECUTION_LOCKED', 'HUMAN_APPROVED'].includes(currentStatus)) return 'active';
        return 'idle';
      case 'reconciliation':
        if (eventTypes.includes('reconciliation.completed') || eventTypes.includes('exception.detected')) return 'completed';
        if (currentStatus === 'RECONCILING') return 'active';
        return 'idle';
      case 'audit':
        if (eventTypes.includes('run.completed')) return 'completed';
        return 'idle';
      default:
        return 'idle';
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-5 border border-white/10 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
          <Shield className="w-4 h-4 text-brand-400" />
          Autonomous Operator Lifecycle Pipeline — VENDOR_PAYOUT
        </h3>
        <span className="text-[11px] text-slate-400 font-mono">
          Stage {events.length > 0 ? Math.min(10, events.length) : 0} / 10
        </span>
      </div>

      {/* Pipeline Stepper Horizontal */}
      <div className="grid grid-cols-2 md:grid-cols-5 lg:grid-cols-10 gap-2">
        {WORKFLOW_STAGES.map((stage) => {
          const status = getStageStatus(stage.id);
          const Icon = stage.icon;

          let cardStyle = 'bg-dark-950/40 border-white/5 text-slate-500';
          let iconStyle = 'text-slate-600';

          if (status === 'completed') {
            cardStyle = 'bg-emerald-950/30 border-emerald-500/30 text-emerald-300 shadow-sm shadow-emerald-900/10';
            iconStyle = 'text-emerald-400';
          } else if (status === 'active') {
            cardStyle = 'bg-brand-950/40 border-brand-500/50 text-brand-300 ring-1 ring-brand-500/40 animate-pulse';
            iconStyle = 'text-brand-400 animate-spin';
          } else if (status === 'pending_approval') {
            cardStyle = 'bg-purple-950/40 border-purple-500/60 text-purple-200 ring-1 ring-purple-500/50 animate-bounce';
            iconStyle = 'text-purple-300';
          } else if (status === 'rejected') {
            cardStyle = 'bg-red-950/30 border-red-500/30 text-red-300';
            iconStyle = 'text-red-400';
          } else if (status === 'skipped') {
            cardStyle = 'bg-slate-900/40 border-slate-800 text-slate-600 line-through';
            iconStyle = 'text-slate-600';
          }

          return (
            <div
              key={stage.id}
              className={`p-2.5 rounded-xl border flex flex-col items-center justify-center text-center transition-all ${cardStyle}`}
            >
              <div className="mb-1.5 p-1.5 rounded-lg bg-black/30">
                <Icon className={`w-4 h-4 ${iconStyle}`} />
              </div>
              <span className="text-[10px] font-semibold leading-tight line-clamp-2">
                {stage.label}
              </span>
              {stage.provider && (
                <span className="mt-1 text-[9px] font-mono px-1 py-0.2 rounded bg-black/40 text-slate-400">
                  {stage.provider}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
