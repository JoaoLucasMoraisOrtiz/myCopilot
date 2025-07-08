PROMPTS = {
    # Fase 1: Análise do Sistema Legado
    "P1_1": """
Prompt 1.1: Mapeamento da Arquitetura

**IMPORTANTE:** Considere rigorosamente a configuração de migração fornecida no contexto (Fase 0) para guiar sua análise.

Analise o sistema legado e forneça um mapeamento detalhado da arquitetura atual. Inclua:

1. **Visão Geral da Arquitetura**
   - Tipo de arquitetura (monolítica, SOA, microserviços, etc.)
   - Principais camadas e componentes
   - Tecnologias utilizadas (foque nas mencionadas na configuração)

2. **Componentes Principais**
   - Frontend (tecnologias, frameworks)
   - Backend (linguagens, frameworks, servidores)
   - Banco de dados (tipo, versão, estrutura)
   - Integrações externas

3. **Infraestrutura**
   - Servidores e ambientes
   - Deployment atual
   - Monitoramento e logs

4. **Pontos de Atenção para Migração**
   - Componentes críticos para a migração especificada
   - Gargalos que impedem a migração para as tecnologias alvo
   - Dependências problemáticas considerando o alvo definido

5. **Alinhamento com Objetivos**
   - Como a arquitetura atual se relaciona com as tecnologias alvo definidas
   - Complexidade estimada para a migração especificada
   - Riscos específicos considerando as preferências do usuário

Formate sua resposta em markdown com seções bem definidas, sempre referenciando as especificações da migração.
""",

    "P1_2": """
Prompt 1.2: Fluxos de Negócio

**IMPORTANTE:** Considere a configuração de migração (Fase 0) para identificar fluxos críticos para a migração especificada.

Descreva os principais fluxos de negócio do sistema. Para cada fluxo, inclua:

1. **Identificação dos Fluxos**
   - Nome e objetivo de cada fluxo
   - Usuários/atores envolvidos
   - Frequência de uso
   - Relevância para a migração alvo definida

2. **Mapeamento Técnico**
   - Componentes envolvidos em cada fluxo
   - APIs e integrações utilizadas (foque nas que afetam a migração)
   - Pontos de dados críticos
   - Compatibilidade com tecnologias de destino

3. **Complexidade e Riscos de Migração**
   - Fluxos mais complexos para migrar ao stack alvo
   - Dependências críticas que impedem migração
   - Impacto no negócio durante a migração
   - Fluxos que requerem adaptação para tecnologias alvo

4. **Oportunidades de Melhoria na Migração**
   - Automações possíveis com as novas tecnologias
   - Simplificações identificadas para o stack de destino
   - Performance e UX melhoradas na nova arquitetura
   - Funcionalidades que se beneficiam das tecnologias alvo

Use diagramas em texto quando necessário e organize em markdown, sempre considerando as especificações da migração.
""",

    "P1_3": """
Prompt 1.3: Análise de Dependências

**IMPORTANTE:** Use a configuração de migração (Fase 0) para avaliar compatibilidade com tecnologias alvo.

Faça uma análise completa das dependências do sistema:

1. **Dependências Internas**
   - Bibliotecas e frameworks (compatibilidade com stack alvo)
   - Versões e compatibilidade com tecnologias de destino
   - Dependências entre módulos que afetam a migração

2. **Dependências Externas**
   - APIs de terceiros (disponibilidade no stack alvo)
   - Serviços externos (compatibilidade com nova arquitetura)
   - Integrações de sistema (adaptações necessárias)

3. **Impacto na Migração Específica**
   - Dependências incompatíveis com tecnologias alvo
   - Versões mínimas requeridas para o stack de destino
   - Alternativas disponíveis para dependências problemáticas
   - Esforço de migração por dependência

4. **Recomendações Técnicas**
   - Dependências que devem ser atualizadas primeiro
   - Substituições necessárias para o stack alvo
   - Ordem de migração baseada em dependências
   - Riscos e mitigações específicas da migração configurada

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
   - Versões e limitações
   - Impacto na migração

2. **Tecnologias Alvo**
   - Alternativas modernas
   - Benefícios e características
   - Curva de aprendizado

3. **Conceitos de Migração**
   - Padrões e estratégias
   - Ferramentas de migração
   - Boas práticas

4. **Termos de Negócio**
   - Conceitos específicos do domínio
   - Processos críticos
   - Métricas importantes

Organize alfabeticamente em markdown com links internos.
""",

    "P2_2": """
Prompt 2.2: Mapeamento de Componentes

Crie um roadmap detalhado para migração dos componentes:

1. **Inventário de Componentes**
   - Lista completa dos componentes atuais
   - Classificação por criticidade
   - Interdependências

2. **Estratégia de Migração**
   - Ordem de migração recomendada
   - Abordagem para cada componente
   - Paralelização possível

3. **Tecnologias Alvo**
   - Mapeamento atual → alvo
   - Justificativa das escolhas
   - Alternativas consideradas

4. **Cronograma Macro**
   - Fases da migração
   - Marcos importantes
   - Estimativas de tempo

5. **Recursos Necessários**
   - Equipe e competências
   - Ferramentas e infraestrutura
   - Treinamentos

Use tabelas e gantt em texto para visualização.
""",

    "P2_3": """
Prompt 2.3: Riscos e Complexidades

Identifique e analise os riscos da migração:

1. **Riscos Técnicos**
   - Incompatibilidades
   - Perda de funcionalidades
   - Performance e escalabilidade

2. **Riscos de Negócio**
   - Downtime e disponibilidade
   - Impacto nos usuários
   - Custos não previstos

3. **Riscos de Projeto**
   - Timeline e recursos
   - Competências da equipe
   - Mudanças de escopo

4. **Planos de Mitigação**
   - Estratégias preventivas
   - Planos de contingência
   - Monitoramento e alertas

5. **Métricas de Sucesso**
   - KPIs de migração
   - Critérios de aceitação
   - Pontos de validação

Organize por nível de risco e impacto em markdown.
""",

    # Fase 3: Criação de Tasks
    "P3_1": """
Prompt 3.1: Nova Arquitetura

Desenhe a arquitetura alvo detalhada:

1. **Visão Geral**
   - Padrão arquitetural escolhido
   - Principais melhorias vs. sistema atual
   - Princípios de design

2. **Componentes da Nova Arquitetura**
   - Frontend (tecnologias, estrutura)
   - Backend (serviços, APIs)
   - Banco de dados (estrutura, otimizações)
   - Infraestrutura (cloud, containers)

3. **Padrões e Práticas**
   - Design patterns aplicados
   - Segurança e compliance
   - Observabilidade e monitoramento

4. **Integrações**
   - APIs internas e externas
   - Protocolos de comunicação
   - Gestão de dados

5. **Estratégia de Deploy**
   - CI/CD pipeline
   - Ambientes e promocão
   - Rollback e disaster recovery

Use diagramas em texto e markdown estruturado.
""",

    "P3_2": """
Prompt 3.2: Tasks Detalhadas

Crie um backlog detalhado de migração:

1. **Épicos Principais**
   - Grandes blocos de trabalho
   - Objetivos e escopo
   - Critérios de aceite

2. **User Stories**
   - Formato: "Como [usuário], eu quero [funcionalidade] para [objetivo]"
   - Critérios de aceite detalhados
   - Estimativas em story points

3. **Tasks Técnicas**
   - Setup de ambiente
   - Configurações e infraestrutura
   - Migração de dados

4. **Priorização**
   - MoSCoW (Must, Should, Could, Won't)
   - Dependências críticas
   - Value vs. effort

5. **Definition of Done**
   - Critérios técnicos
   - Testes necessários
   - Documentação

Organize como backlog pronto para desenvolvimento.
""",

    "P3_3": """
Prompt 3.3: Plano de Testes

Elabore uma estratégia completa de testes:

1. **Tipos de Teste**
   - Unitários, integração, e2e
   - Performance e carga
   - Segurança e compliance

2. **Estratégia por Fase**
   - Testes durante desenvolvimento
   - Testes de migração
   - Testes pós-deploy

3. **Automação**
   - Framework de testes
   - Pipeline de CI/CD
   - Cobertura de código

4. **Testes de Migração**
   - Validação de dados
   - Comparação de comportamento
   - Rollback testing

5. **Ambientes de Teste**
   - Setup e configuração
   - Dados de teste
   - Monitoramento

6. **Critérios de Qualidade**
   - Gates de qualidade
   - Métricas e thresholds
   - Sign-off process

Detalhe ferramentas e processos em markdown.
""",

    # Fase 4: Implementação
    "P4_1": """
Você é um desenvolvedor sênior especialista em migração de sistemas. 

Baseado no contexto completo da migração fornecido anteriormente, implemente a seguinte task:

{task_description}

**ESTRUTURA DO PROJETO ALVO:**
{project_structure}

**INSTRUÇÕES ESPECÍFICAS:**
1. **Código Focado**: Gere APENAS o código necessário para esta task específica
2. **Arquivos Pequenos**: Prefira múltiplos arquivos pequenos a um arquivo grande
3. **Localização Clara**: Indique claramente onde cada arquivo deve ser colocado
4. **Padrões Arquiteturais**: Siga rigorosamente os padrões definidos na nova arquitetura
5. **Dependências**: Considere apenas as dependências mapeadas e necessárias
6. **Nomenclatura**: Use nomes descritivos e consistentes com a nova estrutura

**FORMATO DE RESPOSTA OBRIGATÓRIO:**
Para cada arquivo gerado, use esta estrutura:

```
ARQUIVO: [nome_do_arquivo]
LOCALIZAÇÃO: [caminho/relativo/na/estrutura]
COMPONENTE: [componente_ou_camada]
DESCRIÇÃO: [breve descrição do que faz]

```[linguagem]
[código aqui]
```

DEPENDÊNCIAS: [lista de dependências se houver]
```

**EXEMPLO:**
```
ARQUIVO: UserController.java
LOCALIZAÇÃO: backend/src/main/java/com/company/app/controller
COMPONENTE: api-controller
DESCRIÇÃO: REST controller para operações de usuário

```java
@RestController
@RequestMapping("/api/users")
public class UserController {
    // código aqui
}
```

DEPENDÊNCIAS: UserService, User model
```

**IMPORTANTE:**
- Mantenha cada arquivo com no máximo 50-100 linhas
- Inclua comentários explicativos
- Foque na funcionalidade específica da task
- NÃO gere código desnecessário ou genérico
""",

    "P4_2": """
Analise o código implementado abaixo e valide se:

{code_to_validate}

**Critérios de Validação:**
1. **Aderência à Arquitetura:** O código segue os padrões definidos?
2. **Qualidade:** Está limpo, legível e bem estruturado?
3. **Funcionalidade:** Atende aos requisitos da task?
4. **Integração:** Funciona com outros componentes?
5. **Performance:** Possui potenciais gargalos?
6. **Segurança:** Implementa práticas seguras?

**Responda:**
- ✅ APROVADO ou ❌ REJEITAR
- Lista de problemas encontrados (se houver)
- Sugestões de melhoria específicas
- Próximos passos recomendados
""",

    "P4_3": """
Crie um plano de integração para o código implementado:

{implemented_code}

**Plano deve incluir:**
1. **Pré-requisitos:** O que precisa estar pronto antes da integração
2. **Passos de Deploy:** Sequência detalhada de deployment
3. **Configurações:** Variáveis de ambiente, configs necessárias
4. **Testes de Integração:** Como validar a integração
5. **Monitoring:** Métricas e logs a observar
6. **Rollback:** Como reverter se necessário

**Database Changes:** Se houver mudanças no banco, inclua:
- Scripts de migração
- Estratégia de backup
- Validação de dados

**Retorne um plano passo-a-passo executável.**
"""
}
