export interface AcademicRecord {
  id?: string;
  Title: string;
  "Link Pub"?: string;
  Autor?: string;
  "Revista / Fonte"?: string;
  Ano?: string | number;
  Base: string;
  Resumo?: string;
  "Palavras-Chave"?: string;
  DOI?: string;
  "ID Origem"?: string;
  ISSN?: string;

  // Cienciometria & Qualis
  qualis_estrato?: string;
  qualis_area?: string;
  cited_by_count?: number;
  fwci?: number;
  is_open_access?: boolean;
  oa_status?: string;

  // Texto Completo (Open Access PDF)
  pdf_url?: string;

  // Workflow de Triagem PRISMA
  screening_status?: 'pendente' | 'incluido' | 'excluido' | 'duvida';
  screening_reason?: string;
  screening_notes?: string;
  tags?: string[];

  [key: string]: any;
}

export interface BaseInfo {
  id: string;
  name: string;
  description: string;
  category: string;
  status: "ready" | "requires_key" | "error";
  badge: string;
  requires_key: boolean;
  has_key: boolean;
  note: string;
}

export interface SearchMetrics {
  total_records: number;
  bases_count: Record<string, number>;
  years_range: string;
  top_journals: Record<string, number>;
}

export interface PrismaStats {
  records_identified: number;
  duplicates_removed: number;
  records_screened: number;
  records_pending: number;
  records_excluded: number;
  records_uncertain: number;
  records_included: number;
}

export interface SearchSession {
  id: string;
  query: string;
  year_start: number;
  year_end: number;
  field: string;
  bases: string[];
  total_raw: number;
  total_dedup: number;
  created_at: string;
}

export interface LogMessage {
  id: string;
  timestamp: string;
  base?: string;
  message: string;
  level: "INFO" | "SUCCESS" | "WARNING" | "ERROR";
}
