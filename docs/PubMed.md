## PubMed & PubMed Central (NCBI / National Library of Medicine)

- **Categoria:** Ciências Biomédicas, Saúde Pública, Medicina e Biotecnologia
- **Tipo de Acesso:** API REST Oficial NCBI E-utilities (esearch + esummary) com resolução integrada de PMCID/DOI
- **Autenticação:** Pública gratuita (sem chave: 3 req/s; com API Key NCBI: 10 req/s)
- **URL Endpoint de Busca:** `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi`
- **URL Endpoint de Resumo:** `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi`
- **Endpoint PMC ID Converter:** `https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/`
- **Formato de Retorno:** JSON (`retmode=json`)

---

#### 1. Parâmetros de Consulta (Esearch)
- `db`: `"pubmed"`
- `term`: Query com qualificadores MeSH (ex: `"machine learning"[Title/Abstract] AND ("2020"[pdat] : "2024"[pdat])`)
- `retmode`: `"json"`
- `retmax`: Quantidade de PMIDs a recuperar (ex: 20 a 100)
- `tool`: `"AcademicOmniSearch"`
- `email`: e-mail de contato do pesquisador

---

#### 2. Resolução de Identificadores (PMID $\rightarrow$ PMCID $\rightarrow$ DOI)
O endpoint `esummary.fcgi` já retorna a lista `articleids` contendo os múltiplos identificadores de cada artigo:
- `idtype == 'pubmed'` $\rightarrow$ `PMID`
- `idtype == 'pmc'` $\rightarrow$ `PMCID` (indica texto completo em acesso aberto no PubMed Central)
- `idtype == 'doi'` $\rightarrow$ `DOI` (Digital Object Identifier)

#### Priorização de Link:
1. Se `pmcid` existir $\rightarrow$ `https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/` (Acesso direto ao texto completo livre)
2. Se `doi` existir $\rightarrow$ `https://doi.org/{doi}` (Link canônico da editora)
3. Caso contrário $\rightarrow$ `https://pubmed.ncbi.nlm.nih.gov/{pmid}/` (Página do resumo no PubMed)

---

#### 3. Regra de De-Para (Schema Padronizado)
- `Title` <- `doc['title'].rstrip('.')`
- `Link Pub` <- Link priorizado (PMC Open Access > DOI > PubMed)
- `Autor` <- Autores unidos com `; ` via lista `doc['authors']`
- `Revista / Fonte` <- `doc.get('fulljournalname') or doc.get('source')`
- `Ano` <- Extraído de `doc['pubdate']` via regex `\b(19\d{2}|20\d{2})\b`
- `Base` <- `"PubMed"`
- `DOI` <- Extraído de `doc['articleids']` onde `idtype == 'doi'`
- `ID Origem` <- `f"PMID:{pmid}" + (f" | {pmcid}" if pmcid else "")`
