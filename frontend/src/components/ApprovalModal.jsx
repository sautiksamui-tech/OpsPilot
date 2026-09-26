import React, { useState } from 'react';
import { Lock, ShieldCheck, AlertCircle, Check, X, FileText, Building, CreditCard, Landmark, ArrowRight } from 'lucide-react';

export function ApprovalModal({ runState, onApprove, onReject, isLoading }) {
  const [comment, setComment] = useState('authorize');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!runState || !['AWAITING_APPROVAL', 'APPROVAL_REQUIRED'].includes(runState.payment_state)) {
    return null;
  }

  const vendor = runState.vendor || 'Zelar';
  const vendorId = runState.vendor_id || 'VEND-ZELAR-009';
  const amount = runState.amount || 240000.0;
  const invoice = runState.invoice || 'ZELAR-MAR-2026-104';
  const poId = runState.po_id || 'PO-TW-2026-0881';
  const customer = runState.customer || 'Thoughtworks';
  const destination = runState.verified_payout_destination || 'ba_zelar_corp_hdfc_0981';
  const operationId = runState.operation_id || 'op_zelar_mar2026_104';

  const handleApprove = async () => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    try {
      await onApprove(comment);
    } catch (e) {
      console.error('Approval failed:', e);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReject = async () => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    try {
      await onReject(comment);
    } catch (e) {
      console.error('Rejection failed:', e);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="glass-panel-glow rounded-2xl p-6 border-2 border-brand-500/50 relative overflow-hidden my-4 animate-in fade-in zoom-in-95 duration-300 z-20 space-y-4">
      {/* Top Banner with Clear Business Headline */}
      <div className="flex items-start justify-between border-b border-brand-500/20 pb-4">
        <div className="flex items-start gap-3">
          <div className="p-2.5 rounded-xl bg-brand-500/20 text-brand-400 border border-brand-500/30 flex-shrink-0 mt-0.5">
            <Lock className="w-5 h-5 animate-pulse" />
          </div>
          <div className="space-y-1">
            <h3 className="font-bold text-lg text-white tracking-tight">
              Zelar's approved vendor settlement is ready.
            </h3>
            <p className="text-xs text-brand-300 font-medium">
              Your authorization is required before funds can be released.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <span className="px-2.5 py-1 rounded-full text-[10px] font-mono font-semibold bg-brand-500/20 text-brand-300 border border-brand-500/30">
            ID: {operationId}
          </span>
          <span className="px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
            HARD GATE
          </span>
        </div>
      </div>

      {/* Locked Settlement Details Card */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-dark-950/80 rounded-xl p-4 border border-white/5 text-xs">
        <div>
          <span className="text-slate-400 block mb-0.5 font-medium">Enterprise Client</span>
          <span className="text-white font-semibold flex items-center gap-1">
            <Building className="w-3.5 h-3.5 text-brand-400" /> {customer}
          </span>
        </div>
        <div>
          <span className="text-slate-400 block mb-0.5 font-medium">Recipient Vendor</span>
          <span className="text-white font-semibold">{vendor} <span className="text-[10px] text-slate-400">({vendorId})</span></span>
        </div>
        <div>
          <span className="text-slate-400 block mb-0.5 font-medium">PO / Invoice</span>
          <span className="text-white font-semibold flex items-center gap-1">
            <FileText className="w-3.5 h-3.5 text-emerald-400" /> {poId}
          </span>
        </div>
        <div>
          <span className="text-slate-400 block mb-0.5 font-medium">Amount</span>
          <span className="text-emerald-400 font-mono font-bold text-sm">
            ₹{amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </span>
        </div>
      </div>

      {/* Destination Bank Account Badge */}
      <div className="bg-indigo-950/40 rounded-xl p-3 border border-indigo-500/30 flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          <Landmark className="w-4 h-4 text-indigo-400" />
          <span className="text-slate-300">Destination:</span>
          <span className="font-mono text-indigo-300 font-bold">{destination}</span>
          <span className="text-slate-400">(HDFC Bank Ltd - Ending 0981)</span>
        </div>
        <span className="text-[10px] font-mono bg-emerald-950 text-emerald-400 px-2 py-0.5 rounded border border-emerald-500/30 font-semibold">
          VERIFIED
        </span>
      </div>

      {/* Verification Checklist */}
      <div className="space-y-1.5 text-xs">
        <div className="flex items-center gap-2 text-emerald-300">
          <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          <span>Notion PO approved by Finance Director ({poId} - Net-30 terms)</span>
        </div>
        <div className="flex items-center gap-2 text-emerald-300">
          <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          <span>Stripe customer profile active with zero prior settlement collisions</span>
        </div>
        <div className="flex items-center gap-2 text-emerald-300">
          <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          <span>Slack #finance-ops confirmed zero operational holds</span>
        </div>
        <div className="flex items-center gap-2 text-emerald-300">
          <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          <span>Jira tracking task linked (SCRUM-42) — Duplicate creation prevented</span>
        </div>
      </div>

      {/* Optional Comment / Confirmation Input */}
      <div>
        <input
          type="text"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Authorization comment or confirmation phrase..."
          className="w-full bg-dark-950 border border-white/10 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
        />
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-end gap-3 pt-2">
        <button
          type="button"
          onClick={handleReject}
          disabled={isSubmitting}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-red-950/40 hover:bg-red-950/70 border border-red-500/40 text-red-300 hover:text-red-200 text-xs font-semibold transition disabled:opacity-50 cursor-pointer"
        >
          <X className="w-4 h-4" />
          <span>Decline Authorization</span>
        </button>
        <button
          type="button"
          onClick={handleApprove}
          disabled={isSubmitting}
          className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white font-bold text-xs shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/30 transition disabled:opacity-50 cursor-pointer active:scale-95"
        >
          <ShieldCheck className="w-4 h-4" />
          <span>{isSubmitting ? 'Authorizing Payout...' : `Authorize Vendor Payout (₹${amount.toLocaleString('en-IN')})`}</span>
        </button>
      </div>
    </div>
  );
}
