# AcademicOmniSearch: Multi-Database Academic Harvester

O **AcademicOmniSearch** é uma ferramenta de _Data Extraction_ e _Web Scraping_ projetada para apoiar pesquisadores, profissionais de Ciência da Informação e cientistas de dados na recuperação massiva e padronizada de metadados acadêmicos.

Inspirado na arquitetura do protótipo **ScraperCI**, o projeto expande a capacidade de busca para além da BRAPCI, integrando mecanismos modulares de automação de consultas às principais bases de dados nacionais e internacionais:

- **PubMed** (Ciências da Saúde e Biomedicina) _Funcionando_
- **BRAPCI** (Ciência da Informação) _Em Andamento_
- **ACM Digital Library** (Ciência da Computação) _Em Andamento_
- **Scopus** (Multidisciplinar / Elsevier) _Em Andamento_
- **IEEE Xplore** (Engenharia Elétrica e Computação) _Não Iniciado_
- **Web of Science** _Não Iniciado_ 
- **ScienceDirect** _Não Iniciado_

## 🚀 Funcionalidades

- **Seleção Multi-Base:** Seleção modular via dashboard para consultar uma ou múltiplas bases simultaneamente.
- **Parametrização Flexível:** Busca por palavras-chave, título, autores, resumo ou texto completo.
- **Recorte Temporal:** Definição de janelas de tempo personalizadas (ano inicial e final).
- **Deduplicação Inteligente:** Remoção automática de títulos duplicados entre bases distintas.
- **Exportação Padronizada:** Download direto dos metadados extraídos em arquivo `.xlsx`.
- **Interface Interativa:** Dashboard web responsivo construído em Streamlit com métricas agregadas da busca.


## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python (>= 3.10)
- **Gerenciador de Pacotes:** [uv](https://docs.astral.sh/uv/) / pip
- **Interface Web:** [Streamlit](https://streamlit.io/)
- **Extração & Requisições:** Requests, BeautifulSoup4
- **Manipulação de Dados:** Pandas

## 📂 Estrutura do Repositório

```text
AcademicOmniSearch/
├── src/
│   ├── __init__.py           # Exportação e registro dos scrapers
│   ├── base.py               # Classe base abstrata e Dataclass AcademicRecord
│   ├── brapci_scraper.py     # Cliente oficial da API REST v5 da BRAPCI
│   ├── pubmed_scraper.py     # Cliente oficial da API NCBI E-utilities (PubMed)
│   ├── acm_scraper.py        # Parser HTML & cliente com tratamento de WAF para ACM
│   ├── ieee_scraper.py       # Integração com IEEE Xplore Search API
│   └── scopus_scraper.py     # Integração com Elsevier Scopus API
├── utils/
│   ├── __init__.py           # Exportação dos utilitários
│   ├── config.py             # Configurações globais, headers e colunas padrão
│   └── data_export.py        # Normalização de schemas, métricas e exportação Excel (.xlsx)
├── docs/
│   └── API.md                # Template e especificações completas das APIs
├── app.py                    # Aplicação Streamlit com orquestração multi-base
├── pyproject.toml            # Especificação de dependências do projeto
├── .gitignore
└── README.md
```

---

## ⚙️ Pré-requisitos e Instalação

### Opção 1: Usando `uv` (Recomendado - Ultra Rápido)

```bash
# Clone o repositório
git clone https://github.com/bernardonogueira8/AcademicOmniSearch.git
cd AcademicOmniSearch

# Instale o ambiente e sincronize as dependências
uv sync

# Execute o aplicativo Streamlit via uv
uv run streamlit run app.py
```

### Opção 2: Usando `pip` tradicional e ambiente virtual

```bash
# Clone o repositório
git clone https://github.com/bernardonogueira8/AcademicOmniSearch.git
cd AcademicOmniSearch

# Crie e ative o ambiente virtual
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

# Instale o projeto
pip install .

# Execute o Streamlit
streamlit run app.py
```

## 🖥️ Como Executar

A partir da raiz do projeto, execute:

```bash
streamlit run app.py
```

Acesse localmente em seu navegador:
`http://localhost:8501`


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
