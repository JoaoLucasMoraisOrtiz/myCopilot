# MyCopilot - Agent de Análise e Criação de Código

## Descrição

O myCopilot é um agente automatizado para análise e criação de código, com foco em auxiliar o entendimento e a geração de projetos de software. Ele pode operar em dois modos principais:

- **edit**: Analisa um projeto existente
- **new**: Cria um novo projeto do zero

## Funcionalidades Principais

### Análise Multi-Projeto (NOVO!)

A partir da versão atual, o myCopilot suporta **análise simultânea de múltiplos projetos**:

1. **Projeto Principal**: O projeto sendo analisado (edit) ou criado (new)
2. **Projetos Externos**: Projetos de referência ou legados que podem ser analisados simultaneamente
3. **Comandos Específicos por Projeto**: Especifique de qual projeto buscar informações
4. **Ideal para Migrações**: Compare sistema legado com novo sistema em desenvolvimento

**Casos de Uso:**
- Migração de sistemas legados
- Comparação entre diferentes versões
- Análise de projetos de referência
- Desenvolvimento baseado em sistemas existentes

### Build Automático e Correção de Erros

O myCopilot inclui funcionalidade de **build automático** com correção inteligente de erros:

1. **Detecção Automática**: Identifica projetos Java com Maven/Gradle
2. **Build Automático**: Executa `mvn clean install` ou `gradle build` automaticamente
3. **Correção de Erros**: Usa LLM para analisar e corrigir erros de compilação
4. **Iteração Inteligente**: Repete o processo até eliminar todos os erros
5. **Finalização Segura**: Só finaliza quando o projeto compila sem erros

### Análise de Projetos

- Suporte a projetos Java, React/Next.js e projetos mistos
- Análise de estrutura de classes, métodos e relacionamentos
- Detecção automática do tipo de projeto
- Geração de relatórios detalhados

### Criação de Código

- Geração de código Java com Spring Boot
- Correção automática de sintaxe
- Integração com frameworks modernos
- Validação através de build

## Uso

### Instalação

```bash
# Clone o repositório
git clone <repo-url>
cd myCopilot

# Instale dependências Python
pip install -r requirements.txt

# Certifique-se de ter o Chrome instalado para uso do LLM
```

### Iniciando o Chrome para LLM

O projeto usa GitHub Copilot via browser. Inicie o Chrome com:

**Linux/Mac:**
```bash
google-chrome --remote-debugging-port=9222 --remote-debugging-address=127.0.0.1 --remote-allow-origins=* --user-data-dir=/tmp/chrome_debug_profile --no-first-run --no-default-browser-check --disable-web-security --disable-features=VizDisplayCompositor --disable-dev-shm-usage --no-sandbox https://vscode.dev
```

**Windows:**
```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --remote-debugging-address=127.0.0.1 --remote-allow-origins=* --user-data-dir="C:\tmp\chrome_debug_profile" --no-first-run --no-default-browser-check --disable-web-security --disable-features=VizDisplayCompositor --disable-dev-shm-usage --no-sandbox https://vscode.dev
```

### Comandos Básicos

#### Analisar Projeto Existente
```bash
python3 main.py edit --project-path="/caminho/para/projeto" --goal="Entenda este sistema e crie um plano de modernização"
```

#### Criar Novo Projeto com Referência a Sistema Legado
```bash
python3 main.py new \
  --project-path="/caminho/para/novo/projeto" \
  --goal="Crie um microserviço REST moderno baseado no sistema legado em /caminho/para/sistema/legado. Analise o legado e crie versão com Spring Boot 3 e Java 17"
```

#### Migração de Sistema Legado
```bash
python3 main.py new \
  --project-path="/home/user/new-system" \
  --goal="Migre o sistema SOAP legado em /home/user/legacy-soap para REST com Spring Boot. O legado está documentado em /home/user/legacy-soap/README.md"
```

#### Continuar Conversa Anterior
```bash
python3 main.py edit --continue --project-path="/caminho/para/projeto"
```

### Casos de Uso Avançados

#### Análise Comparativa de Projetos
```bash
python3 main.py edit \
  --project-path="/projeto/principal" \
  --goal="Compare este projeto com o projeto de referência em /projeto/referencia e identifique diferenças arquiteturais importantes" \
  --max-turns=15
```

#### Migração Completa SOAP→REST
```bash
# Crie um exemplo de projeto legado para teste:
python3 create_legacy_example.py

# Execute a migração automática:
python3 main.py new \
  --project-path="/home/user/modernized-service" \
  --goal="Analise o sistema SOAP legado em /tmp/legacy_soap_XXXXX e crie versão REST com Spring Boot 3. Migre autenticação LDAP e todas as funcionalidades." \
  --max-turns=25
```

## Fluxo de Build Automático

Quando o agente finaliza a criação/modificação de código:

1. **Detecção**: Verifica se é projeto Java com Maven/Gradle
2. **Build Inicial**: Executa comando de build apropriado
3. **Análise de Erros**: Se houver erros, analisa com LLM
4. **Correção**: LLM sugere e aplica correções nos arquivos
5. **Rebuild**: Executa build novamente
6. **Iteração**: Repete até eliminar todos os erros (máx. 5 iterações)
7. **Finalização**: Confirma sucesso ou reporta problemas restantes

## Estrutura do Projeto

```
myCopilot/
├── main.py                 # Ponto de entrada principal
├── requirements.txt        # Dependências Python
├── core/                   # Módulos principais
│   ├── agent/             # Lógica do agente
│   ├── llm/               # Cliente LLM
│   └── code_corrector/    # Correção de código
├── analyzers/             # Analisadores por linguagem
├── devtools/              # Integração Chrome DevTools
└── output_project/        # Diretório padrão para novos projetos
```

## Dependências

### Sistema
- Python 3.8+
- Google Chrome
- Maven ou Gradle (para projetos Java)

### Python
- websocket-client
- javalang

## Resolução de Problemas

### Chrome não conecta
- Certifique-se que o Chrome foi iniciado com os parâmetros corretos
- Verifique se a porta 9222 está livre
- Teste acesso em http://localhost:9222/json

### Build falha
- Verifique se Maven/Gradle estão instalados e no PATH
- Confirme que o Java está configurado corretamente
- O agente tentará corrigir automaticamente até 5 vezes

### LLM não responde
- Verifique conexão com o Chrome
- Confirme que o GitHub Copilot está ativo no VS Code
- Teste manualmente no chat do Copilot

## Exemplo de Uso Multi-Projeto

```bash
# 1. Inicie o Chrome
google-chrome --remote-debugging-port=9222 --remote-debugging-address=127.0.0.1 --remote-allow-origins=* --user-data-dir=/tmp/chrome_debug_profile --no-first-run --no-default-browser-check --disable-web-security --disable-features=VizDisplayCompositor --disable-dev-shm-usage --no-sandbox https://vscode.dev

# 2. Crie um novo sistema baseado em legado
python3 main.py new \
  --project-path="/home/user/modernized-app" \
  --goal="Analise o sistema SOAP legado em /home/user/legacy-soap e crie uma versão REST moderna com Spring Boot 3. Migre a lógica de autenticação LDAP e os serviços principais." \
  --max-turns=20

# 3. O agente irá:
#    - Analisar automaticamente o projeto legado (/home/user/legacy-soap)
#    - Entender a arquitetura e funcionalidades existentes
#    - Criar o novo projeto modernizado (/home/user/modernized-app)
#    - Migrar funcionalidades do legado para o novo
#    - Executar build automático e corrigir erros
#    - Finalizar com projeto funcionando e compilando
```

### Comandos Disponíveis para LLM

Quando o LLM está executando, ele tem acesso aos seguintes comandos:

#### Análise Multi-Projeto:
- `analyze("/caminho/projeto/legado")`: Analisa projeto externo
- `list_projects()`: Lista todos os projetos analisados
- `list_classes("/caminho/projeto")`: Lista classes de projeto específico
- `get_code("Classe", "metodo", true, "/caminho/projeto")`: Código de projeto específico

#### Exemplo de Fluxo do LLM:
```json
{"command": "analyze", "args": ["/home/user/legacy-soap"]}
{"command": "list_projects", "args": []}
{"command": "list_classes", "args": ["/home/user/legacy-soap"]}
{"command": "get_code", "args": ["com.legacy.AuthService", null, true, "/home/user/legacy-soap"]}
{"command": "save_code", "args": ["src/main/java/com/modern/auth/AuthService.java", "codigo_modernizado"]}
```
