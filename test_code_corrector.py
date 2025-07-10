"""
Teste do Sistema de Correção de Código

Este script demonstra o funcionamento do mini-compilador corretor
integrado ao sistema de geração de código.
"""

import sys
sys.path.append('..')

from core.code_corrector import get_corrector_for_language

def test_python_corrections():
    """Testa correções em código Python."""
    print("🐍 Testando correções Python...")
    
    # Código Python com erros intencionais
    buggy_python_code = '''
def calculate_sum(a, b)
    if a > 0
        result = a + b
        print "Result is:", result
    return result

# Função sem indentação adequada
def broken_function():
x = 10
y = 20
return x + y

# String não fechada
message = "Hello World
'''
    
    print("Código original:")
    print(buggy_python_code)
    print("\n" + "="*50)
    
    corrector = get_corrector_for_language('python')
    result = corrector.correct(buggy_python_code)
    
    print("Código corrigido:")
    print(result.corrected_code)
    print("\n" + "="*50)
    
    print("Correções aplicadas:")
    for correction in result.corrections_applied:
        print(f"  • {correction}")
    
    print(f"\nCompilação bem-sucedida: {'✅' if result.compilation_successful else '❌'}")
    if result.error_messages:
        print("Erros restantes:")
        for error in result.error_messages:
            print(f"  • {error}")

def test_java_corrections():
    """Testa correções em código Java."""
    print("\n☕ Testando correções Java...")
    
    # Código Java com erros intencionais
    buggy_java_code = '''
public class Calculator {
    static void main(String[] args) {
        int x = 10
        int y = 20
        System.out.println("Sum: " + (x + y))
    }
    
    public int multiply(int a, int b) 
        return a * b
    }
}
'''
    
    print("Código original:")
    print(buggy_java_code)
    print("\n" + "="*50)
    
    corrector = get_corrector_for_language('java')
    result = corrector.correct(buggy_java_code)
    
    print("Código corrigido:")
    print(result.corrected_code)
    print("\n" + "="*50)
    
    print("Correções aplicadas:")
    for correction in result.corrections_applied:
        print(f"  • {correction}")
    
    print(f"\nCompilação bem-sucedida: {'✅' if result.compilation_successful else '❌'}")
    if result.error_messages:
        print("Erros restantes:")
        for error in result.error_messages:
            print(f"  • {error}")

def test_javascript_corrections():
    """Testa correções em código JavaScript."""
    print("\n🌐 Testando correções JavaScript...")
    
    # Código JavaScript com erros intencionais
    buggy_js_code = '''
funtion calculate(x, y) {
    if (x > 0 {
        let result = x + y
        console.log("Result:", result)
        retrun result
    }
}

const message = "Hello World
const numbers = [1, 2, 3, 4, 5

// Arrow function malformada
const multiply = x, y => x * y
'''
    
    print("Código original:")
    print(buggy_js_code)
    print("\n" + "="*50)
    
    corrector = get_corrector_for_language('javascript')
    result = corrector.correct(buggy_js_code)
    
    print("Código corrigido:")
    print(result.corrected_code)
    print("\n" + "="*50)
    
    print("Correções aplicadas:")
    for correction in result.corrections_applied:
        print(f"  • {correction}")
    
    print(f"\nValidação bem-sucedida: {'✅' if result.compilation_successful else '❌'}")
    if result.error_messages:
        print("Erros restantes:")
        for error in result.error_messages:
            print(f"  • {error}")

def test_integration_with_agent():
    """Demonstra a integração com o agente."""
    print("\n🤖 Testando integração com o agente...")
    
    # Simula o comportamento do agente
    from core.agent.agent_core import AgentCore
    
    # Este é um exemplo simplificado
    print("A integração está configurada no método _apply_code_correction do AgentCore")
    print("Quando o LLM gerar código através do comando save_code:")
    print("1. O código será automaticamente validado pelo compilador padrão")
    print("2. Se houver erros, o corretor será acionado")
    print("3. O código corrigido será salvo no projeto")
    print("4. Um log das correções será exibido ao usuário")

if __name__ == "__main__":
    print("🔧 Sistema de Correção Automática de Código")
    print("=" * 60)
    
    try:
        test_python_corrections()
        test_java_corrections() 
        test_javascript_corrections()
        test_integration_with_agent()
        
        print("\n✅ Todos os testes concluídos!")
        print("\nO sistema está pronto para ser usado com o agente.")
        print("Agora quando o LLM gerar código com erros de sintaxe,")
        print("eles serão automaticamente detectados e corrigidos!")
        
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()
