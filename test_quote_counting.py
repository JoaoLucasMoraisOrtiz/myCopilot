#!/usr/bin/env python3
"""
Teste específico para a funcionalidade de contagem de aspas no parser.
"""

from core.agent.response_parser import AgentResponseParser

def test_quote_counting_parser():
    """Testa o parser com JSONs que têm problemas de aspas."""
    
    parser = AgentResponseParser()
    
    # Teste 1: JSON malformado com aspas não escapadas (o caso do usuário)
    print("🧪 Teste 1: JSON malformado com aspas não escapadas")
    malformed_json = '''
    {
        "command": "edit_code",
        "args": ["src/main.py", "print("hello")", "print("Hello, World!")"]
    }
    '''
    
    result = parser.parse_action_from_response(malformed_json)
    print(f"Resultado: {result}")
    print(f"Comando: {result.get('command')}")
    print(f"Args: {result.get('args')}")
    
    if result.get('command') == 'edit_code' and len(result.get('args', [])) == 3:
        print("✅ Teste 1 PASSOU!")
    else:
        print("❌ Teste 1 FALHOU!")
    
    # Teste 2: JSON com aspas simples e duplas misturadas
    print("\n🧪 Teste 2: Aspas simples e duplas misturadas")
    mixed_quotes = '''
    {
        "command": "edit_code",
        "args": ["file.py", "def hello(): print('world')", "def hello(): print("Hello World")"]
    }
    '''
    
    result = parser.parse_action_from_response(mixed_quotes)
    print(f"Resultado: {result}")
    
    if result.get('command') == 'edit_code':
        print("✅ Teste 2 PASSOU!")
    else:
        print("❌ Teste 2 FALHOU!")
    
    # Teste 3: JSON com múltiplas linhas
    print("\n🧪 Teste 3: JSON com código de múltiplas linhas")
    multiline_json = '''
    {
        "command": "edit_code",
        "args": [
            "src/user.py",
            "def get_name(self):
    return self.name",
            "def get_name(self):
    if self.name:
        return self.name
    return "Unknown""
        ]
    }
    '''
    
    result = parser.parse_action_from_response(multiline_json)
    print(f"Resultado: {result}")
    
    if result.get('command') == 'edit_code':
        print("✅ Teste 3 PASSOU!")
        # Mostra os argumentos extraídos
        args = result.get('args', [])
        for i, arg in enumerate(args):
            print(f"  Arg {i}: {repr(arg)}")
    else:
        print("❌ Teste 3 FALHOU!")
    
    # Teste 4: JSON com caracteres especiais
    print("\n🧪 Teste 4: JSON com caracteres especiais")
    special_chars = '''
    {
        "command": "edit_code",
        "args": ["test.py", "text = "hello\nworld"", "text = "hello\\nworld""]
    }
    '''
    
    result = parser.parse_action_from_response(special_chars)
    print(f"Resultado: {result}")
    
    if result.get('command') == 'edit_code':
        print("✅ Teste 4 PASSOU!")
    else:
        print("❌ Teste 4 FALHOU!")
    
    # Teste 5: Teste de performance com texto longo
    print("\n🧪 Teste 5: Texto longo com JSON no final")
    long_text = '''
    Esta é uma explicação muito longa sobre o que vou fazer.
    Primeiro vou analisar o código existente.
    Depois vou identificar os problemas.
    Em seguida vou implementar a correção.
    
    Aqui está minha ação:
    {
        "command": "edit_code",
        "args": ["main.py", "old_code_here", "new_code_here"]
    }
    '''
    
    result = parser.parse_action_from_response(long_text)
    print(f"Resultado: {result}")
    
    if result.get('command') == 'edit_code':
        print("✅ Teste 5 PASSOU!")
    else:
        print("❌ Teste 5 FALHOU!")

def test_quote_counting_direct():
    """Testa diretamente o método de contagem de aspas."""
    
    parser = AgentResponseParser()
    
    print("\n🔧 Teste direto do método de contagem de aspas")
    
    # Teste com o exemplo problemático
    test_text = '["src/main.py", "print("hello")", "print("Hello, World!")"]'
    start_pos = test_text.find('[')
    
    args = parser._extract_args_with_quote_counting(test_text, start_pos)
    
    print(f"Texto de teste: {test_text}")
    print(f"Argumentos extraídos: {args}")
    
    if args and len(args) == 3:
        print("✅ Extração direta PASSOU!")
        for i, arg in enumerate(args):
            print(f"  Arg {i}: {repr(arg)}")
    else:
        print("❌ Extração direta FALHOU!")

if __name__ == "__main__":
    print("🧪 Testando parser com contagem de aspas")
    print("=" * 60)
    
    test_quote_counting_parser()
    test_quote_counting_direct()
    
    print("\n✅ Testes de contagem de aspas concluídos!")
