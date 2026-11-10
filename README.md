# AcademicOmniSearch: Multi-Database Academic Harvester

O **AcademicOmniSearch** é uma ferramenta de _Data Extraction_ e _Web Scraping_ projetada para apoiar pesquisadores, profissionais de Ciência da Informação e cientistas de dados na recuperação massiva e padronizada de metadados acadêmicos.

Inspirado na arquitetura do protótipo **ScraperCI**, o projeto expande a capacidade de busca para além da BRAPCI, integrando mecanismos modulares de automação de consultas às principais bases de dados nacionais e internacionais:

- **Periódicos CAPES** (Multidisciplinar / MEC-CAPES com Qualis & OpenAlex) _Funcionando_
- **PubMed** (Ciências da Saúde e Biomedicina) _Funcionando_
- **BRAPCI** (Ciência da Informação) _Em Andamento_
- **ACM Digital Library** (Ciência da Computação) _Em Andamento_
- **Scopus** (Multidisciplinar / Elsevier) _Em Andamento_
- **IEEE Xplore** (Engenharia Elétrica e Computação) _Não Iniciado_
- **Web of Science** _Não Iniciado_ 
- **ScienceDirect** _Não Iniciado_

## 🚀 Funcionalidades

- **Nova Interface Moderna (v2.0):** Dashboard SPA reativo construído em **React + Tailwind CSS** inspirado na estética **Resend** (dark-first OLED, alta performance, tipografia refinada e microinterações).
- **Orquestrador de Alta Vazão (FastAPI):** Backend assíncrono com streaming em tempo real via **Server-Sent Events (SSE)** para acompanhamento base a base, logs ao vivo e cancelamento sob demanda.
- **Seleção Multi-Base:** Seleção modular via dashboard para consultar uma ou múltiplas bases simultaneamente (CAPES, PubMed, BRAPCI, ACM, IEEE, Scopus).
- **Parametrização Flexível:** Busca por palavras-chave, título, autores, resumo ou texto completo.
- **Recorte Temporal:** Definição de janelas de tempo personalizadas (ano inicial e final).
- **Enriquecimento Cienciométrico:** Classificação Qualis (via SQLite local) e métricas de impacto/citação OpenAlex (FWCI e citações totais).
- **Deduplicação Inteligente:** Remoção automática de títulos duplicados entre bases distintas.
- **Exportação Bibliográfica Completa:** Download com 1 clique nos formatos **Excel (.xlsx)**, **RIS (.ris)** para Zotero/Mendeley, **BibTeX (.bib)** para LaTeX e **CSV (.csv)**.
- **Terminal de Execução Integrado:** Drawer de logs ao vivo com níveis de severidade, cópia rápida e diagnósticos detalhados.


## 🛠️ Tecnologias Utilizadas

- **Backend:** Python (>= 3.12 / 3.14), [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/)
- **Frontend Moderno:** [React 19](https://react.dev/), [Vite](https://vite.dev/), [Tailwind CSS v4](https://tailwindcss.com/), [Lucide React](https://lucide.dev/) (Design System Resend)
- **Gerenciador de Pacotes:** [uv](https://docs.astral.sh/uv/) / pip e npm
- **Extração & Requisições:** Requests, BeautifulSoup4, SSE (Server-Sent Events)
- **Manipulação de Dados:** Pandas, OpenPyXL, SQLite (Qualis)

## 📂 Estrutura do Repositório

```text
AcademicOmniSearch/
├── frontend/                     # Aplicação SPA moderna (React + Tailwind v4 + Vite)
│   ├── src/
│   │   ├── components/           # Componentes (Navbar, SearchBar, ResultsTable, etc.)
│   │   ├── types.ts              # Definições TypeScript
│   │   ├── App.tsx               # Componente principal com streaming SSE
│   │   └── index.css             # Design System Resend (Dark OLED)
│   ├── dist/                     # Build de produção servido pelo FastAPI
│   └── package.json
├── src/
│   ├── __init__.py               # Exportação e registro dos scrapers
│   ├── base.py                   # Classe base abstrata e Dataclass AcademicRecord
│   ├── capes_scraper.py          # Extrator do Portal CAPES com WAF bypass e enriquecimento
│   ├── qualis_service.py         # Consulta de classificação Qualis em SQLite local
│   ├── openalex_service.py       # Integração com API OpenAlex para citações e FWCI
│   ├── brapci_scraper.py         # Cliente oficial da API REST v5 da BRAPCI
│   ├── pubmed_scraper.py         # Cliente oficial da API NCBI E-utilities (PubMed)
│   ├── acm_scraper.py            # Parser HTML & cliente com tratamento de WAF para ACM
│   ├── ieee_scraper.py           # Integração com IEEE Xplore Search API
│   └── scopus_scraper.py         # Integração com Elsevier Scopus API
├── data/
│   └── qualis.db                 # Banco local de estratos Qualis da CAPES
├── utils/
│   ├── __init__.py               # Exportação dos utilitários
│   ├── config.py                 # Carregamento de .env, headers e constantes
│   ├── data_export.py            # Normalização de schemas e exportação Excel (.xlsx) / CSV
│   └── bibliographic_exporter.py # Exportação para formatos bibliográficos RIS e BibTeX
├── docs/
│   └── API.md                    # Template e especificações completas das APIs
├── main.py                       # Servidor unificado (FastAPI + SPA compilada)
├── server.py                     # API REST e endpoints SSE do FastAPI
├── app.py                        # Interface legado em Streamlit
├── pyproject.toml                # Especificação de dependências do projeto
├── .env                          # Variáveis de ambiente e chaves de API
├── .env.example                  # Modelo de variáveis de ambiente
├── .gitignore
└── README.md
```

---

## ⚙️ Pré-requisitos e Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/bernardonogueira8/AcademicOmniSearch.git
cd AcademicOmniSearch

# 2. Configure suas variáveis de ambiente
cp .env.example .env

# 3. Instale as dependências via uv (recomendado) ou pip
uv sync
```

---

## 🖥️ Como Executar

### Opção Recomendada: Servidor Unificado (Modern Web App)

Basta executar um único comando na raiz do projeto:

```bash
python main.py
# ou via uv:
uv run python main.py
```

O servidor unificado irá verificar o frontend compilado (gerando automaticamente se necessário) e disponibilizar a aplicação em:
- **Interface Web Moderna:** `http://localhost:8000`
- **Documentação Interativa Swagger:** `http://localhost:8000/docs`

### Desenvolvimento com Hot-Reload (Opcional)

Se desejar desenvolver o frontend com Vite HMR:
```bash
# Terminal 1 - Backend FastAPI
uv run uvicorn server:app --reload --port 8000

# Terminal 2 - Frontend Vite
cd frontend
npm run dev
# Acesse http://localhost:5173
```

### Interface Legado (Streamlit)

Caso deseje executar o painel anterior do Streamlit:
```bash
streamlit run app.py
```


## 📊 Estrutura dos Dados Gerados

O arquivo `.xlsx` (Excel) exportado possui o seguinte padrão tabular obrigatório:

| Campo             | Descrição                                         | Exemplo |
| :---------------- | :------------------------------------------------ | :--- |
| `Title`           | Título da publicação                              | Recuperação da Informação em Saúde |
| `Link Pub`        | Link direto / DOI para acesso ao documento        | `https://brapci.inf.br/v/324067` |
| `Autor`           | Autor(es) da obra separados por ponto-e-vírgula   | Soares, J. R.; Silva, P. N. |
| `Revista / Fonte` | Periódico, conferência ou evento de publicação    | Biblionline / SIGGRAPH |
| `Ano`             | Ano de publicação                                 | 2024 |
| `Base`            | Nome da base de origem                            | BRAPCI, PubMed, ACM |

_Campos auxiliares como `Resumo`, `Palavras-Chave`, `DOI` e `ID Origem` são preservados nas colunas subsequentes sempre que fornecidos pela fonte._

---

## 🛡️ Boas Práticas e Diretrizes Éticas

- **Respeito aos Servidores:** Requisições contam com pausas éticas (_polite delays_) e headers identificados (`User-Agent` e e-mail de contato para o NCBI).
- **Prioridade para APIs Oficiais:** Bases com APIs públicas (BRAPCI e PubMed) são consultadas via JSON estruturado, reduzindo tráfego e garantindo estabilidade.
- **Tratamento de WAF e Bloqueios:** Para bases que utilizam proteção Cloudflare/Akamai (como ACM Digital Library), o sistema possui mecanismo de leitura de dumps HTML locais (`app.html`), viabilizando a continuidade da pesquisa bibliométrica.
- **Destinação Científica:** O projeto destina-se estritamente à pesquisa acadêmica, mineração de textos para fins científicos e desenvolvimento de estudos bibliométricos.

---

## 📄 Licença

Distribuído sob a licença MIT. Consulte `LICENSE` para mais informações.
