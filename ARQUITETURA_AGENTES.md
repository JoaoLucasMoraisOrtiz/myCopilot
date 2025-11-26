# Arquitetura de Agentes do OpenCode

## 1. Fluxo de Execução dos Agentes

### Início da Execução

**Ponto de entrada**: `packages/opencode/src/session/prompt.ts`

```
Usuário envia mensagem
    ↓
SessionPrompt.prompt() (linha ~100)
    ↓
resolveSystemPrompt() (linha ~621)
    ↓
Construção das mensagens
    ↓
streamText() / generateText() (AI SDK)
    ↓
Loop de geração de tokens
    ↓
Decisão de parar
```

### Primeira Instrução

1. **Sistema determina qual prompt usar** (`system.ts:28-35`):
   ```typescript
   export function provider(modelID: string) {
     if (modelID.includes("gpt-5")) return [PROMPT_CODEX]
     if (modelID.includes("gpt-") || modelID.includes("o1")) return [PROMPT_BEAST]
     if (modelID.includes("gemini-")) return [PROMPT_GEMINI]
     if (modelID.includes("claude")) return [PROMPT_ANTHROPIC]
     return [PROMPT_ANTHROPIC_WITHOUT_TODO]  // ← Nosso modelo local usa este
   }
   ```

2. **Construção do contexto** (`system.ts:37-58`):
   ```typescript
   async function environment() {
     return [
       "Working directory: ...",
       "Is directory a git repo: ...",
       "Platform: ...",
       "Today's date: ...",
       "File tree (até 200 arquivos)"
     ]
   }
   ```

3. **Adiciona instruções customizadas** (`system.ts:70-123`):
   - Busca por `AGENTS.md`, `CLAUDE.md`, `CONTEXT.md` no projeto
   - Busca por arquivos globais em `~/.config/opencode/AGENTS.md`
   - Adiciona ao contexto do sistema

### Próximas Instruções (Loop de Ferramentas)

**Localização**: `packages/opencode/src/session/prompt.ts:465+`

```
1. Modelo recebe prompt completo
2. Modelo decide ações:
   - Responder texto
   - Chamar ferramenta (tool call)
   - Ambos
3. Se chamou ferramenta:
   ├─ Executa ferramenta
   ├─ Adiciona resultado ao contexto
   └─ Volta ao passo 1 (nova iteração)
4. Se só respondeu texto:
   └─ Termina execução
```

**Exemplo de ciclo**:
```
User: "Fix the bug in file.ts"
  ↓
Agent: [Tool Call: Read file.ts]
  ↓
System: [Returns file content]
  ↓
Agent: [Tool Call: Edit file.ts with fix]
  ↓
System: [Confirms edit]
  ↓
Agent: "Bug fixed." (termina)
```

### Quando o Agente Para

O agente para em uma das seguintes condições:

1. **Não há mais tool calls**: Modelo retorna apenas texto
2. **Limite de iterações**: `stepCountIs()` no AI SDK
3. **finish_reason = "stop"**: Modelo decide que terminou
4. **finish_reason = "length"**: Atingiu max_tokens
5. **Erro**: Exception durante execução
6. **Abort manual**: Usuário cancela (Ctrl+C)

**Código relevante** (`prompt.ts:~500`):
```typescript
const result = await streamText({
  model: wrappedModel,
  messages,
  tools,
  maxSteps: 100, // ← Limite de iterações
  onFinish: async ({ finishReason, usage }) => {
    // Lógica de finalização
  }
})
```

---

## 2. Sistema de Prompts

### Localização dos Arquivos

**Diretório**: `packages/opencode/src/session/prompt/`

```
prompt/
├── anthropic.txt          # Prompt para Claude
├── anthropic_spoof.txt    # Header para Claude
├── beast.txt              # Prompt para GPT-4/o1/o3
├── codex.txt              # Prompt para GPT-5
├── gemini.txt             # Prompt para Gemini
├── qwen.txt              # Prompt padrão (nosso modelo usa este)
├── polaris.txt           # Prompt para Polaris
├── compaction.txt        # Para compactação de contexto
├── summarize.txt         # Para resumos
└── title.txt             # Para gerar títulos
```

### Estrutura dos Prompts

**Prompt base** (ex: `qwen.txt`):
- Identidade do agente
- Regras de comportamento
- Estilo de comunicação
- Políticas de uso de ferramentas
- Exemplos de interação

**Componentes adicionados dinamicamente**:
1. **Header**: Específico do provider (ex: Anthropic spoof)
2. **Environment**: Info do sistema (diretório, git, platform, data)
3. **File tree**: Estrutura de arquivos do projeto (até 200 arquivos)
4. **Custom instructions**: Conteúdo de `AGENTS.md`, `CLAUDE.md`, etc.

### Exemplo de Montagem Final

```
[Header do Provider]            ← system.ts:header()
[Prompt Base (qwen.txt)]        ← system.ts:provider()
[Informações do Ambiente]       ← system.ts:environment()
[Instruções Customizadas]       ← system.ts:custom()
───────────────────────────
[Conversa anterior]
[Mensagem do usuário]
```

### Seleção de Prompt

**Código** (`system.ts:28-35`):
```typescript
export function provider(modelID: string) {
  if (modelID.includes("gpt-5")) return [PROMPT_CODEX]
  if (modelID.includes("gpt-") || modelID.includes("o1")) return [PROMPT_BEAST]
  if (modelID.includes("gemini-")) return [PROMPT_GEMINI]
  if (modelID.includes("claude")) return [PROMPT_ANTHROPIC]
  if (modelID.includes("polaris-alpha")) return [PROMPT_POLARIS]
  return [PROMPT_ANTHROPIC_WITHOUT_TODO] // ← qwen.txt (nosso caso)
}
```

**Nosso modelo** (`Phi-3-mini-128k-instruct-qnn-npu:1`) não contém nenhuma das strings acima, então usa **`qwen.txt`** como fallback.

---

## 3. Adaptação para SLM (Small Language Model)

### Desafios

| Aspecto | LLM (GPT-4, Claude) | SLM (Phi-3) |
|---------|---------------------|-------------|
| Contexto | 128k - 200k tokens | **4096 tokens** |
| Raciocínio | Excelente | Limitado |
| Tool calling | Nativo | Precisa treino específico |
| Seguir instruções | Alta precisão | Menor precisão |

### Problema Atual

**Cálculo de tokens típico**:
```
Prompt base (qwen.txt):       ~1,500 tokens
Informações de ambiente:        ~100 tokens
Árvore de arquivos (200):    ~2,000 tokens
Instruções customizadas:        ~300 tokens
────────────────────────────────────────
Subtotal (antes da conversa): ~3,900 tokens
                                        ↓
Limite total:                  4,096 tokens
                                        ↓
Sobra para conversa:             196 tokens ❌
```

**Resultado**: Requests com 4590 tokens falham imediatamente!

### Estratégias de Redução de Contexto

#### 1. Reduzir Árvore de Arquivos

**Arquivo**: `packages/opencode/src/session/system.ts:50`

**Atual**:
```typescript
await Ripgrep.tree({
  cwd: Instance.directory,
  limit: 200,  // ← 200 arquivos
})
```

**Sugestão**:
```typescript
await Ripgrep.tree({
  cwd: Instance.directory,
  limit: 30,   // ← Reduzir para 30 arquivos
})
```

**Impacto**: Reduz ~1,700 tokens → ~300 tokens

#### 2. Simplificar Prompt Base

**Arquivo**: `packages/opencode/src/session/prompt/qwen.txt`

**Estratégia**:
- Remover exemplos extensos
- Reduzir instruções redundantes
- Focar em instruções essenciais
- Versão compacta: ~500 tokens (vs ~1500)

**Exemplo de versão compacta**:
```txt
You are opencode, a CLI coding assistant. Be concise.

Rules:
- Keep responses under 3 lines
- Use tools, not explanations
- No emojis unless requested
- Edit files directly, don't show code
- Call multiple tools in parallel when possible

Only answer what's asked. No extra info.
```

#### 3. Desabilitar Contexto de Ambiente Detalhado

**Arquivo**: `packages/opencode/src/session/system.ts:37`

**Opção A** - Versão mínima:
```typescript
export async function environment() {
  return [`Working directory: ${Instance.directory}`]
}
```

**Opção B** - Condicional baseado no modelo:
```typescript
export async function environment(modelID?: string) {
  const isSmallModel = modelID?.includes("phi-") || modelID?.includes("qnn")
  
  if (isSmallModel) {
    return [`Working directory: ${Instance.directory}`]
  }
  
  // Versão completa para LLMs grandes
  return [/* ... versão atual ... */]
}
```

#### 4. Implementar Compactação Inteligente

**Nova funcionalidade** - Detectar modelo pequeno e ajustar automaticamente:

```typescript
// Em packages/opencode/src/session/prompt.ts

async function resolveSystemPrompt(input: {
  providerID: string
  modelID: string
  agent: Agent
}) {
  const model = await Provider.getModel(input.providerID, input.modelID)
  const contextLimit = model.info.limit.context
  
  // Detecção de SLM
  const isSmallModel = contextLimit < 8192
  
  let system = SystemPrompt.header(input.providerID)
  
  if (isSmallModel) {
    // Modo compacto para SLMs
    system.push(...SystemPrompt.providerCompact(input.modelID))
    system.push(...await SystemPrompt.environmentMinimal())
    // Pular árvore de arquivos
  } else {
    // Modo completo para LLMs
    system.push(...SystemPrompt.provider(input.modelID))
    system.push(...await SystemPrompt.environment())
  }
  
  system.push(...await SystemPrompt.custom())
  return system
}
```

#### 5. Usar Task Tool para Delegação

**Estratégia**: Delegar operações que precisam de muito contexto para sub-agentes.

**Exemplo**:
```
Usuário: "Analyze the entire codebase and find performance issues"

Agente principal (SLM):
  ↓
  [Tool Call: Task - Analyze codebase for performance]
      ↓
  Sub-agente (pode ser outro modelo ou chunked):
      - Lê arquivos em batches
      - Analisa performance
      - Retorna resumo compacto
  ↓
Agente principal: Recebe resumo (300 tokens)
```

---

## Implementação Recomendada

### Passo 1: Criar Perfil de Modelo

**Arquivo**: `packages/opencode/src/provider/provider.ts`

```typescript
export function isSmallLanguageModel(info: ModelsDev.Model): boolean {
  return info.limit.context < 8192
}
```

### Passo 2: Prompts Compactos

**Novo arquivo**: `packages/opencode/src/session/prompt/compact.txt`

```txt
You are opencode, a coding CLI tool. Be extremely concise.

Rules:
- Max 2 lines per response
- Use tools, not text
- Call tools in parallel
- No explanations

Work efficiently with minimal context.
```

### Passo 3: Lógica Adaptativa

**Modificar**: `packages/opencode/src/session/system.ts`

```typescript
export function provider(modelID: string, contextLimit: number) {
  // Modo compacto para SLMs
  if (contextLimit < 8192) {
    return [PROMPT_COMPACT]
  }
  
  // Lógica atual para LLMs
  if (modelID.includes("gpt-5")) return [PROMPT_CODEX]
  // ... resto do código
}

export async function environment(contextLimit: number) {
  if (contextLimit < 8192) {
    return [`WD: ${Instance.directory}`]
  }
  
  // Versão completa para LLMs
  // ... código atual
}
```

### Passo 4: Configuração no local-model-config.json

```json
{
  "phi-local": {
    "models": {
      "Phi-3-mini-128k-instruct-qnn-npu:1": {
        "limit": { 
          "context": 4096,    // ← Sistema detecta SLM
          "output": 2048 
        },
        "options": {
          "compactMode": true  // ← Flag explícita
        }
      }
    }
  }
}
```

---

## Checklist de Otimização

- [ ] Reduzir limit de file tree: 200 → 30
- [ ] Criar prompt compacto (compact.txt)
- [ ] Implementar detecção de SLM no código
- [ ] Simplificar environment() para SLMs
- [ ] Adicionar flag no local-model-config.json
- [ ] Testar com requests reais
- [ ] Ajustar max_tokens para respostas curtas
- [ ] Documentar limitações no README

---

## Resultado Esperado

**Antes** (4590 tokens):
```
❌ Request rejeitado: "Input too long: 4590 tokens"
```

**Depois** (~2500 tokens):
```
Prompt compacto:               ~500 tokens
Environment mínimo:            ~50 tokens
File tree (30 arquivos):       ~300 tokens
Custom instructions:           ~300 tokens
────────────────────────────────────────
Subtotal:                    ~1,150 tokens
Conversa disponível:         ~2,950 tokens ✅
```

---

## Recursos Adicionais

- **Código-fonte relevante**:
  - `packages/opencode/src/session/prompt.ts` - Lógica principal
  - `packages/opencode/src/session/system.ts` - Montagem de prompts
  - `packages/opencode/src/provider/provider.ts` - Info dos modelos

- **Documentação**:
  - https://opencode.ai/docs/agents
  - https://opencode.ai/docs/providers

- **AI SDK** (usado internamente):
  - https://sdk.vercel.ai/docs
