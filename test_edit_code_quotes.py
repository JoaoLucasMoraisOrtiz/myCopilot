#!/usr/bin/env python3
"""
Teste específico para o tratamento de aspas na funcionalidade edit_code.
"""

import tempfile
import json
from pathlib import Path
from core.agent.tool_executor import AgentToolExecutor
from core.agent.response_parser import AgentResponseParser

def test_quote_handling():
    """Testa o tratamento de aspas conflitantes."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Diretório de teste: {temp_dir}")
        
        # Cria arquivo de teste com aspas
        test_file = Path(temp_dir) / "test_quotes.py"
        original_content = '''def greet():
    print("hello")
    return "world"

def format_message(name):
    return f'Hello, {name}!'
'''
        
        with open(test_file, 'w') as f:
            f.write(original_content)
        
        print("📝 Arquivo original:")
        print(original_content)
        
        # Mock do toolbox
        class MockToolbox:
            def __init__(self):
                self.symbol_table = {}
        
        toolbox = MockToolbox()
        executor = AgentToolExecutor(toolbox, temp_dir)
        
        # Teste 1: Mudança com aspas duplas
        print("\n🔧 Teste 1: Alterando print com aspas duplas")
        result = executor._execute_edit_code([
            "test_quotes.py",
            'print("hello")',
            'print("Hello, World!")'
        ])
        
        print(f"Resultado: {result}")
        
        # Verifica o conteúdo após a mudança
        with open(test_file, 'r') as f:
            content_after_1 = f.read()
        
        print("📝 Conteúdo após primeira mudança:")
        print(content_after_1)
        
        # Teste 2: Mudança com aspas simples
        print("\n🔧 Teste 2: Alterando return com aspas duplas internas")
        result = executor._execute_edit_code([
            "test_quotes.py",
            'return "world"',
            'return "beautiful world"'
        ])
        
        print(f"Resultado: {result}")
        
        # Teste 3: Mudança com aspas mistas
        print("\n🔧 Teste 3: Alterando f-string")
        result = executor._execute_edit_code([
            "test_quotes.py",
            "return f'Hello, {name}!'",
            'return f"Hello, {name}! Welcome!"'
        ])
        
        print(f"Resultado: {result}")
        
        # Verifica conteúdo final
        with open(test_file, 'r') as f:
            final_content = f.read()
        
        print("📝 Conteúdo final:")
        print(final_content)

def test_parser_quote_handling():
    """Testa se o parser consegue extrair JSONs com aspas problemáticas."""
    
    parser = AgentResponseParser()
    
    # Teste 1: JSON com aspas duplas problemáticas (como no exemplo do usuário)
    problematic_json = '''
    {
        "command": "edit_code",
        "args": ["src/main.py", "print("hello")", "print("Hello, World!")"]
    }
    '''
    
    print("\n🔍 Teste do parser com JSON problemático:")
    print(f"Input: {problematic_json}")
    
    result = parser.parse_action_from_response(problematic_json)
    print(f"Resultado: {result}")
    
    # Teste 2: JSON com escape correto
    correct_json = '''
    {
        "command": "edit_code",
        "args": ["src/main.py", "print(\\"hello\\")", "print(\\"Hello, World!\\")"]
    }
    '''
    
    print("\n🔍 Teste do parser com JSON correto:")
    print(f"Input: {correct_json}")
    
    result = parser.parse_action_from_response(correct_json)
    print(f"Resultado: {result}")
    
    # Teste 3: JSON com aspas simples
    simple_quotes_json = '''
    {
        "command": "edit_code",
        "args": ["src/main.py", "print('hello')", "print('Hello, World!')"]
    }
    '''
    
    print("\n🔍 Teste do parser com aspas simples:")
    print(f"Input: {simple_quotes_json}")
    
    result = parser.parse_action_from_response(simple_quotes_json)
    print(f"Resultado: {result}")

def test_quote_variants():
    """Testa se o executor consegue encontrar código com diferentes tipos de aspas."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"\n📁 Teste de variantes de aspas em: {temp_dir}")
        
        # Cria arquivo com código usando aspas simples
        test_file = Path(temp_dir) / "test_variants.py"
        content_with_single_quotes = "print('hello world')\n"
        
        with open(test_file, 'w') as f:
            f.write(content_with_single_quotes)
        
        print(f"📝 Arquivo criado com: {repr(content_with_single_quotes)}")
        
        class MockToolbox:
            def __init__(self):
                self.symbol_table = {}
        
        toolbox = MockToolbox()
        executor = AgentToolExecutor(toolbox, temp_dir)
        
        # Tenta buscar usando aspas duplas (diferente do que está no arquivo)
        print("\n🔧 Testando busca com aspas duplas quando arquivo tem aspas simples")
        result = executor._execute_edit_code([
            "test_variants.py",
            'print("hello world")',  # Aspas duplas
            'print("goodbye world")'
        ])
        
        print(f"Resultado: {result}")
        
        # Verifica se a mudança foi aplicada
        with open(test_file, 'r') as f:
            final_content = f.read()
        
        print(f"📝 Conteúdo final: {repr(final_content)}")

if __name__ == "__main__":
    print("🧪 Testando tratamento de aspas na funcionalidade edit_code")
    print("=" * 60)
    
    test_quote_handling()
    test_parser_quote_handling()
    test_quote_variants()
    
    print("\n✅ Testes de aspas concluídos!")
