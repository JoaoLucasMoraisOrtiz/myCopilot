#!/usr/bin/env python3
"""
Teste rápido do sistema de correção de código
"""

try:
    from core.code_corrector import get_corrector_for_language
    print("✅ Imports funcionando corretamente!")
    
    # Teste básico com Python
    corrector = get_corrector_for_language('python')
    print(f"✅ Corretor Python criado: {type(corrector).__name__}")
    
    # Teste básico de correção
    test_code = "def hello()\n    print('Hello World')"
    result = corrector.correct(test_code)
    
    print(f"✅ Correção testada com sucesso!")
    print(f"   Código original: {test_code!r}")
    print(f"   Código corrigido: {result.corrected_code!r}")
    print(f"   Correções aplicadas: {result.corrections_applied}")
    
except ImportError as e:
    print(f"❌ Erro de import: {e}")
except Exception as e:
    print(f"❌ Erro durante teste: {e}")
    import traceback
    traceback.print_exc()
