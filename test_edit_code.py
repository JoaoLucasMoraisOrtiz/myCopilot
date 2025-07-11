#!/usr/bin/env python3
"""
Teste da funcionalidade edit_code do AgentToolExecutor.
"""

import tempfile
import os
from pathlib import Path
from core.agent.tool_executor import AgentToolExecutor
from core.agent.response_parser import AgentResponseParser

def test_edit_code_functionality():
    """Testa a funcionalidade de edição de código."""
    
    # Cria um diretório temporário para o teste
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Diretório de teste: {temp_dir}")
        
        # Cria um arquivo de teste
        test_file = Path(temp_dir) / "test_class.py"
        original_content = '''class TestClass:
    def __init__(self):
        self.value = 0
    
    def get_value(self):
        return self.value
    
    def set_value(self, new_value):
        self.value = new_value
'''
        
        with open(test_file, 'w') as f:
            f.write(original_content)
        
        print("📝 Arquivo original criado:")
        print(original_content)
        
        # Mock do toolbox (simplificado para o teste)
        class MockToolbox:
            def __init__(self):
                self.symbol_table = {}
        
        # Inicializa o executor
        toolbox = MockToolbox()
        executor = AgentToolExecutor(toolbox, temp_dir)
        
        # Teste 1: Edição simples - trocar valor inicial
        print("\n🔧 Teste 1: Alterando valor inicial de 0 para 42")
        old_code = "        self.value = 0"
        new_code = "        self.value = 42"
        
        result = executor._execute_edit_code([
            "test_class.py", 
            old_code, 
            new_code
        ])
        
        print(f"Resultado: {result}")
        
        # Verifica se a alteração foi aplicada
        with open(test_file, 'r') as f:
            modified_content = f.read()
        
        print("📝 Conteúdo após primeira edição:")
        print(modified_content)
        
        # Teste 2: Adicionar método novo
        print("\n🔧 Teste 2: Adicionando método increment")
        old_code = "    def set_value(self, new_value):\n        self.value = new_value"
        new_code = """    def set_value(self, new_value):
        self.value = new_value
    
    def increment(self):
        self.value += 1"""
        
        result = executor._execute_edit_code([
            "test_class.py", 
            old_code, 
            new_code
        ])
        
        print(f"Resultado: {result}")
        
        # Verifica se a alteração foi aplicada
        with open(test_file, 'r') as f:
            final_content = f.read()
        
        print("📝 Conteúdo final:")
        print(final_content)
        
        # Teste 3: Erro - trecho não encontrado
        print("\n🔧 Teste 3: Testando erro - trecho não encontrado")
        result = executor._execute_edit_code([
            "test_class.py", 
            "def nonexistent_method():", 
            "def new_method():"
        ])
        
        print(f"Resultado esperado de erro: {result}")

def test_parser_edit_code():
    """Testa se o parser reconhece comandos edit_code."""
    
    parser = AgentResponseParser()
    
    # Teste 1: JSON direto
    json_response = '''
    {
        "command": "edit_code",
        "args": ["file.py", "old code", "new code"]
    }
    '''
    
    result = parser.parse_action_from_response(json_response)
    print(f"🔍 Parser JSON: {result}")
    
    # Teste 2: JSON em bloco markdown
    markdown_response = '''
    Vou editar o arquivo:
    
    ```json
    {
        "command": "edit_code",
        "args": ["src/main.py", "print('hello')", "print('Hello, World!')"]
    }
    ```
    '''
    
    result = parser.parse_action_from_response(markdown_response)
    print(f"🔍 Parser Markdown: {result}")
    
    # Teste 3: Menção semântica
    semantic_response = "Preciso editar o arquivo main.py e modificar a função de saudação"
    
    result = parser.parse_action_from_response(semantic_response)
    print(f"🔍 Parser Semântico: {result}")

if __name__ == "__main__":
    print("🧪 Testando funcionalidade edit_code")
    print("=" * 50)
    
    print("\n📋 Testando executor...")
    test_edit_code_functionality()
    
    print("\n📋 Testando parser...")
    test_parser_edit_code()
    
    print("\n✅ Testes concluídos!")
