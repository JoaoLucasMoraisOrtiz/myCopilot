#!/usr/bin/env python3
"""
Exemplo prático de uso do SQLite Vector Store

Este exemplo demonstra como usar o vector store para:
1. Indexar código Java
2. Gerar embeddings com CodeBERT
3. Realizar buscas por similaridade
4. Analisar estatísticas e métricas
"""

import sys
import os
from pathlib import Path
import numpy as np
import logging

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from rag.vector_store import SQLiteVectorStore, VectorStoreManager, CodeChunk
from rag.codebert_encoder import CodeBERTEncoder

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_java_files():
    """Cria arquivos Java de exemplo para demonstração"""
    sample_files = {
        "UserService.java": """
package com.example.service;

import com.example.model.User;
import com.example.repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.Optional;

@Service
public class UserService {
    
    @Autowired
    private UserRepository userRepository;
    
    public List<User> getAllUsers() {
        return userRepository.findAll();
    }
    
    public Optional<User> getUserById(Long id) {
        if (id == null || id <= 0) {
            throw new IllegalArgumentException("ID deve ser positivo");
        }
        return userRepository.findById(id);
    }
    
    public User createUser(User user) {
        validateUser(user);
        return userRepository.save(user);
    }
    
    public User updateUser(Long id, User user) {
        Optional<User> existingUser = getUserById(id);
        if (existingUser.isPresent()) {
            user.setId(id);
            validateUser(user);
            return userRepository.save(user);
        }
        throw new RuntimeException("Usuário não encontrado");
    }
    
    public void deleteUser(Long id) {
        if (getUserById(id).isPresent()) {
            userRepository.deleteById(id);
        }
    }
    
    private void validateUser(User user) {
        if (user == null) {
            throw new IllegalArgumentException("Usuário não pode ser nulo");
        }
        if (user.getName() == null || user.getName().trim().isEmpty()) {
            throw new IllegalArgumentException("Nome é obrigatório");
        }
        if (user.getEmail() == null || !user.getEmail().contains("@")) {
            throw new IllegalArgumentException("Email inválido");
        }
    }
}
""",
        
        "OrderService.java": """
package com.example.service;

import com.example.model.Order;
import com.example.model.User;
import com.example.repository.OrderRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

@Service
public class OrderService {
    
    @Autowired
    private OrderRepository orderRepository;
    
    @Autowired
    private UserService userService;
    
    public List<Order> getOrdersByUser(Long userId) {
        User user = userService.getUserById(userId)
            .orElseThrow(() -> new RuntimeException("Usuário não encontrado"));
        return orderRepository.findByUserId(userId);
    }
    
    public Order createOrder(Order order) {
        validateOrder(order);
        order.setCreatedAt(LocalDateTime.now());
        order.setStatus("PENDING");
        return orderRepository.save(order);
    }
    
    public Order updateOrderStatus(Long orderId, String status) {
        Order order = orderRepository.findById(orderId)
            .orElseThrow(() -> new RuntimeException("Pedido não encontrado"));
        
        validateStatusTransition(order.getStatus(), status);
        order.setStatus(status);
        order.setUpdatedAt(LocalDateTime.now());
        
        return orderRepository.save(order);
    }
    
    public BigDecimal calculateOrderTotal(Order order) {
        if (order.getItems() == null || order.getItems().isEmpty()) {
            return BigDecimal.ZERO;
        }
        
        return order.getItems().stream()
            .map(item -> item.getPrice().multiply(BigDecimal.valueOf(item.getQuantity())))
            .reduce(BigDecimal.ZERO, BigDecimal::add);
    }
    
    private void validateOrder(Order order) {
        if (order == null) {
            throw new IllegalArgumentException("Pedido não pode ser nulo");
        }
        if (order.getUserId() == null) {
            throw new IllegalArgumentException("ID do usuário é obrigatório");
        }
        if (order.getItems() == null || order.getItems().isEmpty()) {
            throw new IllegalArgumentException("Pedido deve ter pelo menos um item");
        }
    }
    
    private void validateStatusTransition(String currentStatus, String newStatus) {
        // Regras de negócio para transição de status
        if ("CANCELLED".equals(currentStatus)) {
            throw new IllegalStateException("Não é possível alterar pedido cancelado");
        }
        if ("DELIVERED".equals(currentStatus) && !"RETURNED".equals(newStatus)) {
            throw new IllegalStateException("Pedido entregue só pode ser devolvido");
        }
    }
}
""",
        
        "ValidationUtils.java": """
package com.example.util;

import java.util.regex.Pattern;

public class ValidationUtils {
    
    private static final Pattern EMAIL_PATTERN = 
        Pattern.compile("^[A-Za-z0-9+_.-]+@([A-Za-z0-9.-]+\\.[A-Za-z]{2,})$");
    
    private static final Pattern PHONE_PATTERN = 
        Pattern.compile("^\\+?[1-9]\\d{1,14}$");
    
    public static boolean isValidEmail(String email) {
        if (email == null || email.trim().isEmpty()) {
            return false;
        }
        return EMAIL_PATTERN.matcher(email.trim()).matches();
    }
    
    public static boolean isValidPhone(String phone) {
        if (phone == null || phone.trim().isEmpty()) {
            return false;
        }
        String cleanPhone = phone.replaceAll("[\\s()-]", "");
        return PHONE_PATTERN.matcher(cleanPhone).matches();
    }
    
    public static boolean isValidCPF(String cpf) {
        if (cpf == null || cpf.trim().isEmpty()) {
            return false;
        }
        
        cpf = cpf.replaceAll("[^0-9]", "");
        
        if (cpf.length() != 11) {
            return false;
        }
        
        // Verificar se todos os dígitos são iguais
        if (cpf.matches("(\\d)\\1{10}")) {
            return false;
        }
        
        // Calcular dígitos verificadores
        int sum = 0;
        for (int i = 0; i < 9; i++) {
            sum += Character.getNumericValue(cpf.charAt(i)) * (10 - i);
        }
        int firstDigit = 11 - (sum % 11);
        if (firstDigit >= 10) firstDigit = 0;
        
        sum = 0;
        for (int i = 0; i < 10; i++) {
            sum += Character.getNumericValue(cpf.charAt(i)) * (11 - i);
        }
        int secondDigit = 11 - (sum % 11);
        if (secondDigit >= 10) secondDigit = 0;
        
        return Character.getNumericValue(cpf.charAt(9)) == firstDigit &&
               Character.getNumericValue(cpf.charAt(10)) == secondDigit;
    }
    
    public static String sanitizeInput(String input) {
        if (input == null) {
            return null;
        }
        return input.trim().replaceAll("[<>\"'&]", "");
    }
}
"""
    }
    
    return sample_files


def parse_java_code_to_chunks(file_path: str, content: str) -> List[CodeChunk]:
    """
    Parser simples para extrair chunks de código Java
    Em uma implementação real, usaria tree-sitter ou similar
    """
    chunks = []
    lines = content.split('\n')
    
    current_chunk = []
    chunk_start = 0
    chunk_type = "unknown"
    in_method = False
    in_class = False
    brace_count = 0
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Detectar início de classe
        if 'class ' in stripped and not stripped.startswith('//'):
            if current_chunk:
                # Finalizar chunk anterior
                chunks.append(create_chunk_from_lines(
                    file_path, current_chunk, chunk_start, i-1, chunk_type
                ))
            current_chunk = [line]
            chunk_start = i
            chunk_type = "class"
            in_class = True
            brace_count = stripped.count('{') - stripped.count('}')
            continue
        
        # Detectar início de método
        if (('public ' in stripped or 'private ' in stripped or 'protected ' in stripped) 
            and '(' in stripped and ')' in stripped and not stripped.startswith('//')):
            if current_chunk and not in_class:
                # Finalizar chunk anterior
                chunks.append(create_chunk_from_lines(
                    file_path, current_chunk, chunk_start, i-1, chunk_type
                ))
            if not in_class:
                current_chunk = [line]
                chunk_start = i
                chunk_type = "method"
            else:
                current_chunk.append(line)
            in_method = True
            brace_count += stripped.count('{') - stripped.count('}')
            continue
        
        # Adicionar linha ao chunk atual
        if current_chunk:
            current_chunk.append(line)
            brace_count += stripped.count('{') - stripped.count('}')
            
            # Verificar se chunk terminou
            if brace_count == 0 and (in_method or in_class):
                chunks.append(create_chunk_from_lines(
                    file_path, current_chunk, chunk_start, i, chunk_type
                ))
                current_chunk = []
                in_method = False
                if chunk_type == "class":
                    in_class = False
        elif stripped and not stripped.startswith('//') and not stripped.startswith('import'):
            # Início de novo chunk
            current_chunk = [line]
            chunk_start = i
            chunk_type = "block"
    
    # Finalizar último chunk
    if current_chunk:
        chunks.append(create_chunk_from_lines(
            file_path, current_chunk, chunk_start, len(lines), chunk_type
        ))
    
    return chunks


def create_chunk_from_lines(file_path: str, lines: List[str], start: int, end: int, chunk_type: str) -> CodeChunk:
    """Cria um CodeChunk a partir de linhas de código"""
    content = '\n'.join(lines)
    complexity = calculate_simple_complexity(content)
    hash_value = str(hash(content))
    
    return CodeChunk(
        file_path=file_path,
        content=content,
        start_line=start,
        end_line=end,
        chunk_type=chunk_type,
        complexity_score=complexity,
        hash=hash_value
    )


def calculate_simple_complexity(content: str) -> float:
    """Calcula complexidade simples baseada em palavras-chave"""
    keywords = ['if', 'else', 'for', 'while', 'switch', 'case', 'try', 'catch']
    complexity = 1.0
    
    for keyword in keywords:
        complexity += content.lower().count(keyword) * 0.5
    
    return min(complexity, 10.0)  # Cap em 10


def demonstrate_vector_store():
    """Demonstração completa do vector store"""
    
    print("🚀 Demonstração do SQLite Vector Store")
    print("=" * 50)
    
    # 1. Inicializar vector store
    print("\n1. Inicializando Vector Store...")
    db_path = "examples/demo_vector_store.db"
    os.makedirs("examples", exist_ok=True)
    
    vector_store = SQLiteVectorStore(db_path, embedding_dim=768)
    manager = VectorStoreManager(db_path, embedding_dim=768)
    
    print(f"✅ Vector store criado: {db_path}")
    
    # 2. Criar arquivos de exemplo
    print("\n2. Criando arquivos Java de exemplo...")
    sample_files = create_sample_java_files()
    
    files_data = []
    for filename, content in sample_files.items():
        file_path = f"/example/src/main/java/{filename}"
        chunks = parse_java_code_to_chunks(file_path, content)
        
        files_data.append({
            'path': file_path,
            'content': content,
            'chunks': chunks
        })
        
        print(f"✅ Processado {filename}: {len(chunks)} chunks")
    
    # 3. Inserir arquivos no vector store
    print("\n3. Inserindo arquivos no vector store...")
    file_ids = manager.bulk_insert_files(files_data)
    
    for path, file_id in file_ids.items():
        print(f"✅ Arquivo inserido: {Path(path).name} (ID: {file_id})")
    
    # 4. Gerar embeddings (simulados)
    print("\n4. Gerando embeddings (simulados)...")
    
    # Em uma implementação real, usaria CodeBERTEncoder
    # Aqui vamos simular embeddings aleatórios
    for file_path, file_id in file_ids.items():
        chunks = vector_store.get_file_chunks(file_id)
        embeddings_data = []
        
        for chunk in chunks:
            # Simular embedding baseado no conteúdo
            np.random.seed(hash(chunk['content']) % 2**32)
            embedding = np.random.rand(768).astype(np.float32)
            embeddings_data.append((chunk['id'], embedding))
        
        vector_store.add_embeddings(file_id, embeddings_data)
        print(f"✅ Embeddings gerados para {Path(file_path).name}: {len(embeddings_data)}")
    
    # 5. Mostrar estatísticas
    print("\n5. Estatísticas do Vector Store:")
    stats = vector_store.get_statistics()
    
    print(f"📊 Total de arquivos: {stats['total_files']}")
    print(f"📊 Total de chunks: {stats['total_chunks']}")
    print(f"📊 Total de embeddings: {stats['total_embeddings']}")
    print(f"📊 Complexidade média: {stats['avg_complexity']:.2f}")
    print(f"📊 Chunks por tipo: {stats['chunks_by_type']}")
    
    # 6. Demonstrar busca por similaridade
    print("\n6. Demonstrando busca por similaridade:")
    
    queries = [
        "validação de usuário",
        "calcular total do pedido",
        "verificar email válido",
        "salvar no repositório"
    ]
    
    for query in queries:
        print(f"\n🔍 Busca: '{query}'")
        
        # Simular embedding da query
        np.random.seed(hash(query) % 2**32)
        query_embedding = np.random.rand(768).astype(np.float32)
        
        results = manager.search_similar_code(
            query,
            query_embedding,
            top_k=3,
            include_metadata=True
        )
        
        for i, result in enumerate(results, 1):
            print(f"  {i}. {Path(result['file_path']).name} "
                  f"(linhas {result['start_line']}-{result['end_line']}) "
                  f"- Similaridade: {result['similarity']:.3f}")
            print(f"     Tipo: {result['chunk_type']}, "
                  f"Complexidade: {result['complexity_score']:.1f}")
            
            # Mostrar trecho do código
            content_preview = result['chunk_content'][:100].replace('\n', ' ')
            print(f"     Preview: {content_preview}...")
    
    # 7. Status de saúde
    print("\n7. Status de saúde do sistema:")
    health = manager.get_health_status()
    
    print(f"🏥 Status: {health['status']}")
    print(f"🏥 Cobertura de embeddings: {health['embedding_coverage']:.1%}")
    
    if health['recommendations']:
        print("🏥 Recomendações:")
        for rec in health['recommendations']:
            print(f"   - {rec}")
    
    # 8. Demonstrar cache
    print("\n8. Demonstrando cache de consultas:")
    
    # Primeira busca
    query_embedding = np.random.rand(768).astype(np.float32)
    
    import time
    start_time = time.time()
    results1 = vector_store.similarity_search(query_embedding, top_k=5)
    first_search_time = time.time() - start_time
    
    # Segunda busca (mesma query, deve usar cache)
    start_time = time.time()
    results2 = vector_store.similarity_search(query_embedding, top_k=5)
    second_search_time = time.time() - start_time
    
    print(f"⚡ Primeira busca: {first_search_time:.4f}s")
    print(f"⚡ Segunda busca (cache): {second_search_time:.4f}s")
    print(f"⚡ Speedup: {first_search_time/second_search_time:.1f}x")
    
    # 9. Limpeza
    print("\n9. Limpeza e finalização:")
    vector_store.cleanup_old_cache(days=0)
    vector_store.close()
    
    print("✅ Demonstração concluída!")
    print(f"📁 Banco de dados salvo em: {db_path}")
    print("🔍 Você pode explorar o banco usando um cliente SQLite")


def demonstrate_advanced_queries():
    """Demonstra consultas avançadas no vector store"""
    
    print("\n" + "=" * 50)
    print("🔬 CONSULTAS AVANÇADAS")
    print("=" * 50)
    
    db_path = "examples/demo_vector_store.db"
    
    if not os.path.exists(db_path):
        print("❌ Execute primeiro a demonstração básica!")
        return
    
    vector_store = SQLiteVectorStore(db_path, embedding_dim=768)
    
    # Consultas SQL diretas para análise
    with vector_store._get_connection() as conn:
        
        print("\n1. Arquivos com maior complexidade:")
        cursor = conn.execute("""
            SELECT f.path, AVG(c.complexity_score) as avg_complexity
            FROM files f
            JOIN chunks c ON f.id = c.file_id
            GROUP BY f.id, f.path
            ORDER BY avg_complexity DESC
        """)
        
        for row in cursor.fetchall():
            print(f"   📄 {Path(row['path']).name}: {row['avg_complexity']:.2f}")
        
        print("\n2. Distribuição de tipos de chunks:")
        cursor = conn.execute("""
            SELECT chunk_type, COUNT(*) as count, AVG(complexity_score) as avg_complexity
            FROM chunks
            GROUP BY chunk_type
            ORDER BY count DESC
        """)
        
        for row in cursor.fetchall():
            print(f"   🧩 {row['chunk_type']}: {row['count']} chunks "
                  f"(complexidade média: {row['avg_complexity']:.2f})")
        
        print("\n3. Chunks mais complexos:")
        cursor = conn.execute("""
            SELECT c.content, c.complexity_score, f.path, c.start_line, c.end_line
            FROM chunks c
            JOIN files f ON c.file_id = f.id
            ORDER BY c.complexity_score DESC
            LIMIT 5
        """)
        
        for i, row in enumerate(cursor.fetchall(), 1):
            content_preview = row['content'][:80].replace('\n', ' ')
            print(f"   {i}. {Path(row['path']).name} "
                  f"(linhas {row['start_line']}-{row['end_line']}) "
                  f"- Complexidade: {row['complexity_score']:.1f}")
            print(f"      {content_preview}...")
    
    vector_store.close()


if __name__ == "__main__":
    try:
        demonstrate_vector_store()
        demonstrate_advanced_queries()
        
    except Exception as e:
        logger.error(f"Erro na demonstração: {e}")
        import traceback
        traceback.print_exc()
