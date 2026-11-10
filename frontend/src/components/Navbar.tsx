import React from 'react';
import { Terminal, BookOpen, Sparkles, Database, History } from 'lucide-react';

interface NavbarProps {
  apiStatus: 'online' | 'connecting' | 'offline';
  logsCount: number;
  showLogs: boolean;
  setShowLogs: (show: boolean) => void;
  basesCount: number;
  onOpenHistory?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  apiStatus,
  logsCount,
  showLogs,
  setShowLogs,
  basesCount,
  onOpenHistory,
}) => {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-white/[0.08] bg-black/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg bg-zinc-900 border border-white/10 flex items-center justify-center text-emerald-400 shadow-sm shadow-emerald-500/10">
            <Sparkles className="w-5 h-5" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-white tracking-tight text-base sm:text-lg">
                Academic<span className="text-zinc-400 font-normal">OmniSearch</span>
              </span>
              <span className="px-1.5 py-0.5 text-[10px] font-medium tracking-wide uppercase rounded bg-white/10 text-zinc-300 border border-white/10">
                v2.0
              </span>
            </div>
            <span className="text-[11px] text-zinc-500 hidden sm:inline">
              Multi-Database Academic Harvester & Cienciometria
            </span>
          </div>
        </div>

        {/* Status & Actions */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Health indicator */}
          <div className="hidden md:flex items-center gap-2 px-2.5 py-1 rounded-full bg-zinc-900/80 border border-white/[0.06] text-xs">
            <span className="relative flex h-2 w-2">
              <span
                className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                  apiStatus === 'online'
                    ? 'bg-emerald-400'
                    : apiStatus === 'connecting'
                    ? 'bg-amber-400'
                    : 'bg-rose-400'
                }`}
              />
              <span
                className={`relative inline-flex rounded-full h-2 w-2 ${
                  apiStatus === 'online'
                    ? 'bg-emerald-500'
                    : apiStatus === 'connecting'
                    ? 'bg-amber-500'
                    : 'bg-rose-500'
                }`}
              />
            </span>
            <span className="text-zinc-400 text-[11px] font-medium">
              {apiStatus === 'online' ? 'API Online' : apiStatus === 'connecting' ? 'Conectando...' : 'Offline'}
            </span>
            <span className="text-zinc-600">|</span>
            <span className="text-zinc-400 text-[11px] flex items-center gap-1">
              <Database className="w-3 h-3 text-zinc-500" /> {basesCount} bases
            </span>
          </div>

          {/* History sessions */}
          {onOpenHistory && (
            <button
              onClick={onOpenHistory}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-zinc-900/60 text-zinc-400 hover:text-white border border-white/[0.08] hover:border-white/15 transition-all flex items-center gap-1.5 cursor-pointer"
              title="Histórico de Buscas Salvas"
            >
              <History className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Histórico</span>
            </button>
          )}

          {/* Logs toggle */}
          <button
            onClick={() => setShowLogs(!showLogs)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all flex items-center gap-1.5 cursor-pointer ${
              showLogs
                ? 'bg-zinc-800 text-white border-white/20'
                : 'bg-zinc-900/60 text-zinc-400 hover:text-white border-white/[0.08] hover:border-white/15'
            }`}
            title="Abrir/Fechar Terminal de Logs"
          >
            <Terminal className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Terminal</span>
            {logsCount > 0 && (
              <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                {logsCount}
              </span>
            )}
          </button>

          {/* Docs link */}
          <a
            href="/docs"
            target="_blank"
            rel="noreferrer"
            className="px-3 py-1.5 rounded-lg text-xs font-medium text-zinc-400 hover:text-white bg-zinc-900/60 hover:bg-zinc-900 border border-white/[0.08] hover:border-white/15 transition-all flex items-center gap-1.5"
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">API Docs</span>
          </a>
        </div>
      </div>
    </header>
  );
};

