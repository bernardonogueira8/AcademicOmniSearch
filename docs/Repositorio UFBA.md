### 

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
