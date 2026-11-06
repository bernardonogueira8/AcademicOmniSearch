## ACM Digital Library

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