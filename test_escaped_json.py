#!/usr/bin/env python3
"""
Teste específico para comandos com JSON escapado.
"""

import json
from core.agent.response_parser import AgentResponseParser

def test_escaped_json_parsing():
    """Testa o parsing de comandos com JSON escapado."""
    
    parser = AgentResponseParser()
    
    print("🧪 Testando comandos com JSON escapado")
    print("=" * 60)
    
    # Teste 1: O caso exato do usuário
    print("📝 Teste 1: Caso do usuário (create_file com package.json)")
    user_case = '''
    **Ação:**
    {"command": "create_file", "args": ["package.json", "{\\n  \\"name\\": \\"form-builder\\",\\n  \\"version\\": \\"1.0.0\\",\\n  \\"main\\": \\"index.js\\",\\n  \\"scripts\\": {\\n    \\"dev\\": \\"next dev\\",\\n    \\"build\\": \\"next build\\",\\n    \\"start\\": \\"next start\\"\\n  },\\n  \\"dependencies\\": {\\n    \\"next\\": \\"latest\\",\\n    \\"react\\": \\"latest\\",\\n    \\"react-dom\\": \\"latest\\"\\n  },\\n  \\"devDependencies\\": {\\n    \\"typescript\\": \\"latest\\",\\n    \\"@types/react\\": \\"latest\\",\\n    \\"@types/node\\": \\"latest\\"\\n  }\\n}"]}
    '''
    
    result = parser.parse_action_from_response(user_case)
    
    print(f"✅ Resultado:")
    print(f"  Comando: {result.get('command')}")
    print(f"  Número de argumentos: {len(result.get('args', []))}")
    
    if result.get('command') == 'create_file':
        args = result.get('args', [])
        if len(args) >= 2:
            print(f"  Arquivo: {args[0]}")
            print(f"  Conteúdo (primeiros 100 chars): {args[1][:100]}...")
            
            # Verifica se o conteúdo JSON é válido
            try:
                json_content = json.loads(args[1])
                print(f"✅ JSON interno é válido! Nome: {json_content.get('name', 'N/A')}")
            except json.JSONDecodeError as e:
                print(f"❌ JSON interno inválido: {e}")
        else:
            print("❌ Argumentos insuficientes")
    else:
        print("❌ Comando não reconhecido")
    
    # Teste 2: JSON simples escapado
    print("\n" + "=" * 60)
    print("📝 Teste 2: JSON simples escapado")
    
    simple_case = '''
    {"command": "create_file", "args": ["config.json", "{\\"debug\\": true, \\"port\\": 3000}"]}
    '''
    
    result2 = parser.parse_action_from_response(simple_case)
    
    print(f"Resultado: {result2}")
    
    if result2.get('command') == 'create_file':
        args = result2.get('args', [])
        if len(args) >= 2 and args[1] == '{"debug": true, "port": 3000}':
            print("✅ JSON simples funcionou!")
        else:
            print("❌ JSON simples falhou")
    else:
        print("❌ Comando não reconhecido")
    
    # Teste 3: Múltiplos escapes
    print("\n" + "=" * 60)
    print("📝 Teste 3: Múltiplos tipos de escape")
    
    complex_escape = '''
    {"command": "create_file", "args": ["test.txt", "Line 1\\nLine 2\\tTabbed\\nQuote: \\"Hello\\""]}
    '''
    
    result3 = parser.parse_action_from_response(complex_escape)
    
    print(f"Resultado: {result3}")
    
    if result3.get('command') == 'create_file':
        args = result3.get('args', [])
        if len(args) >= 2:
            print(f"Conteúdo decodificado:")
            print(repr(args[1]))
            
            expected = 'Line 1\nLine 2\tTabbed\nQuote: "Hello"'
            if args[1] == expected:
                print("✅ Múltiplos escapes funcionaram!")
            else:
                print("❌ Múltiplos escapes falharam")
                print(f"Esperado: {repr(expected)}")
                print(f"Obtido: {repr(args[1])}")
    
    # Teste 4: edit_code com JSON escapado
    print("\n" + "=" * 60)
    print("📝 Teste 4: edit_code com JSON escapado")
    
    edit_case = '''
    {"command": "edit_code", "args": ["config.js", "old_config = {}", "new_config = {\\"key\\": \\"value\\"}"]}
    '''
    
    result4 = parser.parse_action_from_response(edit_case)
    
    print(f"Resultado: {result4}")
    
    if result4.get('command') == 'edit_code' and len(result4.get('args', [])) == 3:
        print("✅ edit_code com JSON escapado funcionou!")
    else:
        print("❌ edit_code com JSON escapado falhou")

if __name__ == "__main__":
    test_escaped_json_parsing()
