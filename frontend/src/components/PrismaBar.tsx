import React from 'react';
import type { PrismaStats } from '../types';
import { CheckCircle2, XCircle, HelpCircle, Clock, ShieldCheck, Filter } from 'lucide-react';

interface PrismaBarProps {
  stats: PrismaStats;
  currentFilter: 'ALL' | 'pendente' | 'incluido' | 'excluido' | 'duvida';
  onFilterChange: (status: 'ALL' | 'pendente' | 'incluido' | 'excluido' | 'duvida') => void;
}

export const PrismaBar: React.FC<PrismaBarProps> = ({
  stats,
  currentFilter,
  onFilterChange,
}) => {
  return (
    <div className="resend-card p-4 space-y-3 bg-gradient-to-r from-zinc-950 via-zinc-900/60 to-zinc-950 border-white/10">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/[0.06] pb-2.5">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-semibold text-white uppercase tracking-wider">
            Fluxo de Triagem Sistemática (Diretrizes PRISMA)
          </span>
        </div>

        {/* Filter buttons */}
        <div className="flex items-center gap-1.5 flex-wrap text-xs">
          <div className="flex items-center gap-1 text-zinc-500 mr-1 text-[11px]">
            <Filter className="w-3 h-3" />
            <span>Filtro:</span>
          </div>

          <button
            onClick={() => onFilterChange('ALL')}
            className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors cursor-pointer ${
              currentFilter === 'ALL'
                ? 'bg-white text-black font-semibold'
                : 'bg-zinc-900 text-zinc-400 hover:text-white border border-white/10'
            }`}
          >
            Todos ({stats.records_screened + stats.records_pending})
          </button>

          <button
            onClick={() => onFilterChange('pendente')}
            className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors cursor-pointer flex items-center gap-1 ${
              currentFilter === 'pendente'
                ? 'bg-zinc-200 text-black font-semibold'
                : 'bg-zinc-900 text-zinc-400 hover:text-white border border-white/10'
            }`}
          >
            <Clock className="w-2.5 h-2.5" />
            Pendentes ({stats.records_pending})
          </button>

          <button
            onClick={() => onFilterChange('incluido')}
            className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors cursor-pointer flex items-center gap-1 ${
              currentFilter === 'incluido'
                ? 'bg-emerald-500 text-black font-semibold'
                : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
            }`}
          >
            <CheckCircle2 className="w-2.5 h-2.5" />
            Incluídos ({stats.records_included})
          </button>

          <button
            onClick={() => onFilterChange('excluido')}
            className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors cursor-pointer flex items-center gap-1 ${
              currentFilter === 'excluido'
                ? 'bg-rose-500 text-white font-semibold'
                : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
            }`}
          >
            <XCircle className="w-2.5 h-2.5" />
            Excluídos ({stats.records_excluded})
          </button>

          <button
            onClick={() => onFilterChange('duvida')}
            className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors cursor-pointer flex items-center gap-1 ${
              currentFilter === 'duvida'
                ? 'bg-amber-500 text-black font-semibold'
                : 'bg-amber-500/10 text-amber-300 border border-amber-500/20'
            }`}
          >
            <HelpCircle className="w-2.5 h-2.5" />
            Dúvidas ({stats.records_uncertain})
          </button>
        </div>
      </div>

      {/* PRISMA Visual Stages */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
        {/* Stage 1: Identification */}
        <div className="p-2.5 rounded-lg bg-black/40 border border-white/[0.06]">
          <span className="text-[10px] text-zinc-400 uppercase tracking-wider block">
            1. Identificados
          </span>
          <span className="text-lg font-bold font-mono text-white">
            {stats.records_identified}
          </span>
          <span className="text-[10px] text-zinc-500 block truncate">
            {stats.duplicates_removed} duplicatas
          </span>
        </div>

        {/* Stage 2: Screened */}
        <div className="p-2.5 rounded-lg bg-black/40 border border-white/[0.06]">
          <span className="text-[10px] text-zinc-400 uppercase tracking-wider block">
            2. Triados
          </span>
          <span className="text-lg font-bold font-mono text-cyan-400">
            {stats.records_screened}
          </span>
          <span className="text-[10px] text-zinc-500 block truncate">
            {stats.records_pending} pendentes
          </span>
        </div>

        {/* Stage 3: Included */}
        <div className="p-2.5 rounded-lg bg-emerald-950/20 border border-emerald-500/20">
          <span className="text-[10px] text-emerald-400 uppercase tracking-wider block font-medium">
            3. Incluídos
          </span>
          <span className="text-lg font-bold font-mono text-emerald-400">
            {stats.records_included}
          </span>
          <span className="text-[10px] text-emerald-500/70 block truncate">
            Para síntese
          </span>
        </div>

        {/* Stage 4: Excluded */}
        <div className="p-2.5 rounded-lg bg-rose-950/20 border border-rose-500/20">
          <span className="text-[10px] text-rose-400 uppercase tracking-wider block font-medium">
            4. Excluídos
          </span>
          <span className="text-lg font-bold font-mono text-rose-400">
            {stats.records_excluded}
          </span>
          <span className="text-[10px] text-rose-500/70 block truncate">
            Fora do escopo
          </span>
        </div>
      </div>
    </div>
  );
};
