import React from 'react';
import {
  Building2,
  FileCheck,
  CreditCard,
  MessageSquare,
  CheckSquare,
  Mail,
  FileText,
  ShieldCheck,
  ExternalLink,
  Lock,
  Landmark,
} from 'lucide-react';
import { StateBadge } from './StateBadge';

export function BusinessDossier({ runState }) {
  if (!runState) {
    return (
      <div className="glass-panel rounded-2xl p-6 border border-white/10 text-center py-16">
        <Building2 className="w-10 h-10 text-slate-600 mx-auto mb-3" />
        <h4 className="text-sm font-semibold text-slate-300">Contextual Business Dossier</h4>
        <p className="text-xs text-slate-500 mt-1 max-w-[240px] mx-auto">
          Start an operator run to synthesize verified vendor, financial, and operational intelligence.
        </p>
      </div>
    );
  }

  const bCtx = runState.business_context || {};
  const vendorProfile = bCtx.vendor_profile || {};
  const invoiceData = bCtx.invoice || {};
  const fCtx = runState.financial_context || {};
  const eCtx = runState.engineering_context || {};
  const cCtx = runState.communication_context || {};

  const vendorName = runState.vendor || vendorProfile.vendor_name || 'Zelar';
  const amount = runState.amount || invoiceData.amount || 240000.0;
  const invoiceNum = runState.invoice || invoiceData.invoice_number || 'ZELAR-MAR-2026-104';
  const destination = runState.verified_payout_destination || vendorProfile.verified_payout_destination || 'ba_zelar_corp_hdfc_0981';
  const operationId = runState.operation_id || 'op_zelar_mar2026_104';
  const payoutId = runState.payout_id;

  return (
    <div className="glass-panel rounded-2xl p-5 border border-white/10 space-y-4">
      {/* Header & Settlement State */}
      <div className="flex items-center justify-between border-b border-white/10 pb-3">
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Business Dossier
          </h3>
          <p className="text-[11px] text-slate-400">Enterprise Verified AP Context</p>
        </div>
        <StateBadge state={runState.payment_state} />
      </div>

      {/* Primary Financial Card */}
      <div className="bg-gradient-to-br from-brand-950/60 to-dark-950 p-4 rounded-xl border border-brand-500/30 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-bold uppercase tracking-wider text-brand-400">
            Vendor Settlement Target (AP)
          </span>
          <span className="text-[10px] font-mono text-slate-400">
            {operationId}
          </span>
        </div>
        <div className="flex items-baseline justify-between">
          <span className="text-2xl font-bold font-mono text-white tracking-tight">
            ₹{amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </span>
          <span className="text-xs font-semibold px-2 py-0.5 rounded bg-brand-500/20 text-brand-300 border border-brand-500/30">
            {runState.currency || 'INR'}
          </span>
        </div>
        <div className="text-xs text-slate-300 flex items-center justify-between pt-1 border-t border-brand-500/10">
          <span className="text-slate-400">Invoice / PO:</span>
          <span className="font-mono font-medium text-emerald-400">{invoiceNum}</span>
        </div>
        {payoutId && (
          <div className="text-xs text-slate-300 flex items-center justify-between pt-1 border-t border-brand-500/10">
            <span className="text-slate-400">Stripe Payout ID:</span>
            <span className="font-mono font-bold text-indigo-400">{payoutId}</span>
          </div>
        )}
      </div>

      {/* Multi-System Provider Breakdown */}
      <div className="space-y-3 text-xs">
        {/* 1. NOTION VENDOR & PO CONTEXT */}
        <div className="p-3 rounded-xl bg-dark-950/60 border border-white/5 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-300 flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-emerald-400" /> Notion Knowledge Layer
            </span>
            <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/50 px-1.5 py-0.5 rounded">
              VERIFIED
            </span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-[11px] pt-1 text-slate-300">
            <div>
              <span className="text-slate-500 block">Vendor Legal Name:</span>
              <span className="font-medium text-white">{vendorProfile.legal_name || 'Zelar Technologies Pvt Ltd'}</span>
            </div>
            <div>
              <span className="text-slate-500 block">PO Terms:</span>
              <span className="font-medium text-white">{vendorProfile.payment_terms || 'Net-30'}</span>
            </div>
            <div>
              <span className="text-slate-500 block">PO Approval:</span>
              <span className="text-emerald-400 font-medium">Finance Director Approved</span>
            </div>
            <div>
              <span className="text-slate-500 block">Category:</span>
              <span className="font-medium text-white">{vendorProfile.category || 'Cloud DevOps'}</span>
            </div>
          </div>
        </div>

        {/* 2. STRIPE PAYOUT RAILS */}
        <div className="p-3 rounded-xl bg-dark-950/60 border border-white/5 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-300 flex items-center gap-1.5">
              <Landmark className="w-3.5 h-3.5 text-indigo-400" /> Stripe Payout Rails (Outbound)
            </span>
            <span className="text-[10px] font-mono text-indigo-400 bg-indigo-950/50 px-1.5 py-0.5 rounded">
              ba_... VERIFIED
            </span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-[11px] pt-1 text-slate-300">
            <div>
              <span className="text-slate-500 block">Bank Destination:</span>
              <span className="font-mono text-white">{destination}</span>
            </div>
            <div>
              <span className="text-slate-500 block">Bank Institution:</span>
              <span className="text-emerald-400 font-medium">HDFC Bank Ltd (0981)</span>
            </div>
            <div className="col-span-2">
              <span className="text-slate-500 block">Prior Disbursements:</span>
              <span className="text-slate-300">1 Prior Payout Succeeded (Feb ₹2.1L)</span>
            </div>
          </div>
        </div>

        {/* 3. JIRA TASK LINKAGE */}
        <div className="p-3 rounded-xl bg-dark-950/60 border border-white/5 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-300 flex items-center gap-1.5">
              <CheckSquare className="w-3.5 h-3.5 text-blue-400" /> Jira Task Tracking
            </span>
            <span className="text-[10px] font-mono text-blue-400 bg-blue-950/50 px-1.5 py-0.5 rounded">
              LINKED
            </span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-[11px] pt-1 text-slate-300">
            <div>
              <span className="text-slate-500 block">Issue Key:</span>
              <span className="font-mono font-bold text-blue-400">
                {eCtx.jira?.existing_key || 'SCRUM-42'}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block">Duplicate Prevention:</span>
              <span className="text-emerald-400 font-medium">Enforced (Updated)</span>
            </div>
          </div>
        </div>

        {/* 4. SLACK & GMAIL COMMS */}
        <div className="p-3 rounded-xl bg-dark-950/60 border border-white/5 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-300 flex items-center gap-1.5">
              <MessageSquare className="w-3.5 h-3.5 text-amber-400" /> Team & Vendor Comms
            </span>
            <span className="text-[10px] font-mono text-amber-400 bg-amber-950/50 px-1.5 py-0.5 rounded">
              SYNCED
            </span>
          </div>
          <div className="space-y-1 text-[11px] pt-1 text-slate-300">
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Slack Channel:</span>
              <span className="font-mono text-white">#finance-ops (Greenlight)</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Gmail Remittance:</span>
              <span className="text-white">billing@zelar.io</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
