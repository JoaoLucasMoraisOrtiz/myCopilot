#!/usr/bin/env python3
"""
Teste demonstrando que o problema das aspas conflitantes foi resolvido.
"""

from core.agent.response_parser import AgentResponseParser

def test_user_specific_case():
    """Testa exatamente o caso que o usuário reportou."""
    
    parser = AgentResponseParser()
    
    print("🧪 Testando o caso específico do usuário")
    print("=" * 60)
    
    # Exatamente como o usuário demonstrou o problema
    user_problematic_json = '''
    {
        "command": "edit_code",
        "args": ["src/main.py", "print("hello")", "print("Hello, World!")"]
    }
    '''
    
    print("📝 JSON do usuário (problemático):")
    print(user_problematic_json)
    
    result = parser.parse_action_from_response(user_problematic_json)
    
    print(f"\n✅ Resultado parseado:")
    print(f"  Comando: {result.get('command')}")
    print(f"  Número de argumentos: {len(result.get('args', []))}")
    
    args = result.get('args', [])
    for i, arg in enumerate(args):
        print(f"  Arg {i}: {repr(arg)}")
    
    # Verifica se está correto
    if (result.get('command') == 'edit_code' and 
        len(args) == 3 and 
        args[0] == 'src/main.py' and
        args[1] == 'print("hello")' and
        args[2] == 'print("Hello, World!")'):
        print("\n🎉 PROBLEMA RESOLVIDO! O parser agora consegue lidar com aspas conflitantes!")
    else:
        print("\n❌ Ainda há problemas...")
    
    # Teste adicional: verificar se funciona com diferentes tipos de aspas
    print("\n" + "=" * 60)
    print("🧪 Teste adicional: Mistura de aspas simples e duplas")
    
    mixed_quotes = '''
    {
        "command": "edit_code", 
        "args": ["file.py", "print('old')", "print("new")"]
    }
    '''
    
    result2 = parser.parse_action_from_response(mixed_quotes)
    print(f"Resultado: {result2}")
    
    if result2.get('command') == 'edit_code' and len(result2.get('args', [])) == 3:
        print("✅ Aspas mistas também funcionam!")
    else:
        print("❌ Problema com aspas mistas")

if __name__ == "__main__":
    test_user_specific_case()
