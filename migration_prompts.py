PROMPTS = {
    # Fase 1: Análise do Sistema Legado
    "P1_1": """
Prompt 1.1: Mapeamento da Arquitetura

**CONTEXTO DISPONÍVEL:**
- Configuração de migração da Fase 0 (objetivos, tecnologias atuais/alvo, prioridades)
- Estrutura do workspace do sistema legado (diretórios, arquivos, tecnologias detectadas)
- Amostras de código do sistema atual

**TAREFA:**
Analise o sistema legado fornecido no contexto e forneça um mapeamento detalhado da arquitetura atual. Use as informações específicas do código e configurações encontradas.

1. **Visão Geral da Arquitetura**
   - Tipo de arquitetura identificada no código analisado
   - Principais camadas e componentes encontrados nos arquivos
   - Tecnologias confirmadas pela análise do código (compare com a configuração da Fase 0)

2. **Componentes Principais**
   - Frontend: tecnologias e arquivos identificados (HTML, JSP, CSS, JS, etc.)
   - Backend: linguagens, frameworks e padrões encontrados no código
   - Banco de dados: scripts SQL, configurações de conexão, entidades
   - Integrações externas: chamadas de API, bibliotecas externas identificadas

3. **Infraestrutura Detectada**
   - Servidores e configurações encontradas (web.xml, application.properties, etc.)
   - Scripts de deployment identificados
   - Configurações de ambiente e logs

4. **Pontos de Atenção para Migração Específica**
   - Componentes incompatíveis com as tecnologias alvo da configuração
   - Dependências problemáticas para a migração configurada
   - Código legado que requer refatoração para o stack de destino

5. **Alinhamento com Objetivos da Fase 0**
   - Como a arquitetura atual se relaciona com as tecnologias alvo especificadas
   - Complexidade estimada para a migração baseada no código analisado
   - Riscos específicos identificados no código para a migração configurada

**IMPORTANTE:** Base sua análise exclusivamente no código e configurações fornecidas no contexto. Cite arquivos específicos e trechos de código quando relevante. Relacione tudo com os objetivos definidos na Fase 0.

Formate sua resposta em markdown com seções bem definidas.
""",

    "P1_2": """
Prompt 1.2: Fluxos de Negócio

**CONTEXTO DISPONÍVEL:**
- Configuração de migração da Fase 0 (objetivos, tecnologias atuais/alvo, prioridades)
- Estrutura do workspace do sistema legado analisada
- Componentes e arquivos identificados na análise anterior
- Amostras de código que implementam funcionalidades

**TAREFA:**
Baseando-se no código fornecido no contexto, identifique e descreva os principais fluxos de negócio do sistema. Use evidências específicas do código analisado.

1. **Identificação dos Fluxos (baseada no código)**
   - Fluxos identificados através da análise de controllers, services, endpoints
   - Usuários/atores extraídos dos comentários, documentação e estrutura de código
   - Frequência estimada baseada na complexidade e estrutura dos métodos
   - Relevância para a migração específica configurada na Fase 0

2. **Mapeamento Técnico (evidências do código)**
   - Componentes e classes envolvidas em cada fluxo (cite arquivos específicos)
   - APIs, endpoints e integrações identificadas no código
   - Estruturas de dados e entidades encontradas
   - Compatibilidade com as tecnologias de destino da Fase 0

3. **Complexidade e Riscos de Migração**
   - Fluxos com código mais complexo para migrar ao stack alvo
   - Dependências críticas identificadas que impedem migração
   - Impacto estimado no negócio durante a migração desses fluxos
   - Adaptações necessárias para as tecnologias alvo especificadas

4. **Oportunidades de Melhoria na Migração**
   - Automações possíveis identificadas no código atual
   - Simplificações viáveis com as tecnologias de destino
   - Melhorias de performance identificadas para o novo stack
   - Refatorações que se beneficiam das tecnologias alvo

**IMPORTANTE:** Cite arquivos específicos, métodos e classes encontrados no contexto. Base sua análise em evidências concretas do código fornecido. Relacione tudo com os objetivos da migração definidos na Fase 0.

Use diagramas em texto quando necessário e organize em markdown.
""",

    "P1_3": """
Prompt 1.3: Análise de Dependências

**CONTEXTO DISPONÍVEL:**
- Configuração de migração da Fase 0 (tecnologias atuais/alvo, restrições, prioridades)
- Estrutura do sistema legado com arquivos de configuração identificados
- Arquivos de build e dependências (pom.xml, build.gradle, etc.) encontrados
- Código fonte com imports e dependências identificadas

**TAREFA:**
Baseando-se nos arquivos de configuração e código fornecidos no contexto, faça uma análise completa das dependências do sistema.

1. **Dependências Internas (extraídas do código)**
   - Bibliotecas e frameworks identificadas nos arquivos de build
   - Versões específicas encontradas nos arquivos de configuração
   - Imports e dependências entre módulos descobertas no código
   - Compatibilidade com as tecnologias alvo da Fase 0

2. **Dependências Externas (identificadas no workspace)**
   - APIs de terceiros encontradas no código (URLs, clients, etc.)
   - Serviços externos identificados em configurações
   - Integrações descobertas no código (especialmente componentes críticos da Fase 0)
   - Jars e bibliotecas externas encontradas

3. **Impacto na Migração Específica**
   - Dependências incompatíveis com as tecnologias alvo especificadas
   - Versões que precisam ser atualizadas para o stack de destino
   - Alternativas disponíveis para dependências problemáticas
   - Esforço estimado de migração por dependência baseado na análise

4. **Recomendações Técnicas (baseadas na configuração)**
   - Dependências que devem ser atualizadas primeiro para a migração
   - Substituições necessárias para atingir o stack alvo
   - Ordem de migração baseada na análise de dependências
   - Riscos e mitigações específicas da migração configurada

**IMPORTANTE:** Cite arquivos específicos de configuração, versões exatas encontradas e trechos de código relevantes. Base suas recomendações na análise concreta dos arquivos fornecidos e relacione com os objetivos da Fase 0.

Organize por criticidade e impacto na migração especificada.
""",

    # Fase 2: Construção do Roadmap
    "P2_1": """
Prompt 2.1: Glossário Técnico

**IMPORTANTE:** Base-se na configuração de migração (Fase 0) para priorizar tecnologias relevantes.

Com base na análise anterior, crie um glossário técnico completo:

1. **Tecnologias Atuais**
   - Definição e uso no sistema atual
   - Versões específicas utilizadas
   - Limitações identificadas para a migração alvo

2. **Tecnologias de Destino**
   - Definição das tecnologias especificadas na configuração
   - Benefícios para o contexto específico da migração
   - Requisitos e dependências das novas tecnologias

3. **Conceitos de Migração**
   - Terminologia específica da migração configurada
   - Padrões arquiteturais envolvidos
   - Metodologias aplicáveis ao stack alvo

4. **Mapeamento de Equivalências**
   - Correspondência entre tecnologias atuais e de destino
   - Alternativas disponíveis para componentes incompatíveis
   - Gaps que requerem soluções específicas

Organize alfabeticamente com definições claras e contextualizadas para a migração especificada.
""",

    "P2_2": """
Prompt 2.2: Estrutura de Fases

**IMPORTANTE:** Considere a configuração de migração para definir prioridades e sequenciamento.

Defina as fases da migração considerando as especificações da Fase 0:

1. **Fase de Preparação**
   - Atualizações de infraestrutura necessárias para o stack alvo
   - Preparação do ambiente para as tecnologias de destino
   - Treinamento da equipe nas novas tecnologias especificadas

2. **Fases de Migração Técnica**
   - Ordem de migração baseada nas tecnologias alvo
   - Componentes que podem ser migrados em paralelo
   - Dependências críticas que definem a sequência

3. **Marcos e Entregas**
   - Deliverables específicos para cada fase
   - Critérios de sucesso alinhados com os objetivos da migração
   - Pontos de validação e rollback

4. **Recursos e Timeline**
   - Estimativas baseadas na complexidade das tecnologias alvo
   - Recursos necessários por fase
   - Cronograma realista considerando a migração especificada

Organize em cronograma detalhado com dependências claras.
""",

    "P2_3": """
Prompt 2.3: Análise de Riscos

**IMPORTANTE:** Foque nos riscos específicos da migração configurada na Fase 0.

Identifique e analise os riscos da migração:

1. **Riscos Técnicos Específicos**
   - Incompatibilidades com as tecnologias alvo
   - Complexidade de migração para o stack especificado
   - Perda de funcionalidades durante a transição

2. **Riscos de Negócio**
   - Impacto nos usuários durante a migração
   - Interrupções de serviço relacionadas às mudanças tecnológicas
   - Custos adicionais específicos das tecnologias escolhidas

3. **Riscos de Projeto**
   - Curva de aprendizado das novas tecnologias
   - Disponibilidade de expertise no stack alvo
   - Timeline e escopo da migração específica

4. **Planos de Mitigação**
   - Estratégias específicas para cada risco identificado
   - Planos de contingência para problemas com as tecnologias alvo
   - Monitoramento e alertas durante a migração

Classifique por probabilidade e impacto, priorizando riscos da migração configurada.
""",

    # Fase 3: Planejamento Detalhado
    "P3_1": """
Prompt 3.1: Especificação Técnica Detalhada

**IMPORTANTE:** Detalhe especificamente como implementar a migração conforme configuração da Fase 0.

Crie especificações técnicas detalhadas para a migração:

1. **Arquitetura de Destino**
   - Desenho detalhado usando as tecnologias especificadas
   - Padrões arquiteturais específicos do stack alvo
   - Integrações e interfaces na nova arquitetura

2. **Componentes e Serviços**
   - Especificação de cada componente nas tecnologias de destino
   - APIs e contratos de interface
   - Configurações específicas do stack alvo

3. **Estratégia de Dados**
   - Migração de dados para as tecnologias especificadas
   - Estruturas de dados na nova arquitetura
   - Sincronização e consistência durante a transição

4. **Infraestrutura e Deployment**
   - Requisitos de infraestrutura para o stack alvo
   - Pipelines de CI/CD para as novas tecnologias
   - Monitoramento e observabilidade específicos

Forneça diagramas, esquemas e especificações técnicas precisas.
""",

    "P3_2": """
Prompt 3.2: Planos de Execução

**IMPORTANTE:** Detalhe a execução considerando as tecnologias e preferências da configuração.

Desenvolva planos detalhados de execução:

1. **Cronograma Detalhado**
   - Atividades específicas para migração ao stack alvo
   - Dependências entre tarefas
   - Marcos de validação das tecnologias implementadas

2. **Recursos e Responsabilidades**
   - Perfis necessários para as tecnologias especificadas
   - Responsabilidades por fase da migração
   - Estrutura de governança do projeto

3. **Procedimentos de Migração**
   - Scripts e ferramentas específicas para o stack alvo
   - Procedimentos de backup e rollback
   - Validações técnicas pós-migração

4. **Comunicação e Gestão de Mudança**
   - Plano de comunicação sobre as novas tecnologias
   - Treinamento específico do stack de destino
   - Gestão de resistência à mudança tecnológica

Organize por sprints/iterações com deliverables claros.
""",

    "P3_3": """
Prompt 3.3: Estratégias de Teste

**IMPORTANTE:** Foque em testes específicos das tecnologias alvo configuradas.

Defina estratégias abrangentes de teste:

1. **Testes de Migração**
   - Validação da migração para as tecnologias especificadas
   - Testes de compatibilidade com o stack alvo
   - Verificação de funcionalidades nas novas tecnologias

2. **Testes de Performance**
   - Benchmarks específicos das tecnologias de destino
   - Comparação de performance entre stacks
   - Testes de carga na nova arquitetura

3. **Testes de Integração**
   - Validação de integrações no stack alvo
   - Testes end-to-end na nova arquitetura
   - Compatibilidade com sistemas externos

4. **Testes de Aceitação**
   - Critérios específicos para as tecnologias implementadas
   - Validação de requisitos de negócio na nova plataforma
   - Testes de usabilidade com as mudanças tecnológicas

Inclua casos de teste, automação e critérios de aceite específicos.
""",

    # Fase 4: Implementação e Validação
    "P4_1": """
Prompt 4.1: Implementação por Componente

**IMPORTANTE:** Implemente considerando as especificações exatas da configuração de migração.

Para cada componente identificado, forneça:

1. **Código de Migração**
   - Implementação específica para as tecnologias alvo
   - Padrões de código do stack de destino
   - Configurações específicas das novas tecnologias

2. **Scripts de Automação**
   - Scripts de migração para o stack especificado
   - Automação de deployment nas tecnologias alvo
   - Ferramentas específicas de migração

3. **Configurações de Ambiente**
   - Configurações específicas das tecnologias de destino
   - Variáveis de ambiente para o novo stack
   - Dependências e requisitos específicos

4. **Documentação Técnica**
   - Documentação específica das implementações
   - Guias de uso das novas tecnologias
   - Troubleshooting específico do stack alvo

Forneça código executável e configurações funcionais.
""",

    "P4_2": """
Prompt 4.2: Validação e Integração

**IMPORTANTE:** Valide especificamente se a implementação atende à configuração definida na Fase 0.

Realize validação completa da migração:

1. **Validação Técnica**
   - Verificação de funcionamento nas tecnologias alvo
   - Testes de compatibilidade com especificações
   - Validação de performance no novo stack

2. **Testes de Integração**
   - Integração entre componentes migrados
   - Compatibilidade com sistemas externos
   - Fluxos end-to-end na nova arquitetura

3. **Verificação de Requisitos**
   - Atendimento aos objetivos da migração configurada
   - Validação das tecnologias implementadas vs. especificadas
   - Gaps e ajustes necessários

4. **Feedback para Context3**
   - Resultados da validação técnica
   - Lições aprendidas específicas das tecnologias
   - Recomendações para próximas migrações similares
   - Atualizações do contexto global baseadas na experiência

**SAÍDA PARA FEEDBACK LOOP P4_2 -> Context3:**
[Estruturar resposta para atualizar contexto global com resultados da validação]
""",

    "P4_3": """
Prompt 4.3: Documentação e Entrega

**IMPORTANTE:** Documente especificamente a implementação das tecnologias configuradas.

Produza documentação completa da migração:

1. **Documentação Técnica Final**
   - Arquitetura implementada com as tecnologias especificadas
   - Configurações e procedimentos específicos do stack alvo
   - Guias de operação para as novas tecnologias

2. **Manuais de Operação**
   - Procedimentos operacionais para o novo stack
   - Monitoramento específico das tecnologias implementadas
   - Troubleshooting e manutenção

3. **Guias de Desenvolvimento**
   - Padrões de desenvolvimento para as tecnologias alvo
   - Boas práticas específicas do stack implementado
   - Guidelines para futuras evoluções

4. **Lições Aprendidas e Melhorias**
   - Experiências específicas com as tecnologias migradas
   - Otimizações identificadas durante a implementação
   - Recomendações para migrações futuras similares

5. **Feedback para Context3**
   - Conhecimento consolidado sobre a migração
   - Padrões reutilizáveis para migrações similares
   - Atualizações de best practices baseadas na experiência
   - Métricas e resultados alcançados

**SAÍDA PARA FEEDBACK LOOP P4_3 -> Context3:**
[Estruturar resposta para atualizar contexto global com conhecimento consolidado]
"""
}

# Feedback loops mapping
FEEDBACK_LOOPS = {
    "P4_2_to_Context3": {
        "description": "Feedback de validação técnica para contexto global",
        "fields": ["validation_results", "technical_issues", "performance_metrics", "compatibility_status"]
    },
    "P4_3_to_Context3": {
        "description": "Feedback de conhecimento consolidado para contexto global", 
        "fields": ["lessons_learned", "best_practices", "reusable_patterns", "success_metrics"]
    }
}
