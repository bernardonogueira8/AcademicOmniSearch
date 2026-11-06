## PubMed (NCBI / National Library of Medicine)

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
