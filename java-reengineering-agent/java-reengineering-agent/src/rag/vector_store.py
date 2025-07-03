"""
SQLite Vector Store para embeddings do CodeBERT

Este módulo implementa um sistema de armazenamento vetorial otimizado para embeddings
de código Java, com suporte a busca por similaridade e cache inteligente.
"""

import sqlite3
import numpy as np
import json
import hashlib
import logging
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime
import pickle
from dataclasses import dataclass, asdict
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@dataclass
class CodeChunk:
    """Representa um chunk de código com metadados"""
    file_path: str
    content: str
    start_line: int
    end_line: int
    chunk_type: str  # 'class', 'method', 'block', 'comment'
    complexity_score: float
    hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EmbeddingRecord:
    """Registro de embedding no banco"""
    id: Optional[int]
    file_id: int
    chunk_id: int
    embedding: np.ndarray
    chunk_content: str
    metadata: Dict[str, Any]
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['embedding'] = self.embedding.tolist()  # Converter numpy para lista
        result['created_at'] = self.created_at.isoformat()
        return result


class SQLiteVectorStore:
    """
    Sistema de armazenamento vetorial otimizado para embeddings de código Java
    
    Features:
    - Armazenamento eficiente de embeddings em SQLite
    - Busca por similaridade usando produto escalar
    - Cache inteligente de consultas
    - Indexação por metadados
    - Suporte a atualizações incrementais
    """
    
    def __init__(self, db_path: str, embedding_dim: int = 768):
        """
        Inicializa o vector store
        
        Args:
            db_path: Caminho para o arquivo SQLite
            embedding_dim: Dimensão dos embeddings (768 para CodeBERT)
        """
        self.db_path = Path(db_path)
        self.embedding_dim = embedding_dim
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Cache para consultas frequentes
        self._query_cache = {}
        self._cache_size_limit = 1000
        
        # Inicializar banco
        self._init_database()
        
        logger.info(f"SQLiteVectorStore inicializado: {self.db_path}")
    
    def _init_database(self):
        """Inicializa o schema do banco de dados"""
        with self._get_connection() as conn:
            # Tabela de arquivos
            conn.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE NOT NULL,
                    content_hash TEXT NOT NULL,
                    last_modified TIMESTAMP NOT NULL,
                    file_type TEXT DEFAULT 'java',
                    complexity_score REAL DEFAULT 0.0,
                    total_lines INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de chunks
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    start_line INTEGER NOT NULL,
                    end_line INTEGER NOT NULL,
                    chunk_type TEXT NOT NULL,
                    complexity_score REAL DEFAULT 0.0,
                    metadata TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
                )
            """)
            
            # Tabela de embeddings
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id INTEGER NOT NULL,
                    chunk_id INTEGER NOT NULL,
                    embedding BLOB NOT NULL,
                    norm REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
                    FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE CASCADE
                )
            """)
            
            # Tabela de cache de consultas
            conn.execute("""
                CREATE TABLE IF NOT EXISTS query_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_hash TEXT UNIQUE NOT NULL,
                    query_embedding BLOB NOT NULL,
                    results TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 1,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Índices para performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_files_path ON files(path)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_files_hash ON files(content_hash)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_file_id ON chunks(file_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_hash ON chunks(content_hash)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_file_id ON embeddings(file_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_id ON embeddings(chunk_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_query_cache_hash ON query_cache(query_hash)")
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Context manager para conexões SQLite"""
        conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        # Otimizações SQLite
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
        
        try:
            yield conn
        finally:
            conn.close()
    
    def add_file(self, file_path: str, content: str, chunks: List[CodeChunk]) -> int:
        """
        Adiciona um arquivo e seus chunks ao banco
        
        Args:
            file_path: Caminho do arquivo
            content: Conteúdo completo do arquivo
            chunks: Lista de chunks do arquivo
            
        Returns:
            ID do arquivo inserido
        """
        content_hash = self._calculate_hash(content)
        
        with self._get_connection() as conn:
            # Verificar se arquivo já existe
            existing = conn.execute(
                "SELECT id, content_hash FROM files WHERE path = ?",
                (file_path,)
            ).fetchone()
            
            if existing and existing['content_hash'] == content_hash:
                logger.debug(f"Arquivo não modificado: {file_path}")
                return existing['id']
            
            # Inserir ou atualizar arquivo
            if existing:
                conn.execute("""
                    UPDATE files 
                    SET content_hash = ?, last_modified = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (content_hash, datetime.now(), existing['id']))
                file_id = existing['id']
                
                # Remover chunks antigos
                conn.execute("DELETE FROM chunks WHERE file_id = ?", (file_id,))
                conn.execute("DELETE FROM embeddings WHERE file_id = ?", (file_id,))
            else:
                cursor = conn.execute("""
                    INSERT INTO files (path, content_hash, last_modified, total_lines)
                    VALUES (?, ?, ?, ?)
                """, (file_path, content_hash, datetime.now(), len(content.split('\n'))))
                file_id = cursor.lastrowid
            
            # Inserir chunks
            for chunk in chunks:
                chunk_hash = self._calculate_hash(chunk.content)
                cursor = conn.execute("""
                    INSERT INTO chunks (
                        file_id, content, content_hash, start_line, end_line,
                        chunk_type, complexity_score, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    file_id, chunk.content, chunk_hash, chunk.start_line,
                    chunk.end_line, chunk.chunk_type, chunk.complexity_score,
                    json.dumps(chunk.to_dict())
                ))
            
            conn.commit()
            logger.info(f"Arquivo adicionado: {file_path} ({len(chunks)} chunks)")
            return file_id
    
    def add_embeddings(self, file_id: int, embeddings: List[Tuple[int, np.ndarray]]):
        """
        Adiciona embeddings para os chunks de um arquivo
        
        Args:
            file_id: ID do arquivo
            embeddings: Lista de tuplas (chunk_id, embedding)
        """
        with self._get_connection() as conn:
            for chunk_id, embedding in embeddings:
                # Normalizar embedding
                norm = np.linalg.norm(embedding)
                normalized_embedding = embedding / norm if norm > 0 else embedding
                
                # Serializar embedding
                embedding_blob = pickle.dumps(normalized_embedding.astype(np.float32))
                
                conn.execute("""
                    INSERT OR REPLACE INTO embeddings (file_id, chunk_id, embedding, norm)
                    VALUES (?, ?, ?, ?)
                """, (file_id, chunk_id, embedding_blob, float(norm)))
            
            conn.commit()
            logger.info(f"Embeddings adicionados: {len(embeddings)} para arquivo {file_id}")
    
    def similarity_search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        file_types: Optional[List[str]] = None,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Busca por similaridade usando produto escalar
        
        Args:
            query_embedding: Embedding da consulta
            top_k: Número de resultados
            file_types: Filtrar por tipos de arquivo
            min_similarity: Similaridade mínima
            
        Returns:
            Lista de resultados ordenados por similaridade
        """
        # Verificar cache
        query_hash = self._calculate_hash(query_embedding.tobytes())
        cache_key = f"{query_hash}_{top_k}_{file_types}_{min_similarity}"
        
        if cache_key in self._query_cache:
            logger.debug("Cache hit para consulta")
            return self._query_cache[cache_key]
        
        # Normalizar query embedding
        query_norm = np.linalg.norm(query_embedding)
        if query_norm > 0:
            query_embedding = query_embedding / query_norm
        
        results = []
        
        with self._get_connection() as conn:
            # Query base
            query = """
                SELECT 
                    e.id as embedding_id,
                    e.chunk_id,
                    e.file_id,
                    e.embedding,
                    e.norm,
                    c.content as chunk_content,
                    c.start_line,
                    c.end_line,
                    c.chunk_type,
                    c.complexity_score,
                    c.metadata,
                    f.path as file_path
                FROM embeddings e
                JOIN chunks c ON e.chunk_id = c.id
                JOIN files f ON e.file_id = f.id
            """
            
            params = []
            if file_types:
                query += " WHERE f.file_type IN ({})".format(','.join('?' * len(file_types)))
                params.extend(file_types)
            
            cursor = conn.execute(query, params)
            
            for row in cursor:
                # Deserializar embedding
                stored_embedding = pickle.loads(row['embedding'])
                
                # Calcular similaridade (produto escalar de vetores normalizados)
                similarity = float(np.dot(query_embedding, stored_embedding))
                
                if similarity >= min_similarity:
                    result = {
                        'embedding_id': row['embedding_id'],
                        'chunk_id': row['chunk_id'],
                        'file_id': row['file_id'],
                        'file_path': row['file_path'],
                        'chunk_content': row['chunk_content'],
                        'start_line': row['start_line'],
                        'end_line': row['end_line'],
                        'chunk_type': row['chunk_type'],
                        'complexity_score': row['complexity_score'],
                        'metadata': json.loads(row['metadata']),
                        'similarity': similarity
                    }
                    results.append(result)
        
        # Ordenar por similaridade
        results.sort(key=lambda x: x['similarity'], reverse=True)
        results = results[:top_k]
        
        # Cache resultado
        self._cache_query_result(cache_key, results)
        
        logger.info(f"Busca por similaridade: {len(results)} resultados")
        return results
    
    def get_file_chunks(self, file_id: int) -> List[Dict[str, Any]]:
        """Retorna todos os chunks de um arquivo"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    c.*,
                    f.path as file_path,
                    e.embedding IS NOT NULL as has_embedding
                FROM chunks c
                JOIN files f ON c.file_id = f.id
                LEFT JOIN embeddings e ON c.id = e.chunk_id
                WHERE c.file_id = ?
                ORDER BY c.start_line
            """, (file_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_files_without_embeddings(self) -> List[Dict[str, Any]]:
        """Retorna arquivos que ainda não têm embeddings"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT DISTINCT f.*
                FROM files f
                JOIN chunks c ON f.id = c.file_id
                LEFT JOIN embeddings e ON c.id = e.chunk_id
                WHERE e.id IS NULL
            """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas do banco"""
        with self._get_connection() as conn:
            stats = {}
            
            # Contadores básicos
            stats['total_files'] = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
            stats['total_chunks'] = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
            stats['total_embeddings'] = conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
            
            # Estatísticas por tipo
            cursor = conn.execute("""
                SELECT chunk_type, COUNT(*) as count
                FROM chunks
                GROUP BY chunk_type
            """)
            stats['chunks_by_type'] = dict(cursor.fetchall())
            
            # Complexidade média
            avg_complexity = conn.execute("""
                SELECT AVG(complexity_score) FROM chunks
            """).fetchone()[0]
            stats['avg_complexity'] = float(avg_complexity) if avg_complexity else 0.0
            
            # Cache stats
            stats['cache_entries'] = len(self._query_cache)
            
            return stats
    
    def cleanup_old_cache(self, days: int = 7):
        """Remove entradas antigas do cache"""
        with self._get_connection() as conn:
            conn.execute("""
                DELETE FROM query_cache 
                WHERE created_at < datetime('now', '-{} days')
            """.format(days))
            conn.commit()
        
        # Limpar cache em memória
        if len(self._query_cache) > self._cache_size_limit:
            # Manter apenas as mais recentes
            items = list(self._query_cache.items())
            self._query_cache = dict(items[-self._cache_size_limit//2:])
    
    def _calculate_hash(self, content) -> str:
        """Calcula hash SHA-256 do conteúdo"""
        if isinstance(content, str):
            return hashlib.sha256(content.encode('utf-8')).hexdigest()
        elif isinstance(content, bytes):
            return hashlib.sha256(content).hexdigest()
        else:
            # Convert to string first
            return hashlib.sha256(str(content).encode('utf-8')).hexdigest()
    
    def _cache_query_result(self, cache_key: str, results: List[Dict[str, Any]]):
        """Cache resultado de consulta"""
        if len(self._query_cache) >= self._cache_size_limit:
            # Remove entrada mais antiga
            oldest_key = next(iter(self._query_cache))
            del self._query_cache[oldest_key]
        
        self._query_cache[cache_key] = results
    
    def close(self):
        """Fecha conexões e limpa recursos"""
        self._query_cache.clear()
        logger.info("SQLiteVectorStore fechado")


class VectorStoreManager:
    """
    Manager de alto nível para operações do vector store
    """
    
    def __init__(self, db_path: str, embedding_dim: int = 768):
        self.vector_store = SQLiteVectorStore(db_path, embedding_dim)
        self.logger = logging.getLogger(__name__)
    
    def bulk_insert_files(self, files_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Inserção em lote de múltiplos arquivos
        
        Args:
            files_data: Lista de dicts com 'path', 'content', 'chunks'
            
        Returns:
            Mapeamento path -> file_id
        """
        file_ids = {}
        
        for file_data in files_data:
            try:
                file_id = self.vector_store.add_file(
                    file_data['path'],
                    file_data['content'],
                    file_data['chunks']
                )
                file_ids[file_data['path']] = file_id
                
            except Exception as e:
                self.logger.error(f"Erro ao inserir arquivo {file_data['path']}: {e}")
        
        return file_ids
    
    def search_similar_code(
        self,
        query: str,
        query_embedding: np.ndarray,
        top_k: int = 10,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Busca código similar com metadados enriquecidos
        """
        results = self.vector_store.similarity_search(
            query_embedding,
            top_k=top_k
        )
        
        if include_metadata:
            # Enriquecer resultados com informações adicionais
            for result in results:
                result['query'] = query
                result['relevance_score'] = result['similarity']
                result['context_lines'] = self._get_context_lines(
                    result['file_path'],
                    result['start_line'],
                    result['end_line']
                )
        
        return results
    
    def _get_context_lines(self, file_path: str, start_line: int, end_line: int, context: int = 3) -> Dict[str, List[str]]:
        """Obtém linhas de contexto ao redor do chunk"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            before_start = max(0, start_line - context - 1)
            after_end = min(len(lines), end_line + context)
            
            return {
                'before': lines[before_start:start_line-1],
                'after': lines[end_line:after_end]
            }
        except Exception as e:
            self.logger.warning(f"Erro ao obter contexto para {file_path}: {e}")
            return {'before': [], 'after': []}
    
    def get_health_status(self) -> Dict[str, Any]:
        """Retorna status de saúde do vector store"""
        try:
            stats = self.vector_store.get_statistics()
            
            # Calcular métricas de saúde
            embedding_coverage = (
                stats['total_embeddings'] / stats['total_chunks'] 
                if stats['total_chunks'] > 0 else 0
            )
            
            return {
                'status': 'healthy' if embedding_coverage > 0.8 else 'degraded',
                'embedding_coverage': embedding_coverage,
                'statistics': stats,
                'recommendations': self._get_health_recommendations(stats)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'recommendations': ['Verificar conectividade com banco de dados']
            }
    
    def _get_health_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Gera recomendações baseadas nas estatísticas"""
        recommendations = []
        
        if stats['total_embeddings'] == 0:
            recommendations.append("Nenhum embedding encontrado - executar processo de indexação")
        
        embedding_coverage = (
            stats['total_embeddings'] / stats['total_chunks'] 
            if stats['total_chunks'] > 0 else 0
        )
        
        if embedding_coverage < 0.5:
            recommendations.append("Baixa cobertura de embeddings - reprocessar arquivos")
        
        if stats['cache_entries'] > 1000:
            recommendations.append("Cache muito grande - executar limpeza")
        
        return recommendations
