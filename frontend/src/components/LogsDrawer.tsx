import React, { useEffect, useRef } from 'react';
import type { LogMessage } from '../types';
import { Terminal, Trash2, X, Copy, Check } from 'lucide-react';

interface LogsDrawerProps {
  logs: LogMessage[];
  isOpen: boolean;
  onClose: () => void;
  onClear: () => void;
}

export const LogsDrawer: React.FC<LogsDrawerProps> = ({
  logs,
  isOpen,
  onClose,
  onClear,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);
  const [copied, setCopied] = React.useState(false);

  useEffect(() => {
    if (isOpen) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, isOpen]);

  if (!isOpen) return null;

  const copyLogs = () => {
    const text = logs
      .map((l) => `[${l.timestamp}] [${l.level}] ${l.base ? `[${l.base}] ` : ''}${l.message}`)
      .join('\n');
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-x-0 bottom-0 z-50 bg-black/95 border-t border-white/10 shadow-2xl backdrop-blur-xl max-h-96 flex flex-col transition-all">
      {/* Drawer Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/[0.08] bg-zinc-950/80">
        <div className="flex items-center gap-2 text-xs font-medium text-zinc-300">
          <Terminal className="w-4 h-4 text-emerald-400" />
          <span>Terminal de Execução dos Coletores</span>
          <span className="text-[10px] px-1.5 py-0.2 rounded bg-zinc-800 text-zinc-400 font-mono">
            {logs.length} eventos
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={copyLogs}
            className="p-1.5 rounded text-zinc-400 hover:text-white hover:bg-zinc-800 text-xs flex items-center gap-1 transition-colors"
            title="Copiar Logs"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={onClear}
            className="p-1.5 rounded text-zinc-400 hover:text-rose-400 hover:bg-zinc-800 text-xs transition-colors"
            title="Limpar Logs"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onClose}
            className="p-1.5 rounded text-zinc-400 hover:text-white hover:bg-zinc-800 text-xs transition-colors"
            title="Fechar"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Logs Viewport */}
      <div className="p-4 overflow-y-auto space-y-1 font-mono text-[11px] leading-relaxed select-text">
        {logs.length === 0 ? (
          <div className="text-zinc-600 italic py-6 text-center">
            Nenhum evento registrado ainda. Inicie uma busca para acompanhar os logs em tempo real.
          </div>
        ) : (
          logs.map((log) => {
            let levelColor = 'text-zinc-400';
            if (log.level === 'SUCCESS') levelColor = 'text-emerald-400 font-medium';
            if (log.level === 'WARNING') levelColor = 'text-amber-400';
            if (log.level === 'ERROR') levelColor = 'text-rose-400 font-medium';

            return (
              <div key={log.id} className="flex items-start gap-2 hover:bg-white/[0.02] px-1 py-0.5 rounded">
                <span className="text-zinc-600 shrink-0">[{log.timestamp}]</span>
                {log.base && (
                  <span className="text-cyan-400/80 shrink-0">[{log.base}]</span>
                )}
                <span className={`${levelColor} shrink-0`}>[{log.level}]</span>
                <span className="text-zinc-300 break-all">{log.message}</span>
              </div>
            );
          })
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};
