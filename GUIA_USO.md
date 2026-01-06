# Guia de Uso - codingOS

## Para Exportar e Distribuir

1. No workspace do projeto (onde está o código), execute:
   ```bash
   python build.py
   ```

2. Isso gera `dist/project_launcher.exe` e `dist/supervisor.exe` (embutido no launcher).

3. **Distribua apenas** `dist/project_launcher.exe` — é um arquivo único, self-contained.

## Para Usar o Sistema (Usuário Final)

### Passo 1: Preparar o ambiente
1. Copie `project_launcher.exe` para a **pasta raiz do seu projeto** (onde você quer trabalhar).
2. Abra um terminal (PowerShell/cmd) nessa pasta.

### Passo 2: Iniciar o sistema
Execute:
```bash
project_launcher.exe "Sua tarefa aqui"
```

Exemplo:
```bash
project_launcher.exe "Criar um sistema de gestão de tarefas em Python com FastAPI"
```

### O que acontece automaticamente:
- Cria `.gemini/` e copia `supervisor.exe`
- Cria `GEMINI.md` (instruções do sistema)
- Cria `.gemini/settings.json` (configuração MCP)
- Abre **UMA** janela do Gemini CLI (instância principal)

### Passo 3: Interagir com a instância principal

A janela do Gemini que abriu é o **Action Manager + Context Scout**. Ela deve:

1. **Consultar o supervisor** (obrigatório pela PRIME DIRECTIVE):
   - Chamar a tool MCP: `consult_supervisor("sua tarefa")`
   - O supervisor responde com instruções iniciais

2. **Seguir o loop de gerenciamento**:
   - Chamar `get_manager_next_action()` para saber o que fazer
   - Executar a ação (ex.: scan do repo, criar `docs/CONTEXT.md`)
   - Chamar `report_manager_action_completion(action_id, result_summary, user_update="Mensagem para o usuário")`
   - Repetir até completar todas as ações

3. **Bootstrap do pool de agentes** (quando instruído):
   - Chamar `spawn_agent_pool(planners=1, workers=1, stagger_seconds=8.0)`
   - O supervisor abre novas janelas com papéis específicos (PLANNER_1, WORKER_1, etc.)
   - **Limite de segurança**: máximo 4 agentes (planners + workers ≤ 4)

4. **Monitorar progresso**:
   - Chamar `get_user_facing_progress()` para ver resumo (fase, agentes ativos, últimas ações)
   - Narrar ao usuário usando os `user_update` registrados

### Ferramentas MCP Disponíveis

**Coordenação do Manager:**
- `consult_supervisor(user_request)` → Inicia o processo
- `get_manager_next_action()` → Próxima ação a executar
- `report_manager_action_completion(action_id, result_summary, user_update)` → Reporta conclusão
- `get_user_facing_progress()` → Resumo para o usuário
- `get_system_status()` → Status completo (fase, agentes, logs)

**Spawning:**
- `spawn_agent_pool(planners, workers, model?, stagger_seconds?, keep_open?)` → Cria agentes secundários
- `register_agent(role, note)` → Agentes secundários se registram

**Protocolo 4 Fases:**
- `submit_intent_analysis(technologies, patterns, changes)`
- `submit_context_selection(files, reasoning)`
- `submit_architecture_plan(current_state, expected_state, subtasks)`
- `get_next_subtask()`
- `report_subtask_completion(result_summary)`
- `submit_global_validation(success, issues)`

**ACE (Memória Adaptativa):**
- `record_ace_correction(original_action, error, corrected_action, tags, ...)`

## Flags Opcionais do Launcher

- `--model <nome>`: Override do modelo (ex.: `--model gemini-2.0-flash`)
- `--keep-open`: Mantém janela aberta após prompt (default: True)
- `--help`: Mostra ajuda

Exemplo com flags:
```bash
project_launcher.exe --model gemini-2.0-flash "Criar API REST"
```

## Troubleshooting

### Erro: "capacity" ou "quota exceeded"
- **Causa**: Muitas requisições simultâneas ao modelo
- **Solução**: Use `stagger_seconds=10` ou superior no `spawn_agent_pool`

### Erro: "Gemini CLI não encontrado"
- **Causa**: Node/npm não instalado ou Gemini CLI não configurado
- **Solução**: Instale NodeJS e depois `npm install -g @google/gemini-cli`

### Muitas janelas abertas (50+)
- **Causa corrigida**: Launcher antigo spawnava instâncias em loop
- **Solução**: Use a versão rebuild (após a correção de 22/12/2025)
- **Garantia**: Supervisor agora tem limite hard-coded de 4 agentes

### Validar instalação do MCP
No diretório do projeto configurado:
```bash
gemini mcp list
```
Deve listar todas as ferramentas do supervisor (consult_supervisor, spawn_agent_pool, etc.)

## Arquitetura do Sistema

```
┌─────────────────────────────────────────────┐
│  Usuário executa:                           │
│  project_launcher.exe "tarefa"              │
└───────────────┬─────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│  Launcher cria ambiente:                    │
│  - .gemini/supervisor.exe                   │
│  - .gemini/settings.json                    │
│  - GEMINI.md                                │
└───────────────┬─────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│  Abre 1 Gemini (Action Manager)             │
│  ├─ consult_supervisor("tarefa")            │
│  ├─ get_manager_next_action()               │
│  ├─ spawn_agent_pool(planners, workers)     │
│  └─ Narrar progresso ao usuário             │
└───────────────┬─────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│  Supervisor MCP (supervisor.exe)            │
│  - Coordena fases do protocolo              │
│  - Spawna PLANNER_n / WORKER_n              │
│  - Rastreia estado global                   │
│  - Limite: max 4 agentes                    │
└─────────────────────────────────────────────┘
```

## Próximos Passos

Depois que o sistema estiver rodando e o pool bootstrapped:
1. A instância principal continua narrando progresso
2. Planners/Workers pegam subtasks e reportam via MCP
3. O supervisor valida e coordena o fluxo
4. Ao final, `submit_global_validation(success=True)` encerra o ciclo

Para desenvolvimento avançado, consulte `src/codingos/` para entender a implementação interna do supervisor, ACE memory e context scout.
