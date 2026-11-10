import React, { useState } from 'react';
import type { AcademicRecord } from '../types';
import {
  X,
  ExternalLink,
  Sparkles,
  BookOpen,
  Tag,
  Calendar,
  User,
  FileDown,
  CheckCircle2,
  XCircle,
  HelpCircle,
} from 'lucide-react';

interface DetailModalProps {
  record: AcademicRecord | null;
  onClose: () => void;
  onUpdateScreening?: (
    articleId: string,
    status: 'incluido' | 'excluido' | 'duvida' | 'pendente',
    reason?: string,
    notes?: string
  ) => void;
}

const EXCLUSION_REASONS = [
  'Fora do escopo temático',
  'Metodologia incompatível',
  'Tipo de documento inadequado (editorial, anais parciais)',
  'População ou amostra divergente',
  'Sem acesso ao texto completo',
  'Outro motivo específico',
];

export const DetailModal: React.FC<DetailModalProps> = ({
  record,
  onClose,
  onUpdateScreening,
}) => {
  if (!record) return null;

  const currentStatus = record.screening_status || 'pendente';
  const [selectedReason, setSelectedReason] = useState(record.screening_reason || EXCLUSION_REASONS[0]);
  const [notes, setNotes] = useState(record.screening_notes || '');

  const handleScreening = (status: 'incluido' | 'excluido' | 'duvida' | 'pendente') => {
    if (!record.id) return;
    const reason = status === 'excluido' ? selectedReason : undefined;
    onUpdateScreening?.(record.id, status, reason, notes);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div
        className="relative w-full max-w-2xl bg-zinc-950 border border-white/10 rounded-2xl shadow-2xl overflow-hidden max-h-[92vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-white/[0.08] flex items-start justify-between gap-4 bg-black/40">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="px-2 py-0.5 rounded text-[10px] font-medium uppercase bg-white/10 text-white border border-white/10">
                {record.Base}
              </span>
              {record.Ano && (
                <span className="text-xs text-zinc-400 font-mono flex items-center gap-1">
                  <Calendar className="w-3 h-3 text-zinc-500" /> {record.Ano}
                </span>
              )}
              {record.qualis_estrato && (
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">
                  QUALIS {record.qualis_estrato}
                </span>
              )}
              {record.is_open_access && (
                <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-amber-500/10 text-amber-300 border border-amber-500/20">
                  Acesso Aberto
                </span>
              )}
            </div>
            <h2 className="text-lg font-semibold text-white tracking-tight leading-snug">
              {record.Title}
            </h2>
          </div>

          <button
            onClick={onClose}
            className="p-1 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-900 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* PRISMA Screening Bar inside Modal */}
        <div className="px-6 py-3 border-b border-white/[0.06] bg-zinc-900/40 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-xs text-zinc-400">
            <span className="text-[11px] uppercase font-semibold text-zinc-300">
              Decisão de Triagem:
            </span>
            <span
              className={`px-2 py-0.5 rounded text-[11px] font-medium capitalize ${
                currentStatus === 'incluido'
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : currentStatus === 'excluido'
                  ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                  : currentStatus === 'duvida'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  : 'bg-zinc-800 text-zinc-400'
              }`}
            >
              {currentStatus}
            </span>
          </div>

          <div className="flex items-center gap-1.5">
            <button
              onClick={() => handleScreening('incluido')}
              className={`px-2.5 py-1 rounded text-xs font-medium flex items-center gap-1 transition-all ${
                currentStatus === 'incluido'
                  ? 'bg-emerald-500 text-black font-semibold'
                  : 'bg-zinc-900 text-zinc-400 hover:text-emerald-400 border border-white/10'
              }`}
            >
              <CheckCircle2 className="w-3.5 h-3.5" /> Incluir
            </button>

            <button
              onClick={() => handleScreening('excluido')}
              className={`px-2.5 py-1 rounded text-xs font-medium flex items-center gap-1 transition-all ${
                currentStatus === 'excluido'
                  ? 'bg-rose-500 text-white font-semibold'
                  : 'bg-zinc-900 text-zinc-400 hover:text-rose-400 border border-white/10'
              }`}
            >
              <XCircle className="w-3.5 h-3.5" /> Excluir
            </button>

            <button
              onClick={() => handleScreening('duvida')}
              className={`px-2.5 py-1 rounded text-xs font-medium flex items-center gap-1 transition-all ${
                currentStatus === 'duvida'
                  ? 'bg-amber-500 text-black font-semibold'
                  : 'bg-zinc-900 text-zinc-400 hover:text-amber-400 border border-white/10'
              }`}
            >
              <HelpCircle className="w-3.5 h-3.5" /> Dúvida
            </button>
          </div>
        </div>

        {/* Body content */}
        <div className="p-6 overflow-y-auto space-y-5 text-sm">
          {/* Exclusion reason selector if marked as excluido */}
          {currentStatus === 'excluido' && (
            <div className="p-3 rounded-xl bg-rose-950/20 border border-rose-500/20 space-y-2">
              <label className="text-[11px] font-medium text-rose-300 block">
                Motivo de Exclusão PRISMA:
              </label>
              <select
                value={selectedReason}
                onChange={(e) => {
                  setSelectedReason(e.target.value);
                  if (record.id) onUpdateScreening?.(record.id, 'excluido', e.target.value, notes);
                }}
                className="w-full resend-input text-xs py-1.5 bg-zinc-950"
              >
                {EXCLUSION_REASONS.map((r) => (
                  <option key={r} value={r} className="bg-zinc-900 text-white">
                    {r}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Research notes for screening */}
          {currentStatus !== 'pendente' && (
            <div className="space-y-1.5">
              <label className="text-[11px] font-medium text-zinc-400 block">
                Anotações de Elegibilidade / Síntese:
              </label>
              <textarea
                value={notes}
                onChange={(e) => {
                  setNotes(e.target.value);
                  if (record.id) onUpdateScreening?.(record.id, currentStatus, selectedReason, e.target.value);
                }}
                placeholder="Registre observações sobre metodologia, amostra ou relevância..."
                className="w-full resend-input text-xs py-2 bg-zinc-950 resize-none h-16"
              />
            </div>
          )}

          {/* Authors */}
          {record.Autor && (
            <div>
              <div className="text-xs font-medium text-zinc-400 uppercase tracking-wider mb-1 flex items-center gap-1.5">
                <User className="w-3.5 h-3.5 text-zinc-500" /> Autores
              </div>
              <p className="text-zinc-200 leading-relaxed">{record.Autor}</p>
            </div>
          )}

          {/* Journal / Venue */}
          {record['Revista / Fonte'] && (
            <div>
              <div className="text-xs font-medium text-zinc-400 uppercase tracking-wider mb-1 flex items-center gap-1.5">
                <BookOpen className="w-3.5 h-3.5 text-zinc-500" /> Periódico / Evento
              </div>
              <p className="text-zinc-200">{record['Revista / Fonte']}</p>
            </div>
          )}

          {/* Cienciometrics OpenAlex */}
          {(record.cited_by_count !== undefined || record.fwci !== undefined) && (
            <div className="p-3.5 rounded-xl bg-zinc-900/60 border border-white/[0.06] flex items-center justify-around text-center">
              <div>
                <span className="text-[11px] text-zinc-400 block">Citações OpenAlex</span>
                <span className="text-base font-bold text-white font-mono">
                  {record.cited_by_count ?? 0}
                </span>
              </div>
              <div className="h-6 w-px bg-white/10" />
              <div>
                <span className="text-[11px] text-zinc-400 block">Impacto FWCI</span>
                <span className="text-base font-bold text-emerald-400 font-mono">
                  {record.fwci ? record.fwci.toFixed(2) : 'N/D'}
                </span>
              </div>
              <div className="h-6 w-px bg-white/10" />
              <div>
                <span className="text-[11px] text-zinc-400 block">Estrato Qualis</span>
                <span className="text-base font-bold text-purple-400 font-mono">
                  {record.qualis_estrato || 'Não Classif.'}
                </span>
              </div>
            </div>
          )}

          {/* Abstract */}
          <div>
            <div className="text-xs font-medium text-zinc-400 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-zinc-500" /> Resumo (Abstract)
            </div>
            <div className="text-zinc-300 leading-relaxed text-xs sm:text-sm bg-zinc-900/30 p-3.5 rounded-xl border border-white/[0.04]">
              {record.Resumo ? (
                record.Resumo
              ) : (
                <span className="text-zinc-500 italic">
                  Resumo não fornecido diretamente na consulta aos metadados. Acesse o link oficial para visualizar o documento integral.
                </span>
              )}
            </div>
          </div>

          {/* Keywords */}
          {record['Palavras-Chave'] && (
            <div>
              <div className="text-xs font-medium text-zinc-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Tag className="w-3.5 h-3.5 text-zinc-500" /> Palavras-Chave
              </div>
              <div className="flex flex-wrap gap-1.5">
                {record['Palavras-Chave'].split(/[;,]/).map((kw, i) => {
                  const clean = kw.trim();
                  if (!clean) return null;
                  return (
                    <span
                      key={i}
                      className="px-2 py-0.5 rounded-md text-xs bg-zinc-900 border border-white/10 text-zinc-300"
                    >
                      {clean}
                    </span>
                  );
                })}
              </div>
            </div>
          )}

          {/* Identifiers */}
          <div className="pt-3 border-t border-white/[0.06] flex items-center justify-between text-xs text-zinc-500 font-mono">
            {record.DOI && <span>DOI: {record.DOI}</span>}
            {record['ID Origem'] && <span>ID Base: {record['ID Origem']}</span>}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-3.5 border-t border-white/[0.08] bg-black/60 flex items-center justify-between gap-3">
          <div>
            {record.pdf_url && (
              <a
                href={record.pdf_url}
                target="_blank"
                rel="noreferrer"
                className="px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20 flex items-center gap-1.5 transition-colors"
              >
                <FileDown className="w-3.5 h-3.5" />
                <span>Abrir PDF Completo (Open Access)</span>
              </a>
            )}
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="resend-btn-secondary py-1.5 px-3 text-xs"
            >
              Fechar
            </button>
            {record['Link Pub'] && (
              <a
                href={record['Link Pub']}
                target="_blank"
                rel="noreferrer"
                className="resend-btn-primary py-1.5 px-3.5 text-xs"
              >
                <span>Acessar Publicação Oficial</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
