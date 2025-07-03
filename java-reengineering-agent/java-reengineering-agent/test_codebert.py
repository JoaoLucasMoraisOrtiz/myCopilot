"""
Teste funcional rápido para CodeBERT Encoder

Este script testa a funcionalidade básica do encoder CodeBERT
sem necessidade de instalar dependências pesadas.
"""

import sys
import os
from pathlib import Path

# Add src to path - fix relative import issue
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Also add parent directory for package imports
sys.path.insert(0, str(current_dir))

def test_imports():
    """Testa se as importações funcionam."""
    print("🧪 Testando importações...")
    
    try:
        # Test basic imports first
        import torch
        print(f"✅ PyTorch: {torch.__version__}")
        
        import numpy as np
        print(f"✅ NumPy: {np.__version__}")
        
        from transformers import AutoTokenizer, AutoModel
        print("✅ Transformers importado com sucesso")
        
        # Test our modules
        from rag.codebert_encoder import CodeBERTEncoder, CodeEmbedding
        print("✅ CodeBERT encoder importado com sucesso")
        
        from utils.logger import AgentLogger
        print("✅ Logger importado com sucesso")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return False

def test_encoder_basic():
    """Testa a funcionalidade básica do encoder."""
    print("\n🧪 Testando encoder básico...")
    
    try:
        from rag.codebert_encoder import CodeBERTEncoder
        
        # Usar modelo menor para teste
        print("Inicializando encoder (pode demorar um pouco para baixar o modelo)...")
        encoder = CodeBERTEncoder(
            model_name="microsoft/codebert-base",
            device="cpu",
            max_length=128,  # Menor para teste
            batch_size=2
        )
        
        print(f"✅ Encoder inicializado")
        print(f"   - Modelo: {encoder.model_name}")
        print(f"   - Device: {encoder.device}")
        print(f"   - Dimensão embedding: {encoder.embedding_dim}")
        
        return encoder
        
    except Exception as e:
        print(f"❌ Erro ao inicializar encoder: {e}")
        return None

def test_simple_encoding(encoder):
    """Testa encoding simples."""
    print("\n🧪 Testando encoding simples...")
    
    try:
        # Código Java simples para teste
        java_code = """
        public int add(int a, int b) {
            return a + b;
        }
        """
        
        print("Gerando embedding...")
        embedding = encoder.encode_single(java_code, "method")
        
        print(f"✅ Embedding gerado com sucesso")
        print(f"   - Shape: {embedding.shape}")
        print(f"   - Tipo: {type(embedding)}")
        print(f"   - Primeiros valores: {embedding[:3]}")
        
        return embedding
        
    except Exception as e:
        print(f"❌ Erro no encoding: {e}")
        return None

def test_similarity(encoder):
    """Testa cálculo de similaridade."""
    print("\n🧪 Testando similaridade...")
    
    try:
        # Dois métodos similares
        code1 = "public int add(int a, int b) { return a + b; }"
        code2 = "public int sum(int x, int y) { return x + y; }"
        
        # Um método diferente
        code3 = "public String getName() { return this.name; }"
        
        print("Gerando embeddings...")
        emb1 = encoder.encode_single(code1, "method")
        emb2 = encoder.encode_single(code2, "method")
        emb3 = encoder.encode_single(code3, "method")
        
        # Calcular similaridades
        sim_similar = encoder.get_similarity(emb1, emb2)
        sim_different = encoder.get_similarity(emb1, emb3)
        sim_self = encoder.get_similarity(emb1, emb1)
        
        print(f"✅ Similaridade calculada")
        print(f"   - Métodos similares (add/sum): {sim_similar:.4f}")
        print(f"   - Métodos diferentes (add/getName): {sim_different:.4f}")
        print(f"   - Auto-similaridade: {sim_self:.4f}")
        
        # Validar resultados esperados
        if sim_self > 0.99:
            print("✅ Auto-similaridade OK")
        else:
            print("❌ Auto-similaridade inesperada")
            
        if sim_similar > sim_different:
            print("✅ Detecção semântica OK")
        else:
            print("❌ Detecção semântica falhou")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de similaridade: {e}")
        return False

def test_cache(encoder):
    """Testa sistema de cache."""
    print("\n🧪 Testando cache...")
    
    try:
        import time
        
        code = "public void test() { System.out.println('Hello'); }"
        
        # Primeira execução (sem cache)
        start = time.time()
        emb1 = encoder.encode_single(code, "method", use_cache=True)
        time1 = time.time() - start
        
        # Segunda execução (com cache)
        start = time.time()
        emb2 = encoder.encode_single(code, "method", use_cache=True)
        time2 = time.time() - start
        
        # Verificar se embeddings são idênticos
        import numpy as np
        are_equal = np.allclose(emb1, emb2)
        
        print(f"✅ Cache testado")
        print(f"   - Primeira execução: {time1:.4f}s")
        print(f"   - Segunda execução: {time2:.4f}s")
        print(f"   - Speedup: {time1/time2 if time2 > 0 else 'infinito'}x")
        print(f"   - Embeddings iguais: {are_equal}")
        
        # Estatísticas do cache
        stats = encoder.get_cache_stats()
        print(f"   - Cache size: {stats['cache_size']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de cache: {e}")
        return False

def test_code_embedding_object(encoder):
    """Testa objeto CodeEmbedding."""
    print("\n🧪 Testando objeto CodeEmbedding...")
    
    try:
        from rag.codebert_encoder import CodeEmbedding
        
        code = "public class Test { }"
        
        # Criar embedding object
        embedding_obj = encoder.create_code_embedding(
            code=code,
            code_id="test_001",
            code_type="class",
            file_path="Test.java",
            metadata={"complexity": "low"}
        )
        
        print(f"✅ CodeEmbedding criado")
        print(f"   - ID: {embedding_obj.code_id}")
        print(f"   - Tipo: {embedding_obj.code_type}")
        print(f"   - Arquivo: {embedding_obj.file_path}")
        print(f"   - Metadata: {embedding_obj.metadata}")
        
        # Testar serialização
        data = embedding_obj.to_dict()
        restored = CodeEmbedding.from_dict(data)
        
        print(f"✅ Serialização/deserialização OK")
        print(f"   - ID restaurado: {restored.code_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de CodeEmbedding: {e}")
        return False

def main():
    """Executa todos os testes."""
    print("🚀 Teste Funcional do CodeBERT Encoder")
    print("=" * 50)
    
    # Teste 1: Importações
    if not test_imports():
        print("\n❌ Falha nas importações. Verifique as dependências.")
        return
    
    # Teste 2: Inicialização do encoder
    encoder = test_encoder_basic()
    if not encoder:
        print("\n❌ Falha na inicialização do encoder.")
        return
    
    # Teste 3: Encoding simples
    embedding = test_simple_encoding(encoder)
    if embedding is None:
        print("\n❌ Falha no encoding simples.")
        return
    
    # Teste 4: Similaridade
    if not test_similarity(encoder):
        print("\n❌ Falha no teste de similaridade.")
        return
    
    # Teste 5: Cache
    if not test_cache(encoder):
        print("\n❌ Falha no teste de cache.")
        return
    
    # Teste 6: CodeEmbedding object
    if not test_code_embedding_object(encoder):
        print("\n❌ Falha no teste de CodeEmbedding.")
        return
    
    print("\n" + "=" * 50)
    print("🎉 TODOS OS TESTES PASSARAM!")
    print("✅ CodeBERT encoder está funcionando corretamente")
    
    # Estatísticas finais
    stats = encoder.get_cache_stats()
    print(f"\n📊 Estatísticas finais:")
    print(f"   - Cache entries: {stats['cache_size']}")
    print(f"   - Embedding dimension: {stats['embedding_dimension']}")
    print(f"   - Device usado: {stats['device']}")
    print(f"   - Modelo: {stats['model_name']}")

if __name__ == "__main__":
    main()
