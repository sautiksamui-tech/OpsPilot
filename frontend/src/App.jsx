import React, { useState } from 'react';
import { Header } from './components/Header';
import { ScenarioBar } from './components/ScenarioBar';
import { WorkflowGraph } from './components/WorkflowGraph';
import { ApprovalModal } from './components/ApprovalModal';
import { ToolTimeline } from './components/ToolTimeline';
import { DecisionLog } from './components/DecisionLog';
import { BusinessDossier } from './components/BusinessDossier';
import { AuditTrail } from './components/AuditTrail';
import { CommandView } from './components/CommandView';
import { useAgentRun } from './hooks/useAgentRun';
import { CheckCircle2, AlertTriangle, ShieldCheck, Sparkles, Zap, Layers, RefreshCw, ArrowLeft, Terminal } from 'lucide-react';

export default function App() {
  const {
    currentRunId,
    runState,
    events,
    auditLogs,
    isLoading,
    error,
    activeScenario,
    setActiveScenario,
    demoMode,
    setDemoMode,
    startRun,
    handleApproval,
  } = useAgentRun();

  const [activeView, setActiveView] = useState('command'); // 'command' | 'admin'

  const handleReset = () => {
    window.location.reload();
  };

  return (
    <div className="min-h-screen bg-dark-950 text-slate-100 flex flex-col font-sans selection:bg-brand-500 selection:text-white">
      {/* 1. Header with View Navigation (Command vs Admin Console) */}
      <Header
        activeView={activeView}
        setActiveView={setActiveView}
        demoMode={demoMode}
        setDemoMode={setDemoMode}
        onReset={handleReset}
        isRunning={isLoading}
      />

      {/* 2. Main View Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        {activeView === 'command' ? (
          /* PRIMARY BUSINESS COMMAND VIEW */
          <CommandView
            runState={runState}
            events={events}
            auditLogs={auditLogs}
            isLoading={isLoading}
            error={error}
            activeScenario={activeScenario}
            setActiveScenario={setActiveScenario}
            demoMode={demoMode}
            onRun={(prompt, scenId) => startRun(prompt, scenId, demoMode)}
            onApprove={(comment) => handleApproval(true, comment)}
            onReject={(comment) => handleApproval(false, comment)}
            onNavigateToAdmin={() => setActiveView('admin')}
          />
        ) : (
          /* ADMIN / OPERATIONS CONSOLE VIEW */
          <div className="space-y-6 animate-in fade-in duration-200">
            {/* Admin Header & Return Shortcut */}
            <div className="flex items-center justify-between bg-dark-900/60 p-4 rounded-2xl border border-white/10">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-brand-500/20 text-brand-400 border border-brand-500/30">
                  <Layers className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-sm font-bold text-white uppercase tracking-wider">
                    Admin & Operations Console
                  </h2>
                  <p className="text-xs text-slate-400">
                    Full multi-system telemetry, LangGraph execution pipeline, evidence dossiers & sealed audit trail
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setActiveView('command')}
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-xs font-semibold text-slate-300 hover:text-white transition cursor-pointer"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Command Center</span>
              </button>
            </div>

            {/* Scenario Bar for Direct Testing */}
            <ScenarioBar
              activeScenario={activeScenario}
              setActiveScenario={setActiveScenario}
              onRun={(prompt, scenarioId) => startRun(prompt, scenarioId, demoMode)}
              isRunning={isLoading}
            />

            {/* Error Alert */}
            {error && (
              <div className="p-4 rounded-xl bg-red-950/50 border border-red-500/40 text-red-200 flex items-center justify-between text-xs animate-in fade-in">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0" />
                  <span>{error}</span>
                </div>
                <button
                  type="button"
                  onClick={() => window.location.reload()}
                  className="underline hover:text-white font-semibold cursor-pointer"
                >
                  Dismiss
                </button>
              </div>
            )}

            {/* Lifecycle Pipeline Stepper */}
            <WorkflowGraph runState={runState} events={events} />

            {/* Interactive Human Authorization Gate */}
            <ApprovalModal
              runState={runState}
              onApprove={(comment) => handleApproval(true, comment)}
              onReject={(comment) => handleApproval(false, comment)}
              isLoading={isLoading}
            />

            {/* Main 2-Column Operational Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Left Column: Tool Timeline & Decision Log (7 cols) */}
              <div className="lg:col-span-7 space-y-6">
                {/* Operator Response Summary */}
                {runState && runState.final_response && (
                  <div className="glass-panel-glow rounded-2xl p-5 border border-emerald-500/40 space-y-2.5 animate-in fade-in zoom-in-95">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Operator Summary
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-500/20 font-bold">
                        COMPLETE
                      </span>
                    </div>
                    <div className="text-xs text-slate-200 whitespace-pre-line leading-relaxed font-sans bg-black/40 p-3.5 rounded-xl border border-white/5">
                      {runState.final_response}
                    </div>
                  </div>
                )}

                {/* What OpsPilot Handled (Business Actions + Swytchcode details) */}
                <ToolTimeline events={events} />

                {/* Live Decision Log */}
                <DecisionLog events={events} />
              </div>

              {/* Right Column: Business Dossier & Cryptographic Audit Trail (5 cols) */}
              <div className="lg:col-span-5 space-y-6">
                {/* Contextual Business Dossier */}
                <BusinessDossier runState={runState} />

                {/* Tamper-Evident Audit Trail */}
                <AuditTrail logs={auditLogs} />
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 py-4 px-6 text-center text-xs text-slate-500 bg-dark-900/40 mt-auto">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>
            OpsPilot — Swytchcode Hackathon Track 6: AI Business Operator Agent
          </span>
          <span className="font-mono text-[11px] text-slate-400">
            FastAPI • LangGraph • React • Swytchcode MCP
          </span>
        </div>
      </footer>
    </div>
  );
}
