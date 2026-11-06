### BRAPCI (Base de Dados Referencial de Artigos de Periódicos em Ciência da Informação)

- **Categoria / Domínio:** Ciência da Informação, Biblioteconomia, Museologia e Gestão do Conhecimento
- **Tipo de Acesso:** API REST Oficial v5 (com fallback automático para API v1)
- **Autenticação:** Pública (não requer chave de API; exige inicialização de sessão com cookie `ci_session`)
- **URL Base / Endpoint Principal:** `https://cip.brapci.inf.br/api/brapci/search/v5`
- **URL Base / Endpoint Fallback:** `https://cip.brapci.inf.br/api/brapci/search/v1`
- **Formato de Retorno:** JSON

---

#### 1. Parâmetros de Consulta e Mapeamento de Campos (API v5)

| Parâmetro da API | Tipo | Descrição | Equivalente no App |
| :--- | :--- | :--- | :--- |
| `term` | String | Termo ou expressão de busca textual | `termo_busca` |
| `field` | String | Código do campo de busca (`FL`, `TI`, `KW`, `AU`, `AB`) | `campo_busca` |
| `year_start` | String | Ano inicial do recorte temporal | `ano_inicial` |
| `year_end` | String | Ano final do recorte temporal | `ano_final` |
| `offset` | String | **Limite total de resultados** recuperados em lote único | `max_por_base` / `page_size` |
| `collection` | String | Coleções (`JA,JE,EV,BK`) | Coleções completas |

> **Observação sobre `offset` na v5**: Ao contrário de APIs tradicionais de paginação onde `offset` representa o deslocamento (skip), na API v5 da BRAPCI o parâmetro `offset` determina a **quantidade total de registros retornados de uma só vez** (`offset="20"` retorna 20 registros; `offset="50"` retorna 50). Fazer chamadas diretas com o limite desejado evita loops rápidos que acionam proteção HTTP 403.

---

#### 2. Limites de Taxa, Sessão e Diretrizes Éticas

- **Sessão (`ci_session`)**: O backend Apache/CodeIgniter da UFPR exige que o cliente adquira o cookie de sessão `ci_session` através de uma requisição inicial à raiz `https://cip.brapci.inf.br/`.
- **Cabeçalhos Exigidos**:
  - `Referer: https://brapci.inf.br/`
  - `Origin: https://brapci.inf.br`
  - `Accept-Language: pt-BR,pt;q=0.9`
  - `User-Agent` com *Client Hints* (`Sec-Ch-Ua`).
- **Rate Limit**: Recomenda-se realizar uma única consulta direta por busca. Rajadas consecutivas em milissegundos podem ativar proteção de WAF/ModSecurity.

---

#### 3. Exemplo de Requisição (Python / Requests)

```python
import requests

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Referer": "https://brapci.inf.br/",
    "Origin": "https://brapci.inf.br",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
})

# 1. Estabelecer sessão e adquirir cookie ci_session
session.get("https://cip.brapci.inf.br/", timeout=5)

# 2. Executar busca direta com limite desejado
params = {
    "term": "inteligencia artificial",
    "offset": "20",
    "year_start": "2020",
    "year_end": "2024",
    "collection": "JA,JE,EV,BK",
    "field": "FL"
}
response = session.get("https://cip.brapci.inf.br/api/brapci/search/v5", params=params, timeout=20)
data = response.json()
works = data.get("works", [])
print(f"Total encontrado: {data.get('total')}, Recuperados: {len(works)}")
```

---

#### 4. Amostra do Payload Bruto (JSON)

```json
{
  "total": 340,
  "works": [
    {
      "id": "342738",
      "year": "2024",
      "type": "Article",
      "data": {
        "ID": "342738",
        "TITLE": "Potenciais aplicações de inteligência artificial no processo editorial de artigos científicos",
        "AUTHORS": "Silva, Bernardo; Santos, Maria",
        "JOURNAL": "Revista Brasileira de Biblioteconomia e Documentação",
        "LEGEND": "RBBD, v. 20, n. 1, 2024",
        "KEYWORDS": "Inteligência Artificial; Comunicação Científica; Editoração"
      }
    }
  ]
}
```

---

#### 5. Regra de De-Para (Campos Brutos -> Schema Padronizado)

- `Title` <- `data.get('TITLE')`
- `Link Pub` <- `f"https://brapci.inf.br/v/{work_id}"`
- `Autor` <- `data.get('AUTHORS')`
- `Revista / Fonte` <- `data.get('JOURNAL') or data.get('LEGEND')`
- `Ano` <- `str(work.get('year'))`
- `Base` <- `"BRAPCI"`
- `Palavras-Chave` <- `data.get('KEYWORDS', '')`
- `ID Origem` <- `str(work_id)`
