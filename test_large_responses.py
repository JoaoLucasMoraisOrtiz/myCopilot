#!/usr/bin/env python3
"""
Script de teste para validar melhorias de respostas grandes no myCopilot
"""

import sys
import time
import json
from pathlib import Path

# Adiciona o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

from core.agent.agent_core import Agent

def test_large_response_parsing():
    """Testa parsing de respostas grandes"""
    
    # Simula resposta grande com JSON no final
    large_response = """
    SYSTEM: 
    # 1. PERSONA E MISSÃO
    Você é um Arquiteto de Software Sênior autônomo e altamente competente. Sua especialidade é dissecar sistemas Java legados para entender sua arquitetura, fluxos de dados, padrões de design e dependências. Você possui décadas de experiência em refatoração, análise de código e documentação técnica.

    ## OBJETIVO PRINCIPAL
    Analisar completamente o sistema Java fornecido para entender:
    - Arquitetura geral e padrões utilizados
    - Fluxos de dados e processos de negócio
    - Relacionamentos entre classes e componentes
    - Pontos de entrada e saída do sistema
    - Estruturas de dados principais
    - Lógica de negócio crítica

    ## FERRAMENTAS DISPONÍVEIS
    1. **list_classes()** - Lista todas as classes do sistema
    2. **get_class_metadata(class_name)** - Obtém metadados de uma classe específica
    3. **get_code(class_name, method_name=None)** - Obtém código de classe/método
    4. **read_file(filepath)** - Lê arquivo específico
    5. **continue_reading(abstraction_id)** - Continua lendo conteúdo abstraído
    6. **final_answer(response)** - Fornece resposta final

    ## INSTRUÇÕES ESPECÍFICAS
    - Comece sempre com list_classes() para ter visão geral
    - Use get_class_metadata() para entender relacionamentos
    - Analise código apenas quando necessário para entender funcionalidade
    - Mantenha foco no objetivo de entender o sistema como um todo
    - Forneça final_answer() quando tiver compreensão suficiente

    ## FORMATO DE RESPOSTA
    Sempre responda em JSON válido:
    {"command": "nome_da_ferramenta", "args": ["argumento1", "argumento2"]}

    NÃO inclua texto explicativo fora do JSON. Apenas o JSON puro.
    """ + "A" * 10000 + """
    
    Baseado na análise inicial, vou começar listando todas as classes disponíveis no sistema para ter uma visão geral da arquitetura.
    
    {"command": "list_classes", "args": []}
    """
    
    # Cria agente temporário para teste
    agent = Agent("teste", ".", max_turns=1)
    
    print("🧪 Testando parsing de resposta grande...")
    print(f"📊 Tamanho da resposta: {len(large_response)} chars")
    
    # Testa o parsing
    result = agent.parse_action_from_response(large_response)
    
    print(f"✅ Resultado do parsing: {result}")
    
    # Verifica se detectou o comando correto
    if result.get("command") == "list_classes":
        print("✅ SUCESSO: Comando 'list_classes' detectado corretamente")
        return True
    else:
        print(f"❌ FALHA: Comando esperado 'list_classes', obtido '{result.get('command')}'")
        return False

def test_json_extraction():
    """Testa extração de JSON com diferentes formatos"""
    
    agent = Agent("teste", ".", max_turns=1)
    
    test_cases = [
        # JSON em bloco markdown
        '```json\n{"command": "get_code", "args": ["TestClass"]}\n```',
        
        # JSON direto no texto
        'Analisando o código... {"command": "read_file", "args": ["test.java"]} para continuar',
        
        # JSON em linha
        '{"command": "final_answer", "args": ["Sistema analisado"]}',
        
        # JSON malformado que deve ser limpo
        '{"command": "list_classes", "args": []}Extra data here',
    ]
    
    print("\n🧪 Testando extração de JSON...")
    
    success_count = 0
    for i, test_case in enumerate(test_cases):
        print(f"\n📝 Teste {i+1}: {test_case[:50]}...")
        
        result = agent._extract_json_from_response(test_case)
        
        if result and isinstance(result, dict) and "command" in result:
            print(f"✅ SUCESSO: {result}")
            success_count += 1
        else:
            print(f"❌ FALHA: {result}")
    
    print(f"\n📊 Resultados: {success_count}/{len(test_cases)} testes passaram")
    return success_count == len(test_cases)

def test_intelligent_fallback():
    """Testa fallback inteligente"""
    
    agent = Agent("teste", ".", max_turns=1)
    
    test_cases = [
        ("Analisando a classe UserService...", "get_class_metadata"),
        ("Vou examinar o arquivo UserService.java", "read_file"),
        ("Preciso ver o código da classe DatabaseManager", "get_code"),
        ("Continue lendo abs_123", "continue_reading"),
        ("Em resumo, o sistema é um framework de análise completo...", "final_answer"),
    ]
    
    print("\n🧪 Testando fallback inteligente...")
    
    success_count = 0
    for i, (text, expected_command) in enumerate(test_cases):
        print(f"\n📝 Teste {i+1}: {text[:50]}...")
        print(f"🔍 Texto completo: '{text}'")
        
        result = agent._intelligent_fallback(text)
        
        if result.get("command") == expected_command:
            print(f"✅ SUCESSO: {expected_command}")
            success_count += 1
        else:
            print(f"❌ FALHA: esperado '{expected_command}', obtido '{result.get('command')}'")
            # Debug adicional
            content_lower = text.lower()
            print(f"🔍 Debug: 'em resumo' in text: {'em resumo' in content_lower}")
            print(f"🔍 Debug: word count: {len(text.split())}")
    
    print(f"\n📊 Resultados: {success_count}/{len(test_cases)} testes passaram")
    return success_count == len(test_cases)

def main():
    """Executa todos os testes"""
    
    print("🚀 Iniciando testes de melhorias para respostas grandes...")
    print("=" * 60)
    
    tests = [
        ("Parsing de Resposta Grande", test_large_response_parsing),
        ("Extração de JSON", test_json_extraction),
        ("Fallback Inteligente", test_intelligent_fallback),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 EXECUTANDO: {test_name}")
        print("-" * 40)
        
        try:
            success = test_func()
            results.append((test_name, success))
            
            if success:
                print(f"✅ {test_name}: PASSOU")
            else:
                print(f"❌ {test_name}: FALHOU")
                
        except Exception as e:
            print(f"💥 {test_name}: ERRO - {e}")
            results.append((test_name, False))
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{status}: {test_name}")
    
    print(f"\n🎯 RESULTADO FINAL: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM! Sistema pronto para uso.")
    else:
        print("⚠️ Alguns testes falharam. Verifique as melhorias.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
