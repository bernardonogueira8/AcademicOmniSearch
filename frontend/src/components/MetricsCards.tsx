import React from 'react';
import type { SearchMetrics } from '../types';
import { FileText, Layers, Calendar, Award } from 'lucide-react';

interface MetricsCardsProps {
  metrics: SearchMetrics;
  rawCount: number;
  deduplicatedCount: number;
}

export const MetricsCards: React.FC<MetricsCardsProps> = ({
  metrics,
  rawCount,
  deduplicatedCount,
}) => {
  if (deduplicatedCount === 0) return null;

  const dedupDiff = rawCount - deduplicatedCount;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
      {/* 1. Total Encontrado */}
      <div className="resend-card p-4 flex flex-col justify-between">
        <div className="flex items-center justify-between text-zinc-400 text-xs">
          <span>Artigos Únicos</span>
          <FileText className="w-4 h-4 text-emerald-400" />
        </div>
        <div className="mt-2 flex items-baseline gap-2">
          <span className="text-2xl font-bold tracking-tight text-white font-mono">
            {deduplicatedCount}
          </span>
          {dedupDiff > 0 && (
            <span className="text-[11px] text-zinc-500 font-mono">
              ({dedupDiff} duplicatas removidas)
            </span>
          )}
        </div>
        <div className="mt-2 text-[11px] text-zinc-500 truncate">
          Total bruto recuperado: {rawCount}
        </div>
      </div>

      {/* 2. Bases com Dados */}
      <div className="resend-card p-4 flex flex-col justify-between">
        <div className="flex items-center justify-between text-zinc-400 text-xs">
          <span>Bases com Retorno</span>
          <Layers className="w-4 h-4 text-blue-400" />
        </div>
        <div className="mt-2 flex items-baseline gap-2">
          <span className="text-2xl font-bold tracking-tight text-white font-mono">
            {Object.keys(metrics.bases_count || {}).length}
          </span>
          <span className="text-[11px] text-zinc-500">fontes distintas</span>
        </div>
        <div className="mt-2 flex flex-wrap gap-1.5 overflow-hidden">
          {Object.entries(metrics.bases_count || {}).map(([base, count]) => (
            <span
              key={base}
              className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 border border-white/10 text-zinc-300 font-mono"
            >
              {base}: {count}
            </span>
          ))}
        </div>
      </div>

      {/* 3. Recorte Temporal */}
      <div className="resend-card p-4 flex flex-col justify-between">
        <div className="flex items-center justify-between text-zinc-400 text-xs">
          <span>Janela Temporal</span>
          <Calendar className="w-4 h-4 text-amber-400" />
        </div>
        <div className="mt-2 flex items-baseline gap-2">
          <span className="text-2xl font-bold tracking-tight text-white font-mono">
            {metrics.years_range || 'N/D'}
          </span>
        </div>
        <div className="mt-2 text-[11px] text-zinc-500">
          Anos identificados nos metadados
        </div>
      </div>

      {/* 4. Top Periódico */}
      <div className="resend-card p-4 flex flex-col justify-between">
        <div className="flex items-center justify-between text-zinc-400 text-xs">
          <span>Principal Veículo</span>
          <Award className="w-4 h-4 text-purple-400" />
        </div>
        <div className="mt-2">
          {metrics.top_journals && Object.keys(metrics.top_journals).length > 0 ? (
            <div>
              <div className="text-sm font-semibold text-white truncate" title={Object.keys(metrics.top_journals)[0]}>
                {Object.keys(metrics.top_journals)[0]}
              </div>
              <div className="text-[11px] text-zinc-500 font-mono mt-1">
                {Object.values(metrics.top_journals)[0]} publicações indexadas
              </div>
            </div>
          ) : (
            <span className="text-xs text-zinc-500">Diversos veículos</span>
          )}
        </div>
      </div>
    </div>
  );
};
