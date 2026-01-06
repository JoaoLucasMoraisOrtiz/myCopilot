# codingOS - Supervisor Autônomo para Gemini CLI

## Visão Geral

codingOS é um sistema de supervisão autônoma para o Gemini Code CLI, usando MCP (Model Context Protocol) para guiar tarefas complexas através de um protocolo de 4 fases.

## Estrutura do Projeto

- `src/codingos/`: Pacote principal com supervisor, scout de contexto e memória ACE
- `scripts/`: Scripts de entrada e wrappers
- `dist/`: Executáveis compilados (gerados pelo build)

## Construção

Para "compilar" e ocultar o código fonte:

1. Instale dependências:
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```

2. Execute o build:
   ```bash
   python build.py
   ```

Isso cria:
- `dist/supervisor.exe`: Executável do supervisor (código fonte oculto)
- `dist/project_launcher.exe`: Launcher que distribui o supervisor.exe

## Distribuição

O `project_launcher.exe` pode ser copiado para qualquer pasta. Quando executado, ele:
- Cria `.gemini/settings.json` e `GEMINI.md`
- Copia `supervisor.exe` para `.gemini/`
- Configura o Gemini CLI para usar o supervisor compilado

O código fonte permanece oculto nos executáveis.

## Exportação e uso distribuído

1. Execute `python build.py` no workspace para gerar `dist/supervisor.exe` e `dist/project_launcher.exe`.
2. Entregue somente `dist/project_launcher.exe` ao usuário final (ele criará `.gemini/` automaticamente).
3. O usuário roda: `project_launcher.exe "Sua tarefa"` para iniciar a instância principal.
4. A instância principal consulta o MCP (`consult_supervisor`) e usa as novas ferramentas:
   - `get_manager_next_action()` para saber qual ação fazer a seguir (scan, spawn, intent). 
   - `report_manager_action_completion(action_id, result_summary, user_update="Mensagem clara")` para reportar progresso ao usuário.
   - `get_user_facing_progress()` se quiser um resumo pronto que inclua fase, agentes e eventos recentes.
5. Quando precisar criar planejadores/workers, chama `spawn_agent_pool(planners, workers, stagger_seconds=8.0)`; cada nova instância deve fazer `register_agent(role, note)` ao se iniciar.

## Dicas operacionais
- Use `--instances 1` (modo manager-only) quando a cota estiver bonita e você só quiser o context scout/manager.
- Com `--mode pipeline --keep-open`, o launcher abre cada instância sequencialmente e mantém as janelas visíveis.
- Caso queira ver o progresso narrado ao usuário, peça à instância principal para imprimir cada `user_update` retornado por `report_manager_action_completion`.

## Importante: por que `supervisor.exe` “trava” no terminal?

`supervisor.exe` é um **servidor MCP via stdio**. Isso significa que ele fica **aguardando** a conversa MCP em `stdin/stdout` (quem fala com ele é o Gemini CLI), então:

- Rodar `supervisor.exe` direto vai parecer que “travou” (é esperado).
- `supervisor.exe --help` só funciona se você rebuildar após a mudança no wrapper (veja seção “Construção”).

Para validar que está tudo OK, use o host:

- No diretório do projeto com `.gemini/settings.json` configurado: `gemini mcp list`

Isso confirma que o Gemini consegue iniciar o servidor e enxergar as tools.

> Observação de segurança: executáveis gerados por empacotadores como PyInstaller **dificultam**, mas não “blindam” totalmente a engenharia reversa.
> Se existe “segredo” real (chaves, lógica proprietária crítica), a abordagem correta é manter isso no servidor (MCP remoto / API) e distribuir apenas um cliente autenticado.

## Desenvolvimento

Para desenvolvimento local (com código fonte visível):
- Use `scripts/supervisor_server.py` diretamente
- Execute `python -m codingos.mcp` para testar o módulo

## Funcionalidades

- **Protocolo 4 Fases**: Mapeamento Conceitual → Seleção de Contexto → Arquitetura → Execução + Validação
- **Scout de Contexto**: Descoberta automática de estrutura do projeto
- **Memória ACE**: Correções adaptativas para melhorar prompts ao longo do tempo