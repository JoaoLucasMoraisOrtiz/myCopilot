#!/usr/bin/env python3
"""
Debug detalhado do caso problemático específico.
"""

from core.agent.response_parser import AgentResponseParser

def debug_specific_case():
    """Debug do caso específico do usuário."""
    
    parser = AgentResponseParser()
    
    # O caso exato do usuário
    problematic_text = '["src/main.py", "print("hello")", "print("Hello, World!")"]'
    print(f"Texto problemático: {problematic_text}")
    
    # Vamos analisar caractere por caractere
    pos = 1  # Começando após o '['
    in_string = False
    current_arg = ""
    args = []
    
    print("\n📝 Análise caractere por caractere:")
    
    for i, char in enumerate(problematic_text[1:], 1):  # Pula o '['
        print(f"Pos {i:2d}: '{char}' | in_string={in_string} | current_arg='{current_arg}'")
        
        if char == '"':
            current_arg += char
            in_string = not in_string
            print(f"         Aspa encontrada! in_string agora é {in_string}")
        elif not in_string and char == ',':
            print(f"         Vírgula fora de string! Finalizando arg: '{current_arg}'")
            if current_arg.strip().startswith('"') and current_arg.strip().endswith('"'):
                arg_value = current_arg.strip()[1:-1]
                args.append(arg_value)
                print(f"         Argumento adicionado: '{arg_value}'")
            current_arg = ""
        elif not in_string and char == ']':
            print(f"         Fim do array! Arg final: '{current_arg}'")
            if current_arg.strip():
                if current_arg.strip().startswith('"') and current_arg.strip().endswith('"'):
                    arg_value = current_arg.strip()[1:-1]
                    args.append(arg_value)
                    print(f"         Argumento final adicionado: '{arg_value}'")
            break
        elif not in_string and char.isspace():
            if current_arg.strip():
                current_arg += char
        else:
            current_arg += char
    
    print(f"\n🔍 Argumentos finais: {args}")
    print(f"Número de argumentos: {len(args)}")
    
    # Agora teste com o método real
    print(f"\n🔧 Teste com método real:")
    start_pos = problematic_text.find('[')
    real_args = parser._extract_args_with_quote_counting(problematic_text, start_pos)
    print(f"Argumentos pelo método real: {real_args}")

def analyze_quote_pattern():
    """Analisa o padrão de aspas no texto problemático."""
    
    text = '"print("hello")"'
    print(f"Analisando: {text}")
    
    in_string = False
    quote_positions = []
    
    for i, char in enumerate(text):
        if char == '"':
            quote_positions.append(i)
            in_string = not in_string
            print(f"Pos {i}: Aspa encontrada, in_string={in_string}")
    
    print(f"Posições das aspas: {quote_positions}")
    print(f"Estado final in_string: {in_string}")

if __name__ == "__main__":
    print("🐛 Debug detalhado do caso problemático")
    print("=" * 50)
    
    debug_specific_case()
    
    print("\n" + "=" * 50)
    analyze_quote_pattern()
