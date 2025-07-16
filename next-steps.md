# Next Steps: Implementação Completa do Code-Agent Modular v2.1

Este documento detalha o plano de ação para evoluir o projeto até 100% de aderência ao documento de arquitetura e requisitos, removendo partes "stub" e implementando execuções reais.

---

## 1. Integração Real com Tree-sitter (ASTParser)
- [X] Compilar e integrar as gramáticas tree-sitter para Python e Java. (modificado para utilizar a biblioteca diretamente)
- [X] Implementar carregamento dinâmico das gramáticas no `ASTParser`.
- [X] Implementar métodos de análise real de código, retornando ASTs utilizáveis.
- [X] Usar AST real para análise de contexto, localização de falhas e decomposição de tarefas.

## 2. Integração Real com LLM (LLMClient)
- [ ] Integrar o LLMClient com a API real do Codestral (ou outro LLM).
- [ ] Implementar autenticação via variável de ambiente ou arquivo seguro.
- [ ] Tratar respostas reais do LLM, incluindo erros e limites de uso.

## 3. Execução Real em Sandbox (DockerSandbox)
- [ ] Garantir que o Docker esteja disponível e documentar dependências.
- [ ] Implementar execução real de comandos de validação (pytest, mypy, ruff, mvn, checkstyle) dentro do sandbox.
- [ ] Tratar logs, erros e resultados de execução de forma robusta.
- [ ] Permitir configuração dinâmica de imagens Docker para Python e Java.

## 4. Validação e Linting Real
- [ ] No `DirectGeneratorAgent`, `ComposerMCTSAgent` e `CriticPolishAgent`, substituir simulações por execuções reais de:
    - [ ] pytest/mypy/ruff para Python
    - [ ] mvn/junit/checkstyle para Java
- [ ] Capturar e processar resultados reais dos testes e linting.

## 5. Implementação Real do MCTS (ComposerMCTSAgent)
- [ ] Implementar localização de falhas usando AST real e traceback.
- [ ] Implementar geração de mutações reais via LLM, guiadas pelo AST.
- [ ] Implementar ciclo de simulação e convergência do MCTS.

## 6. Decomposição Inteligente de Tasks (HaloPlannerAgent)
- [ ] Integrar LLM para decompor tasks em subtasks de forma contextualizada.
- [ ] Usar análise de código e contexto para sugerir subtasks mais precisas.

## 7. Polimento e Refatoração Real (CriticPolishAgent)
- [ ] Executar ferramentas de linting reais e capturar problemas.
- [ ] Integrar LLM para refatoração baseada em problemas reais detectados.

## 8. Resolução de Dependências e Integração Final (FinalComposerAgent)
- [ ] Implementar análise real de dependências (imports, pom.xml, etc.).
- [ ] Executar testes de integração reais no sandbox.
- [ ] Tratar falhas e sugerir correções automáticas.

## 9. Documentação e Testes
- [ ] Documentar todas as integrações e dependências externas (Docker, tree-sitter, LLM, etc.).
- [ ] Criar testes unitários e de integração para todos os agentes e utilitários.

## 10. Refino do ManifestManager
- [ ] Garantir rastreamento completo de status, erros e logs no manifest.json.
- [ ] Adicionar versionamento e histórico de execuções.

---

## Prioridades Imediatas
1. Tree-sitter funcional (ASTParser).
2. Sandbox Docker funcional para Python e Java.
3. Integração real com Codestral (LLMClient).
4. Execução real de testes/linting/refatoração.

## Observações
- Remover todos os métodos e blocos de código "stub" ou "simulado".
- Garantir que todos os fluxos do pipeline sejam executáveis de ponta a ponta.
- Validar cada etapa com exemplos reais de projetos Python e Java.

---

Com este plano, o projeto estará 100% alinhado ao documento de arquitetura e pronto para uso real em engenharia de software assistida por agentes.
