"""
Scraper / Cliente de API para a BRAPCI (Base de Dados Referencial de Artigos de Periódicos em Ciência da Informação).
Utiliza a API oficial v5 JSON (https://cip.brapci.inf.br/api/brapci/search/v5).
"""

from typing import List, Dict, Any, Optional
import requests
import logging
from src.base import BaseScraper, AcademicRecord
from utils.config import DEFAULT_HEADERS, DEFAULT_TIMEOUT

logger = logging.getLogger(__name__)

class BrapciScraper(BaseScraper):
    """
    Cliente da API v5 da BRAPCI.
    """

    BASE_URL = "https://cip.brapci.inf.br/api/brapci/search/v5"

    # Mapeamento amigável de campos para os códigos da API v5
    FIELD_MAP = {
        "todos": "FL",
        "all": "FL",
        "palavras-chave": "KW",
        "keywords": "KW",
        "autores": "AU",
        "author": "AU",
        "título": "TI",
        "titulo": "TI",
        "title": "TI",
        "resumo": "AB",
        "abstract": "AB",
        "texto completo": "FL",
        "text": "FL",
    }

    # Coleções disponíveis na BRAPCI:
    # JA = Revistas Brasileiras, JE = Revistas Estrangeiras, EV = Anais de Eventos, BK = Livros e Capítulos
    DEFAULT_COLLECTIONS = "JA,JE,EV,BK"

    def __init__(self, max_por_base: Optional[int] = None, page_size: Optional[int] = None):
        super().__init__(name="BRAPCI", is_api=True, requires_auth=False)
        self.page_size = max_por_base if max_por_base is not None else (page_size if page_size is not None else 20)
        self.max_por_base = self.page_size

    def search(
        self,
        query: str,
        year_start: int,
        year_end: int,
        field: str = "Todos",
        max_results: Optional[int] = None,
        max_por_base: Optional[int] = None,
        page_size: Optional[int] = None,
        collection: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Executa a busca direta na API v5 da BRAPCI e formata os resultados.
        Na API v5 da BRAPCI, o parâmetro 'offset' define a quantidade total desejada (limite).
        Uma única requisição otimizada evita disparos múltiplos em loop e bloqueios de WAF (HTTP 403).
        """
        self.validate_years(year_start, year_end)
        
        if not query or not query.strip():
            return []

        # Determina a quantidade de registros solicitada
        target_limit = (
            max_por_base
            if max_por_base is not None
            else (page_size if page_size is not None else (max_results if max_results is not None else self.page_size))
        )
        target_limit = max(1, int(target_limit))

        field_code = self.FIELD_MAP.get(field.strip().lower(), "FL")
        collections_param = collection or self.DEFAULT_COLLECTIONS

        session = requests.Session()
        session.headers.update(DEFAULT_HEADERS)
        session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://brapci.inf.br/",
            "Origin": "https://brapci.inf.br",
            "Sec-Ch-Ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        })

        self.logs = []
        self.log(f"Iniciando busca por '{query}' (Janela: {year_start}-{year_end}, Campo: {field}, Limite: {target_limit})")

        # Inicialização suave de sessão na raiz da CIP para adquirir o cookie 'ci_session'
        try:
            r_init = session.get("https://cip.brapci.inf.br/", timeout=5)
            cookies_acquired = list(session.cookies.keys())
            self.log(f"Priming de sessão em https://cip.brapci.inf.br/ -> Status: {r_init.status_code}, Cookies: {cookies_acquired}")
        except Exception as e_init:
            self.log(f"Aviso ao inicializar sessão em https://cip.brapci.inf.br/: {e_init}", level="WARNING")

        params = {
            "term": query.strip(),
            "offset": str(target_limit),
            "year_start": str(year_start),
            "year_end": str(year_end),
            "collection": collections_param,
            "field": field_code
        }

        records: List[Dict[str, Any]] = []

        try:
            self.log(f"Requisitando API v5: {self.BASE_URL} com params: {params}")
            response = session.get(self.BASE_URL, params=params, timeout=DEFAULT_TIMEOUT)
            
            # Se a API v5 retornar 403 ou erro de WAF, registra detalhe e executa fallback para a API v1
            if response.status_code == 403 or response.status_code != 200:
                body_preview = response.text[:250].replace("\n", " ").strip()
                headers_summary = f"Server={response.headers.get('Server', 'N/A')}, Content-Type={response.headers.get('Content-Type', 'N/A')}"
                self.log(
                    f"AVISO: API v5 retornou Status {response.status_code} ({response.reason}). Headers: [{headers_summary}]. Resposta: {body_preview}",
                    level="WARNING"
                )
                self.log("Tentando endpoint alternativo fallback API v1...")
                
                v1_url = "https://cip.brapci.inf.br/api/brapci/search/v1"
                v1_params = {
                    "q": query.strip(),
                    "offset": str(target_limit)
                }
                self.log(f"Requisitando API v1: {v1_url} com params: {v1_params}")
                response = session.get(v1_url, params=v1_params, timeout=DEFAULT_TIMEOUT)

            if response.status_code != 200:
                body_err = response.text[:250].replace("\n", " ").strip()
                self.log(f"ERRO: BRAPCI API retornou status HTTP {response.status_code} ({response.reason}). Resposta: {body_err}", level="ERROR")
                self.last_status = f"Erro HTTP {response.status_code}"
                return []

            try:
                payload = response.json()
            except Exception as e_json:
                body_raw = response.text[:250].replace("\n", " ").strip()
                self.log(f"ERRO: Resposta não pôde ser decodificada como JSON: {e_json}. Conteúdo: {body_raw}", level="ERROR")
                self.last_status = "Erro JSON"
                return []

            if not isinstance(payload, dict):
                self.log(f"ERRO: Payload retornado não é um objeto JSON válido (tipo {type(payload)}).", level="ERROR")
                self.last_status = "Formato inválido"
                return []

            works = payload.get("works", [])
            total_reported = payload.get("total", len(works))
            self.log(f"Resposta recebida com sucesso: total reportado {total_reported}, artigos na lista: {len(works)}")

            for work in works[:target_limit]:
                data = work.get("data", {})
                work_id = str(work.get("id") or data.get("ID", "")).strip()
                
                title = data.get("TITLE") or "Sem título"
                authors = data.get("AUTHORS") or "Autor não informado"
                journal = data.get("JOURNAL") or data.get("LEGEND") or "Revista não informada"
                year = str(work.get("year") or "").strip()
                keywords = data.get("KEYWORDS") or ""
                link = f"https://brapci.inf.br/v/{work_id}" if work_id else ""

                record = AcademicRecord(
                    title=title.strip(),
                    link_pub=link,
                    autor=authors.strip(),
                    revista_fonte=journal.strip(),
                    ano=year,
                    base=self.name,
                    palavras_chave=keywords.strip(),
                    id_origem=work_id
                )
                records.append(record.to_dict())

            self.last_status = f"Sucesso: {len(records)} registros"
            self.log(f"Processamento concluído: {len(records)} artigos catalogados.")

        except requests.exceptions.Timeout:
            self.log(f"ERRO: Timeout excedido ({DEFAULT_TIMEOUT}s) ao consultar servidor da BRAPCI.", level="ERROR")
            self.last_status = "Timeout"
        except requests.exceptions.ConnectionError as e_conn:
            self.log(f"ERRO: Falha de conexão de rede com BRAPCI: {e_conn}", level="ERROR")
            self.last_status = "Erro de Conexão"
        except Exception as e:
            self.log(f"ERRO inesperado ao consultar BRAPCI: {type(e).__name__}: {e}", level="ERROR")
            self.last_status = f"Erro {type(e).__name__}"

        return records
