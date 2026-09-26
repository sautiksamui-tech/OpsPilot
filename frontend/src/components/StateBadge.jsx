import React from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  Clock,
  ShieldAlert,
  XCircle,
  HelpCircle,
  Loader2,
  Lock,
  Layers,
  Send,
  Building,
} from 'lucide-react';

export function StateBadge({ state }) {
  const configs = {
    REQUESTED: {
      label: 'REQUESTED',
      color: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
      icon: Clock,
      pulse: false,
    },
    CONTEXT_VERIFIED: {
      label: 'CONTEXT VERIFIED',
      color: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30',
      icon: Layers,
      pulse: false,
    },
    APPROVAL_REQUIRED: {
      label: 'APPROVAL REQUIRED',
      color: 'bg-purple-500/20 text-purple-300 border-purple-500/40 shadow-sm shadow-purple-500/20',
      icon: Lock,
      pulse: true,
    },
    AWAITING_APPROVAL: {
      label: 'APPROVAL REQUIRED',
      color: 'bg-purple-500/20 text-purple-300 border-purple-500/40 shadow-sm shadow-purple-500/20',
      icon: Lock,
      pulse: true,
    },
    HUMAN_APPROVED: {
      label: 'HUMAN APPROVED',
      color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
      icon: CheckCircle2,
      pulse: false,
    },
    EXECUTION_LOCKED: {
      label: 'EXECUTION LOCKED',
      color: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/40',
      icon: Lock,
      pulse: false,
    },
    PAYOUT_CREATING: {
      label: 'PAYOUT CREATING',
      color: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
      icon: Loader2,
      pulse: true,
    },
    PAYOUT_CREATED: {
      label: 'PAYOUT CREATED',
      color: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
      icon: Send,
      pulse: false,
    },
    RECONCILING: {
      label: 'RECONCILING',
      color: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40',
      icon: Loader2,
      pulse: true,
    },
    PAID: {
      label: 'PAYOUT PAID',
      color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 shadow-sm shadow-emerald-500/20',
      icon: CheckCircle2,
      pulse: false,
    },
    SUCCEEDED: {
      label: 'PAYOUT PAID',
      color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 shadow-sm shadow-emerald-500/20',
      icon: CheckCircle2,
      pulse: false,
    },
    FAILED: {
      label: 'PAYOUT FAILED',
      color: 'bg-red-500/20 text-red-300 border-red-500/40',
      icon: XCircle,
      pulse: false,
    },
    UNKNOWN: {
      label: 'GATEWAY TIMEOUT (UNKNOWN)',
      color: 'bg-amber-500/20 text-amber-300 border-amber-500/40 animate-pulse',
      icon: HelpCircle,
      pulse: true,
    },
    BLOCKED: {
      label: 'COMPLIANCE BLOCKED',
      color: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
      icon: ShieldAlert,
      pulse: false,
    },
    CANCELLED: {
      label: 'CANCELLED BY APPROVER',
      color: 'bg-slate-500/20 text-slate-300 border-slate-500/40',
      icon: XCircle,
      pulse: false,
    },
  };

  const config = configs[state] || {
    label: state || 'UNKNOWN',
    color: 'bg-slate-800 text-slate-400 border-slate-700',
    icon: Clock,
    pulse: false,
  };

  const Icon = config.icon;

  return (
    <div
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold uppercase tracking-wider border ${config.color}`}
    >
      <Icon className={`w-3.5 h-3.5 ${config.pulse ? 'animate-spin' : ''}`} />
      <span>{config.label}</span>
    </div>
  );
}
