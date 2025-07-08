# Sistema de Paginação Inteligente - Agent Core

## Visão Geral

O Agent Core agora inclui um sistema de paginação inteligente que resolve o problema de overflow de contexto. Em vez de truncar brutalmente o código, o sistema:

1. **Abstrai automaticamente** conteúdo longo (métodos, arquivos)
2. **Cria marcadores de continuação** com IDs únicos
3. **Permite expansão sob demanda** via `continue_reading`

## Como Funciona

### 1. Abstração Automática

Quando o LLM solicita código ou arquivos:

```python
# Por padrão, retorna versão abstraída
agent.get_code("MinhaClasse")  # Métodos longos são resumidos

# Para forçar versão completa (cuidado com overflow!)
agent.get_code("MinhaClasse", abstracted=False)
```

### 2. Marcadores de Continuação

Métodos/arquivos abstraídos mostram marcadores como:
```
public void metodoComplexo() {
    // primeiras linhas do método...
    String resultado = processarDados();
    // ... [MÉTODO ABSTRAÍDO: ~45 linhas restantes - use continue_reading('abs_1') para ver o método completo]
}
```

### 3. Expansão Sob Demanda

O LLM pode expandir o conteúdo usando o ID:
```json
{"command": "continue_reading", "args": ["abs_1"]}
```

## Benefícios

### ✅ Evita Overflow de Contexto
- Nunca mais prompts de 16k+ caracteres
- API não trava por excesso de dados
- Mantém informação essencial visível

### ✅ Navegação Inteligente
- LLM vê estrutura completa primeiro
- Pode "mergulhar" em detalhes específicos
- Controle granular sobre o que examinar

### ✅ Memória Eficiente
- IDs de abstração são limpos após uso
- Estado controlado e previsível
- Previne acúmulo de dados desnecessários

## Comandos Disponíveis

### `get_code(classe, método=None, abstracted=True)`
- `abstracted=True`: Versão resumida (padrão)
- `abstracted=False`: Versão completa (risco de overflow)

### `read_file(arquivo, abstracted=True)`  
- `abstracted=True`: Primeiras linhas + marcador (padrão)
- `abstracted=False`: Arquivo completo

### `continue_reading(abstraction_id)`
- Expande conteúdo abstraído
- Remove o ID após uso (limpeza automática)

## Exemplo de Uso Prático

```python
# 1. LLM obtém visão geral da classe
response = agent.get_code("UsuarioService")
# Retorna: estrutura + assinaturas + marcadores [abs_1], [abs_2]...

# 2. LLM identifica método interessante e expande
response = agent.continue_reading("abs_1")  
# Retorna: código completo do método específico

# 3. LLM continua análise com contexto completo mas controlado
```

## Estratégias de Abstração

### Para Métodos
- Mantém: assinatura completa + modifiers
- Mostra: primeiras 3 linhas de conteúdo
- Abstrai: resto do corpo se > 300 caracteres

### Para Classes
- Mantém: imports, declaração, campos
- Mostra: métodos pequenos completos
- Abstrai: métodos grandes individualmente

### Para Arquivos
- Mantém: primeiras 30 linhas
- Abstrai: resto se > 2000 caracteres
- Preserva: estrutura e contexto inicial

## Configurações

```python
# Limites atuais (podem ser ajustados)
MAX_METHOD_CHARS = 300      # Abstrai métodos maiores que isso
MAX_FILE_CHARS = 2000       # Abstrai arquivos maiores que isso  
MAX_TOTAL_RESPONSE = 6000   # Limite total da resposta
MAX_ABSTRACT_LINES = 30     # Linhas visíveis antes da abstração
```

## Troubleshooting

### "ID de abstração não encontrado"
- IDs são temporários e removidos após uso
- Use `list(agent.toolbox.abstracted_content.keys())` para ver IDs ativos

### "Ainda há overflow mesmo com abstração"
- Verifique os limites configurados
- Considere abstrair mais agressivamente
- Use métodos específicos em vez de classes inteiras

### "Perdi o contexto depois da abstração"
- Abstrações preservam informação estrutural
- Use `get_class_metadata()` para visão geral
- Combine abstrações com metadata para contexto completo
