### ScienceDirect (Elsevier ScienceDirect Search API)

- **Categoria / Domínio:** Multidisciplinar (Periódicos e livros científicos publicados pela Elsevier)
- **Tipo de Acesso:** Elsevier ScienceDirect Search API (REST JSON)
- **Autenticação:** Requer `X-ELS-APIKey` e convênio institucional via `https://dev.elsevier.com/`
- **URL Base / Endpoint:** `https://api.elsevier.com/content/search/scidir`
- **Formato de Retorno:** JSON

---

#### 1. Parâmetros de Consulta e Mapeamento de Campos

| Parâmetro da API | Tipo | Descrição | Equivalente no App |
| :--- | :--- | :--- | :--- |
| `query` | String | Expressão de busca (ex: `title-abs-key(...)` ou `pub-date > ...`) | `termo_busca` |
| `count` | Int | Quantidade de registros por página (máx: 25) | `page_size` / `max_por_base` |
| `start` | Int | Índice inicial de paginação (0-based) | `offset` |
| `httpAccept` | String | Formato de retorno (`application/json`) | `"application/json"` |

---

#### 2. Limites de Taxa e Diretrizes Éticas

- **Rate Limit:** Monitorado pelos cabeçalhos `X-RateLimit-Limit` e `X-RateLimit-Remaining`.
- **Acesso ao Texto Completo:** A API de busca retorna metadados e resumos; para recuperar o PDF completo via API (`/content/article/doi/...`), o IP de origem deve possuir assinatura institucional ativa de ScienceDirect.

---

#### 3. Exemplo de Requisição (Python / Requests)

```python
import os
import requests

api_key = os.getenv("ELSEVIER_API_KEY", "SUA_CHAVE_AQUI")
url = "https://api.elsevier.com/content/search/scidir"

headers = {
    "X-ELS-APIKey": api_key,
    "Accept": "application/json"
}

params = {
    "query": "title-abs-key(data science) and pub-date > 2022",
    "count": "20",
    "httpAccept": "application/json"
}

response = requests.get(url, params=params, headers=headers, timeout=20)
if response.status_code == 200:
    data = response.json()
    entries = data.get("search-results", {}).get("entry", [])
    print(f"Resultados obtidos: {len(entries)}")
```

---

#### 4. Amostra do Payload Bruto (JSON)

```json
{
  "search-results": {
    "opensearch:totalResults": "4520",
    "opensearch:startIndex": "0",
    "opensearch:itemsPerPage": "20",
    "entry": [
      {
        "dc:identifier": "doi:10.1016/j.artint.2024.103980",
        "dc:title": "Explainable Artificial Intelligence for Scientific Discovery",
        "authors": {
          "author": [
            { "$": "Carlos Silva" },
            { "$": "Maria Santos" }
          ]
        },
        "prism:publicationName": "Artificial Intelligence",
        "prism:coverDate": "2024-03-01",
        "prism:doi": "10.1016/j.artint.2024.103980",
        "link": [
          {
            "@ref": "scidir",
            "@href": "https://www.sciencedirect.com/science/article/pii/S000437022400015X"
          }
        ]
      }
    ]
  }
}
```

---

#### 5. Regra de De-Para (Campos Brutos -> Schema Padronizado)

- `Title` <- `entry.get('dc:title', 'Sem título')`
- `Link Pub` <- Link com `@ref == 'scidir'` ou fallback `f"https://doi.org/{doi}"`
- `Autor` <- Lista de autores concatenada a partir de `entry.get('authors', {}).get('author', [])`
- `Revista / Fonte` <- `entry.get('prism:publicationName', 'ScienceDirect')`
- `Ano` <- Primeiros 4 dígitos de `entry.get('prism:coverDate', '')`
- `Base` <- `"ScienceDirect"`
- `DOI` <- `entry.get('prism:doi', '')`
- `ID Origem` <- `entry.get('dc:identifier', '')`
