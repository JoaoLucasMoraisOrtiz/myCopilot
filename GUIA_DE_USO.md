# 📖 GUIA DE USO DO SISTEMA DE MIGRAÇÃO

## 🚀 **INICIANDO O SISTEMA**

Para executar o sistema de migração:

```bash
python main.py
```

O sistema apresentará o menu principal:

```
🚀 MIGRADOR DE SISTEMAS LEGADOS

[0] Fase 0: Configuração da Migração
[1] Executar todas as fases de migração
[2] Fase 1: Análise do Sistema Legado
[3] Fase 2: Construção do Roadmap
[4] Fase 3: Criação de Tasks
[5] Fase 4: Implementação
[6] Analisar código de projeto existente
```

## 📋 **1. FORMATO DO ARQUIVO DE CONFIGURAÇÃO (FASE 0)**

### **Localização do Arquivo**
O sistema solicitará o caminho para seu arquivo de configuração YAML ou JSON. Você pode criar o arquivo em qualquer local e fornecer o caminho completo.

### **Formato YAML (Recomendado)**

```yaml
# migration_config.yaml
migration_config:
  # === INFORMAÇÕES BÁSICAS ===
  project_name: "Sistema ERP Corporativo"
  current_version: "v2.1.3"
  migration_objective: "Modernizar sistema legado para arquitetura cloud-native"
  
  # === TECNOLOGIAS ATUAIS ===
  current_stack:
    language: "Java"
    version: "6"
    framework: "Struts 1.3"
    server: "WebLogic 10.3"
    database:
      type: "Oracle"
      version: "11g"
    frontend: "JSP + JavaScript"
    build_tool: "Ant"
    
  # === TECNOLOGIAS DE DESTINO ===
  target_stack:
    language: "Java"
    version: "17"
    framework: "Spring Boot 3.x"
    server: "WildFly 27"
    database:
      type: "PostgreSQL"
      version: "15"
    frontend: "React 18 + TypeScript"
    build_tool: "Maven"
    
  # === ARQUITETURA ALVO ===
  target_architecture:
    type: "microservices"  # ou "monolith", "modular_monolith"
    api_style: "REST"      # ou "SOAP", "GraphQL"
    messaging: "RabbitMQ"  # ou "Kafka", "ActiveMQ", "none"
    cache: "Redis"         # ou "Hazelcast", "none"
    
  # === INFRAESTRUTURA ===
  infrastructure:
    deployment: "Kubernetes"    # ou "Docker", "Traditional"
    cloud_provider: "AWS"       # ou "Azure", "GCP", "OnPremise"
    database_strategy: "migration"  # ou "rewrite", "hybrid"
    
  # === PREFERÊNCIAS DE MIGRAÇÃO ===
  migration_preferences:
    strategy: "strangler_fig"   # ou "big_bang", "parallel_run", "phased"
    data_migration: "incremental"  # ou "bulk", "realtime_sync"
    testing_approach: "automated"  # ou "manual", "hybrid"
    rollback_strategy: "blue_green"  # ou "canary", "feature_flags"
    
  # === RESTRIÇÕES E REQUISITOS ===
  constraints:
    max_downtime: "4 hours"
    budget_limit: "500k USD"
    timeline: "12 months"
    team_size: 8
    compliance_requirements:
      - "SOX"
      - "GDPR"
      - "ISO27001"
      
  # === PRIORIDADES DE NEGÓCIO ===
  business_priorities:
    - "performance_improvement"
    - "maintainability"
    - "scalability"
    - "cost_reduction"
    - "security_enhancement"
    
  # === COMPONENTES CRÍTICOS ===
  critical_components:
    - name: "Payment Processing"
      description: "Sistema de processamento de pagamentos"
      technology: "Java + Oracle"
      criticality: "high"
      
    - name: "User Authentication"
      description: "Sistema de autenticação LDAP"
      technology: "Java + LDAP"
      criticality: "high"
      
    - name: "Reporting Engine"
      description: "Motor de relatórios em batch"
      technology: "Java + Crystal Reports"
      criticality: "medium"
```

### **Formato JSON (Alternativo)**

```json
{
  "migration_config": {
    "project_name": "Sistema ERP Corporativo",
    "current_version": "v2.1.3",
    "migration_objective": "Modernizar sistema legado para arquitetura cloud-native",
    
    "current_stack": {
      "language": "Java",
      "version": "6",
      "framework": "Struts 1.3",
      "server": "WebLogic 10.3",
      "database": {
        "type": "Oracle",
        "version": "11g"
      },
      "frontend": "JSP + JavaScript",
      "build_tool": "Ant"
    },
    
    "target_stack": {
      "language": "Java",
      "version": "17",
      "framework": "Spring Boot 3.x",
      "server": "WildFly 27",
      "database": {
        "type": "PostgreSQL",
        "version": "15"
      },
      "frontend": "React 18 + TypeScript",
      "build_tool": "Maven"
    },
    
    "target_architecture": {
      "type": "microservices",
      "api_style": "REST",
      "messaging": "RabbitMQ",
      "cache": "Redis"
    },
    
    "infrastructure": {
      "deployment": "Kubernetes",
      "cloud_provider": "AWS",
      "database_strategy": "migration"
    },
    
    "migration_preferences": {
      "strategy": "strangler_fig",
      "data_migration": "incremental",
      "testing_approach": "automated",
      "rollback_strategy": "blue_green"
    },
    
    "constraints": {
      "max_downtime": "4 hours",
      "budget_limit": "500k USD",
      "timeline": "12 months",
      "team_size": 8,
      "compliance_requirements": ["SOX", "GDPR", "ISO27001"]
    },
    
    "business_priorities": [
      "performance_improvement",
      "maintainability", 
      "scalability",
      "cost_reduction",
      "security_enhancement"
    ],
    
    "critical_components": [
      {
        "name": "Payment Processing",
        "description": "Sistema de processamento de pagamentos",
        "technology": "Java + Oracle",
        "criticality": "high"
      }
    ]
  }
}
```

## 📁 **2. ESPECIFICANDO O DIRETÓRIO DO SISTEMA LEGADO**

### **Durante a Execução**

O sistema solicita o diretório do projeto legado em **dois momentos**:

#### **A) Opção [6] - Análise de Código do Projeto**

```
Escolha a operação:
[6] Analisar código de projeto existente

Digite o caminho do projeto para analisar: /caminho/para/seu/projeto/legado
```

**Exemplo:**
```
Digite o caminho do projeto para analisar: /home/usuario/projetos/sistema-erp-legado
```

#### **B) Durante as Fases de Migração (quando necessário)**

O sistema pode solicitar o caminho durante as fases de análise para examinar o código fonte:

```
📁 Para análise detalhada, forneça o caminho do sistema legado:
Caminho: /home/usuario/projetos/sistema-erp-legado
```

### **Estrutura Esperada do Projeto Legado**

O sistema suporta diferentes estruturas de projeto:

#### **Projeto Java Maven/Gradle:**
```
meu-projeto-legado/
├── src/
│   ├── main/
│   │   ├── java/
│   │   └── resources/
│   └── test/
├── pom.xml (ou build.gradle)
└── README.md
```

#### **Projeto Java Ant:**
```
meu-projeto-legado/
├── src/
├── lib/
├── build.xml
└── web/
    ├── WEB-INF/
    └── jsp/
```

#### **Projeto Python:**
```
meu-projeto-legado/
├── src/
│   └── app/
├── requirements.txt
├── setup.py
└── tests/
```

## 🔄 **FLUXO DE EXECUÇÃO RECOMENDADO**

### **Primeira Execução (Completa):**

1. **Preparar configuração**:
   ```bash
   # Criar arquivo de configuração
   nano migration_config.yaml
   ```

2. **Executar Fase 0**:
   ```
   python main.py
   [0] Fase 0: Configuração da Migração
   ```

3. **Executar todas as fases**:
   ```
   [1] Executar todas as fases de migração
   ```

4. **Analisar código (opcional)**:
   ```
   [6] Analisar código de projeto existente
   ```

### **Execução Incremental:**

Se quiser executar fase por fase:

```
python main.py
[0] Fase 0: Configuração da Migração
# ... configurar

python main.py  
[2] Fase 1: Análise do Sistema Legado
# ... analisar

python main.py
[3] Fase 2: Construção do Roadmap
# ... roadmap

# E assim por diante...
```

## 📂 **ESTRUTURA DE SAÍDA**

Após a execução, o sistema cria:

```
migration_docs/
├── migration_config.yaml          # Sua configuração
├── global_context.md              # Contexto global acumulado
├── architecture-analysis.md       # Análise da arquitetura
├── business-flows.md              # Fluxos de negócio
├── target-architecture.md         # Arquitetura alvo
├── migration-backlog.md           # Tasks de migração
├── project_structure.json         # Estrutura do novo projeto
├── files_metadata.json            # Metadados dos arquivos
├── project_summary.md             # Resumo do projeto
└── new_system/                    # 🎯 NOVO SISTEMA MIGRADO
    ├── backend/
    ├── frontend/
    ├── database/
    └── infrastructure/
```

## ⚠️ **DICAS IMPORTANTES**

### **1. Configuração Inicial**
- Use YAML para melhor legibilidade
- Seja específico nas versões de tecnologia
- Detalhe componentes críticos
- Defina restrições realistas

### **2. Diretório do Sistema Legado**
- Forneça caminho absoluto: `/home/usuario/projeto`
- Não use caminho relativo: `./projeto`
- Certifique-se que o diretório existe e é acessível
- O sistema analisa recursivamente todos os subdiretórios

### **3. Validação da Configuração**
O sistema valida automaticamente:
- ✅ Formato YAML/JSON válido
- ✅ Campos obrigatórios presentes
- ✅ Valores coerentes
- ✅ Tecnologias suportadas

### **4. Troubleshooting**

**Erro: "Arquivo de configuração inválido"**
- Verifique sintaxe YAML/JSON
- Use validador online se necessário

**Erro: "Diretório não encontrado"**
- Confirme que o caminho está correto
- Verifique permissões de acesso

**Erro: "Nenhum arquivo de código encontrado"**
- Verifique se o diretório contém código fonte
- Sistema suporta: `.java`, `.py`, `.js`, `.ts`

## 📞 **SUPORTE**

Para mais ajuda:
- Verifique os logs em `migration_docs/`
- Consulte exemplos em `examples/`
- Execute testes: `python test_project_structure.py`
