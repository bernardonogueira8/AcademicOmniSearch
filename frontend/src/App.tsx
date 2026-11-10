import { useState, useEffect, useRef } from 'react';
import { Navbar } from './components/Navbar';
import { BaseSelector } from './components/BaseSelector';
import { SearchBar } from './components/SearchBar';
import { MetricsCards } from './components/MetricsCards';
import { PrismaBar } from './components/PrismaBar';
import { ResultsTable } from './components/ResultsTable';
import { ExportToolbar } from './components/ExportToolbar';
import { LogsDrawer } from './components/LogsDrawer';
import { DetailModal } from './components/DetailModal';
import { SessionsModal } from './components/SessionsModal';
import type { BaseInfo, AcademicRecord, SearchMetrics, LogMessage, PrismaStats } from './types';
import { Sparkles } from 'lucide-react';

export function App() {
  const [apiStatus, setApiStatus] = useState<'online' | 'connecting' | 'offline'>('connecting');
  const [bases, setBases] = useState<BaseInfo[]>([]);
  const [selectedBases, setSelectedBases] = useState<string[]>(['capes', 'pubmed', 'brapci', 'acm']);

  // Search parameters
  const [query, setQuery] = useState('');
  const [yearStart, setYearStart] = useState(2020);
  const [yearEnd, setYearEnd] = useState(2026);
  const [field, setField] = useState('Todos');
  const [maxPerBase, setMaxPerBase] = useState(30);

  // Search execution state
  const [currentSessionId, setCurrentSessionId] = useState<string>('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchProgress, setSearchProgress] = useState(0);
  const [currentBaseExecuting, setCurrentBaseExecuting] = useState('');
  const [rawCount, setRawCount] = useState(0);
  const [deduplicatedCount, setDeduplicatedCount] = useState(0);
  const [records, setRecords] = useState<AcademicRecord[]>([]);
  const [metrics, setMetrics] = useState<SearchMetrics>({
    total_records: 0,
    bases_count: {},
    years_range: 'N/D',
    top_journals: {},
  });

  // PRISMA screening state
  const [screeningFilter, setScreeningFilter] = useState<'ALL' | 'pendente' | 'incluido' | 'excluido' | 'duvida'>('ALL');
  const [prismaStats, setPrismaStats] = useState<PrismaStats>({
    records_identified: 0,
    duplicates_removed: 0,
    records_screened: 0,
    records_pending: 0,
    records_excluded: 0,
    records_uncertain: 0,
    records_included: 0,
  });

  // Logs & UI drawers
  const [logs, setLogs] = useState<LogMessage[]>([]);
  const [showLogs, setShowLogs] = useState(false);
  const [showSessions, setShowSessions] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState<AcademicRecord | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  const appendLog = (message: string, level: LogMessage['level'] = 'INFO', base?: string) => {
    const newLog: LogMessage = {
      id: Math.random().toString(36).substring(2, 9),
      timestamp: new Date().toLocaleTimeString('pt-BR'),
      message,
      level,
      base,
    };
    setLogs((prev) => [...prev, newLog]);
  };

  // Inicialização e consulta às bases disponíveis
  useEffect(() => {
    const fetchBases = async () => {
      try {
        const res = await fetch('/api/bases');
        if (res.ok) {
          const data = await res.json();
          setBases(data.bases || []);
          setApiStatus('online');
          appendLog('Backend conectado. Banco SQLite de pesquisas pronto.', 'SUCCESS');
        } else {
          setApiStatus('offline');
        }
      } catch (err) {
        console.error('Falha ao conectar com o backend:', err);
        setApiStatus('offline');
      }
    };

    fetchBases();
  }, []);

  // Recálculo local das estatísticas PRISMA
  const computePrismaStats = (currentRecords: AcademicRecord[], totalRaw: number, totalDedup: number) => {
    const counts = { incluido: 0, excluido: 0, duvida: 0, pendente: 0 };
    currentRecords.forEach((r) => {
      const s = r.screening_status || 'pendente';
      if (s in counts) counts[s as keyof typeof counts]++;
      else counts.pendente++;
    });

    const screened = counts.incluido + counts.excluido + counts.duvida;
    setPrismaStats({
      records_identified: totalRaw,
      duplicates_removed: Math.max(0, totalRaw - totalDedup),
      records_screened: screened,
      records_pending: counts.pendente,
      records_excluded: counts.excluido,
      records_uncertain: counts.duvida,
      records_included: counts.incluido,
    });
  };

  // Execução de Busca com Server-Sent Events (SSE) e Concorrência
  const handleSearch = async () => {
    if (!query.trim() || selectedBases.length === 0) return;

    setIsSearching(true);
    setSearchProgress(5);
    setCurrentBaseExecuting('Iniciando orquestração concorrente...');
    setRecords([]);
    setRawCount(0);
    setDeduplicatedCount(0);
    setScreeningFilter('ALL');

    appendLog(
      `Nova busca iniciada: "${query}" | Janela: ${yearStart}-${yearEnd} | Campo: ${field} | Bases: ${selectedBases.join(', ')}`,
      'INFO'
    );

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      const params = new URLSearchParams({
        query: query.trim(),
        year_start: yearStart.toString(),
        year_end: yearEnd.toString(),
        field,
        max_per_base: maxPerBase.toString(),
        bases: selectedBases.join(','),
      });

      const response = await fetch(`/api/search/stream?${params.toString()}`, {
        signal: abortController.signal,
      });

      if (!response.ok || !response.body) {
        throw new Error(`Erro HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      const handleEvent = (event: any) => {
        if (event.type === 'init') {
          setCurrentSessionId(event.session_id);
        } else if (event.type === 'base_start') {
          setCurrentBaseExecuting(`Consultando ${event.base_name}...`);
          setSearchProgress(event.percent);
        } else if (event.type === 'base_done') {
          setSearchProgress(event.percent);
          appendLog(
            `Base ${event.base_name} finalizada: ${event.count} registros obtidos.`,
            event.count > 0 ? 'SUCCESS' : 'WARNING',
            event.base_name
          );
          if (event.logs && Array.isArray(event.logs)) {
            event.logs.forEach((logText: string) => {
              appendLog(logText, 'INFO', event.base_name);
            });
          }
          // Atualização progressiva: artigos aparecem imediatamente conforme cada base finaliza
          if (event.records && Array.isArray(event.records) && event.records.length > 0) {
            setRecords((prev) => {
              const combined = [...prev, ...event.records];
              const seen = new Set<string>();
              return combined.filter((item) => {
                const k = (item.Title || '').toLowerCase().trim();
                if (!k || seen.has(k)) return false;
                seen.add(k);
                return true;
              });
            });
            setRawCount((prev) => prev + event.count);
          }
        } else if (event.type === 'enriching') {
          setCurrentBaseExecuting(event.message || 'Aplicando enriquecimento cienciométrico...');
          appendLog('Enriquecendo com OpenAlex (citações/FWCI/PDFs) e Qualis CAPES...', 'INFO');
        } else if (event.type === 'complete') {
          setSearchProgress(100);
          setCurrentBaseExecuting('Busca finalizada!');
          setCurrentSessionId(event.session_id);
          setRawCount(event.raw_count);
          setDeduplicatedCount(event.deduplicated_count);
          setRecords(event.records || []);
          setMetrics(event.metrics);
          if (event.prisma_stats) {
            setPrismaStats(event.prisma_stats);
          } else {
            computePrismaStats(event.records || [], event.raw_count, event.deduplicated_count);
          }
          appendLog(
            `Processamento e persistência concluídos: ${event.deduplicated_count} artigos únicos consolidados e salvos na sessão ${event.session_id}.`,
            'SUCCESS'
          );
        }
      };

      const parseBuffer = (chunkText: string, flush = false) => {
        buffer += chunkText;
        // Normaliza quebras de linha Windows/HTTP CRLF para LF padrão
        const normalized = buffer.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
        const parts = normalized.split('\n\n');

        if (!flush) {
          buffer = parts.pop() || '';
        } else {
          buffer = '';
        }

        for (const part of parts) {
          const lines = part.split('\n');
          let dataStr = '';
          for (const l of lines) {
            const trimmed = l.trim();
            if (trimmed.startsWith('data:')) {
              dataStr += trimmed.slice(5).trim();
            }
          }
          if (dataStr) {
            try {
              const event = JSON.parse(dataStr);
              handleEvent(event);
            } catch (err) {
              console.error('Erro ao interpretar JSON SSE:', err, dataStr);
            }
          }
        }
      };

      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          parseBuffer('', true);
          break;
        }
        parseBuffer(decoder.decode(value, { stream: true }));
      }
    } catch (err: any) {
      if (err.name === 'AbortError') {
        appendLog('Busca cancelada pelo usuário.', 'WARNING');
        setCurrentBaseExecuting('Busca cancelada');
      } else {
        console.error('Falha na busca:', err);
        appendLog(`Erro durante a busca: ${err.message}`, 'ERROR');
        setCurrentBaseExecuting('Erro na execução');
      }
    } finally {
      setIsSearching(false);
      abortControllerRef.current = null;
    }
  };

  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };

  // Atualização persistente de decisão de triagem
  const handleUpdateScreening = async (
    articleId: string,
    status: 'incluido' | 'excluido' | 'duvida' | 'pendente',
    reason?: string,
    notes?: string
  ) => {
    // 1. Atualização otimista no estado do React
    const updated = records.map((r) => {
      if (r.id === articleId) {
        return {
          ...r,
          screening_status: status,
          screening_reason: reason ?? r.screening_reason,
          screening_notes: notes ?? r.screening_notes,
        };
      }
      return r;
    });
    setRecords(updated);
    computePrismaStats(updated, rawCount, deduplicatedCount);

    if (selectedRecord && selectedRecord.id === articleId) {
      setSelectedRecord({
        ...selectedRecord,
        screening_status: status,
        screening_reason: reason ?? selectedRecord.screening_reason,
        screening_notes: notes ?? selectedRecord.screening_notes,
      });
    }

    // 2. Persistência assíncrona no SQLite
    try {
      await fetch(`/api/articles/${articleId}/screening`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status, reason, notes }),
      });
    } catch (e) {
      console.error('Erro ao salvar decisão de triagem:', e);
    }
  };

  // Carregar sessão anterior a partir do histórico
  const handleLoadSession = async (sessionId: string) => {
    try {
      appendLog(`Carregando sessão ${sessionId} do banco de dados...`, 'INFO');
      const res = await fetch(`/api/sessions/${sessionId}`);
      if (!res.ok) throw new Error('Sessão não encontrada');
      const data = await res.json();

      setCurrentSessionId(data.id);
      setQuery(data.query || '');
      setYearStart(data.year_start || 2020);
      setYearEnd(data.year_end || 2026);
      setField(data.field || 'Todos');
      if (data.bases && Array.isArray(data.bases)) {
        setSelectedBases(data.bases);
      }
      setRawCount(data.total_raw || 0);
      setDeduplicatedCount(data.total_dedup || 0);
      setRecords(data.records || []);
      setScreeningFilter('ALL');

      if (data.prisma_stats) {
        setPrismaStats(data.prisma_stats);
      } else {
        computePrismaStats(data.records || [], data.total_raw, data.total_dedup);
      }

      appendLog(`Sessão ${sessionId} restaurada: ${data.total_dedup} artigos com status de triagem preservado.`, 'SUCCESS');
    } catch (err: any) {
      appendLog(`Erro ao carregar sessão: ${err.message}`, 'ERROR');
    }
  };

  return (
    <div className="min-h-screen bg-black text-zinc-100 flex flex-col relative selection:bg-zinc-800">
      {/* Background radial gradient spotlight */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-96 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-zinc-800/20 via-zinc-900/0 to-transparent pointer-events-none -z-10" />

      {/* Navbar */}
      <Navbar
        apiStatus={apiStatus}
        logsCount={logs.length}
        showLogs={showLogs}
        setShowLogs={setShowLogs}
        basesCount={bases.length}
        onOpenHistory={() => setShowSessions(true)}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-8 space-y-6">
        {/* Hero title */}
        <div className="space-y-2 text-center sm:text-left">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900 border border-white/10 text-xs text-zinc-400">
            <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
            <span>Colheita automatizada, cienciometria & triagem PRISMA</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-white">
            Explorador de Literatura Acadêmica
          </h1>
          <p className="text-sm sm:text-base text-zinc-400 max-w-3xl">
            Consulte simultaneamente os Periódicos CAPES, PubMed, BRAPCI, ACM, IEEE e Scopus com classificação Qualis integrada, métricas de impacto OpenAlex e fluxo de elegibilidade PRISMA.
          </p>
        </div>

        {/* Search Panel */}
        <SearchBar
          query={query}
          setQuery={setQuery}
          yearStart={yearStart}
          setYearStart={setYearStart}
          yearEnd={yearEnd}
          setYearEnd={setYearEnd}
          field={field}
          setField={setField}
          maxPerBase={maxPerBase}
          setMaxPerBase={setMaxPerBase}
          onSearch={handleSearch}
          isSearching={isSearching}
          onCancel={handleCancel}
        />

        {/* Base Selector */}
        <BaseSelector
          bases={bases}
          selectedBases={selectedBases}
          onChange={setSelectedBases}
          disabled={isSearching}
        />

        {/* Live Search Progress Bar */}
        {isSearching && (
          <div className="resend-card p-4 space-y-2 border-emerald-500/30 bg-zinc-950">
            <div className="flex items-center justify-between text-xs">
              <span className="font-medium text-emerald-400 flex items-center gap-2">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
                </span>
                {currentBaseExecuting}
              </span>
              <span className="font-mono text-zinc-400">{searchProgress}%</span>
            </div>
            <div className="w-full bg-zinc-900 h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-emerald-400 h-full transition-all duration-300 ease-out"
                style={{ width: `${searchProgress}%` }}
              />
            </div>
          </div>
        )}

        {/* Metrics Summary */}
        <MetricsCards
          metrics={metrics}
          rawCount={rawCount}
          deduplicatedCount={deduplicatedCount}
        />

        {/* PRISMA Screening Bar (Shown when results are present) */}
        {records.length > 0 && (
          <PrismaBar
            stats={prismaStats}
            currentFilter={screeningFilter}
            onFilterChange={setScreeningFilter}
          />
        )}

        {/* Export Toolbar */}
        <ExportToolbar records={records} />

        {/* Results Table */}
        {records.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-white tracking-tight">
                Publicações Encontradas ({records.length})
                {currentSessionId && (
                  <span className="ml-2 text-xs font-mono text-zinc-500 font-normal">
                    [{currentSessionId}]
                  </span>
                )}
              </h2>
            </div>
            <ResultsTable
              records={records}
              onSelectRecord={setSelectedRecord}
              screeningFilter={screeningFilter}
              onUpdateScreening={handleUpdateScreening}
            />
          </div>
        )}

        {/* Empty state when no search yet */}
        {!isSearching && records.length === 0 && (
          <div className="resend-card py-16 px-6 text-center space-y-4 border-dashed border-white/10">
            <div className="w-12 h-12 rounded-2xl bg-zinc-900 border border-white/10 flex items-center justify-center mx-auto text-zinc-400">
              <Sparkles className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <h3 className="text-base font-semibold text-white">
                Pronto para iniciar a recuperação
              </h3>
              <p className="text-xs text-zinc-400 max-w-md mx-auto">
                Selecione as bases desejadas, defina seu termo de busca e clique em <b className="text-white">Buscar</b> para colher publicações com enriquecimento cienciométrico e fluxo PRISMA.
              </p>
            </div>
          </div>
        )}
      </main>

      {/* Detail Modal with PRISMA Screening decisions */}
      <DetailModal
        record={selectedRecord}
        onClose={() => setSelectedRecord(null)}
        onUpdateScreening={handleUpdateScreening}
      />

      {/* Sessions History Modal */}
      <SessionsModal
        isOpen={showSessions}
        onClose={() => setShowSessions(false)}
        onSelectSession={handleLoadSession}
      />

      {/* Terminal Logs Drawer */}
      <LogsDrawer
        logs={logs}
        isOpen={showLogs}
        onClose={() => setShowLogs(false)}
        onClear={() => setLogs([])}
      />
    </div>
  );
}

export default App;
