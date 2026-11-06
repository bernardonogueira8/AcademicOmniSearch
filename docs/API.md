# AcademicOmniSearch: Guia de Especificação e Integração de APIs / Scrapers

Este documento define o **padrão oficial de especificação técnica** para a integração de novas fontes de dados acadêmicas no **AcademicOmniSearch**, além de documentar os endpoints, parâmetros e payloads das bases já mapeadas.

---

## 📋 Schema Padronizado de Saída (De-Para Obrigatório)

Independentemente da origem (API REST, GraphQL, E-utilities ou Web Scraping em HTML), todo coletor deve mapear seus dados para a seguinte estrutura tabular:

| Campo Oficial | Tipo | Obrigatório | Descrição | Exemplo |
| :--- | :--- | :--- | :--- | :--- |
| `Title` | String | Sim | Título completo da publicação | `"Recuperação em fontes de informação..."` |
| `Link Pub` | String | Sim | URL direta para o artigo ou DOI | `"https://brapci.inf.br/v/324067"` |
| `Autor` | String | Sim | Lista de autores separados por `; ` | `"Soares, J. R.; Silva, P. N."` |
| `Revista / Fonte` | String | Sim | Periódico, evento ou conferência | `"Biblionline"` ou `"SIGGRAPH '26"` |
| `Ano` | String | Sim | Ano de publicação (4 dígitos) | `"2024"` |
| `Base` | String | Sim | Nome padronizado da base de dados | `"BRAPCI"`, `"PubMed"`, `"ACM"` |
| `Resumo` | String | Não | Abstract ou resumo do documento | `"Este artigo analisa os métodos..."` |
| `Palavras-Chave` | String | Não | Termos-chave separados por `; ` | `"Sistemas de recuperação; Enfermagem"` |
| `DOI` | String | Não | Digital Object Identifier | `"10.1145/3799885.3816014"` |
| `ID Origem` | String | Não | Identificador interno da base | `"324067"` ou `"PMID:39738309"` |

---

## 📐 Template Padrão para Especificação de Novas Bases

Ao documentar uma nova base de dados, replique a estrutura abaixo:

```markdown
### [Nome da Base de Dados]

- **Categoria / Domínio:** (ex: Ciência da Computação, Multidisciplinar, Saúde)
- **Tipo de Acesso:** (API REST Oficial | E-utilities | GraphQL | HTML Scraping | Headless Browser / Playwright)
- **Autenticação:** (Pública sem chave | Requer API Key gratuita | Requer IP / Convênio institucional)
- **URL Base / Endpoint:** `https://...`
- **Formato de Retorno:** (JSON | XML | HTML)

#### 1. Parâmetros de Consulta e Mapeamento de Campos
| Parâmetro da API | Tipo | Descrição | Equivalente no App |
| :--- | :--- | :--- | :--- |
| `query` / `term` | String | Termo de busca | `termo_busca` |
| `field` | String | Qualificador de campo (Título, Resumo, etc.) | `campo_busca` |
| `year_start` | Int | Ano inicial | `ano_inicial` |
| `year_end` | Int | Ano final | `ano_final` |
| `offset` / `page` | Int | Paginação | `offset` |

#### 2. Limites de Taxa e Diretrizes Éticas
- **Rate Limit:** (ex: máximo 3 req/segundo)
- **Cabeçalhos Exigidos:** (ex: User-Agent com e-mail de contato)
- **Desafios Anti-Bot / WAF:** (ex: Cloudflare, Akamai, Captcha)

#### 3. Exemplo de Requisição (Python / Requests)
```python
import requests
# Código de exemplo funcional
```

#### 4. Amostra do Payload Bruto (JSON ou Snippet HTML)
```json
// Trecho de resposta bruta
```

#### 5. Regra de De-Para (Campos Brutos -> Schema Padronizado)
- `Title` <- `data['...']`
- `Link Pub` <- `f"https://.../{id}"`
- `Autor` <- `...`
- `Revista / Fonte` <- `...`
- `Ano` <- `...`
- `Base` <- `"Nome"`
```

---

## 🗂️ Bases Mapeadas e Implementadas

### 1. BRAPCI (Base de Dados Referencial de Artigos de Periódicos em Ciência da Informação)

- **Categoria:** Ciência da Informação, Biblioteconomia e Gestão do Conhecimento
- **Tipo de Acesso:** API REST Oficial v5
- **Autenticação:** Pública (não requer chave de API)
- **URL Endpoint:** `https://cip.brapci.inf.br/api/brapci/search/v5`
- **Formato de Retorno:** JSON

#### Parâmetros de Consulta
- `term`: Termo ou frase de pesquisa
- `offset`: Deslocamento da paginação (0, 10, 20, ...)
- `year_start`: Ano inicial (ex: `"2020"`)
- `year_end`: Ano final (ex: `"2026"`)
- `collection`: Coleções de publicações:
  - `JA`: Revistas Brasileiras
  - `JE`: Revistas Estrangeiras
  - `EV`: Anais de Eventos
  - `BK`: Livros e Capítulos
  - *Padrão:* `"JA,JE,EV,BK"`
- `field`: Código de campo de busca:
  - `FL`: Todos / Texto Completo
  - `TI`: Título
  - `KW`: Palavras-Chave
  - `AU`: Autor
  - `AB`: Resumo

#### Exemplo de Requisição
```python
import requests

url = "https://cip.brapci.inf.br/api/brapci/search/v5"
params = {
    "term": "recuperação da informação",
    "offset": "0",
    "year_start": "2020",
    "year_end": "2024",
    "collection": "JA,JE,EV,BK",
    "field": "FL"
}
headers = {"User-Agent": "AcademicOmniSearch/1.0"}
resp = requests.get(url, params=params, headers=headers, timeout=20)
data = resp.json()
```

#### Amostra de Retorno
```json
{
  "total": 10,
  "works": [
    {
      "id": "324067",
      "score": 8.217242,
      "type": "Article",
      "year": "2024",
      "data": {
        "ID": "324067",
        "JOURNAL": "Biblionline",
        "TITLE": "Recuperacao em fontes de informacao em saude: o portal BVS enfermagem",
        "AUTHORS": "Jordana Rabelo Soares; Patrícia Nascimento Silva",
        "KEYWORDS": "Sistemas de recuperação de informação; Fontes de informação"
      }
    }
  ]
}
```

#### Regra de De-Para
- `Title` <- `work['data']['TITLE']`
- `Link Pub` <- `f"https://brapci.inf.br/v/{work['id']}"`
- `Autor` <- `work['data']['AUTHORS']`
- `Revista / Fonte` <- `work['data'].get('JOURNAL') or work['data'].get('LEGEND')`
- `Ano` <- `work['year']`
- `Base` <- `"BRAPCI"`
- `Palavras-Chave` <- `work['data'].get('KEYWORDS')`
- `ID Origem` <- `work['id']`

---

### 2. PubMed (NCBI / National Library of Medicine)

- **Categoria:** Ciências Biomédicas, Saúde Pública, Medicina e Biotecnologia
- **Tipo de Acesso:** API REST Oficial E-utilities (esearch + esummary)
- **Autenticação:** Pública gratuita (sem chave: 3 req/s; com API Key NCBI: 10 req/s)
- **URL Endpoint de Busca:** `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi`
- **URL Endpoint de Resumo:** `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi`
- **Formato de Retorno:** JSON (`retmode=json`)

#### Parâmetros de Consulta (Esearch)
- `db`: `"pubmed"`
- `term`: Query com qualificadores MeSH (ex: `"machine learning"[Title/Abstract] AND ("2020"[pdat] : "2024"[pdat])`)
- `retmode`: `"json"`
- `retmax`: Quantidade de PMIDs a recuperar (ex: 50)
- `tool`: `"AcademicOmniSearch"`
- `email`: e-mail de contato do pesquisador

#### Regra de De-Para
- `Title` <- `doc['title'].rstrip('.')`
- `Link Pub` <- `f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"`
- `Autor` <- Autores unidos com `; ` via lista `doc['authors']`
- `Revista / Fonte` <- `doc.get('fulljournalname') or doc.get('source')`
- `Ano` <- Extraído de `doc['pubdate']` via regex `\b(19\d{2}|20\d{2})\b`
- `Base` <- `"PubMed"`
- `DOI` <- Extraído de `doc['articleids']` onde `idtype == 'doi'`
- `ID Origem` <- `pmid`

---

### 3. ACM Digital Library

- **Categoria:** Ciência da Computação, Engenharia de Software e Informática
- **Tipo de Acesso:** Web Scraping (HTML) ou Ingestão de Dumps Salvos
- **Autenticação:** Pública / Protegida por Cloudflare WAF (HTTP 403 para requests automatizados sem JavaScript)
- **URL Base:** `https://dl.acm.org/action/doSearch`
- **Formato de Retorno:** HTML (Document Object Model)

#### Seletores CSS Identificados (via `app.html`)
- **Container do Artigo:** `.issue-item`
- **Título & Link:** `.issue-item__title a` / `.hlFld-Title a` (Href contém `/doi/...`)
- **Autores:** `.loa a span` / `.hlFld-ContribAuthor a span`
- **Fonte / Conferência:** `.issue-item__detail .epub-section__title` ou `.issue-item__detail a:not(.issue-item__doi)`
- **Data / Ano:** `.bookPubDate` (atributo `data-title` ou texto interno)
- **Resumo:** `.issue-item__abstract, .abstract p`
- **DOI:** Extraído do link relativo `/doi/10.1145/...`

#### Regra de De-Para
- `Title` <- Texto do elemento `.issue-item__title a`
- `Link Pub` <- `f"https://dl.acm.org{href}"`
- `Autor` <- Lista de nomes de autores concatenados com `; `
- `Revista / Fonte` <- Título da conferência ou periódico extraído de `.issue-item__detail`
- `Ano` <- Ano regex `(19|20)\d{2}` extraído de `.bookPubDate`
- `Base` <- `"ACM Digital Library"`
- `Resumo` <- Texto limpo de `.issue-item__abstract`
- `DOI` <- Identificador DOI extraído

---

## 🚧 Fichas de Especificação para Próximas Bases (Em Desenvolvimento)

### 4. IEEE Xplore

- **Categoria:** Engenharia Elétrica, Automação, Telecomunicações e Ciência da Computação
- **Tipo de Acesso:** IEEE Xplore Search API (Oficial) ou Headless Browser
- **Autenticação:** Requer chave de API cadastrada em `https://developer.ieee.org/`
- **URL Endpoint:** `https://ieeexploreapi.ieee.org/api/v1/search/articles`
- **Formato de Retorno:** JSON
- **Campos Principais:**
  - `apikey`: Chave da API
  - `querytext`: Consulta textual
  - `start_year` / `end_year`: Intervalo temporal
  - `articles[]`: Lista de documentos com `title`, `authors`, `publication_title`, `publication_year`, `doi`.

### 5. Scopus (Elsevier)

- **Categoria:** Multidisciplinar
- **Tipo de Acesso:** Elsevier Developer API
- **Autenticação:** Requer `X-ELS-APIKey` e `X-ELS-Insttoken` institucional via `https://dev.elsevier.com/`
- **URL Endpoint:** `https://api.elsevier.com/content/search/scopus`
- **Formato de Retorno:** JSON
- **Campos Principais:**
  - `query`: Sintaxe de consulta Scopus (ex: `TITLE-ABS-KEY(...) AND PUBYEAR > ...`)
  - `search-results.entry[]`: `dc:title`, `dc:creator`, `prism:publicationName`, `prism:coverDate`, `prism:doi`.

### 6. ScienceDirect (Elsevier)

- **Categoria:** Multidisciplinar / Periódicos Elsevier
- **Tipo de Acesso:** Elsevier ScienceDirect Search API
- **Autenticação:** API Key Elsevier + Acesso Institucional
- **URL Endpoint:** `https://api.elsevier.com/content/search/scidir`
- **Formato de Retorno:** JSON

### 7. Web of Science (Clarivate)

- **Categoria:** Multidisciplinar / Índices de Citação
- **Tipo de Acesso:** Web of Science Starter / Expanded API
- **Autenticação:** Requer chave de API Clarivate (`X-ApiKey`)
- **URL Endpoint:** `https://api.clarivate.com/api/wos`
- **Formato de Retorno:** JSON / XML
