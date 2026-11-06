## 📐 Template Padrão para Especificação de Novas Bases

Ao documentar uma nova base de dados, replique a estrutura abaixo:

```markdown
### [Nome da Base de Dados]

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

---

## 🗂️ Bases Mapeadas e Implementadas

### 1. BRAPCI (Base de Dados Referencial de Artigos de Periódicos em Ciência da Informação)

- **Categoria:** Ciência da Informação, Biblioteconomia e Gestão do Conhecimento
- **Tipo de Acesso:** API REST Oficial v5
- **Autenticação:** Pública (não requer chave de API)
- **URL Endpoint:** `https://cip.brapci.inf.br/api/brapci/search/v5`
- **Formato de Retorno:** JSON

#### Parâmetros de Consulta
- `term`: Termo ou frase de pesquisa
- `offset`: Deslocamento da paginação (0, 10, 20, ...)
- `year_start`: Ano inicial (ex: `"2020"`)
- `year_end`: Ano final (ex: `"2026"`)
- `collection`: Coleções de publicações:
  - `JA`: Revistas Brasileiras
  - `JE`: Revistas Estrangeiras
  - `EV`: Anais de Eventos
  - `BK`: Livros e Capítulos
  - *Padrão:* `"JA,JE,EV,BK"`
- `field`: Código de campo de busca:
  - `FL`: Todos / Texto Completo
  - `TI`: Título
  - `KW`: Palavras-Chave
  - `AU`: Autor
  - `AB`: Resumo

#### Exemplo de Requisição
```python
import requests

url = "https://cip.brapci.inf.br/api/brapci/search/v5"
params = {
    "term": "recuperação da informação",
    "offset": "0",
    "year_start": "2020",
    "year_end": "2024",
    "collection": "JA,JE,EV,BK",
    "field": "FL"
}
headers = {"User-Agent": "AcademicOmniSearch/1.0"}
resp = requests.get(url, params=params, headers=headers, timeout=20)
data = resp.json()
```

#### Amostra de Retorno
```json
{
  "total": 10,
  "works": [
    {
      "id": "324067",
      "score": 8.217242,
      "type": "Article",
      "year": "2024",
      "data": {
        "ID": "324067",
        "JOURNAL": "Biblionline",
        "TITLE": "Recuperacao em fontes de informacao em saude: o portal BVS enfermagem",
        "AUTHORS": "Jordana Rabelo Soares; Patrícia Nascimento Silva",
        "KEYWORDS": "Sistemas de recuperação de informação; Fontes de informação"
      }
    }
  ]
}
```

#### Regra de De-Para
- `Title` <- `work['data']['TITLE']`
- `Link Pub` <- `f"https://brapci.inf.br/v/{work['id']}"`
- `Autor` <- `work['data']['AUTHORS']`
- `Revista / Fonte` <- `work['data'].get('JOURNAL') or work['data'].get('LEGEND')`
- `Ano` <- `work['year']`
- `Base` <- `"BRAPCI"`
- `Palavras-Chave` <- `work['data'].get('KEYWORDS')`
- `ID Origem` <- `work['id']`
