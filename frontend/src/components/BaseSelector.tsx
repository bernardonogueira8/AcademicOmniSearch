import React from 'react';
import type { BaseInfo } from '../types';
import { Check, Key, ShieldCheck } from 'lucide-react';

interface BaseSelectorProps {
  bases: BaseInfo[];
  selectedBases: string[];
  onChange: (selected: string[]) => void;
  disabled?: boolean;
}

export const BaseSelector: React.FC<BaseSelectorProps> = ({
  bases,
  selectedBases,
  onChange,
  disabled = false,
}) => {
  const toggleBase = (id: string) => {
    if (disabled) return;
    if (selectedBases.includes(id)) {
      if (selectedBases.length > 1) {
        onChange(selectedBases.filter((b) => b !== id));
      }
    } else {
      onChange([...selectedBases, id]);
    }
  };

  const selectAll = () => {
    if (disabled) return;
    onChange(bases.map((b) => b.id));
  };

  const selectDefault = () => {
    if (disabled) return;
    onChange(['capes', 'pubmed', 'brapci', 'acm']);
  };

  return (
    <div className="space-y-2.5">
      <div className="flex items-center justify-between text-xs">
        <span className="text-zinc-400 font-medium uppercase tracking-wider text-[11px] flex items-center gap-1.5">
          Fontes & Bases Acadêmicas ({selectedBases.length}/{bases.length})
        </span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={selectAll}
            disabled={disabled}
            className="text-zinc-400 hover:text-white transition-colors cursor-pointer disabled:opacity-50 text-[11px]"
          >
            Todas
          </button>
          <span className="text-zinc-700">•</span>
          <button
            type="button"
            onClick={selectDefault}
            disabled={disabled}
            className="text-zinc-400 hover:text-white transition-colors cursor-pointer disabled:opacity-50 text-[11px]"
          >
            Padrão
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
        {bases.map((base) => {
          const isSelected = selectedBases.includes(base.id);
          const isWarning = base.status === 'requires_key';

          return (
            <div
              key={base.id}
              onClick={() => toggleBase(base.id)}
              className={`group relative p-3 rounded-xl border text-left transition-all duration-150 select-none ${
                disabled ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'
              } ${
                isSelected
                  ? 'bg-zinc-900/90 border-white/20 shadow-sm shadow-white/5 ring-1 ring-white/10'
                  : 'bg-black/60 border-white/[0.06] hover:border-white/15 hover:bg-zinc-950'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <div
                    className={`w-4 h-4 rounded flex items-center justify-center border transition-all ${
                      isSelected
                        ? 'bg-white border-white text-black'
                        : 'border-zinc-700 bg-zinc-900 group-hover:border-zinc-500'
                    }`}
                  >
                    {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                  </div>
                  <span className="text-sm font-semibold text-white tracking-tight">
                    {base.name}
                  </span>
                </div>

                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-medium tracking-wide uppercase border ${
                    isWarning
                      ? 'bg-amber-500/10 text-amber-300 border-amber-500/20'
                      : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                  }`}
                >
                  {base.badge}
                </span>
              </div>

              <p className="text-xs text-zinc-400 mt-1.5 line-clamp-1">
                {base.description}
              </p>

              <div className="mt-2.5 pt-2 border-t border-white/[0.05] flex items-center justify-between text-[11px] text-zinc-500">
                <span className="truncate">{base.category}</span>
                {isWarning ? (
                  <span className="flex items-center gap-1 text-amber-400/90 text-[10px]">
                    <Key className="w-2.5 h-2.5" /> Requer .env
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-emerald-400/80 text-[10px]">
                    <ShieldCheck className="w-2.5 h-2.5" /> Pronto
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
