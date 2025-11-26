# API Local Phi-3 para OpenCode

Este diretório contém uma implementação de API OpenAI-compatível para usar o modelo Phi-3 localmente com o OpenCode.

## Arquivos

- **`api.py`**: Servidor FastAPI que expõe o modelo Phi-3 via API OpenAI-compatível
- **`client.py`**: Cliente simples para testar o endpoint legado `/generate`
- **`test-openai-api.py`**: Suite de testes completa para validar a API OpenAI-compatível
- **`local-model-config.json`**: Configuração do provider para o OpenCode
- **`start-local.ps1`**: Script PowerShell para iniciar e testar o ambiente

## Como Usar

### 1. Iniciar a API

Em um terminal, execute:

```powershell
python api.py
```

Aguarde até ver a mensagem: `Model loaded successfully.`

### 2. Testar a API

Em outro terminal, execute:

```powershell
python test-openai-api.py
```

Ou use o script de inicialização:

```powershell
.\start-local.ps1
```

### 3. Usar com OpenCode

#### Opção A - Script automatizado (Recomendado):

```powershell
# Em um terminal, inicie a API:
python api.py

# Em outro terminal, inicie o OpenCode local:
.\start-opencode-local.ps1
```

#### Opção B - Manual:

1. **Configurar variáveis de ambiente:**

```powershell
$env:MODELS_DEV_API_JSON = "C:\Users\jluca\Documents\code\myCopilot\local-model-config.json"
$env:PHI_LOCAL_API_KEY = "unused"
```

2. **Iniciar OpenCode em modo dev:**

```powershell
bun dev
```

3. **Selecionar o modelo:**

No OpenCode, selecione o modelo `phi-local/Phi-4-mini-reasoning-qnn-npu:1`

#### Testar a integração:

```powershell
.\test-integration.ps1
```

Ou manualmente:

```powershell
$env:MODELS_DEV_API_JSON = "$PWD\local-model-config.json"
$env:PHI_LOCAL_API_KEY = "unused"
bun run test-phi-local.ts
```

## Endpoints da API

### `GET /`
Status do servidor e se o modelo está carregado.

### `GET /v1/models`
Lista os modelos disponíveis (compatível com OpenAI).

### `POST /v1/chat/completions`
Endpoint principal compatível com OpenAI para chat completions.

**Parâmetros:**
- `model`: ID do modelo (padrão: "Phi-4-mini-reasoning-qnn-npu:1")
- `messages`: Array de mensagens no formato OpenAI
- `max_tokens`: Máximo de tokens a gerar (padrão: 2048)
- `temperature`: Temperatura de geração (padrão: 0.1)
- `top_p`: Top-p sampling (padrão: 0.9)
- `stream`: Habilitar streaming (padrão: false)
- `repetition_penalty`: Penalidade de repetição (padrão: 1.05)

### `POST /generate` (Legacy)
Endpoint legado para compatibilidade com o `client.py`.

## Modificações Realizadas

### `api.py`
1. Adicionado suporte para formato de API OpenAI (`/v1/chat/completions`)
2. Implementado endpoint `/v1/models`
3. Suporte para streaming e não-streaming
4. Conversão de mensagens OpenAI para template Phi-3
5. Mantido endpoint legacy `/generate` para compatibilidade

### `local-model-config.json`
- Atualizado a URL da API de `http://localhost:5272/v1` para `http://localhost:8000/v1`

## Configuração do Modelo

O caminho do modelo é configurado via variável de ambiente `MODEL_PATH`:

```powershell
$env:MODEL_PATH = "C:\Users\jluca\.aitk\models\Microsoft\phi-3-mini-4k-instruct-qnn-npu-2\phi-3-mini-4k"
```

Ou deixe usar o padrão especificado no `api.py`.

## Troubleshooting

### API não inicia
- Verifique se o caminho do modelo está correto
- Verifique se `onnxruntime_genai` está instalado: `pip install onnxruntime-genai`

### OpenCode não encontra o provider
- Confirme que `MODELS_DEV_API_JSON` aponta para o arquivo correto
- Confirme que `PHI_LOCAL_API_KEY` está definida (pode ser qualquer valor)
- Execute `bun run test-phi-local.ts` para validar

### Respostas lentas
- Normal para modelos locais, especialmente em CPU/NPU
- Ajuste `temperature` e `max_tokens` conforme necessário
