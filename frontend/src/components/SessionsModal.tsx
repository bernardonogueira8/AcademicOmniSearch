import React, { useEffect, useState } from 'react';
import type { SearchSession } from '../types';
import { History, X, Calendar, Database, ArrowRight, Loader2 } from 'lucide-react';

interface SessionsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectSession: (sessionId: string) => void;
}

export const SessionsModal: React.FC<SessionsModalProps> = ({
  isOpen,
  onClose,
  onSelectSession,
}) => {
  const [sessions, setSessions] = useState<SearchSession[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      fetch('/api/sessions')
        .then((res) => res.json())
        .then((data) => {
          setSessions(data.sessions || []);
        })
        .catch((err) => console.error('Erro ao listar sessões:', err))
        .finally(() => setLoading(false));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div
        className="relative w-full max-w-xl bg-zinc-950 border border-white/10 rounded-2xl shadow-2xl overflow-hidden max-h-[85vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-white/[0.08] flex items-center justify-between bg-black/40">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-emerald-400" />
            <h2 className="text-base font-semibold text-white tracking-tight">
              Histórico de Buscas Salvas
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-900 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-3">
          {loading ? (
            <div className="py-12 flex flex-col items-center justify-center gap-2 text-zinc-500 text-xs">
              <Loader2 className="w-5 h-5 animate-spin text-emerald-400" />
              <span>Carregando histórico de pesquisas...</span>
            </div>
          ) : sessions.length === 0 ? (
            <div className="py-12 text-center text-zinc-500 text-xs">
              Nenhuma busca registrada no banco local ainda.
            </div>
          ) : (
            sessions.map((s) => {
              const dateStr = new Date(s.created_at).toLocaleString('pt-BR');
              return (
                <div
                  key={s.id}
                  onClick={() => {
                    onSelectSession(s.id);
                    onClose();
                  }}
                  className="group p-3.5 rounded-xl border border-white/[0.06] hover:border-white/20 bg-black/40 hover:bg-zinc-900/60 transition-all cursor-pointer flex items-center justify-between gap-4"
                >
                  <div className="space-y-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-semibold text-white text-sm truncate">
                        "{s.query}"
                      </span>
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-zinc-800 text-zinc-400 font-mono">
                        {s.total_dedup} artigos
                      </span>
                    </div>

                    <div className="flex items-center gap-3 text-[11px] text-zinc-500 flex-wrap">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" /> {s.year_start}-{s.year_end}
                      </span>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        <Database className="w-3 h-3" /> {(s.bases || []).join(', ')}
                      </span>
                      <span>•</span>
                      <span>{dateStr}</span>
                    </div>
                  </div>

                  <div className="shrink-0 text-zinc-500 group-hover:text-emerald-400 transition-colors">
                    <ArrowRight className="w-4 h-4" />
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
