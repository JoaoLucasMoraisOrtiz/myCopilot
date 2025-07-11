#!/usr/bin/env python3
"""
Teste específico para reproduzir o erro exato do usuário.
"""

from core.agent.response_parser import AgentResponseParser

def test_exact_user_error():
    """Reproduz exatamente o erro reportado pelo usuário."""
    
    parser = AgentResponseParser()
    
    print("🐛 Reproduzindo o erro exato do usuário")
    print("=" * 60)
    
    # Exatamente como o usuário reportou
    exact_user_input = '''{"command": "create_file", "args": ["package.json", "{\\n  \\"name\\": \\"form-builder\\",\\n  \\"version\\": \\"1.0.0\\",\\n  \\"main\\": \\"index.js\\",\\n  \\"scripts\\": {\\n    \\"dev\\": \\"next dev\\",\\n    \\"build\\": \\"next build\\",\\n    \\"start\\": \\"next start\\"\\n  },\\n  \\"dependencies\\": {\\n    \\"next\\": \\"latest\\",\\n    \\"react\\": \\"latest\\",\\n    \\"react-dom\\": \\"latest\\"\\n  },\\n  \\"devDependencies\\": {\\n    \\"typescript\\": \\"latest\\",\\n    \\"@types/react\\": \\"latest\\",\\n    \\"@types/node\\": \\"latest\\"\\n  }\\n}"]}'''
    
    print("📝 Input exato do usuário:")
    print(exact_user_input[:200] + "...")
    
    print("\n🔍 Tentando fazer parse...")
    result = parser.parse_action_from_response(exact_user_input)
    
    print(f"\n✅ Resultado final:")
    print(f"  Comando: {result.get('command')}")
    print(f"  Número de argumentos: {len(result.get('args', []))}")
    
    if result.get('command') == 'create_file':
        args = result.get('args', [])
        if len(args) >= 2:
            print(f"  Arquivo: {args[0]}")
            print(f"  Conteúdo (primeiros 200 chars):")
            print(f"    {args[1][:200]}...")
            
            # Verifica se foi decodificado corretamente
            content = args[1]
            if '"name": "form-builder"' in content and '\\n' not in content:
                print("🎉 SUCCESS: JSON foi decodificado corretamente!")
                print("✅ As quebras de linha foram convertidas de \\n para \\n reais")
                print("✅ As aspas foram decodificadas de \\\\ para \\\"")
            else:
                print("❌ FAILED: JSON não foi decodificado corretamente")
                if '\\\\n' in content:
                    print("  - Ainda contém \\\\n escapado")
                if '\\\\"' in content:
                    print("  - Ainda contém aspas escapadas")
        else:
            print("❌ Argumentos insuficientes")
    else:
        print("❌ Comando não foi reconhecido corretamente")
    
    # Teste para verificar se o content pode ser parseado como JSON válido
    if result.get('command') == 'create_file' and len(result.get('args', [])) >= 2:
        import json
        try:
            parsed_json = json.loads(result['args'][1])
            print(f"\n✅ VALIDATION: Conteúdo é JSON válido!")
            print(f"  Nome do projeto: {parsed_json.get('name')}")
            print(f"  Versão: {parsed_json.get('version')}")
            print(f"  Dependências: {list(parsed_json.get('dependencies', {}).keys())}")
        except json.JSONDecodeError as e:
            print(f"\n❌ VALIDATION: Conteúdo NÃO é JSON válido: {e}")

def test_manual_json_parsing():
    """Teste manual para entender o problema."""
    
    # Exemplo de como o JSON deveria ser
    correct_json = '{"command": "create_file", "args": ["package.json", "{\\"name\\": \\"test\\"}"]}'
    
    print("\n" + "=" * 60)
    print("🔧 Teste manual de parsing JSON")
    
    print(f"JSON correto simples: {correct_json}")
    
    import json
    try:
        parsed = json.loads(correct_json)
        print(f"✅ Parse bem-sucedido: {parsed}")
        print(f"Conteúdo decodificado: {parsed['args'][1]}")
    except json.JSONDecodeError as e:
        print(f"❌ Erro de parse: {e}")

if __name__ == "__main__":
    test_exact_user_error()
    test_manual_json_parsing()
