### Web of Science (Clarivate WoS Starter / Expanded API)

- **Categoria / Domínio:** Multidisciplinar (Ciências Naturais, Exatas, Sociais, Artes e Humanidades) e Índices de Citação
- **Tipo de Acesso:** Clarivate Developer API (REST JSON)
- **Autenticação:** Requer chave de API institucional (`X-ApiKey`) cadastrada no portal `https://developer.clarivate.com/`
- **URL Base / Endpoint Principal:** `https://api.clarivate.com/apis/wos-starter/v1/documents`
- **URL Base / Endpoint Expandido:** `https://api.clarivate.com/api/wos`
- **Formato de Retorno:** JSON

---

#### 1. Parâmetros de Consulta e Mapeamento de Campos (WoS Starter API)

| Parâmetro da API | Tipo | Descrição | Equivalente no App |
| :--- | :--- | :--- | :--- |
| `q` | String | Expressão de busca com campos WoS (ex: `TS=(artificial intelligence) AND PY=(2020-2024)`) | `termo_busca` / `campo_busca` |
| `limit` | Int | Quantidade de registros por página (máx: 50 na Starter) | `max_por_base` / `page_size` |
| `page` | Int | Número da página (1-based) | `(offset // limit) + 1` |
| `db` | String | Base de dados alvo (`WOS`, `BIOABS`, `MEDLINE`, etc.) | `"WOS"` |
| `sortField` | String | Critério de ordenação (`RS+D` relevância, `PY+D` ano) | `"PY+D"` |

##### Qualificadores de Campo mais Comuns:
- `TS`: Tópico (Título, Resumo, Palavras-Chave do autor e Keywords Plus)
- `TI`: Título do documento
- `AU`: Autor
- `SO`: Nome da publicação (periódico/conferência)
- `PY`: Ano de publicação

---

#### 2. Limites de Taxa e Diretrizes Éticas

- **Rate Limit:** 2 a 5 requisições por segundo (conforme o plano de assinatura institucional); cotas de requisições mensais monitoradas no Developer Portal.
- **Cabeçalhos Exigidos:**
  - `X-ApiKey: SUA_CHAVE_AQUI`
  - `Accept: application/json`
  - `User-Agent: AcademicOmniSearch/1.0`
- **Acesso ao Texto Completo:** O Web of Science indexa citações e metadados. Links de acesso aberto utilizam Open Access links ou DOI via Unpaywall.

---

#### 3. Exemplo de Requisição (Python / Requests)

```python
import os
import requests

api_key = os.getenv("WOS_API_KEY", "SUA_CHAVE_AQUI")
url = "https://api.clarivate.com/apis/wos-starter/v1/documents"

headers = {
    "X-ApiKey": api_key,
    "Accept": "application/json",
    "User-Agent": "AcademicOmniSearch/1.0"
}

params = {
    "q": 'TS=("deep learning") AND PY=(2022-2024)',
    "limit": 20,
    "page": 1,
    "db": "WOS",
    "sortField": "PY+D"
}

response = requests.get(url, params=params, headers=headers, timeout=20)
if response.status_code == 200:
    data = response.json()
    hits = data.get("hits", [])
    print(f"Total encontrado: {data.get('metadata', {}).get('total')}")
```

---

#### 4. Amostra do Payload Bruto (JSON)

```json
{
  "metadata": {
    "total": 4510,
    "page": 1,
    "limit": 20
  },
  "hits": [
    {
      "uid": "WOS:000987654300001",
      "title": "Explainable Artificial Intelligence for Clinical Decision Support Systems",
      "types": ["Article"],
      "source": {
        "sourceTitle": "Nature Biomedical Engineering",
        "publishYear": 2024,
        "volume": "8",
        "issue": "3"
      },
      "names": {
        "authors": [
          { "displayName": "Smith, John", "wosStandard": "Smith, J" },
          { "displayName": "Silva, Bernardo", "wosStandard": "Silva, B" }
        ]
      },
      "identifiers": {
        "doi": "10.1038/s41551-024-00123-x"
      },
      "links": {
        "record": "https://www.webofscience.com/wos/woscc/full-record/WOS:000987654300001"
      }
    }
  ]
}
```

---

#### 5. Regra de De-Para (Campos Brutos -> Schema Padronizado)

- `Title` <- `hit.get('title', 'Sem título')`
- `Link Pub` <- `f"https://doi.org/{doi}"` se DOI existir, senão `hit.get('links', {}).get('record')`
- `Autor` <- Lista de `author['displayName']` concatenados por `; `
- `Revista / Fonte` <- `hit.get('source', {}).get('sourceTitle', 'Web of Science')`
- `Ano` <- `str(hit.get('source', {}).get('publishYear', ''))`
- `Base` <- `"Web of Science"`
- `DOI` <- `hit.get('identifiers', {}).get('doi', '')`
- `ID Origem` <- `hit.get('uid', '')`
