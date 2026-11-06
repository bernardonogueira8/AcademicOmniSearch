# AcademicOmniSearch: Guia de Especificação e Integração de APIs / Scrapers

Este documento define o **padrão oficial de especificação técnica** para a integração de novas fontes de dados acadêmicas no **AcademicOmniSearch**, além de documentar os endpoints, parâmetros e payloads das bases já mapeadas.

---

## 📋 Schema Padronizado de Saída (De-Para Obrigatório)

Independentemente da origem (API REST, GraphQL, E-utilities ou Web Scraping em HTML), todo coletor deve mapear seus dados para a seguinte estrutura tabular:

| Campo Oficial | Tipo | Obrigatório | Descrição | Exemplo |
| :--- | :--- | :--- | :--- | :--- |
| `Title` | String | Sim | Título completo da publicação | `"Recuperação em fontes de informação..."` |
| `Link Pub` | String | Sim | URL direta para o artigo ou DOI | `"https://brapci.inf.br/v/324067"` |
| `Autor` | String | Sim | Lista de autores separados por `; ` | `"Soares, J. R.; Silva, P. N."` |
| `Revista / Fonte` | String | Sim | Periódico, evento ou conferência | `"Biblionline"` ou `"SIGGRAPH '26"` |
| `Ano` | String | Sim | Ano de publicação (4 dígitos) | `"2024"` |
| `Base` | String | Sim | Nome padronizado da base de dados | `"BRAPCI"`, `"PubMed"`, `"ACM"` |
| `Resumo` | String | Não | Abstract ou resumo do documento | `"Este artigo analisa os métodos..."` |
| `Palavras-Chave` | String | Não | Termos-chave separados por `; ` | `"Sistemas de recuperação; Enfermagem"` |
| `DOI` | String | Não | Digital Object Identifier | `"10.1145/3799885.3816014"` |
| `ID Origem` | String | Não | Identificador interno da base | `"324067"` ou `"PMID:39738309"` |
