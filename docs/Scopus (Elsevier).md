## Scopus (Elsevier)

- **Categoria:** Multidisciplinar
- **Tipo de Acesso:** Elsevier Developer API
- **Autenticação:** Requer `X-ELS-APIKey` e `X-ELS-Insttoken` institucional via `https://dev.elsevier.com/`
- **URL Endpoint:** `https://api.elsevier.com/content/search/scopus`
- **Formato de Retorno:** JSON
- **Campos Principais:**
  - `query`: Sintaxe de consulta Scopus (ex: `TITLE-ABS-KEY(...) AND PUBYEAR > ...`)
  - `search-results.entry[]`: `dc:title`, `dc:creator`, `prism:publicationName`, `prism:coverDate`, `prism:doi`.