# Sistema de Logging - Java Reengineering Agent

Sistema de logging centralizado e estruturado usando **loguru** para o agente de reengenharia Java.

## 🎯 Características

- **Logging estruturado** com categorias específicas para diferentes operações
- **Rotação automática** de arquivos de log
- **Formatação JSON** para análise automatizada
- **Console colorido** para melhor experiência de desenvolvimento
- **Decorador automático** para logging de funções
- **Context manager** para logging temporário
- **Configuração flexível** via código ou variáveis de ambiente

## 📁 Arquivos de Log Gerados

```
logs/
├── agent.log          # Log geral (todas as mensagens)
├── analysis.log       # Logs específicos de análise
├── generation.log     # Logs específicos de geração de código
├── errors.log         # Apenas erros e críticos
└── structured.jsonl   # Logs estruturados em JSON
```

## 🚀 Uso Básico

### Configuração Inicial

```python
from utils.logger import setup_logging, get_logger

# Configurar o sistema de logging
config = setup_logging(log_dir="logs", debug=True)

# Obter instância do logger
logger = get_logger()

# Usar o logger
logger.info("Sistema iniciado")
```

### Logging Categorizados

```python
# Logs específicos por categoria
logger.analysis("Analisando código legacy", file_count=150)
logger.generation("Gerando novo código", feature="UserService")
logger.rag("Executando consulta RAG", query="business rules")
logger.amazon_q("Chamando Amazon Q", tokens=1200)
logger.pipeline("Executando pipeline", step="validation")
logger.performance("Operação completada", duration=2.5)
```

### Decorador Automático

```python
from utils.logger import log_execution

@log_execution(category="analysis", log_args=True)
def analyze_java_file(file_path: str) -> dict:
    # Função será automaticamente logada
    return {"classes": 3, "methods": 15}

# Logs automáticos:
# INFO: Starting analyze_java_file with args=('/path/file.java',)
# INFO: Completed analyze_java_file in 1.23s
```

### Context Manager para Logging Temporário

```python
from utils.logger import TemporaryLogging

with TemporaryLogging(log_dir="temp_logs", debug=True) as temp_logger:
    temp_logger.info("Este log vai para diretório temporário")
    # Configuração anterior é restaurada automaticamente
```

## 📊 Logs Estruturados (JSON)

Os logs em `structured.jsonl` seguem o formato:

```json
{
  "timestamp": "2025-01-01T12:00:00.000000",
  "level": "INFO",
  "logger": "main",
  "function": "analyze_system",
  "line": 42,
  "message": "Análise concluída",
  "module": "analyzers.legacy_analyzer",
  "extra": {
    "category": "analysis",
    "files_processed": 150,
    "duration_seconds": 45.2
  }
}
```

## ⚙️ Configuração Avançada

### Variáveis de Ambiente

```bash
# Habilitar modo debug
export DEBUG=true

# Diretório customizado para logs
export LOG_DIR=/custom/logs/path
```

### Programática

```python
# Configuração personalizada
config = LoggerConfig(
    log_dir="custom_logs",
    enable_debug=True
)

# Verificar se logging está configurado
if is_logging_configured():
    logger = get_logger()

# Limpar recursos
cleanup_logging()
```

## 📝 Categorias de Log Disponíveis

| Categoria | Método | Uso |
|-----------|---------|-----|
| `analysis` | `logger.analysis()` | Análise de código legacy |
| `generation` | `logger.generation()` | Geração de código novo |
| `rag` | `logger.rag()` | Operações RAG/embedding |
| `amazon_q` | `logger.amazon_q()` | Chamadas para Amazon Q |
| `pipeline` | `logger.pipeline()` | Orquestração de pipeline |
| `feature` | `logger.feature()` | Processamento de features |
| `performance` | `logger.performance()` | Métricas de performance |
| `legacy_system` | `logger.legacy_system()` | Sistema legacy específico |
| `new_system` | `logger.new_system()` | Sistema novo específico |

## 🛠️ Exemplos Práticos

### Pipeline de Reengenharia

```python
def reengineer_system(legacy_path: str):
    logger = get_logger()
    
    # 1. Análise
    logger.analysis("Iniciando análise", system_path=legacy_path)
    
    # 2. Decomposição
    logger.pipeline("Decompondo em features", step="decomposition")
    
    # 3. Geração
    logger.generation("Gerando código Spring Boot", framework="spring-boot")
    
    # 4. Validação
    logger.pipeline("Validando código gerado", step="validation")
```

### Análise de Performance

```python
import time

@log_execution(category="performance")
def heavy_operation():
    start = time.time()
    # ... operação pesada ...
    duration = time.time() - start
    
    logger = get_logger()
    logger.performance("Operação pesada completada", 
                      duration=duration,
                      memory_used_mb=256)
```

### Integração com Amazon Q

```python
def call_amazon_q(prompt: str):
    logger = get_logger()
    
    logger.amazon_q("Enviando prompt", 
                   prompt_length=len(prompt),
                   estimated_tokens=len(prompt.split()) * 1.3)
    
    # ... chamada real ...
    
    logger.amazon_q("Resposta recebida",
                   response_length=len(response),
                   code_blocks=response.count("```"))
```

## 🔧 Troubleshooting

### Problemas Comuns

1. **Loguru não instalado**
   ```bash
   pip install loguru>=0.7.0
   ```

2. **Permissões de escrita**
   - O sistema automaticamente fallback para diretório temporário
   - Logs de aviso são exibidos no console

3. **Performance em produção**
   - Configure `debug=False` para reduzir overhead
   - Use rotação de arquivos apropriada

### Debug de Logs

```python
# Verificar configuração
if is_logging_configured():
    print("Logging configurado ✓")
else:
    print("Logging não configurado ✗")

# Testar diferentes níveis
logger = get_logger()
logger.debug("Debug message")
logger.info("Info message") 
logger.warning("Warning message")
logger.error("Error message")
```

## 📋 Checklist de Implementação

- [x] Sistema base de logging estruturado
- [x] Categorias específicas para o agente
- [x] Rotação automática de arquivos
- [x] Formatação JSON para análise
- [x] Decorador para logging automático
- [x] Context manager para uso temporário
- [x] Configuração via ambiente
- [x] Tratamento robusto de erros
- [x] Documentação completa
- [x] Exemplos práticos

## 🚀 Próximos Passos

1. **Integração com métricas**: Adicionar integração com Prometheus
2. **Dashboard**: Criar dashboard Grafana para visualização
3. **Alertas**: Sistema de alertas para erros críticos
4. **Sampling**: Implementar sampling para logs de alta frequência

---

**Nota**: Este sistema de logging é otimizado especificamente para o Java Reengineering Agent, fornecendo visibilidade completa do processo de reengenharia desde análise até geração do código final.
