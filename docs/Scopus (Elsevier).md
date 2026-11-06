### Scopus (Elsevier Scopus Search API)

- **Categoria / Domínio:** Multidisciplinar (Ciências Exatas, Saúde, Sociais e Humanidades)
- **Tipo de Acesso:** Elsevier Developer API (REST JSON)
- **Autenticação:** Requer `X-ELS-APIKey` (e opcionalmente `X-ELS-Insttoken` institucional) cadastrados em `https://dev.elsevier.com/`
- **URL Base / Endpoint:** `https://api.elsevier.com/content/search/scopus`
- **Formato de Retorno:** JSON

---

#### 1. Parâmetros de Consulta e Mapeamento de Campos

| Parâmetro da API | Tipo | Descrição | Equivalente no App |
| :--- | :--- | :--- | :--- |
| `query` | String | Expressão com campos Scopus (ex: `TITLE-ABS-KEY(...)`) | `termo_busca` / `campo_busca` |
| `count` | Int | Quantidade de registros por requisição (máx: 25) | `page_size` / `max_por_base` |
| `start` | Int | Deslocamento de paginação (0-based) | `offset` |
| `view` | String | Nível de detalhe dos metadados (`STANDARD`, `COMPLETE`) | `"STANDARD"` |
| `httpAccept` | String | Formato de conteúdo (`application/json`) | `"application/json"` |

---

#### 2. Limites de Taxa e Diretrizes Éticas

- **Rate Limit:** Varia conforme o nível da chave (contas não-institucionais: até 20.000 requisições/semana; cotas por segundo monitoradas pelo header `X-RateLimit-Reset`).
- **Autenticação:** A chave de API deve ser passada no cabeçalho HTTP `X-ELS-APIKey`. Se estiver em rede universitária conveniada, passar também `X-ELS-Insttoken`.

---

#### 3. Exemplo de Requisição (Python / Requests)

```python
import os
import requests

api_key = os.getenv("SCOPUS_API_KEY", "SUA_CHAVE_AQUI")
inst_token = os.getenv("ELSEVIER_INST_TOKEN", "")

url = "https://api.elsevier.com/content/search/scopus"
headers = {
    "X-ELS-APIKey": api_key,
    "Accept": "application/json"
}
if inst_token:
    headers["X-ELS-Insttoken"] = inst_token

params = {
    "query": "TITLE-ABS-KEY(artificial intelligence) AND PUBYEAR > 2021",
    "count": "20",
    "start": "0",
    "httpAccept": "application/json"
}

response = requests.get(url, params=params, headers=headers, timeout=20)
if response.status_code == 200:
    data = response.json()
    entries = data.get("search-results", {}).get("entry", [])
    print(f"Total encontrado: {data.get('search-results', {}).get('opensearch:totalResults')}")
```

---

#### 4. Amostra do Payload Bruto (JSON)

```json
{
  "search-results": {
    "opensearch:totalResults": "18420",
    "opensearch:startIndex": "0",
    "opensearch:itemsPerPage": "20",
    "entry": [
      {
        "dc:identifier": "SCOPUS_ID:85123456789",
        "dc:title": "Artificial Intelligence in Medical Imaging: A Comprehensive Review",
        "dc:creator": "Silva, B.",
        "prism:publicationName": "IEEE Transactions on Medical Imaging",
        "prism:coverDate": "2024-05-15",
        "prism:doi": "10.1109/TMI.2024.1234567",
        "link": [
          {
            "@ref": "scopus",
            "@href": "https://www.scopus.com/inward/record.uri?partnerID=HzOxMe3b&scp=85123456789"
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
- `Link Pub` <- Link com `@ref == 'scopus'` ou fallback para `f"https://doi.org/{doi}"`
- `Autor` <- `entry.get('dc:creator', 'Autor não informado')`
- `Revista / Fonte` <- `entry.get('prism:publicationName', 'Scopus Source')`
- `Ano` <- Primeiros 4 dígitos de `entry.get('prism:coverDate', '')`
- `Base` <- `"Scopus"`
- `DOI` <- `entry.get('prism:doi', '')`
- `ID Origem` <- `entry.get('dc:identifier', '')`
