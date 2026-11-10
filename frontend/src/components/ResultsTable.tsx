import React, { useState, useMemo } from 'react';
import type { AcademicRecord } from '../types';
import {
  ExternalLink,
  Search,
  Eye,
  ChevronLeft,
  ChevronRight,
  Filter,
  FileDown,
  CheckCircle2,
  XCircle,
  HelpCircle,
} from 'lucide-react';

interface ResultsTableProps {
  records: AcademicRecord[];
  onSelectRecord: (record: AcademicRecord) => void;
  screeningFilter?: 'ALL' | 'pendente' | 'incluido' | 'excluido' | 'duvida';
  onUpdateScreening?: (
    articleId: string,
    status: 'incluido' | 'excluido' | 'duvida' | 'pendente',
    reason?: string
  ) => void;
}

export const ResultsTable: React.FC<ResultsTableProps> = ({
  records,
  onSelectRecord,
  screeningFilter = 'ALL',
  onUpdateScreening,
}) => {
  const [filterText, setFilterText] = useState('');
  const [selectedBaseFilter, setSelectedBaseFilter] = useState('ALL');
  const [onlyQualis, setOnlyQualis] = useState(false);
  const [onlyOA, setOnlyOA] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  // Bases únicas disponíveis nos resultados
  const availableBases = useMemo(() => {
    const set = new Set<string>();
    records.forEach((r) => {
      if (r.Base) set.add(r.Base);
    });
    return Array.from(set);
  }, [records]);

  // Filtragem dos registros
  const filteredRecords = useMemo(() => {
    return records.filter((r) => {
      // Filtro PRISMA
      if (screeningFilter !== 'ALL') {
        const status = r.screening_status || 'pendente';
        if (status !== screeningFilter) return false;
      }
      // Filtro de base
      if (selectedBaseFilter !== 'ALL' && r.Base !== selectedBaseFilter) {
        return false;
      }
      // Filtro Qualis
      if (onlyQualis && !r.qualis_estrato) {
        return false;
      }
      // Filtro Open Access
      if (onlyOA && !r.is_open_access) {
        return false;
      }
      // Filtro de texto
      if (filterText.trim()) {
        const query = filterText.toLowerCase();
        const titleMatch = (r.Title || '').toLowerCase().includes(query);
        const authorMatch = (r.Autor || '').toLowerCase().includes(query);
        const venueMatch = (r['Revista / Fonte'] || '').toLowerCase().includes(query);
        const doiMatch = (r.DOI || '').toLowerCase().includes(query);
        return titleMatch || authorMatch || venueMatch || doiMatch;
      }
      return true;
    });
  }, [records, screeningFilter, filterText, selectedBaseFilter, onlyQualis, onlyOA]);

  // Paginação
  const totalPages = Math.ceil(filteredRecords.length / pageSize) || 1;
  const paginatedRecords = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredRecords.slice(start, start + pageSize);
  }, [filteredRecords, currentPage, pageSize]);

  return (
    <div className="resend-card overflow-hidden">
      {/* Table Toolbar */}
      <div className="p-4 border-b border-white/[0.08] bg-zinc-950/60 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        {/* Search in results */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
          <input
            type="text"
            value={filterText}
            onChange={(e) => {
              setFilterText(e.target.value);
              setCurrentPage(1);
            }}
            placeholder="Filtrar por título, autor, periódico ou DOI..."
            className="w-full bg-black/60 border border-white/10 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-white/30"
          />
        </div>

        {/* Filter chips */}
        <div className="flex items-center gap-2 flex-wrap text-xs">
          <div className="flex items-center gap-1 text-zinc-500 mr-1">
            <Filter className="w-3.5 h-3.5" />
            <span className="text-[11px] uppercase font-medium">Bases:</span>
          </div>
          <select
            value={selectedBaseFilter}
            onChange={(e) => {
              setSelectedBaseFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="resend-input text-xs py-1 px-2.5 bg-zinc-950"
          >
            <option value="ALL">Todas as Bases ({records.length})</option>
            {availableBases.map((b) => (
              <option key={b} value={b}>
                {b}
              </option>
            ))}
          </select>

          {/* Qualis quick toggle */}
          <button
            onClick={() => {
              setOnlyQualis(!onlyQualis);
              setCurrentPage(1);
            }}
            className={`px-2.5 py-1 rounded-md text-[11px] font-medium border transition-colors cursor-pointer ${
              onlyQualis
                ? 'bg-purple-500/20 text-purple-300 border-purple-500/40'
                : 'bg-zinc-900/60 text-zinc-400 border-white/[0.08] hover:border-white/20'
            }`}
          >
            Apenas Qualis
          </button>

          {/* Open Access quick toggle */}
          <button
            onClick={() => {
              setOnlyOA(!onlyOA);
              setCurrentPage(1);
            }}
            className={`px-2.5 py-1 rounded-md text-[11px] font-medium border transition-colors cursor-pointer ${
              onlyOA
                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                : 'bg-zinc-900/60 text-zinc-400 border-white/[0.08] hover:border-white/20'
            }`}
          >
            Acesso Aberto
          </button>
        </div>
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-white/[0.08] bg-black/40 text-zinc-400 font-medium">
              <th className="py-3 px-4 w-12 text-center">#</th>
              <th className="py-3 px-4 min-w-[280px]">Título do Artigo</th>
              <th className="py-3 px-4 min-w-[150px]">Autor(es)</th>
              <th className="py-3 px-4 min-w-[150px]">Periódico / Fonte</th>
              <th className="py-3 px-4 w-16 text-center">Ano</th>
              <th className="py-3 px-4 w-24 text-center">Base</th>
              <th className="py-3 px-4 min-w-[110px] text-center">Cienciometria</th>
              <th className="py-3 px-4 w-28 text-center">Triagem</th>
              <th className="py-3 px-4 w-24 text-right">Ação</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.05]">
            {paginatedRecords.length === 0 ? (
              <tr>
                <td colSpan={9} className="py-12 text-center text-zinc-500">
                  Nenhum registro corresponde aos filtros selecionados.
                </td>
              </tr>
            ) : (
              paginatedRecords.map((record, idx) => {
                const globalIndex = (currentPage - 1) * pageSize + idx + 1;
                const status = record.screening_status || 'pendente';
                const articleId = record.id || `${globalIndex}`;

                return (
                  <tr
                    key={record.id || idx}
                    className="group hover:bg-white/[0.02] transition-colors"
                  >
                    <td className="py-3 px-4 text-center text-zinc-600 font-mono">
                      {globalIndex}
                    </td>

                    {/* Title */}
                    <td className="py-3 px-4">
                      <div className="flex items-start gap-1.5">
                        <button
                          onClick={() => onSelectRecord(record)}
                          className="text-left font-medium text-white hover:text-emerald-400 transition-colors line-clamp-2 cursor-pointer flex-1"
                          title={record.Title}
                        >
                          {record.Title}
                        </button>
                      </div>
                      <div className="flex items-center gap-2 mt-1 flex-wrap">
                        {record.DOI && (
                          <span className="text-[10px] text-zinc-500 font-mono block truncate max-w-xs">
                            DOI: {record.DOI}
                          </span>
                        )}
                        {record.pdf_url && (
                          <a
                            href={record.pdf_url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20 transition-colors"
                            title="Acesso Aberto: Abrir PDF Integral"
                          >
                            <FileDown className="w-2.5 h-2.5" /> PDF
                          </a>
                        )}
                      </div>
                    </td>

                    {/* Author */}
                    <td className="py-3 px-4 text-zinc-300">
                      <span className="line-clamp-2" title={record.Autor}>
                        {record.Autor || '—'}
                      </span>
                    </td>

                    {/* Venue / Source */}
                    <td className="py-3 px-4 text-zinc-300">
                      <div className="line-clamp-2" title={record['Revista / Fonte']}>
                        {record['Revista / Fonte'] || '—'}
                      </div>
                      {record.qualis_estrato && (
                        <span className="inline-block mt-1 px-1.5 py-0.2 rounded text-[10px] font-bold bg-purple-500/15 text-purple-300 border border-purple-500/25">
                          Qualis {record.qualis_estrato}
                        </span>
                      )}
                    </td>

                    {/* Year */}
                    <td className="py-3 px-4 text-center text-zinc-400 font-mono">
                      {record.Ano || '—'}
                    </td>

                    {/* Base */}
                    <td className="py-3 px-4 text-center">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-medium uppercase bg-white/5 border border-white/10 text-zinc-300">
                        {record.Base}
                      </span>
                    </td>

                    {/* Cienciometrics badges */}
                    <td className="py-3 px-4 text-center">
                      <div className="flex items-center justify-center gap-1.5 flex-wrap">
                        {record.cited_by_count !== undefined && (
                          <span
                            className="px-1.5 py-0.5 rounded text-[10px] bg-zinc-900 border border-white/10 text-zinc-300 font-mono"
                            title="Total de Citações OpenAlex"
                          >
                            ★ {record.cited_by_count}
                          </span>
                        )}
                        {record.fwci !== undefined && record.fwci !== null && (
                          <span
                            className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-mono"
                            title="Impacto Ponderado por Citações (FWCI)"
                          >
                            FWCI {record.fwci.toFixed(1)}
                          </span>
                        )}
                        {record.is_open_access && (
                          <span
                            className="px-1.5 py-0.5 rounded text-[10px] bg-amber-500/10 border border-amber-500/20 text-amber-300"
                            title="Acesso Aberto (Open Access)"
                          >
                            OA
                          </span>
                        )}
                        {!record.cited_by_count && !record.fwci && !record.is_open_access && (
                          <span className="text-zinc-600 text-[11px]">—</span>
                        )}
                      </div>
                    </td>

                    {/* Screening Decision (PRISMA Workflow) */}
                    <td className="py-3 px-4 text-center">
                      <div className="flex items-center justify-center gap-1">
                        {/* Incluir */}
                        <button
                          onClick={() => onUpdateScreening?.(articleId, 'incluido')}
                          className={`p-1 rounded transition-colors cursor-pointer ${
                            status === 'incluido'
                              ? 'bg-emerald-500 text-black font-bold ring-1 ring-emerald-400'
                              : 'text-zinc-500 hover:text-emerald-400 hover:bg-emerald-500/10'
                          }`}
                          title="Incluir na Revisão"
                        >
                          <CheckCircle2 className="w-4 h-4" />
                        </button>

                        {/* Excluir */}
                        <button
                          onClick={() => onUpdateScreening?.(articleId, 'excluido', 'Fora do escopo')}
                          className={`p-1 rounded transition-colors cursor-pointer ${
                            status === 'excluido'
                              ? 'bg-rose-500 text-white font-bold ring-1 ring-rose-400'
                              : 'text-zinc-500 hover:text-rose-400 hover:bg-rose-500/10'
                          }`}
                          title="Excluir da Revisão"
                        >
                          <XCircle className="w-4 h-4" />
                        </button>

                        {/* Dúvida */}
                        <button
                          onClick={() => onUpdateScreening?.(articleId, 'duvida')}
                          className={`p-1 rounded transition-colors cursor-pointer ${
                            status === 'duvida'
                              ? 'bg-amber-500 text-black font-bold ring-1 ring-amber-400'
                              : 'text-zinc-500 hover:text-amber-400 hover:bg-amber-500/10'
                          }`}
                          title="Marcar como Dúvida"
                        >
                          <HelpCircle className="w-4 h-4" />
                        </button>
                      </div>
                    </td>

                    {/* Actions */}
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => onSelectRecord(record)}
                          className="p-1 rounded text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors cursor-pointer"
                          title="Ver Detalhes e Resumo"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                        {record['Link Pub'] && (
                          <a
                            href={record['Link Pub']}
                            target="_blank"
                            rel="noreferrer"
                            className="p-1 rounded text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors"
                            title="Abrir URL Oficial"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                          </a>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="p-4 border-t border-white/[0.08] bg-zinc-950/60 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-zinc-400">
        <div>
          Exibindo <span className="font-mono text-white">{filteredRecords.length}</span> publicações
          {filteredRecords.length !== records.length && (
            <span> (de um total de {records.length})</span>
          )}
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="text-[11px]">Por página:</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setCurrentPage(1);
              }}
              className="resend-input text-xs py-0.5 px-2 bg-zinc-950"
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
              disabled={currentPage === 1}
              className="p-1.5 rounded text-zinc-400 hover:text-white hover:bg-zinc-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="font-mono text-zinc-300 px-2">
              {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
              disabled={currentPage === totalPages}
              className="p-1.5 rounded text-zinc-400 hover:text-white hover:bg-zinc-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
