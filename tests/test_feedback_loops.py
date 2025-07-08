#!/usr/bin/env python3
"""
Teste das funcionalidades de feedback loop implementadas
"""

import os
import sys
import tempfile
import shutil

# Adiciona o diretório atual ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import (
    initialize_global_context, 
    update_global_context_with_validation,
    update_global_context_with_integration,
    load_enhanced_context,
    OUTPUT_DIR
)

def test_feedback_loops():
    """Testa os feedback loops P4_2 -.-> Context3 e P4_3 -.-> Context3"""
    
    # Cria um diretório temporário para testes
    original_output_dir = OUTPUT_DIR
    test_dir = tempfile.mkdtemp()
    
    try:
        # Sobrescreve OUTPUT_DIR temporariamente
        import main
        main.OUTPUT_DIR = test_dir
        
        print("🧪 Testando Feedback Loops...")
        
        # Testa inicialização do contexto global
        print("\n1. Testando inicialização do contexto global...")
        initialize_global_context()
        
        global_context_file = os.path.join(test_dir, "global_context.md")
        assert os.path.exists(global_context_file), "Arquivo de contexto global não foi criado"
        print("✅ Contexto global inicializado")
        
        # Testa feedback de validação aprovada
        print("\n2. Testando feedback de validação aprovada...")
        validation_result = "✅ APROVADO - Código atende aos critérios de qualidade"
        update_global_context_with_validation(1, "Implementar API de usuários", validation_result, is_approved=True)
        print("✅ Feedback de validação aprovada registrado")
        
        # Testa feedback de validação rejeitada
        print("\n3. Testando feedback de validação rejeitada...")
        validation_result = "❌ REJEITAR - Problemas de segurança identificados"
        update_global_context_with_validation(2, "Implementar autenticação", validation_result, is_approved=False)
        print("✅ Feedback de validação rejeitada registrado")
        
        # Testa feedback de integração
        print("\n4. Testando feedback de integração...")
        integration_plan = """
        1. Deploy em ambiente de staging
        2. Testes de integração com banco de dados
        3. Validação de APIs externas
        """
        update_global_context_with_integration(1, "Implementar API de usuários", integration_plan, success=True)
        print("✅ Feedback de integração registrado")
        
        # Testa carregamento de contexto melhorado
        print("\n5. Testando carregamento de contexto melhorado...")
        
        # Cria arquivos de contexto das fases anteriores
        phase_files = ["architecture-analysis.md", "business-flows.md", "target-architecture.md"]
        for filename in phase_files:
            filepath = os.path.join(test_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# {filename}\nConteúdo de exemplo para {filename}")
        
        enhanced_context = load_enhanced_context(phase_files)
        assert "CONTEXTO GLOBAL ACUMULADO" in enhanced_context, "Contexto global não foi incluído"
        assert "Feedback de Validação" in enhanced_context, "Feedback de validação não encontrado"
        assert "Feedback de Integração" in enhanced_context, "Feedback de integração não encontrado"
        print("✅ Contexto melhorado carregado com sucesso")
        
        # Verifica conteúdo do arquivo global
        print("\n6. Verificando conteúdo do contexto global...")
        with open(global_context_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "Task 1" in content, "Task 1 não encontrada no contexto"
        assert "Task 2" in content, "Task 2 não encontrada no contexto"
        assert "✅ APROVADO" in content, "Validação aprovada não encontrada"
        assert "❌ REJEITADO" in content, "Validação rejeitada não encontrada"
        assert "INTEGRAÇÃO PLANEJADA" in content, "Integração não encontrada"
        print("✅ Conteúdo do contexto global está correto")
        
        print("\n🎉 Todos os testes passaram! Os feedback loops estão funcionando corretamente.")
        print(f"📁 Verifique o arquivo de teste em: {global_context_file}")
        
        # Mostra o conteúdo do contexto global
        print(f"\n📄 Conteúdo do contexto global:")
        print("=" * 60)
        print(content)
        print("=" * 60)
        
    finally:
        # Restaura OUTPUT_DIR original
        main.OUTPUT_DIR = original_output_dir
        
        # Limpa diretório temporário (opcional - descomente para limpar)
        # shutil.rmtree(test_dir)
        print(f"\n🗂️  Arquivos de teste mantidos em: {test_dir}")

if __name__ == "__main__":
    test_feedback_loops()
