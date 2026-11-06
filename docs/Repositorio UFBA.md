### Repositório Institucional da UFBA (RI-UFBA)

- **Categoria / Domínio:** Multidisciplinar (Produção acadêmica, teses, dissertações e artigos da UFBA)
- **Tipo de Acesso:** OAI-PMH (XML/Dublin Core) / DSpace Discovery (HTML) / DSpace REST API
- **Autenticação:** Pública (não requer chave de API)
- **URL Base:** `https://repositorio.ufba.br/`
- **Endpoint OAI-PMH:** `https://repositorio.ufba.br/oai/request`
- **Endpoint de Busca Web:** `https://repositorio.ufba.br/simple-search`
- **Formato de Retorno:** XML (OAI-PMH) ou HTML (DSpace Discovery)

---

#### 1. Parâmetros de Consulta e Mapeamento de Campos

##### Opção A: Via Busca Web / DSpace Simple Search (HTML)
| Parâmetro HTTP | Tipo | Descrição | Equivalente no App |
| :--- | :--- | :--- | :--- |
| `query` | String | Termo de busca textual | `termo_busca` |
| `location` | String | Comunidade/Coleção específica (opcional) | - |
| `rpp` | Int | Resultados por página (ex: 10, 20, 50, 100) | `page_size` / `max_por_base` |
| `page` / `start` | Int | Deslocamento da paginação | `offset` |
| `sort_by` | Int | Ordenação (1 = relevância, 2 = data) | - |

##### Opção B: Via Protocolo OAI-PMH (Metadados Estruturados XML)
| Parâmetro OAI | Valor | Descrição |
| :--- | :--- | :--- |
| `verb` | `ListRecords` / `Identify` | Operação do protocolo OAI-PMH |
| `metadataPrefix` | `oai_dc` | Formato dos metadados (Dublin Core) |
| `from` | `YYYY-MM-DD` | Data inicial de colheita |
| `until` | `YYYY-MM-DD` | Data final de colheita |
| `set` | String | Subcoleção institucional |
| `resumptionToken` | String | Token de paginação |

---

#### 2. Limites de Taxa, SSL e Diretrizes Técnicas

- **Certificado SSL (ICP-Edu / ICP-Brasil):** Servidores acadêmicos de federações brasileiras frequentemente emitem certificados pela autoridade certificadora ICPEdu. Em clientes HTTP como `requests`, pode ser necessário definir `verify=False` ou configurar a cadeia de certificados da RNP/ICPEdu para evitar `SSLCertVerificationError`.
- **WAF SafeLine:** O domínio da UFBA possui proteção SafeLine WAF. Para evitar bloqueio (HTTP 468), recomenda-se enviar cabeçalhos completos de navegador (`User-Agent`, `Accept`, `Accept-Language`, `Sec-Fetch-*`) ou utilizar automação via navegador (Playwright).
- **Delays Éticos:** Manter intervalo mínimo de 1.0 a 1.5 segundo entre requisições para não onerar o servidor institucional.

---

#### 3. Exemplo de Requisição (Python / Requests com OAI-PMH)

```python
import requests
import xml.etree.ElementTree as ET
import urllib3

urllib3.disable_warnings()

url = "https://repositorio.ufba.br/oai/request"
params = {
    "verb": "ListRecords",
    "metadataPrefix": "oai_dc"
}
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
}

response = requests.get(url, params=params, headers=headers, verify=False, timeout=20)
print("Status Code:", response.status_code)

if response.status_code == 200:
    root = ET.fromstring(response.content)
    # Parse dos registros Dublin Core (namespaces dc e oai)
    ns = {
        "oai": "http://www.openarchives.org/OAI/2.0/",
        "dc": "http://purl.org/dc/elements/1.1/",
        "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/"
    }
    for record in root.findall(".//oai:record", ns):
        header = record.find("oai:header", ns)
        metadata = record.find(".//oai_dc:dc", ns)
        if metadata is not None:
            title = metadata.find("dc:title", ns)
            print("Título:", title.text if title is not None else "Sem título")
```

---

#### 4. Amostra do Payload Bruto (XML OAI-PMH Dublin Core)

```xml
<record>
  <header>
    <identifier>oai:repositorio.ufba.br:ri/12345</identifier>
    <datestamp>2024-03-15T12:00:00Z</datestamp>
    <setSpec>com_10405_1</setSpec>
  </header>
  <metadata>
    <oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" xmlns:dc="http://purl.org/dc/elements/1.1/">
      <dc:title>Sistemas de Recuperação da Informação em Ambientes Universitários</dc:title>
      <dc:creator>Silva, Bernardo Nogueira</dc:creator>
      <dc:date>2024</dc:date>
      <dc:publisher>Universidade Federal da Bahia</dc:publisher>
      <dc:identifier>http://hdl.handle.net/10405/12345</dc:identifier>
      <dc:description>Resumo da dissertação apresentada ao programa de pós-graduação...</dc:description>
      <dc:subject>Ciência da Informação; Recuperação da Informação</dc:subject>
    </oai_dc:dc>
  </metadata>
</record>
```

---

#### 5. Regra de De-Para (Campos Brutos -> Schema Padronizado)

- `Title` <- `dc:title` (ou texto do elemento `.artifact-title a` no HTML)
- `Link Pub` <- `dc:identifier` (URI Handle `http://hdl.handle.net/...` ou `https://repositorio.ufba.br/handle/...`)
- `Autor` <- Lista de `dc:creator` ou `dc:contributor.author` concatenados com `; `
- `Revista / Fonte` <- `dc:publisher` ou `"Repositório Institucional UFBA"`
- `Ano` <- Ano extraído de `dc:date` (regex `\b(19\d{2}|20\d{2})\b`)
- `Base` <- `"RI-UFBA"`
- `Resumo` <- `dc:description`
- `Palavras-Chave` <- Lista de `dc:subject` unidos por `; `
- `ID Origem` <- Identificador do handle OAI (ex: `ri/12345`)
