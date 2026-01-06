# Arquitetura do Supervisor MCP (4-Phase Protocol)

Esta documentação descreve a implementação do **Protocolo de Raciocínio em 4 Fases** para o Agente Autônomo Gemini.

## Visão Geral
O Supervisor atua como um "Gerente de Projeto" rigoroso, forçando o Agente (Gemini) a passar por portões de validação antes de escrever qualquer código.

## As 4 Fases do Protocolo

### FASE 1: Mapeamento Conceitual (Intent)
*   **Objetivo**: Entender o "O Quê" e o "Porquê" antes do "Como".
*   **Ação do Agente**: Analisar o pedido do usuário.
*   **Ferramenta**: `submit_intent_analysis(technologies, patterns, changes)`
*   **Portão de Validação**: O Supervisor verifica se a análise está completa. Se rejeitada, o Agente deve refazer.

### FASE 2: Seleção de Contexto (Context)
*   **Objetivo**: Evitar poluição de contexto e alucinações.
*   **Ação do Agente**: Listar arquivos relevantes para a tarefa.
*   **Ferramenta**: `submit_context_selection(files, reasoning)`
*   **Portão de Validação**: O Supervisor verifica se algum arquivo foi selecionado.

### FASE 3: Arquitetura da Solução (Architecture)
*   **Objetivo**: Criar um plano de batalha detalhado.
*   **Ação do Agente**: Definir Estado Atual, Estado Esperado e Subtasks.
*   **Ferramenta**: `submit_architecture_plan(current_state, expected_state, subtasks)`
*   **Portão de Validação**: O Supervisor verifica se existem subtasks definidas.

### FASE 4: Execução Atômica e Validação (Execution)
*   **Objetivo**: Implementação cirúrgica e teste.
*   **Loop de Execução**:
    1.  Agente pede: `get_next_subtask()`
    2.  Supervisor entrega: "Tarefa X"
    3.  Agente executa e reporta: `report_subtask_completion()`
*   **Validação Global**:
    *   Ao final das subtasks, o Agente chama `submit_global_validation(success, issues)`.
    *   **Se Falhar**: O Supervisor reinicia o processo na **FASE 1**.
    *   **Se Sucesso**: A tarefa é dada como concluída.

## Implementação Técnica
O servidor MCP reside em `scripts/supervisor_server.py` e utiliza a biblioteca `FastMCP`. Ele mantém o estado da sessão em memória (reinicia a cada nova execução do CLI).
