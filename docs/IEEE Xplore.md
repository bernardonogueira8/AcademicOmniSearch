## IEEE Xplore

- **Categoria:** Engenharia Elétrica, Automação, Telecomunicações e Ciência da Computação
- **Tipo de Acesso:** IEEE Xplore Search API (Oficial) ou Headless Browser
- **Autenticação:** Requer chave de API cadastrada em `https://developer.ieee.org/`
- **URL Endpoint:** `https://ieeexploreapi.ieee.org/api/v1/search/articles`
- **Formato de Retorno:** JSON
- **Campos Principais:**
  - `apikey`: Chave da API
  - `querytext`: Consulta textual
  - `start_year` / `end_year`: Intervalo temporal
  - `articles[]`: Lista de documentos com `title`, `authors`, `publication_title`, `publication_year`, `doi`.