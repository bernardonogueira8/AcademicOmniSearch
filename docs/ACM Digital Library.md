### ACM Digital Library (Association for Computing Machinery)

- **Categoria / Domínio:** Ciência da Computação, Engenharia de Software, Redes e Informática
- **Tipo de Acesso:** HTML Web Scraping / Parsing de Dumps HTML salvos / Automação Headless Browser (Playwright)
- **Autenticação:** Acesso público; protegido por Cloudflare WAF e desafios JavaScript anti-bot (retorna HTTP 403/503 em requisições automáticas não-navegador)
- **URL Base / Endpoint de Busca:** `https://dl.acm.org/action/doSearch`
- **Formato de Retorno:** HTML (Document Object Model)

---

#### 1. Parâmetros de Consulta e Mapeamento de Campos

| Parâmetro HTTP | Tipo | Descrição | Equivalente no App |
| :--- | :--- | :--- | :--- |
| `AllField` | String | Busca textual em todos os campos | `termo_busca` (quando campo for "Todos") |
| `Title` | String | Busca específica no título do trabalho | `campo_busca` = "Título" |
| `ContribAuthor` | String | Busca por nome de autores | `campo_busca` = "Autores" |
| `Keyword` | String | Busca por palavras-chave indexadas | `campo_busca` = "Palavras-Chave" |
| `Abstract` | String | Busca no resumo da publicação | `campo_busca` = "Resumo" |
| `AfterYear` | String | Ano inicial do intervalo temporal | `ano_inicial` |
| `BeforeYear` | String | Ano final do intervalo temporal | `ano_final` |
| `pageSize` | String | Quantidade de itens por página | `page_size` / `max_por_base` |

---

#### 2. Limites de Taxa e Mitigação de Proteção WAF/Cloudflare

- **Proteção Cloudflare:** A ACM Digital Library emprega Cloudflare WAF ativo. Requisições puras via bibliotecas HTTP padrão (`requests`, `urllib`) frequentemente recebem **HTTP 403 Forbidden** ou **HTTP 503 Service Unavailable** com páginas de desafio (*Turnstile* ou *Challenge*).
- **Estratégias Suportadas no Projeto:**
  1. **Ingestão de Dump HTML Salvo**: O pesquisador navega na ACM no browser, salva o arquivo de resultados como `test/app.html` ou `app.html`, e o módulo [src/acm_scraper.py](file:///c:/Dev/Projeto%20de%20scrapy/AcademicOmniSearch/src/acm_scraper.py) extrai os metadados localmente de forma instantânea e determinística.
  2. **Headless Browser**: Alternativa com Playwright/Puppeteer emulando o contexto de um navegador real para contornar os desafios de JavaScript.

---

#### 3. Seletores CSS Mapeados no HTML da ACM

- **Container do Artigo:** `.issue-item`
- **Título & Link:** `.issue-item__title a` ou `.hlFld-Title a` (atributo `href` contém `/doi/...`)
- **Autores:** `.loa a span` ou `.hlFld-ContribAuthor a span`
- **Fonte / Conferência:** `.issue-item__detail .epub-section__title` ou `.issue-item__detail a:not(.issue-item__doi)`
- **Data / Ano:** `.bookPubDate` (atributo `data-title` ou texto formatado)
- **Resumo:** `.issue-item__abstract, .abstract p`
- **DOI:** Extraído da URL relativa `/doi/10.1145/...`

---

#### 4. Exemplo de Extração com BeautifulSoup (Python)

```python
from bs4 import BeautifulSoup
import re

html_content = open("test/app.html", "r", encoding="utf-8").read()
soup = BeautifulSoup(html_content, "html.parser")
articles = soup.select(".issue-item")

records = []
for item in articles:
    title_tag = item.select_one(".issue-item__title a, .hlFld-Title a")
    if not title_tag:
        continue
    title = title_tag.get_text(strip=True)
    rel_link = title_tag.get("href", "")
    link_pub = f"https://dl.acm.org{rel_link}" if rel_link.startswith("/") else rel_link
    
    author_tags = item.select(".loa a span, .hlFld-ContribAuthor a span")
    authors = "; ".join([a.get_text(strip=True) for a in author_tags]) if author_tags else "Autor não informado"
    
    date_tag = item.select_one(".bookPubDate")
    date_str = date_tag.get_text(strip=True) if date_tag else ""
    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", date_str)
    year = year_match.group(1) if year_match else "Não informado"
    
    source_tag = item.select_one(".issue-item__detail .epub-section__title")
    source = source_tag.get_text(strip=True) if source_tag else "ACM Digital Library"
```

---

#### 5. Regra de De-Para (Campos Brutos -> Schema Padronizado)

- `Title` <- Texto do elemento `.issue-item__title a`
- `Link Pub` <- `f"https://dl.acm.org{href}"`
- `Autor` <- Nomes de autores em `.loa a span` concatenados por `; `
- `Revista / Fonte` <- Título da conferência/periódico em `.issue-item__detail`
- `Ano` <- Ano de 4 dígitos regex extraído de `.bookPubDate`
- `Base` <- `"ACM Digital Library"`
- `Resumo` <- Texto limpo de `.issue-item__abstract`
- `DOI` <- Identificador extraído do padrão `10.1145/...`
- `ID Origem` <- DOI ou link relativo do trabalho
