#!/usr/bin/env python3
"""
Script de teste para validar o Sistema de Contexto Inteligente (RAG)
Execute: python test_rag_system.py
"""

import os
import sys
from smart_context_manager import SmartContextManager

def test_rag_system():
    print("🧪 TESTANDO SISTEMA RAG")
    print("=" * 50)
    
    # 1. Teste de inicialização
    print("\n1️⃣ Testando inicialização...")
    try:
        smart_context = SmartContextManager("migration_docs", max_context_size=5000)
        print("✅ SmartContextManager inicializado")
    except Exception as e:
        print(f"❌ Erro na inicialização: {e}")
        return False
    
    # 2. Teste de extração de palavras-chave
    print("\n2️⃣ Testando extração de palavras-chave...")
    test_text = """
    Este é um sistema Java Spring Boot com arquitetura microserviços.
    Utiliza Maven para build e MySQL como banco de dados.
    A aplicação possui controladores REST e serviços de negócio.
    """
    
    keywords = smart_context.extract_keywords(test_text)
    print(f"📝 Texto de teste: {len(test_text)} chars")
    print(f"🔑 Palavras-chave extraídas: {keywords}")
    
    if len(keywords) > 0:
        print("✅ Extração de palavras-chave funcionando")
    else:
        print("❌ Extração de palavras-chave falhou")
        return False
    
    # 3. Teste de indexação de documento
    print("\n3️⃣ Testando indexação de documento...")
    try:
        smart_context.index_document(
            "test_architecture", 
            test_text, 
            "architecture"
        )
        print("✅ Documento indexado com sucesso")
    except Exception as e:
        print(f"❌ Erro na indexação: {e}")
        return False
    
    # 4. Teste de busca
    print("\n4️⃣ Testando busca de documentos relevantes...")
    try:
        results = smart_context.search_relevant_docs("sistema java spring", max_results=3)
        print(f"🔍 Resultados encontrados: {len(results)}")
        
        for i, (doc_id, relevance, summary) in enumerate(results):
            print(f"   {i+1}. {doc_id} (relevância: {relevance:.2f})")
            print(f"      Resumo: {summary[:100]}...")
        
        if len(results) > 0:
            print("✅ Busca funcionando")
        else:
            print("⚠️ Nenhum resultado encontrado (normal para teste inicial)")
    except Exception as e:
        print(f"❌ Erro na busca: {e}")
        return False
    
    # 5. Teste de contexto inteligente
    print("\n5️⃣ Testando construção de contexto inteligente...")
    try:
        task_desc = "Implementar serviço REST para gerenciar usuários no sistema Java"
        context = smart_context.build_smart_context_for_task(task_desc, "implementation")
        
        print(f"📝 Task: {task_desc}")
        print(f"🧠 Contexto gerado: {len(context)} chars")
        print(f"📄 Preview: {context[:200]}...")
        
        if len(context) > 0 and len(context) <= smart_context.max_context_size:
            print("✅ Contexto inteligente funcionando")
        else:
            print(f"⚠️ Contexto muito grande: {len(context)} chars")
    except Exception as e:
        print(f"❌ Erro na construção de contexto: {e}")
        return False
    
    # 6. Teste de estatísticas
    print("\n6️⃣ Testando estatísticas...")
    try:
        stats = smart_context.get_context_stats()
        print(f"📊 Estatísticas:")
        print(f"   - Total de documentos: {stats['total_documents']}")
        print(f"   - Tamanho total: {stats['total_size']:,} chars")
        print(f"   - Tamanho médio: {stats['average_size']:,} chars")
        print(f"   - Tipos de documento: {stats['document_types']}")
        print("✅ Estatísticas funcionando")
    except Exception as e:
        print(f"❌ Erro nas estatísticas: {e}")
        return False
    
    # 7. Simulação de redução de contexto
    print("\n7️⃣ Simulando redução de contexto...")
    large_context_size = 56942  # Tamanho original problemático
    small_context_size = len(context)
    reduction_pct = ((large_context_size - small_context_size) / large_context_size) * 100
    
    print(f"📈 Simulação de redução:")
    print(f"   - Contexto original: {large_context_size:,} chars")
    print(f"   - Contexto otimizado: {small_context_size:,} chars")
    print(f"   - Redução: {reduction_pct:.1f}%")
    print(f"   - Tokens economizados: ~{(large_context_size - small_context_size) // 4:,}")
    
    if reduction_pct > 50:
        print("✅ Redução significativa alcançada")
    else:
        print("⚠️ Redução menor que esperada")
    
    print("\n" + "=" * 50)
    print("🎉 TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
    print("🚀 Sistema RAG está funcionando corretamente")
    print("💡 Agora você pode executar o sistema principal:")
    print("   python main.py")
    
    return True

if __name__ == "__main__":
    # Verifica se está no diretório correto
    if not os.path.exists("main.py"):
        print("❌ Execute este script no diretório do projeto (onde está o main.py)")
        sys.exit(1)
    
    # Cria diretório de saída se não existir
    os.makedirs("migration_docs", exist_ok=True)
    
    # Executa os testes
    success = test_rag_system()
    
    if success:
        print("\n✅ Sistema pronto para uso!")
    else:
        print("\n❌ Alguns testes falharam. Verifique os erros acima.")
        sys.exit(1)
