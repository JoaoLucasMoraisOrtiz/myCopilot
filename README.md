# 🚀 Sistema de Migração de Sistemas Legados

Sistema inteligente para migração automatizada de sistemas legados utilizando LLM (Large Language Models) integrado com VS Code e Copilot Chat.

## 📋 Visão Geral

Este sistema oferece uma abordagem estruturada para migrar sistemas legados através de 5 fases:

- **Fase 0**: Configuração da Migração (novo!)
- **Fase 1**: Análise do Sistema Legado
- **Fase 2**: Planejamento da Migração
- **Fase 3**: Implementação Incremental
- **Fase 4**: Validação e Integração

### ✨ Características Principais

- 🧠 **Integração com LLM**: Utiliza Copilot Chat via automação de browser
- 🔄 **Sistema de Feedback**: Loops de realimentação inteligente
- 📁 **Organização Automática**: Estrutura profissional de projeto
- ⚙️ **Configuração Flexível**: YAML/JSON para especificar detalhes da migração
- 🧪 **Validação**: Testes automatizados e verificação de qualidade

## 🚀 Início Rápido

### 1. Setup Inicial
```bash
# Configuração interativa
python setup.py

# Ou criar configuração manualmente
cp migration_config_example.yaml minha_migracao.yaml
```

### 2. Validar Configuração
```bash
python validate_config.py minha_migracao.yaml
```

### 3. Executar Migração
```bash
python main.py
# Escolha: [0] Fase 0: Configuração da Migração
```

## 📁 Estrutura do Projeto

```
myCopilot/
├── main.py                     # Orquestrador principal
├── migration_prompts.py        # Prompts para LLM
├── project_structure_manager.py # Organizador de estrutura
├── setup.py                   # Configuração inicial
├── validate_config.py         # Validador de configuração
├── migration_config_example.yaml # Exemplo de configuração
├── GUIA_DE_USO.md             # Documentação completa
├── README.md                  # Este arquivo
├── analyzers/                 # Analisadores de código
│   ├── python_analyzer.py
│   └── java_analyzer.py
├── helper/                    # Módulos auxiliares
│   ├── context_manager.py
│   ├── code_parser.py
│   └── task_manager.py
└── devtools/                  # Automação de browser
    ├── client.py
    ├── chat.py
    ├── dom.py
    ├── input.py
    └── page.py
```

## ⚙️ Configuração

### Arquivo de Configuração (YAML)
```yaml
migration_config:
  project_name: "MeuSistemaLegado"
  migration_objective: "Modernizar de Java 8 para Java 17"
  
  current_stack:
    language: "Java"
    version: "8"
    framework: "Spring"
  
  target_stack:
    language: "Java"
    version: "17"
    framework: "Spring Boot"
  
  target_architecture:
    type: "microservices"
    api_style: "REST"
```

### Diretório do Sistema Legado

O sistema precisa acessar o código fonte do sistema legado. Configure na **Fase 0**:

- 📁 Diretório local: `/caminho/para/sistema/legado`
- 🔗 Repositório Git: Clone primeiro, depois informe o caminho
- 📦 Arquivo compactado: Extraia primeiro, depois informe o caminho

## 🔧 Dependências

```bash
pip install selenium webdriver-manager pyyaml
```

### Requisitos do Sistema
- Python 3.7+
- Google Chrome
- VS Code com Copilot Chat
- Conexão com internet

## 📚 Documentação

- 📖 **[GUIA_DE_USO.md](GUIA_DE_USO.md)**: Documentação completa
- 🧪 **[validate_config.py](validate_config.py)**: Validador de configuração
- 📋 **[migration_config_example.yaml](migration_config_example.yaml)**: Exemplo completo

## 🎯 Fases da Migração

### Fase 0: Configuração 🆕
- Definição de objetivos e restrições
- Especificação de stacks atual e alvo
- Configuração de arquitetura alvo
- Identificação de componentes críticos

### Fase 1: Análise
- Análise completa do código legado
- Identificação de dependências
- Mapeamento de arquitetura atual
- Relatório de complexidade

### Fase 2: Planejamento
- Estratégia de migração
- Plano de implementação
- Identificação de riscos
- Timeline detalhado

### Fase 3: Implementação
- Migração incremental
- Refatoração de código
- Atualização de dependências
- Testes unitários

### Fase 4: Validação
- Testes de integração
- Validação de performance
- Verificação de compatibilidade
- Documentação final

## 🔄 Sistema de Feedback

O sistema inclui loops de realimentação inteligente:

- **P4_2 → Context3**: Feedback de implementação para contexto
- **P4_3 → Context3**: Feedback de validação para contexto
- **Context3**: Base de conhecimento acumulado

## 📊 Estrutura de Saída

O sistema organiza automaticamente o código gerado em uma estrutura profissional:

```
projeto_migrado/
├── src/
│   ├── main/
│   ├── test/
│   └── resources/
├── config/
├── docs/
├── scripts/
└── README.md
```

## 🧪 Testes

Execute os testes para validar o sistema:

```bash
python test1.py  # Teste básico
python test2.py  # Teste de integração
python test3.py  # Teste de validação
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.

## 🆘 Suporte

- 📖 Consulte o [GUIA_DE_USO.md](GUIA_DE_USO.md)
- 🧪 Use `python validate_config.py` para verificar configuração
- 🚀 Execute `python setup.py` para configuração interativa

## 🏆 Características Avançadas

- **🔍 Análise Inteligente**: Detecção automática de tecnologias
- **📋 Templates**: Configurações pré-definidas para cenários comuns
- **🔄 Iterativo**: Processo incremental com validação contínua
- **📊 Relatórios**: Documentação automática do processo
- **🛡️ Segurança**: Validação de configuração e código

---

**Desenvolvido com ❤️ para facilitar migrações de sistemas legados**
