# feat: automação de WAF para ACM e diagnóstico operacional do Portal CAPES

* **Pergunta/Solicitação:**
> "Verifica como automizar o HTML WAF, não é funcional arquivo foi um teste. outra coisa como funciona CAPES? Esta online pesquisavel/"

* **Planejamento:**
1. Analisar a dependência legada de arquivos manuais (`test/app.html`) no scraper da ACM (`AcmScraper`) e no orquestrador (`pipeline/orchestrator.py`).
2. Investigar as alternativas arquiteturais de produção para contornar proteções de WAF (Cloudflare Turnstile e AWS WAF) sem intervenção humana:
   - Estratégia API-First (conector CrossRef ACM filtrado por prefixo `10.1145`).
   - Headless browser com emulação de fingerprint (Playwright Stealth / Camoufox).
   - Smart rotating proxies (Zyte API, ScraperAPI).
3. Implementar a automação direta e em tempo real em `src/acm_scraper.py` via CrossRef REST API, eliminando a dependência do arquivo estático de teste.
4. Remover a injeção do arquivo de teste em `pipeline/orchestrator.py`.
5. Investigar o Portal de Periódicos CAPES (`https://www.periodicos.capes.gov.br`):
   - Testar a conectividade em tempo real com os endpoints de busca (`/index.php/acervo/buscador.html`).
   - Mapear a arquitetura técnica da CAPES (Joomla, busca federada, AWS CloudFront, AWS WAF, CAFe).
   - Executar o scraper nativo `CapesScraper` para verificar se está recuperando registros em tempo real.
6. Consolidar as respostas explicativas de forma clara, didática e com validações práticas.

* **Resumo da Execução:**
- **Automação do WAF da ACM (`AcmScraper`):**
  - O arquivo `test/app.html` foi descartado como requisito de operação.
  - Implementado o método `_fetch_via_crossref` em [`src/acm_scraper.py`](file:///c:/Dev/Projeto%20de%20scrapy/AcademicOmniSearch/src/acm_scraper.py): quando a requisição direta à ACM DL encontra proteção Cloudflare (HTTP 403), o coletor faz o chaveamento automático para a API aberta do CrossRef filtrando pelo prefixo oficial da ACM (`prefix:10.1145`).
  - O orquestrador [`pipeline/orchestrator.py`](file:///c:/Dev/Projeto%20de%20scrapy/AcademicOmniSearch/pipeline/orchestrator.py) foi atualizado para instanciar `AcmScraper()` diretamente sem parâmetros de arquivos estáticos locais.
  - Testes executados confirmaram a recuperação em tempo real de artigos legítimos da ACM com DOI, títulos, autores e publicações em menos de 1 segundo.
- **Diagnóstico e Funcionamento do Portal CAPES:**
  - O portal da CAPES está **100% online e pesquisável**.
  - O teste com `CapesScraper` recuperou 20 publicações reais em 4 segundos (artigos de periódicos como RevBEA, EccoS, RSD, etc.).
  - Documentado o funcionamento de sua arquitetura: distribuição AWS CloudFront com AWS WAF, requisitos de cabeçalhos HTTP legítimos de navegador, integração com o protocolo CAFe para textos completos comerciais e o suporte já embutido de bypass via Zyte API (`ZYTE_API_KEY`) para casos de rate limiting por IP.

