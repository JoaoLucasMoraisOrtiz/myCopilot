# Plano de Implementação: Fluxo de Revisão Bloqueante e Evolução de Papéis

**Data:** 22/12/2025

Resumo: este documento descreve mudanças detalhadas para corrigir as fraquezas apontadas em `ANALYSIS_CRITICA.md`: (1) aproveitar agentes ociosos (Planner/Reviewer), (2) implementar um fluxo de revisão bloqueante (hard gating) para evitar "dummy" deliveries, (3) impedir que o `PRIMARY` execute subtasks de execução.

---

## Objetivos (curto prazo)

- Introduzir um estado e lifecycle de subtask com revisão (`review_pending`, `rejected`, `approved`). ✅
- Fornecer ferramentas MCP para Reviewer aprovar/rejeitar e listar pendências (`approve_subtask`, `reject_subtask`, `get_pending_reviews`). ✅
- Reaproveitar `PLANNER` durante `PHASE_4` como verificador/QA (atribuir `review` tasks).
- Evitar que `PRIMARY` chame/pegue subtasks na fase de execução.

---

## Alterações de modelo de dados (estado persistido)

Atual: `architecture.subtasks` (lista) + `subtask_claims` + `subtask_done` (dict)

Proposto:

1. Adicionar `subtask_statuses: Dict[str, object]` (chave = idx) com entradas como:
   - `status`: one of `pending|claimed|review_pending|rejected|done|approved`
   - `claimed_by`: role or `null`
   - `claimed_at`: ts or `null`
   - `last_update_ts`: ts
   - `result_summary`: str (opcional)
   - `reviewed_by`: role or `null`
   - `review_ts`: ts or `null`
   - `review_notes`: str (opcional)

2. Manter `subtask_done` como histórico (opcional) — ou transformar `subtask_done` em um log append-only. Em curto prazo, manter ambos e migrar gradualmente.

---

## Mudanças de comportamento (funções/fluxo)

### 1) get_next_subtask(role)
- Assinatura: `get_next_subtask()` se mantém, mas o servidor deve usar `self.instance_role` para comportamento.
- Regras:
  - Se `self.instance_role == 'PRIMARY'` e `phase` == `PHASE_4_EXECUTION` → retornar erro/guidance: "PRIMARY não pode pegar subtasks de execução".
  - Para `PLANNER` em `PHASE_4`: atribuir tarefas de verificação (ver `assign_review_tasks`), ou listas de `review_pending` para aprovação.
  - Para `WORKER_*`: normal execution: busca subtask com status `pending` ou `rejected` (re-assign) e marca como `claimed`.

### 2) report_subtask_completion(result_summary)
- Comportamento:
  - Em vez de marcar diretamente como `done`, definir o `subtask_statuses[idx] = { status: 'review_pending', result_summary, claimed_by: null, review_ts: null }` e persistir.
  - Criar comunicação para `REVIEWER_1`/PLANNER (ex: `_log_communication('review_requested', ...)`).
  - Se não houver Reviewer ativo por N segundos, sinalizar um `manager_action` de "assign reviewer" ou auto-assign para `PLANNER_1`.

### 3) approve_subtask(idx) / reject_subtask(idx, reason)
- Ferramentas novas expostas via MCP, restritas ao role `REVIEWER_*` (ou PRIMARY as admin):
  - `approve_subtask(idx, notes='')`:
    - Verifica se `subtask_status[idx].status == 'review_pending'`.
    - Marca `status = 'approved'` e cria entrada definitiva em `subtask_done` (role = reviewer or worker?), set `review_ts`, `reviewed_by`.
    - Atualiza `communication_log` e `manager_log`.
    - Persist.
  - `reject_subtask(idx, reason)`:
    - Verifica `review_pending`.
    - Marca `status = 'rejected'`, fills `review_notes`.
    - Optionally create `manager_action` to reassign or notify original worker.
    - Persist.

### 4) get_pending_reviews() / assign_review_task(role)
- Ferramentas para o Reviewer ou Planner listar e pegar reviews.
- `assign_review_task` pode automatizar distribuição de `review_pending` para `REVIEWER_1` ou `PLANNER_1`.

---

## Mudanças no código (arquivos e locais)

### Arquivo principal: `src/codingos/mcp/supervisor.py`

Alterar/Adicionar:

- Estado & persistência
  - `_state_to_dict` / `_apply_state_dict` / `_merge_state`: incluir `subtask_statuses` e garantir merges idempotentes.
  - Na migração, preencher `subtask_statuses` com base em `subtask_done` existentes: índice com `approved`.

- `get_next_subtask`
  - Adicionar role-aware behavior e impedir PRIMARY de pegar subtasks em `PHASE_4_EXECUTION`.
  - Para PLANNER em PHASE_4, retornar `review` tasks (ou mensagem de instrução) e usar `_assign_review_task`.

- `report_subtask_success` / `report_subtask_completion`
  - Ajustar para marcar `review_pending` e notificar reviewer.
  - Garantir que a `claim` seja liberada (claimed_by -> null) ao entrar `review_pending`.

- Novas ferramentas MCP a adicionar em `create_mcp_server`:
  - `approve_subtask(idx, notes='') -> str` (only for REVIEWER or PRIMARY admin)
  - `reject_subtask(idx, reason) -> str`
  - `get_pending_reviews() -> List[Dict]`
  - `assign_review_task(to_role: str = 'REVIEWER_1') -> Dict` (auto-assign oldest pending review)

- Scheduler/Escalonador simples:
  - Periodic check (executed nos pontos de `persist` ou por polling) para detectar `review_pending` sem `assigned_reviewer` por > TTL (e.g., 60s), então gerar `manager_action` "assign reviewer" ou auto-assign to PLANNER_1.

---

## Interface e Ferramentas MCP (propostas)

- approve_subtask(index: int, notes: str = '') -> str
- reject_subtask(index: int, reason: str) -> str
- get_pending_reviews() -> List[Dict[str, object]]
- assign_review_task(role: str = 'PLANNER_1'|'REVIEWER_1') -> Dict[str, object]
- get_agent_idle_report() -> Dict[str, object] (tempo desde last_seen, sugestões de uso)

**Nota:** proteger ferramentas com checagem de `is_primary` e role patterns. E.g., `approve_subtask` exige role `REVIEWER_*` ou `PRIMARY`.

---

## Migração de Estado

1. Adicionar campo `subtask_statuses` ao estado persistido durante `_save_state_to_disk` (backfill):
   - Para cada idx in range(len(architecture.subtasks)):
     - Se idx in `subtask_done` -> status = `approved` (ou `done`). copy result_summary.
     - Else if idx in `subtask_claims` -> status = `claimed`, claimed_by = existing claim.
     - Else -> `pending`.
2. Incluir `migration_version` no estado para rastrear alterações de schema.

---

## Testes e Critérios de Aceitação

1. Unit Tests (pytest):
   - `test_report_completion_marks_review_pending`
   - `test_reject_moves_to_rejected_and_reassigns`
   - `test_approve_creates_subtask_done_entry`
   - `test_primary_cannot_claim_in_execution_phase`
   - `test_planner_gets_review_tasks_in_phase4`

2. Integration Tests (simular várias instâncias):
   - Spawn PRIMARY, PLANNER, WORKER, REVIEWER. Execute flow: bootstrap -> intent -> context -> architecture -> execution.
   - Worker completes subtask -> status review_pending -> Reviewer rejects -> Worker gets task again and can resubmit -> reviewer approves -> state final.

3. Acceptance Criteria:
   - Reviewer approval required before subtask count advances to 'done' for validation.
   - No subtasks marked `done` without `approved` status (unless auto-approved by policy).
   - PLANNER is used during PHASE_4 for QA tasks when REVIEWER unavailable.
   - PRIMARY no longer picks subtasks in PHASE_4.

---

## Logs & Observability

- Adicionar eventos de log no `_log_manager` e `_log_communication` para:
  - `review_requested`, `review_assigned`, `review_approved`, `review_rejected`, `agent_idle`.
- Expor métricas simples no `get_system_status`: `pending_reviews`, `idle_agents_count`.

---

## Riscos e Mitigações

- Reviewer ausente -> bloqueio: Mitigar com auto-assign para PLANNER ou escalation `manager_action`.
- Deadlocks nas claims -> já mitigado pelo `state_lock`, mas garantir timeouts e `claim` expirations (se um agente claim por muito tempo sem progresso, liberar para reassign após TTL).
- Complexidade de Migração -> adicionar `migration_version` e rollbacks fáceis.

---

## Plano de Rollout (Passos)

1. Implementar schema e ferramentas MCP (merge PR).
2. Escrever testes unitários e integrados.
3. Lançar em ambiente de testes com 3 runs simuladas.
4. Monitorar logs e ajustar TTLs e heurísticas de auto-assign.
5. Reforçar documentação (README e `ANALYSIS_CRITICA.md` atualizado).

---

## Exemplo de Patches / Trechos de Código (Pseudo-Implementação)

Pseudo para `report_subtask_success` change:

```python
# Em report_subtask_success
self._subtask_statuses[str(active_idx)] = {
    'status': 'review_pending',
    'result_summary': result_summary,
    'claimed_by': None,
    'last_update_ts': str(time.time()),
}
self._log_communication('review_requested', f'subtask {active_idx} review requested', details={'subtask_index': active_idx})
self._persist()
```

Pseudo para `approve_subtask`:

```python
def approve_subtask(idx: int, notes: str='') -> str:
    s = self._subtask_statuses.get(str(idx))
    if not s or s['status'] != 'review_pending':
        return 'ERRO: não há revisão pendente para esse índice.'
    s['status'] = 'approved'
    s['reviewed_by'] = self.instance_role
    s['review_ts'] = str(time.time())
    s['review_notes'] = notes
    self._subtask_done[str(idx)] = {
        'role': s.get('claimed_by') or 'unknown',
        'ts': s['review_ts'],
        'result_summary': s.get('result_summary',''),
    }
    self._log_communication('review_approved', f'subtask {idx} approved', details={'by': self.instance_role})
    self._persist()
    return 'OK: subtask aprovada.'
```

---

Se você aprovar este plano, eu posso seguir e:
1. Implementar as mudanças em `src/codingos/mcp/supervisor.py` (adicionando testes).
2. Executar a bateria de testes/unit e rodar um teste de integração local com agentes simulados.
