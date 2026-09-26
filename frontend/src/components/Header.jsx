import React from 'react';
import { Cpu, ShieldCheck, Zap, RefreshCw, Layers, Terminal, LayoutDashboard } from 'lucide-react';

export function Header({
  activeView = 'command',
  setActiveView,
  demoMode,
  setDemoMode,
  onReset,
  isRunning,
}) {
  return (
    <header className="border-b border-white/10 bg-dark-900/90 backdrop-blur-md sticky top-0 z-40 px-6 py-3">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-brand-500/20 border border-brand-400/30 flex-shrink-0">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-base tracking-tight text-white">OpsPilot</span>
              <span className="px-1.5 py-0.2 rounded text-[10px] font-semibold uppercase tracking-wider bg-brand-500/20 text-brand-300 border border-brand-500/30">
                Track 6: AI Operator
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">
              AI Operator for Vendor Settlements, Exceptions & Multi-System Operations
            </p>
          </div>
        </div>

        {/* View Switcher: Command vs Admin Console */}
        <div className="flex items-center bg-dark-950 p-1 rounded-xl border border-white/10 text-xs">
          <button
            type="button"
            onClick={() => setActiveView('command')}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg font-semibold transition-all cursor-pointer ${
              activeView === 'command'
                ? 'bg-brand-500 text-white shadow-sm shadow-brand-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Terminal className="w-3.5 h-3.5" />
            <span>Command</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveView('admin')}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg font-semibold transition-all cursor-pointer ${
              activeView === 'admin'
                ? 'bg-brand-500 text-white shadow-sm shadow-brand-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <LayoutDashboard className="w-3.5 h-3.5" />
            <span>Admin Console</span>
          </button>
        </div>

        {/* Status Badges & Mode Controls */}
        <div className="flex items-center gap-3">
          {/* Swytchcode MCP Status */}
          <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 text-xs">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="font-medium">Swytchcode MCP:</span>
            <span className="text-slate-300 font-mono text-[11px]">5 Providers / 19 Tools</span>
          </div>

          {/* Mode Toggle */}
          <div className="flex items-center bg-dark-950 p-1 rounded-lg border border-white/10 text-xs">
            <button
              type="button"
              onClick={() => setDemoMode(true)}
              className={`px-2.5 py-1 rounded-md font-medium transition-all cursor-pointer ${
                demoMode
                  ? 'bg-brand-500 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Demo Simulation
            </button>
            <button
              type="button"
              onClick={() => setDemoMode(false)}
              className={`px-2.5 py-1 rounded-md font-medium transition-all cursor-pointer ${
                !demoMode
                  ? 'bg-brand-500 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Live Swytchcode
            </button>
          </div>

          {/* Reset Action */}
          <button
            type="button"
            onClick={onReset}
            disabled={isRunning}
            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 hover:text-white transition disabled:opacity-40 cursor-pointer"
            title="Reset Operator State"
          >
            <RefreshCw className={`w-4 h-4 ${isRunning ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>
    </header>
  );
}
