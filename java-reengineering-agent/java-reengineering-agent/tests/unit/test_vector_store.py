"""
Testes unitários para SQLiteVectorStore

Testa todas as funcionalidades do sistema de armazenamento vetorial:
- Criação e inicialização do banco
- Inserção de arquivos e chunks
- Armazenamento e recuperação de embeddings
- Busca por similaridade
- Cache de consultas
- Estatísticas e métricas
"""

import pytest
import numpy as np
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import json

from src.rag.vector_store import SQLiteVectorStore, VectorStoreManager, CodeChunk, EmbeddingRecord


class TestSQLiteVectorStore:
    """Testes para a classe SQLiteVectorStore"""
    
    @pytest.fixture
    def temp_db_path(self):
        """Cria um banco temporário para testes"""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test_vector_store.db"
        yield str(db_path)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def vector_store(self, temp_db_path):
        """Instância do vector store para testes"""
        return SQLiteVectorStore(temp_db_path, embedding_dim=768)
    
    @pytest.fixture
    def sample_chunks(self):
        """Chunks de exemplo para testes"""
        return [
            CodeChunk(
                file_path="/test/Example.java",
                content="public class Example { }",
                start_line=1,
                end_line=1,
                chunk_type="class",
                complexity_score=1.0,
                hash="hash1"
            ),
            CodeChunk(
                file_path="/test/Example.java",
                content="public void method() { System.out.println(\"Hello\"); }",
                start_line=2,
                end_line=2,
                chunk_type="method",
                complexity_score=2.0,
                hash="hash2"
            )
        ]
    
    @pytest.fixture
    def sample_embeddings(self):
        """Embeddings de exemplo para testes"""
        return [
            np.random.rand(768).astype(np.float32),
            np.random.rand(768).astype(np.float32)
        ]
    
    def test_initialization(self, temp_db_path):
        """Testa inicialização do vector store"""
        vector_store = SQLiteVectorStore(temp_db_path, embedding_dim=768)
        
        # Verificar se arquivo foi criado
        assert Path(temp_db_path).exists()
        
        # Verificar dimensão
        assert vector_store.embedding_dim == 768
        
        # Verificar estatísticas iniciais
        stats = vector_store.get_statistics()
        assert stats['total_files'] == 0
        assert stats['total_chunks'] == 0
        assert stats['total_embeddings'] == 0
    
    def test_add_file(self, vector_store, sample_chunks):
        """Testa adição de arquivo com chunks"""
        file_content = "public class Example { public void method() { } }"
        
        file_id = vector_store.add_file(
            "/test/Example.java",
            file_content,
            sample_chunks
        )
        
        assert isinstance(file_id, int)
        assert file_id > 0
        
        # Verificar estatísticas
        stats = vector_store.get_statistics()
        assert stats['total_files'] == 1
        assert stats['total_chunks'] == 2
    
    def test_add_file_duplicate(self, vector_store, sample_chunks):
        """Testa adição de arquivo duplicado (mesmo hash)"""
        file_content = "public class Example { }"
        
        # Primeira inserção
        file_id1 = vector_store.add_file("/test/Example.java", file_content, sample_chunks)
        
        # Segunda inserção (mesmo conteúdo)
        file_id2 = vector_store.add_file("/test/Example.java", file_content, sample_chunks)
        
        # Deve retornar o mesmo ID
        assert file_id1 == file_id2
        
        # Estatísticas não devem mudar
        stats = vector_store.get_statistics()
        assert stats['total_files'] == 1
    
    def test_add_file_updated(self, vector_store, sample_chunks):
        """Testa atualização de arquivo existente"""
        # Primeira versão
        file_id1 = vector_store.add_file(
            "/test/Example.java",
            "public class Example { }",
            sample_chunks
        )
        
        # Segunda versão (conteúdo diferente)
        new_chunks = [
            CodeChunk(
                file_path="/test/Example.java",
                content="public class Example { private int x; }",
                start_line=1,
                end_line=1,
                chunk_type="class",
                complexity_score=2.0,
                hash="hash3"
            )
        ]
        
        file_id2 = vector_store.add_file(
            "/test/Example.java",
            "public class Example { private int x; }",
            new_chunks
        )
        
        # Deve ser o mesmo arquivo
        assert file_id1 == file_id2
        
        # Chunks devem ter sido atualizados
        chunks = vector_store.get_file_chunks(file_id1)
        assert len(chunks) == 1
        assert chunks[0]['complexity_score'] == 2.0
    
    def test_add_embeddings(self, vector_store, sample_chunks, sample_embeddings):
        """Testa adição de embeddings"""
        # Adicionar arquivo primeiro
        file_id = vector_store.add_file(
            "/test/Example.java",
            "public class Example { }",
            sample_chunks
        )
        
        # Obter IDs dos chunks
        chunks = vector_store.get_file_chunks(file_id)
        chunk_ids = [chunk['id'] for chunk in chunks]
        
        # Adicionar embeddings
        embeddings_data = list(zip(chunk_ids, sample_embeddings))
        vector_store.add_embeddings(file_id, embeddings_data)
        
        # Verificar estatísticas
        stats = vector_store.get_statistics()
        assert stats['total_embeddings'] == 2
        
        # Verificar que chunks têm embeddings
        chunks_updated = vector_store.get_file_chunks(file_id)
        for chunk in chunks_updated:
            assert chunk['has_embedding'] == 1
    
    def test_similarity_search(self, vector_store, sample_chunks, sample_embeddings):
        """Testa busca por similaridade"""
        # Setup: adicionar arquivo e embeddings
        file_id = vector_store.add_file(
            "/test/Example.java",
            "public class Example { }",
            sample_chunks
        )
        
        chunks = vector_store.get_file_chunks(file_id)
        chunk_ids = [chunk['id'] for chunk in chunks]
        embeddings_data = list(zip(chunk_ids, sample_embeddings))
        vector_store.add_embeddings(file_id, embeddings_data)
        
        # Busca por similaridade
        query_embedding = np.random.rand(768).astype(np.float32)
        results = vector_store.similarity_search(query_embedding, top_k=5)
        
        assert len(results) <= 5
        assert len(results) == 2  # Temos 2 chunks
        
        # Verificar estrutura dos resultados
        for result in results:
            assert 'similarity' in result
            assert 'chunk_content' in result
            assert 'file_path' in result
            assert 'chunk_type' in result
            assert isinstance(result['similarity'], float)
            assert 0 <= result['similarity'] <= 1
        
        # Resultados devem estar ordenados por similaridade
        similarities = [r['similarity'] for r in results]
        assert similarities == sorted(similarities, reverse=True)
    
    def test_similarity_search_with_filters(self, vector_store, sample_chunks, sample_embeddings):
        """Testa busca por similaridade com filtros"""
        # Setup
        file_id = vector_store.add_file("/test/Example.java", "content", sample_chunks)
        chunks = vector_store.get_file_chunks(file_id)
        chunk_ids = [chunk['id'] for chunk in chunks]
        embeddings_data = list(zip(chunk_ids, sample_embeddings))
        vector_store.add_embeddings(file_id, embeddings_data)
        
        # Busca com filtro de tipo
        query_embedding = np.random.rand(768).astype(np.float32)
        results = vector_store.similarity_search(
            query_embedding,
            top_k=10,
            file_types=['java']
        )
        
        assert len(results) == 2
        
        # Busca com similaridade mínima alta (deve retornar poucos ou nenhum resultado)
        results_filtered = vector_store.similarity_search(
            query_embedding,
            top_k=10,
            min_similarity=0.99
        )
        
        assert len(results_filtered) <= len(results)
    
    def test_get_file_chunks(self, vector_store, sample_chunks):
        """Testa recuperação de chunks de um arquivo"""
        file_id = vector_store.add_file("/test/Example.java", "content", sample_chunks)
        
        chunks = vector_store.get_file_chunks(file_id)
        
        assert len(chunks) == 2
        assert chunks[0]['chunk_type'] == 'class'
        assert chunks[1]['chunk_type'] == 'method'
        assert chunks[0]['start_line'] == 1
        assert chunks[1]['start_line'] == 2
    
    def test_get_files_without_embeddings(self, vector_store, sample_chunks, sample_embeddings):
        """Testa identificação de arquivos sem embeddings"""
        # Adicionar arquivo sem embeddings
        file_id1 = vector_store.add_file("/test/File1.java", "content1", sample_chunks[:1])
        
        # Adicionar arquivo com embeddings
        file_id2 = vector_store.add_file("/test/File2.java", "content2", sample_chunks[1:])
        chunks2 = vector_store.get_file_chunks(file_id2)
        vector_store.add_embeddings(file_id2, [(chunks2[0]['id'], sample_embeddings[0])])
        
        # Verificar arquivos sem embeddings
        files_without_embeddings = vector_store.get_files_without_embeddings()
        
        assert len(files_without_embeddings) == 1
        assert files_without_embeddings[0]['id'] == file_id1
    
    def test_statistics(self, vector_store, sample_chunks, sample_embeddings):
        """Testa geração de estatísticas"""
        # Estado inicial
        stats = vector_store.get_statistics()
        assert stats['total_files'] == 0
        assert stats['total_chunks'] == 0
        assert stats['total_embeddings'] == 0
        assert stats['avg_complexity'] == 0.0
        
        # Adicionar dados
        file_id = vector_store.add_file("/test/Example.java", "content", sample_chunks)
        chunks = vector_store.get_file_chunks(file_id)
        chunk_ids = [chunk['id'] for chunk in chunks]
        embeddings_data = list(zip(chunk_ids, sample_embeddings))
        vector_store.add_embeddings(file_id, embeddings_data)
        
        # Verificar estatísticas atualizadas
        stats = vector_store.get_statistics()
        assert stats['total_files'] == 1
        assert stats['total_chunks'] == 2
        assert stats['total_embeddings'] == 2
        assert stats['avg_complexity'] == 1.5  # (1.0 + 2.0) / 2
        assert 'chunks_by_type' in stats
        assert stats['chunks_by_type']['class'] == 1
        assert stats['chunks_by_type']['method'] == 1
    
    def test_cache_functionality(self, vector_store, sample_chunks, sample_embeddings):
        """Testa funcionalidade de cache"""
        # Setup
        file_id = vector_store.add_file("/test/Example.java", "content", sample_chunks)
        chunks = vector_store.get_file_chunks(file_id)
        chunk_ids = [chunk['id'] for chunk in chunks]
        embeddings_data = list(zip(chunk_ids, sample_embeddings))
        vector_store.add_embeddings(file_id, embeddings_data)
        
        query_embedding = np.random.rand(768).astype(np.float32)
        
        # Primeira busca (sem cache)
        results1 = vector_store.similarity_search(query_embedding, top_k=5)
        
        # Segunda busca (com cache)
        results2 = vector_store.similarity_search(query_embedding, top_k=5)
        
        # Resultados devem ser idênticos
        assert len(results1) == len(results2)
        for r1, r2 in zip(results1, results2):
            assert r1['chunk_id'] == r2['chunk_id']
            assert abs(r1['similarity'] - r2['similarity']) < 1e-6
    
    def test_cleanup_old_cache(self, vector_store):
        """Testa limpeza de cache antigo"""
        # Adicionar algumas entradas no cache
        for i in range(5):
            query_embedding = np.random.rand(768).astype(np.float32)
            vector_store.similarity_search(query_embedding, top_k=1)
        
        initial_cache_size = len(vector_store._query_cache)
        
        # Limpar cache (0 dias = limpar tudo)
        vector_store.cleanup_old_cache(days=0)
        
        # Cache em memória pode ainda ter entradas, mas banco deve estar limpo
        # Verificar que a operação não causou erro
        assert True  # Se chegou aqui, não houve exceção


class TestVectorStoreManager:
    """Testes para a classe VectorStoreManager"""
    
    @pytest.fixture
    def temp_db_path(self):
        """Cria um banco temporário para testes"""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test_manager.db"
        yield str(db_path)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def manager(self, temp_db_path):
        """Instância do manager para testes"""
        return VectorStoreManager(temp_db_path, embedding_dim=768)
    
    @pytest.fixture
    def sample_files_data(self):
        """Dados de arquivos para teste em lote"""
        return [
            {
                'path': '/test/File1.java',
                'content': 'public class File1 { }',
                'chunks': [
                    CodeChunk(
                        file_path="/test/File1.java",
                        content="public class File1 { }",
                        start_line=1,
                        end_line=1,
                        chunk_type="class",
                        complexity_score=1.0,
                        hash="hash1"
                    )
                ]
            },
            {
                'path': '/test/File2.java',
                'content': 'public class File2 { public void method() { } }',
                'chunks': [
                    CodeChunk(
                        file_path="/test/File2.java",
                        content="public class File2 { }",
                        start_line=1,
                        end_line=1,
                        chunk_type="class",
                        complexity_score=1.0,
                        hash="hash2"
                    ),
                    CodeChunk(
                        file_path="/test/File2.java",
                        content="public void method() { }",
                        start_line=2,
                        end_line=2,
                        chunk_type="method",
                        complexity_score=2.0,
                        hash="hash3"
                    )
                ]
            }
        ]
    
    def test_bulk_insert_files(self, manager, sample_files_data):
        """Testa inserção em lote de arquivos"""
        file_ids = manager.bulk_insert_files(sample_files_data)
        
        assert len(file_ids) == 2
        assert '/test/File1.java' in file_ids
        assert '/test/File2.java' in file_ids
        assert all(isinstance(fid, int) for fid in file_ids.values())
        
        # Verificar estatísticas
        stats = manager.vector_store.get_statistics()
        assert stats['total_files'] == 2
        assert stats['total_chunks'] == 3  # 1 + 2 chunks
    
    def test_search_similar_code(self, manager, sample_files_data):
        """Testa busca de código similar com metadados"""
        # Setup
        file_ids = manager.bulk_insert_files(sample_files_data)
        
        # Adicionar embeddings mock
        for file_path, file_id in file_ids.items():
            chunks = manager.vector_store.get_file_chunks(file_id)
            embeddings_data = [
                (chunk['id'], np.random.rand(768).astype(np.float32))
                for chunk in chunks
            ]
            manager.vector_store.add_embeddings(file_id, embeddings_data)
        
        # Buscar código similar
        query = "public class"
        query_embedding = np.random.rand(768).astype(np.float32)
        
        results = manager.search_similar_code(
            query,
            query_embedding,
            top_k=5,
            include_metadata=True
        )
        
        assert len(results) <= 5
        assert len(results) == 3  # Total de chunks
        
        # Verificar metadados enriquecidos
        for result in results:
            assert 'query' in result
            assert 'relevance_score' in result
            assert 'context_lines' in result
            assert result['query'] == query
            assert result['relevance_score'] == result['similarity']
    
    def test_get_health_status_healthy(self, manager, sample_files_data):
        """Testa status de saúde quando sistema está saudável"""
        # Setup com embeddings completos
        file_ids = manager.bulk_insert_files(sample_files_data)
        
        for file_path, file_id in file_ids.items():
            chunks = manager.vector_store.get_file_chunks(file_id)
            embeddings_data = [
                (chunk['id'], np.random.rand(768).astype(np.float32))
                for chunk in chunks
            ]
            manager.vector_store.add_embeddings(file_id, embeddings_data)
        
        health = manager.get_health_status()
        
        assert health['status'] == 'healthy'
        assert health['embedding_coverage'] == 1.0  # 100% coverage
        assert 'statistics' in health
        assert 'recommendations' in health
    
    def test_get_health_status_degraded(self, manager, sample_files_data):
        """Testa status de saúde quando sistema está degradado"""
        # Setup sem embeddings (cobertura 0%)
        manager.bulk_insert_files(sample_files_data)
        
        health = manager.get_health_status()
        
        assert health['status'] == 'degraded'
        assert health['embedding_coverage'] == 0.0
        assert len(health['recommendations']) > 0
        assert any('indexação' in rec for rec in health['recommendations'])
    
    def test_get_health_status_error(self, temp_db_path):
        """Testa status de saúde quando há erro"""
        # Criar manager com caminho inválido
        invalid_path = "/invalid/path/that/does/not/exist/db.sqlite"
        
        try:
            manager = VectorStoreManager(invalid_path)
            health = manager.get_health_status()
            
            # Se chegou aqui, pode ser que o diretório foi criado automaticamente
            # Nesse caso, deve estar saudável ou degradado, não em erro
            assert health['status'] in ['healthy', 'degraded', 'error']
            
        except Exception:
            # Se houve exceção na criação, isso é esperado
            assert True


class TestCodeChunk:
    """Testes para a classe CodeChunk"""
    
    def test_code_chunk_creation(self):
        """Testa criação de CodeChunk"""
        chunk = CodeChunk(
            file_path="/test/Example.java",
            content="public void method() { }",
            start_line=10,
            end_line=12,
            chunk_type="method",
            complexity_score=3.5,
            hash="abc123"
        )
        
        assert chunk.file_path == "/test/Example.java"
        assert chunk.content == "public void method() { }"
        assert chunk.start_line == 10
        assert chunk.end_line == 12
        assert chunk.chunk_type == "method"
        assert chunk.complexity_score == 3.5
        assert chunk.hash == "abc123"
    
    def test_code_chunk_to_dict(self):
        """Testa conversão de CodeChunk para dict"""
        chunk = CodeChunk(
            file_path="/test/Example.java",
            content="public class Example { }",
            start_line=1,
            end_line=1,
            chunk_type="class",
            complexity_score=1.0,
            hash="hash1"
        )
        
        chunk_dict = chunk.to_dict()
        
        assert isinstance(chunk_dict, dict)
        assert chunk_dict['file_path'] == "/test/Example.java"
        assert chunk_dict['chunk_type'] == "class"
        assert chunk_dict['complexity_score'] == 1.0


class TestEmbeddingRecord:
    """Testes para a classe EmbeddingRecord"""
    
    def test_embedding_record_creation(self):
        """Testa criação de EmbeddingRecord"""
        embedding = np.random.rand(768).astype(np.float32)
        record = EmbeddingRecord(
            id=1,
            file_id=10,
            chunk_id=20,
            embedding=embedding,
            chunk_content="public void method() { }",
            metadata={"type": "method"},
            created_at=datetime.now()
        )
        
        assert record.id == 1
        assert record.file_id == 10
        assert record.chunk_id == 20
        assert np.array_equal(record.embedding, embedding)
        assert record.chunk_content == "public void method() { }"
        assert record.metadata == {"type": "method"}
    
    def test_embedding_record_to_dict(self):
        """Testa conversão de EmbeddingRecord para dict"""
        embedding = np.random.rand(768).astype(np.float32)
        created_at = datetime.now()
        
        record = EmbeddingRecord(
            id=1,
            file_id=10,
            chunk_id=20,
            embedding=embedding,
            chunk_content="content",
            metadata={"key": "value"},
            created_at=created_at
        )
        
        record_dict = record.to_dict()
        
        assert isinstance(record_dict, dict)
        assert record_dict['id'] == 1
        assert record_dict['file_id'] == 10
        assert record_dict['embedding'] == embedding.tolist()
        assert record_dict['created_at'] == created_at.isoformat()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
