### IEEE Xplore (IEEE Xplore Search API)

- **Categoria / Domínio:** Engenharia Elétrica, Automação, Telecomunicações e Ciência da Computação
- **Tipo de Acesso:** IEEE Xplore Search API (Oficial REST) ou Headless Browser (Playwright)
- **Autenticação:** Requer chave de API oficial cadastrada no portal `https://developer.ieee.org/`
- **URL Base / Endpoint:** `https://ieeexploreapi.ieee.org/api/v1/search/articles`
- **Formato de Retorno:** JSON

---

#### 1. Parâmetros de Consulta e Mapeamento de Campos

| Parâmetro da API | Tipo | Descrição | Equivalente no App |
| :--- | :--- | :--- | :--- |
| `apikey` | String | Chave de autenticação da aplicação | `IEEE_API_KEY` (.env / Secrets) |
| `querytext` | String | Termo ou expressão de busca booleana | `termo_busca` |
| `start_year` | String | Ano inicial do recorte temporal | `ano_inicial` |
| `end_year` | String | Ano final do recorte temporal | `ano_final` |
| `max_records` | String | Quantidade de registros por página (máx: 100) | `page_size` / `max_por_base` |
| `start_record` | String | Posição inicial para paginação (1-based) | `offset + 1` |
| `format` | String | Formato de resposta (`json` ou `xml`) | `"json"` |

---

#### 2. Limites de Taxa e Diretrizes Éticas

- **Rate Limit:** Limite padrão de 2 requisições por segundo e até 200 chamadas diárias para contas gratuitas/padrão de desenvolvedor.
- **Cabeçalhos:** Enviar `User-Agent` descritivo da aplicação.
- **Acesso ao Texto Completo:** A API de busca retorna metadados e links para PDFs; o download de artigos completos exige convênio institucional ou assinatura IEEE Xplore.

---

#### 3. Exemplo de Requisição (Python / Requests)

```python
import os
import requests

api_key = os.getenv("IEEE_API_KEY", "SUA_CHAVE_AQUI")
url = "https://ieeexploreapi.ieee.org/api/v1/search/articles"

params = {
    "apikey": api_key,
    "querytext": "machine learning",
    "start_year": "2022",
    "end_year": "2024",
    "max_records": "25",
    "format": "json"
}
headers = {"User-Agent": "AcademicOmniSearch/1.0"}

response = requests.get(url, params=params, headers=headers, timeout=20)
if response.status_code == 200:
    data = response.json()
    articles = data.get("articles", [])
    print(f"Total encontrado: {data.get('total_records')}")
```

---

#### 4. Amostra do Payload Bruto (JSON)

```json
{
  "total_records": 1250,
  "total_searched": 1250,
  "articles": [
    {
      "doi": "10.1109/ACCESS.2024.1234567",
      "title": "Deep Learning Techniques in Edge Computing Environments",
      "publication_title": "IEEE Access",
      "publication_year": 2024,
      "authors": {
        "authors": [
          { "full_name": "John Doe" },
          { "full_name": "Jane Smith" }
        ]
      },
      "html_url": "https://ieeexplore.ieee.org/document/1234567/",
      "pdf_url": "https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=1234567",
      "abstract": "This study analyzes the performance of neural networks...",
      "article_number": "1234567"
    }
  ]
}
```

---

#### 5. Regra de De-Para (Campos Brutos -> Schema Padronizado)

- `Title` <- `article['title']`
- `Link Pub` <- `article.get('html_url') or article.get('pdf_url')`
- `Autor` <- Lista de `author['full_name']` unidos por `; `
- `Revista / Fonte` <- `article['publication_title']`
- `Ano` <- `str(article['publication_year'])`
- `Base` <- `"IEEE Xplore"`
- `Resumo` <- `article.get('abstract', '')`
- `DOI` <- `article.get('doi', '')`
- `ID Origem` <- `str(article.get('article_number', ''))`
