import React, { useState } from 'react';
import type { AcademicRecord } from '../types';
import { Download, FileSpreadsheet, BookMarked, Code2, FileText, Loader2, Check } from 'lucide-react';

interface ExportToolbarProps {
  records: AcademicRecord[];
}

export const ExportToolbar: React.FC<ExportToolbarProps> = ({ records }) => {
  const [downloading, setDownloading] = useState<string | null>(null);
  const [successFmt, setSuccessFmt] = useState<string | null>(null);

  if (records.length === 0) return null;

  const handleExport = async (format: 'excel' | 'ris' | 'bibtex' | 'csv') => {
    try {
      setDownloading(format);
      const res = await fetch('/api/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          format,
          records,
          filename: `AcademicOmniSearch_${new Date().toISOString().slice(0, 10)}`,
        }),
      });

      if (!res.ok) {
        throw new Error('Falha ao exportar dados');
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;

      let extension: string = format;
      if (format === 'excel') extension = 'xlsx';
      if (format === 'bibtex') extension = 'bib';

      a.download = `AcademicOmniSearch_export.${extension}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);

      setSuccessFmt(format);
      setTimeout(() => setSuccessFmt(null), 2500);
    } catch (err) {
      console.error('Erro na exportação:', err);
      alert('Ocorreu um erro ao gerar a exportação bibliográfica.');
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="resend-card p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-gradient-to-r from-zinc-950 via-zinc-900/50 to-zinc-950 border-white/10">
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
          <Download className="w-4 h-4" />
        </div>
        <div>
          <h3 className="text-xs font-semibold text-white tracking-tight uppercase">
            Exportar Resultados Bibliográficos
          </h3>
          <p className="text-[11px] text-zinc-400">
            {records.length} registros prontos para importação em gerenciadores de referências
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 flex-wrap w-full sm:w-auto">
        {/* Excel */}
        <button
          onClick={() => handleExport('excel')}
          disabled={!!downloading}
          className="resend-btn-secondary text-xs py-1.5 px-3 flex-1 sm:flex-initial"
          title="Exportar planilha Excel completa com colunas padrão e estendidas"
        >
          {downloading === 'excel' ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-400" />
          ) : successFmt === 'excel' ? (
            <Check className="w-3.5 h-3.5 text-emerald-400" />
          ) : (
            <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
          )}
          <span>Excel (.xlsx)</span>
        </button>

        {/* RIS (Zotero / Mendeley) */}
        <button
          onClick={() => handleExport('ris')}
          disabled={!!downloading}
          className="resend-btn-secondary text-xs py-1.5 px-3 flex-1 sm:flex-initial"
          title="Compatível com Zotero, Mendeley e EndNote"
        >
          {downloading === 'ris' ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-400" />
          ) : successFmt === 'ris' ? (
            <Check className="w-3.5 h-3.5 text-emerald-400" />
          ) : (
            <BookMarked className="w-3.5 h-3.5 text-blue-400" />
          )}
          <span>RIS (Zotero)</span>
        </button>

        {/* BibTeX */}
        <button
          onClick={() => handleExport('bibtex')}
          disabled={!!downloading}
          className="resend-btn-secondary text-xs py-1.5 px-3 flex-1 sm:flex-initial"
          title="Compatível com LaTeX / Overleaf"
        >
          {downloading === 'bibtex' ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin text-purple-400" />
          ) : successFmt === 'bibtex' ? (
            <Check className="w-3.5 h-3.5 text-emerald-400" />
          ) : (
            <Code2 className="w-3.5 h-3.5 text-purple-400" />
          )}
          <span>BibTeX (.bib)</span>
        </button>

        {/* CSV */}
        <button
          onClick={() => handleExport('csv')}
          disabled={!!downloading}
          className="resend-btn-secondary text-xs py-1.5 px-3 flex-1 sm:flex-initial"
          title="Exportar arquivo CSV com codificação UTF-8"
        >
          {downloading === 'csv' ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-400" />
          ) : successFmt === 'csv' ? (
            <Check className="w-3.5 h-3.5 text-emerald-400" />
          ) : (
            <FileText className="w-3.5 h-3.5 text-amber-400" />
          )}
          <span>CSV</span>
        </button>
      </div>
    </div>
  );
};
