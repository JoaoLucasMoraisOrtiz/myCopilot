#!/usr/bin/env python3
"""
Teste que simula exatamente o contexto de erro do usuário.
"""

from core.agent.response_parser import AgentResponseParser

def test_with_user_context():
    """Testa com o contexto exato que o usuário tinha."""
    
    parser = AgentResponseParser()
    
    print("🧪 Simulando contexto exato do usuário")
    print("=" * 60)
    
    # O que o usuário reportou exatamente
    user_response = '''
 Resposta:
 **Ação:**
{"command": "create_file", "args": ["package.json", "{\\n  \\"name\\": \\"form-builder\\",\\n  \\"version\\": \\"1.0.0\\",\\n  \\"main\\": \\"index.js\\",\\n  \\"scripts\\": {\\n    \\"dev\\": \\"next dev\\",\\n    \\"build\\": \\"next build\\",\\n    \\"start\\": \\"next start\\"\\n  },\\n  \\"dependencies\\": {\\n    \\"next\\": \\"latest\\",\\n    \\"react\\": \\"latest\\",\\n    \\"react-dom\\": \\"latest\\"\\n  },\\n  \\"devDependencies\\": {\\n    \\"typescript\\": \\"latest\\",\\n    \\"@types/react\\": \\"latest\\",\\n    \\"@types/node\\": \\"latest\\"\\n  }\\n}"]}
    '''
    
    print("📝 Contexto completo do usuário:")
    print(user_response)
    
    print("\n🔍 Analisando com parser...")
    result = parser.parse_action_from_response(user_response)
    
    print(f"\n📊 Resultado:")
    print(f"  Comando: {result.get('command')}")
    print(f"  Args: {len(result.get('args', []))} argumentos")
    
    if result.get('command') == 'create_file':
        args = result.get('args', [])
        if len(args) >= 2:
            print(f"✅ SUCESSO: Comando create_file extraído corretamente!")
            print(f"  Arquivo: {args[0]}")
            
            # Verifica se o JSON foi decodificado
            content = args[1]
            lines = content.split('\n')
            print(f"  Conteúdo ({len(lines)} linhas):")
            for i, line in enumerate(lines[:5]):  # Primeiras 5 linhas
                print(f"    {i+1}: {line}")
            if len(lines) > 5:
                print(f"    ... mais {len(lines)-5} linhas")
            
            # Testa se é JSON válido
            import json
            try:
                parsed = json.loads(content)
                print(f"✅ JSON é válido! Nome: {parsed.get('name')}")
            except json.JSONDecodeError as e:
                print(f"❌ JSON inválido: {e}")
        else:
            print("❌ Argumentos insuficientes")
    else:
        print(f"❌ Comando incorreto: {result.get('command')}")

def verify_json_structure():
    """Verifica se podemos reproduzir o erro específico."""
    
    print("\n" + "=" * 60)
    print("🔬 Análise detalhada do JSON problemático")
    
    # Vamos tentar reproduzir manualmente o erro
    problematic_json = '{"command": "create_file", "args": ["package.json", "{\\\\n  \\\\"name\\\\": \\\\"form-builder\\\\"}"]}'
    
    print(f"JSON problemático: {problematic_json}")
    
    import json
    try:
        parsed = json.loads(problematic_json)
        print(f"✅ Parse manual bem-sucedido: {parsed}")
    except json.JSONDecodeError as e:
        print(f"❌ Parse manual falhou: {e}")
        print(f"  Posição do erro: {e.pos}")
        print(f"  Contexto: '{problematic_json[max(0, e.pos-10):e.pos+10]}'")

if __name__ == "__main__":
    test_with_user_context()
    verify_json_structure()
