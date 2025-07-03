# CLI Documentation - Java Reengineering Agent

Interface de linha de comando moderna e intuitiva para o agente de reengenharia Java.

## 🎯 Visão Geral

O CLI foi construído com **Typer** e **Rich** para fornecer uma experiência de usuário moderna com:
- ✨ Interface colorida e interativa
- 📊 Tabelas e painéis informativos
- 🚀 Progress bars para operações longas
- 🎯 Modo interativo guiado
- 📋 Help contextual abrangente

## 🚀 Comandos Principais

### Inicialização

```bash
# Mostrar ajuda geral
python src/main.py --help

# Mostrar versão
python src/main.py version

# Inicializar workspace
python src/main.py init my-project
python src/main.py init . --force  # força em diretório não vazio
```

### Análise de Sistema Legacy

```bash
# Análise básica
python src/main.py analyze

# Análise com parâmetros customizados
python src/main.py analyze \
  --legacy-path ./my-legacy-system \
  --output ./results \
  --deep \
  --format json

# Opções de formato: json, yaml, html
python src/main.py analyze --format html
```

### Decomposição em Features

```bash
# Decomposição usando DDD
python src/main.py decompose

# Metodologias disponíveis: ddd, feature, microservice
python src/main.py decompose --methodology microservice
```

### Geração de Código

```bash
# Gerar código Spring Boot
python src/main.py generate

# Framework customizado
python src/main.py generate \
  --framework spring-boot \
  --java-version 17
```

### Gerenciamento de Workspace

```bash
# Ver status do workspace
python src/main.py status

# Limpeza de arquivos gerados
python src/main.py clean
python src/main.py clean --logs --yes  # incluir logs, sem confirmação
```

### Configuração

```bash
# Configuração interativa
python src/main.py configure

# Modo interativo completo
python src/main.py interactive
```

## 🎯 Modo Interativo

O modo interativo guia você através de todo o processo:

```bash
python src/main.py interactive
```

### Fluxo do Modo Interativo:

1. **🏗️ Setup do Workspace**
   - Criação/validação do workspace
   - Configuração inicial

2. **🔍 Análise Legacy**
   - Localização do sistema legacy
   - Escolha do tipo de análise
   - Execução e resultados

3. **🧩 Decomposição**
   - Seleção de metodologia
   - Decomposição em bounded contexts

4. **🏭 Geração**
   - Escolha de framework
   - Versão do Java
   - Geração do código

5. **✅ Validação**
   - Verificação dos resultados
   - Relatórios finais

## ⚙️ Configuração Global

### Opções de Linha de Comando

```bash
python src/main.py [OPÇÕES GLOBAIS] COMANDO [ARGUMENTOS]

Opções Globais:
  --verbose, -v     # Logging verboso
  --debug, -d       # Modo debug
  --workspace, -w   # Diretório workspace
  --config, -c      # Arquivo de configuração
```

### Arquivo de Configuração

O CLI suporta arquivo `agent.toml` para configurações persistentes:

```toml
# agent.toml
project_name = "My Reengineering Project"
legacy_system_path = "./legacy-system"
target_java_version = "17"
target_spring_boot_version = "3.2"
enable_ddd_decomposition = true
use_amazon_q = true
log_level = "INFO"
```

### Variáveis de Ambiente

```bash
export DEBUG=true                    # Habilita modo debug
export LOG_DIR=/custom/logs/path     # Diretório de logs customizado
export WORKSPACE_DIR=/my/workspace   # Workspace padrão
```

## 📁 Estrutura do Workspace

O CLI cria e mantém uma estrutura organizada:

```
my-project/
├── agent.toml              # Configuração do projeto
├── README.md               # Documentação do projeto
├── legacy-system/          # Código legacy a ser analisado
├── analysis-results/       # Resultados da análise
│   ├── analysis_result.json
│   ├── dependencies.graph
│   └── code_smells.report
├── feature-backlog/        # Features decompostas
│   ├── user-management/
│   ├── payment-processing/
│   └── reporting/
├── new-system/            # Código gerado
│   ├── src/main/java/
│   ├── pom.xml
│   └── docker-compose.yml
├── logs/                  # Logs de execução
└── output/               # Artefatos adicionais
```

## 🎨 Features da Interface

### Rich Formatting

O CLI usa formatação rica para melhor experiência:

- **🎨 Cores**: Diferentes cores para diferentes tipos de informação
- **📊 Tabelas**: Dados estruturados em tabelas elegantes
- **📦 Painéis**: Informações importantes em painéis destacados
- **🔄 Progress**: Barras de progresso para operações longas
- **✅ Status**: Indicadores visuais claros de sucesso/erro

### Help Contextual

```bash
# Help geral
python src/main.py --help

# Help específico de comando
python src/main.py analyze --help
python src/main.py generate --help
```

## 🔧 Exemplos Práticos

### Fluxo Completo Básico

```bash
# 1. Criar projeto
python src/main.py init my-legacy-reengineering

# 2. Entrar no diretório
cd my-legacy-reengineering

# 3. Copiar código legacy para legacy-system/

# 4. Analisar
python ../src/main.py analyze

# 5. Ver status
python ../src/main.py status

# 6. Decompor (quando implementado)
python ../src/main.py decompose

# 7. Gerar (quando implementado)
python ../src/main.py generate
```

### Fluxo com Parâmetros Customizados

```bash
# Análise detalhada com output customizado
python src/main.py analyze \
  --legacy-path /path/to/legacy \
  --output ./detailed-analysis \
  --deep \
  --format html

# Geração com Spring Boot específico
python src/main.py generate \
  --framework spring-boot \
  --java-version 21 \
  --output ./modern-system
```

### Uso com Logging Verboso

```bash
# Debug completo
python src/main.py --debug --verbose analyze

# Logs salvos em local customizado
python src/main.py --workspace ./my-workspace analyze
```

## 🛠️ Extensibilidade

### Adicionando Novos Comandos

```python
@app.command()
def meu_comando(
    param: str = typer.Option("default", help="Descrição do parâmetro")
):
    """🔥 Descrição do meu comando"""
    console.print(f"Executando comando com: {param}")
```

### Integrando com Sistema de Logging

```python
def minha_funcao():
    if app_state.logger:
        app_state.logger.info("Minha operação iniciada")
    
    # ... lógica ...
    
    if app_state.logger:
        app_state.logger.info("Operação concluída")
```

## 🧪 Testes

### Executar Testes do CLI

```bash
# Teste completo do CLI
./test_cli.sh

# Teste manual de comandos
python src/main.py version
python src/main.py init test-workspace --force
```

### Teste de Integração

```bash
# Teste do fluxo completo
python src/main.py init integration-test --force
cd integration-test
python ../src/main.py analyze
python ../src/main.py status
```

## 📋 Roadmap do CLI

### ✅ Implementado

- [x] Estrutura base com Typer
- [x] Comandos básicos (init, analyze, status, clean)
- [x] Interface rica com Rich
- [x] Sistema de configuração
- [x] Modo interativo básico
- [x] Integração com logging
- [x] Help contextual

### 🔄 Em Desenvolvimento

- [ ] Integração real com analisadores
- [ ] Comandos de decomposição
- [ ] Comandos de geração
- [ ] Validação de resultados
- [ ] Auto-completion
- [ ] Plugins system

### 🎯 Planejado

- [ ] Dashboard web opcional
- [ ] Integração CI/CD
- [ ] Templates de projeto
- [ ] Métricas avançadas
- [ ] Relatórios customizáveis

## 🚨 Troubleshooting

### Problemas Comuns

1. **Comando não encontrado**
   ```bash
   # Certificar que está no diretório correto
   python src/main.py --help
   ```

2. **Dependências em falta**
   ```bash
   pip install typer rich loguru
   ```

3. **Permissões de workspace**
   ```bash
   # Verificar permissões de escrita
   python src/main.py init --force
   ```

4. **Logs não aparecem**
   ```bash
   # Forçar modo verboso
   python src/main.py --debug --verbose analyze
   ```

---

**O CLI está pronto para uso e fornece uma base sólida para expandir conforme os componentes do agente são implementados!** 🚀
