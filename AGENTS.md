## **Regra de Registro de Missões (History Tracking)**

Sempre que concluir uma missão ou tarefa solicitada, você deve documentar a execução obrigatoriamente seguindo este padrão:

1. **Local de Salvamento:** Acesse ou crie a raiz do diretório `history/`.
2. **Subpasta:** Crie uma subpasta com a data da execução no formato `YYYY-MM-DD` (ex: `history/2026-10-22/`).
3. **Nome do Arquivo:** Crie um arquivo `.md` nomeado com a função principal executada em kebab-case (ex: `criar-processo-agente.md`).
4. **Título do Arquivo:** Use o padrão *Conventional Commits* no título principal (H1). Exemplo: `# feat: criação da regra de histórico para agents`.
5. **Estrutura do Conteúdo:** O arquivo deve ser preenchido exatamente com a seguinte estrutura estruturada:
* **Pergunta/Solicitação:** [A pergunta exata enviada pelo usuário]
* **Planejamento:** [O raciocínio e o passo a passo que você estabeleceu antes de iniciar a execução]
* **Resumo da Execução:** [A resposta final consolidada e o que foi efetivamente construído ou alterado]

Siga este bloco de forma estrita em cada final de interação.