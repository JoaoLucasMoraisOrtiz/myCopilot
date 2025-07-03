-- Schema SQLite para Vector Store do Java Reengineering Agent
-- Otimizado para armazenamento de embeddings CodeBERT e busca por similaridade

-- Configurações de performance
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=10000;
PRAGMA temp_store=MEMORY;

-- =====================================================
-- TABELA DE ARQUIVOS
-- =====================================================
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    content_hash TEXT NOT NULL,
    last_modified TIMESTAMP NOT NULL,
    file_type TEXT DEFAULT 'java',
    complexity_score REAL DEFAULT 0.0,
    total_lines INTEGER DEFAULT 0,
    package_name TEXT,
    class_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABELA DE CHUNKS DE CÓDIGO
-- =====================================================
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    chunk_type TEXT NOT NULL, -- 'class', 'method', 'block', 'comment', 'import'
    complexity_score REAL DEFAULT 0.0,
    method_name TEXT,
    class_name TEXT,
    package_name TEXT,
    access_modifier TEXT, -- 'public', 'private', 'protected', 'package'
    is_static BOOLEAN DEFAULT FALSE,
    is_abstract BOOLEAN DEFAULT FALSE,
    parameters_count INTEGER DEFAULT 0,
    cyclomatic_complexity INTEGER DEFAULT 1,
    lines_of_code INTEGER DEFAULT 0,
    metadata TEXT DEFAULT '{}', -- JSON com metadados adicionais
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);

-- =====================================================
-- TABELA DE EMBEDDINGS
-- =====================================================
CREATE TABLE IF NOT EXISTS embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    chunk_id INTEGER NOT NULL,
    embedding BLOB NOT NULL, -- Embedding serializado (768 dimensões para CodeBERT)
    norm REAL NOT NULL, -- Norma do vetor para otimização
    model_version TEXT DEFAULT 'codebert-base', -- Versão do modelo usado
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE CASCADE,
    UNIQUE(chunk_id) -- Um embedding por chunk
);

-- =====================================================
-- TABELA DE DEPENDÊNCIAS (GraphRAG)
-- =====================================================
CREATE TABLE IF NOT EXISTS dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file_id INTEGER NOT NULL,
    target_file_id INTEGER NOT NULL,
    source_chunk_id INTEGER,
    target_chunk_id INTEGER,
    dependency_type TEXT NOT NULL, -- 'import', 'inheritance', 'composition', 'method_call', 'field_access'
    strength REAL DEFAULT 1.0, -- Peso da dependência (0.0 a 1.0)
    line_number INTEGER, -- Linha onde ocorre a dependência
    context TEXT, -- Contexto da dependência
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_file_id) REFERENCES files(id) ON DELETE CASCADE,
    FOREIGN KEY (target_file_id) REFERENCES files(id) ON DELETE CASCADE,
    FOREIGN KEY (source_chunk_id) REFERENCES chunks(id) ON DELETE SET NULL,
    FOREIGN KEY (target_chunk_id) REFERENCES chunks(id) ON DELETE SET NULL
);

-- =====================================================
-- TABELA DE CACHE DE CONSULTAS
-- =====================================================
CREATE TABLE IF NOT EXISTS query_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_hash TEXT UNIQUE NOT NULL,
    query_text TEXT,
    query_embedding BLOB NOT NULL,
    results TEXT NOT NULL, -- JSON com resultados
    top_k INTEGER DEFAULT 10,
    filters TEXT DEFAULT '{}', -- JSON com filtros aplicados
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 1,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABELA DE BUSINESS RULES EXTRAÍDAS
-- =====================================================
CREATE TABLE IF NOT EXISTS business_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    chunk_id INTEGER,
    rule_type TEXT NOT NULL, -- 'validation', 'calculation', 'workflow', 'constraint'
    rule_description TEXT NOT NULL,
    code_pattern TEXT, -- Padrão de código que implementa a regra
    confidence_score REAL DEFAULT 0.0, -- Confiança na extração (0.0 a 1.0)
    extracted_by TEXT DEFAULT 'auto', -- 'auto', 'manual', 'ai'
    metadata TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE SET NULL
);

-- =====================================================
-- TABELA DE APIs DESCOBERTAS
-- =====================================================
CREATE TABLE IF NOT EXISTS api_endpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    chunk_id INTEGER,
    endpoint_path TEXT NOT NULL,
    http_method TEXT NOT NULL, -- 'GET', 'POST', 'PUT', 'DELETE', etc.
    method_name TEXT,
    class_name TEXT,
    parameters TEXT DEFAULT '[]', -- JSON array com parâmetros
    return_type TEXT,
    annotations TEXT DEFAULT '[]', -- JSON array com anotações
    is_deprecated BOOLEAN DEFAULT FALSE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE SET NULL
);

-- =====================================================
-- TABELA DE MÉTRICAS DE QUALIDADE
-- =====================================================
CREATE TABLE IF NOT EXISTS quality_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    chunk_id INTEGER,
    metric_type TEXT NOT NULL, -- 'complexity', 'maintainability', 'testability', 'coupling'
    metric_value REAL NOT NULL,
    threshold_min REAL,
    threshold_max REAL,
    status TEXT DEFAULT 'unknown', -- 'good', 'warning', 'critical'
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE SET NULL
);

-- =====================================================
-- ÍNDICES PARA PERFORMANCE
-- =====================================================

-- Índices para tabela files
CREATE INDEX IF NOT EXISTS idx_files_path ON files(path);
CREATE INDEX IF NOT EXISTS idx_files_hash ON files(content_hash);
CREATE INDEX IF NOT EXISTS idx_files_type ON files(file_type);
CREATE INDEX IF NOT EXISTS idx_files_package ON files(package_name);
CREATE INDEX IF NOT EXISTS idx_files_class ON files(class_name);

-- Índices para tabela chunks
CREATE INDEX IF NOT EXISTS idx_chunks_file_id ON chunks(file_id);
CREATE INDEX IF NOT EXISTS idx_chunks_hash ON chunks(content_hash);
CREATE INDEX IF NOT EXISTS idx_chunks_type ON chunks(chunk_type);
CREATE INDEX IF NOT EXISTS idx_chunks_method ON chunks(method_name);
CREATE INDEX IF NOT EXISTS idx_chunks_class ON chunks(class_name);
CREATE INDEX IF NOT EXISTS idx_chunks_complexity ON chunks(complexity_score);
CREATE INDEX IF NOT EXISTS idx_chunks_lines ON chunks(start_line, end_line);

-- Índices para tabela embeddings
CREATE INDEX IF NOT EXISTS idx_embeddings_file_id ON embeddings(file_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_id ON embeddings(chunk_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_model ON embeddings(model_version);
CREATE INDEX IF NOT EXISTS idx_embeddings_norm ON embeddings(norm);

-- Índices para tabela dependencies
CREATE INDEX IF NOT EXISTS idx_dependencies_source ON dependencies(source_file_id);
CREATE INDEX IF NOT EXISTS idx_dependencies_target ON dependencies(target_file_id);
CREATE INDEX IF NOT EXISTS idx_dependencies_type ON dependencies(dependency_type);
CREATE INDEX IF NOT EXISTS idx_dependencies_strength ON dependencies(strength);
CREATE INDEX IF NOT EXISTS idx_dependencies_chunks ON dependencies(source_chunk_id, target_chunk_id);

-- Índices para tabela query_cache
CREATE INDEX IF NOT EXISTS idx_query_cache_hash ON query_cache(query_hash);
CREATE INDEX IF NOT EXISTS idx_query_cache_accessed ON query_cache(last_accessed);
CREATE INDEX IF NOT EXISTS idx_query_cache_count ON query_cache(access_count);

-- Índices para tabela business_rules
CREATE INDEX IF NOT EXISTS idx_business_rules_file ON business_rules(file_id);
CREATE INDEX IF NOT EXISTS idx_business_rules_type ON business_rules(rule_type);
CREATE INDEX IF NOT EXISTS idx_business_rules_confidence ON business_rules(confidence_score);

-- Índices para tabela api_endpoints
CREATE INDEX IF NOT EXISTS idx_api_endpoints_file ON api_endpoints(file_id);
CREATE INDEX IF NOT EXISTS idx_api_endpoints_path ON api_endpoints(endpoint_path);
CREATE INDEX IF NOT EXISTS idx_api_endpoints_method ON api_endpoints(http_method);
CREATE INDEX IF NOT EXISTS idx_api_endpoints_class ON api_endpoints(class_name);

-- Índices para tabela quality_metrics
CREATE INDEX IF NOT EXISTS idx_quality_metrics_file ON quality_metrics(file_id);
CREATE INDEX IF NOT EXISTS idx_quality_metrics_type ON quality_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_quality_metrics_value ON quality_metrics(metric_value);
CREATE INDEX IF NOT EXISTS idx_quality_metrics_status ON quality_metrics(status);

-- =====================================================
-- VIEWS ÚTEIS
-- =====================================================

-- View para chunks com embeddings
CREATE VIEW IF NOT EXISTS chunks_with_embeddings AS
SELECT 
    c.*,
    f.path as file_path,
    f.package_name as file_package,
    e.id as embedding_id,
    e.norm as embedding_norm,
    e.model_version,
    CASE WHEN e.id IS NOT NULL THEN 1 ELSE 0 END as has_embedding
FROM chunks c
JOIN files f ON c.file_id = f.id
LEFT JOIN embeddings e ON c.id = e.chunk_id;

-- View para estatísticas por arquivo
CREATE VIEW IF NOT EXISTS file_statistics AS
SELECT 
    f.id,
    f.path,
    f.package_name,
    f.class_name,
    COUNT(c.id) as total_chunks,
    COUNT(e.id) as chunks_with_embeddings,
    AVG(c.complexity_score) as avg_complexity,
    SUM(c.lines_of_code) as total_loc,
    COUNT(CASE WHEN c.chunk_type = 'method' THEN 1 END) as method_count,
    COUNT(CASE WHEN c.chunk_type = 'class' THEN 1 END) as class_count
FROM files f
LEFT JOIN chunks c ON f.id = c.file_id
LEFT JOIN embeddings e ON c.id = e.chunk_id
GROUP BY f.id, f.path, f.package_name, f.class_name;

-- View para dependências com detalhes
CREATE VIEW IF NOT EXISTS dependency_details AS
SELECT 
    d.*,
    sf.path as source_path,
    sf.class_name as source_class,
    tf.path as target_path,
    tf.class_name as target_class,
    sc.method_name as source_method,
    tc.method_name as target_method
FROM dependencies d
JOIN files sf ON d.source_file_id = sf.id
JOIN files tf ON d.target_file_id = tf.id
LEFT JOIN chunks sc ON d.source_chunk_id = sc.id
LEFT JOIN chunks tc ON d.target_chunk_id = tc.id;

-- View para métricas de qualidade agregadas
CREATE VIEW IF NOT EXISTS quality_summary AS
SELECT 
    f.id as file_id,
    f.path,
    f.class_name,
    AVG(CASE WHEN qm.metric_type = 'complexity' THEN qm.metric_value END) as avg_complexity,
    AVG(CASE WHEN qm.metric_type = 'maintainability' THEN qm.metric_value END) as maintainability_index,
    COUNT(CASE WHEN qm.status = 'critical' THEN 1 END) as critical_issues,
    COUNT(CASE WHEN qm.status = 'warning' THEN 1 END) as warning_issues
FROM files f
LEFT JOIN quality_metrics qm ON f.id = qm.file_id
GROUP BY f.id, f.path, f.class_name;

-- =====================================================
-- TRIGGERS PARA MANUTENÇÃO AUTOMÁTICA
-- =====================================================

-- Trigger para atualizar updated_at em files
CREATE TRIGGER IF NOT EXISTS update_files_timestamp
    AFTER UPDATE ON files
    FOR EACH ROW
BEGIN
    UPDATE files SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger para limpar cache quando embeddings são atualizados
CREATE TRIGGER IF NOT EXISTS clear_cache_on_embedding_update
    AFTER INSERT ON embeddings
    FOR EACH ROW
BEGIN
    DELETE FROM query_cache WHERE created_at < datetime('now', '-1 hour');
END;

-- Trigger para manter consistência de dependências
CREATE TRIGGER IF NOT EXISTS cleanup_orphaned_dependencies
    AFTER DELETE ON chunks
    FOR EACH ROW
BEGIN
    DELETE FROM dependencies 
    WHERE source_chunk_id = OLD.id OR target_chunk_id = OLD.id;
END;
