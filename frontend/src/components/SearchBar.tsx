import React from 'react';
import { Search, Loader2, SlidersHorizontal, Calendar, Hash, X } from 'lucide-react';

interface SearchBarProps {
  query: string;
  setQuery: (q: string) => void;
  yearStart: number;
  setYearStart: (y: number) => void;
  yearEnd: number;
  setYearEnd: (y: number) => void;
  field: string;
  setField: (f: string) => void;
  maxPerBase: number;
  setMaxPerBase: (m: number) => void;
  onSearch: () => void;
  isSearching: boolean;
  onCancel?: () => void;
}

const SEARCH_FIELDS = [
  { value: 'Todos', label: 'Todos os Campos' },
  { value: 'Título', label: 'Título' },
  { value: 'Resumo', label: 'Resumo (Abstract)' },
  { value: 'Palavras-Chave', label: 'Palavras-Chave' },
  { value: 'Autores', label: 'Autores' },
  { value: 'Texto Completo', label: 'Texto Completo' },
];

export const SearchBar: React.FC<SearchBarProps> = ({
  query,
  setQuery,
  yearStart,
  setYearStart,
  yearEnd,
  setYearEnd,
  field,
  setField,
  maxPerBase,
  setMaxPerBase,
  onSearch,
  isSearching,
  onCancel,
}) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isSearching) {
      onSearch();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="resend-card p-4 sm:p-5 space-y-4">
      {/* Search Input Hero Row */}
      <div className="relative flex items-center">
        <div className="absolute left-4 text-zinc-500 pointer-events-none">
          <Search className="w-5 h-5" />
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Digite palavras-chave, título, autores ou DOI (ex: machine learning saúde)..."
          className="w-full bg-black/60 border border-white/10 rounded-xl pl-12 pr-28 py-3.5 text-white placeholder-zinc-500 text-sm sm:text-base focus:outline-none focus:border-white/30 focus:ring-2 focus:ring-white/5 transition-all"
          disabled={isSearching}
        />
        {query && !isSearching && (
          <button
            type="button"
            onClick={() => setQuery('')}
            className="absolute right-28 mr-2 text-zinc-500 hover:text-white p-1 rounded-md transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        )}
        <div className="absolute right-2 flex items-center gap-1.5">
          {isSearching ? (
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20 hover:bg-rose-500/20 text-xs font-medium flex items-center gap-1.5 transition-all"
            >
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              Cancelar
            </button>
          ) : (
            <button
              type="submit"
              disabled={!query.trim()}
              className="resend-btn-primary py-2.5 px-5 text-sm"
            >
              <span>Buscar</span>
              <kbd className="hidden sm:inline px-1.5 py-0.5 text-[10px] bg-black/10 rounded text-black font-mono">
                ↵
              </kbd>
            </button>
          )}
        </div>
      </div>

      {/* Advanced Filters Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 pt-1 border-t border-white/[0.05]">
        {/* Search Field Qualifier */}
        <div>
          <label className="block text-[11px] font-medium text-zinc-400 mb-1 flex items-center gap-1">
            <SlidersHorizontal className="w-3 h-3 text-zinc-500" /> Campo de Busca
          </label>
          <select
            value={field}
            onChange={(e) => setField(e.target.value)}
            disabled={isSearching}
            className="w-full resend-input text-xs py-2 bg-zinc-950"
          >
            {SEARCH_FIELDS.map((f) => (
              <option key={f.value} value={f.value} className="bg-zinc-900 text-white">
                {f.label}
              </option>
            ))}
          </select>
        </div>

        {/* Year Start */}
        <div>
          <label className="block text-[11px] font-medium text-zinc-400 mb-1 flex items-center gap-1">
            <Calendar className="w-3 h-3 text-zinc-500" /> Ano Inicial
          </label>
          <input
            type="number"
            min={1950}
            max={2030}
            value={yearStart}
            onChange={(e) => setYearStart(parseInt(e.target.value) || 2020)}
            disabled={isSearching}
            className="w-full resend-input text-xs py-2 font-mono"
          />
        </div>

        {/* Year End */}
        <div>
          <label className="block text-[11px] font-medium text-zinc-400 mb-1 flex items-center gap-1">
            <Calendar className="w-3 h-3 text-zinc-500" /> Ano Final
          </label>
          <input
            type="number"
            min={1950}
            max={2030}
            value={yearEnd}
            onChange={(e) => setYearEnd(parseInt(e.target.value) || 2026)}
            disabled={isSearching}
            className="w-full resend-input text-xs py-2 font-mono"
          />
        </div>

        {/* Max Per Base */}
        <div>
          <label className="block text-[11px] font-medium text-zinc-400 mb-1 flex items-center gap-1">
            <Hash className="w-3 h-3 text-zinc-500" /> Limite por Base
          </label>
          <select
            value={maxPerBase}
            onChange={(e) => setMaxPerBase(parseInt(e.target.value) || 30)}
            disabled={isSearching}
            className="w-full resend-input text-xs py-2 bg-zinc-950 font-mono"
          >
            <option value={10}>10 registros</option>
            <option value={20}>20 registros</option>
            <option value={30}>30 registros (Recomendado)</option>
            <option value={50}>50 registros</option>
            <option value={100}>100 registros (Massivo)</option>
          </select>
        </div>
      </div>
    </form>
  );
};

