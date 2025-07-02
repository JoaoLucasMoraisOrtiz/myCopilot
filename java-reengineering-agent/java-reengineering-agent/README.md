# Java Legacy Reengineering Agent

Agente de IA para reengenharia completa de sistemas Java legados usando Amazon Q.

## Paradigma: Reengenharia em vez de Migração

Este agente não tenta "migrar" código legacy ruim. Em vez disso:
1. Analisa profundamente o sistema legacy
2. Extrai regras de negócio e conhecimento
3. Decompõe em features modernas
4. Reconstrói do zero com arquitetura limpa

## Tecnologias

- **AI**: Amazon Q CLI integration
- **RAG**: CodeBERT + SQLite vector store
- **Architecture**: Clean Architecture + DDD
- **Target**: Spring Boot 3.2 + Java 17

## Quick Start

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar análise
python src/main.py analyze --legacy-path /path/to/legacy/system

# Ver progresso
python src/main.py status
```

Para documentação completa, ver [architecture-diagram.md](../architecture-diagram.md) no diretório pai.
