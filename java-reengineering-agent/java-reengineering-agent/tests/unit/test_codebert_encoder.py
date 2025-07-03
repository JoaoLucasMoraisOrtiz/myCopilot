"""
Unit tests for CodeBERT Encoder

Tests the CodeBERT encoder functionality with proper pytest structure.
"""

import pytest
import sys
import os
import time
from pathlib import Path
import numpy as np

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from rag.codebert_encoder import CodeBERTEncoder, CodeEmbedding


# Test fixtures
@pytest.fixture
def java_samples():
    """Java code samples for testing."""
    return {
        "simple_method": """
public int calculateSum(int a, int b) {
    return a + b;
}
""",
        
        "complex_method": """
public List<User> findActiveUsers(String department, Date since) {
    return userRepository.findAll().stream()
        .filter(user -> user.getDepartment().equals(department))
        .filter(user -> user.getLastLogin().after(since))
        .filter(user -> user.isActive())
        .collect(Collectors.toList());
}
""",
        
        "simple_class": """
public class Calculator {
    private double result;
    
    public Calculator() {
        this.result = 0.0;
    }
    
    public double add(double value) {
        result += value;
        return result;
    }
    
    public double getResult() {
        return result;
    }
}
""",
        
        "god_class": """
public class UserManager {
    private Connection dbConnection;
    private EmailService emailService;
    
    public void createUser(String name, String email, String department) {
        if (!validator.isValidEmail(email)) {
            throw new IllegalArgumentException("Invalid email");
        }
        
        try {
            PreparedStatement stmt = dbConnection.prepareStatement(
                "INSERT INTO users (name, email, department, created_at) VALUES (?, ?, ?, ?)"
            );
            stmt.setString(1, name);
            stmt.setString(2, email);
            stmt.setString(3, department);
            stmt.executeUpdate();
        } catch (SQLException e) {
            throw new RuntimeException("Failed to create user", e);
        }
        
        emailService.sendWelcomeEmail(email, name);
    }
}
"""
    }


@pytest.fixture
def encoder():
    """CodeBERT encoder instance for testing."""
    return CodeBERTEncoder(
        model_name="microsoft/codebert-base",
        device="cpu",  # Use CPU for testing
        max_length=256,  # Smaller for faster testing
        batch_size=4
    )


class TestCodeBERTEncoder:
    """Test suite for CodeBERT encoder."""
    
    def test_encoder_initialization(self):
        """Test encoder initialization."""
        encoder = CodeBERTEncoder(
            model_name="microsoft/codebert-base",
            device="cpu",
            max_length=256,
            batch_size=4
        )
        
        assert encoder.model_name == "microsoft/codebert-base"
        assert encoder.device == "cpu"
        assert encoder.max_length == 256
        assert encoder.batch_size == 4
        assert encoder.cache_embeddings is True
        assert hasattr(encoder, 'embedding_dim')
        assert encoder.embedding_dim > 0
    
    def test_single_encoding(self, encoder, java_samples):
        """Test single code encoding."""
        code = java_samples["simple_method"]
        embedding = encoder.encode_single(code, "method")
        
        assert isinstance(embedding, np.ndarray)
        assert len(embedding.shape) == 1
        assert embedding.shape[0] == encoder.embedding_dim
        assert not np.allclose(embedding, 0)  # Should not be all zeros
    
    def test_batch_encoding(self, encoder, java_samples):
        """Test batch encoding."""
        codes = list(java_samples.values())
        code_types = ["method", "method", "class", "class"]
        
        embeddings = encoder.encode_batch(codes, code_types)
        
        assert len(embeddings) == len(codes)
        assert all(isinstance(emb, np.ndarray) for emb in embeddings)
        assert all(emb.shape[0] == encoder.embedding_dim for emb in embeddings)
    
    def test_similarity_calculation(self, encoder, java_samples):
        """Test similarity calculation."""
        code1 = java_samples["simple_method"]
        code2 = java_samples["complex_method"]
        
        emb1 = encoder.encode_single(code1, "method")
        emb2 = encoder.encode_single(code2, "method")
        
        # Test similarity calculation
        similarity = encoder.get_similarity(emb1, emb2)
        assert 0 <= similarity <= 1
        
        # Test self-similarity (should be 1.0)
        self_similarity = encoder.get_similarity(emb1, emb1)
        assert abs(self_similarity - 1.0) < 1e-6
    
    def test_find_similar_codes(self, encoder, java_samples):
        """Test finding similar codes."""
        codes = list(java_samples.values())
        embeddings = encoder.encode_batch(codes)
        
        # Find similar codes to the first one
        similar = encoder.find_similar_codes(embeddings[0], embeddings[1:], top_k=2)
        
        assert len(similar) <= 2
        assert all(isinstance(item, tuple) for item in similar)
        assert all(len(item) == 2 for item in similar)
        assert all(isinstance(item[0], int) for item in similar)
        assert all(isinstance(item[1], float) for item in similar)
        
        # Check that similarities are in descending order
        similarities = [item[1] for item in similar]
        assert similarities == sorted(similarities, reverse=True)
    
    def test_code_embedding_object(self, encoder, java_samples):
        """Test CodeEmbedding object creation."""
        code = java_samples["simple_method"]
        
        embedding_obj = encoder.create_code_embedding(
            code=code,
            code_id="test_method_001",
            code_type="method",
            file_path="Calculator.java",
            metadata={"complexity": "low", "lines": 3}
        )
        
        assert isinstance(embedding_obj, CodeEmbedding)
        assert embedding_obj.code_id == "test_method_001"
        assert embedding_obj.code_text == code
        assert embedding_obj.code_type == "method"
        assert embedding_obj.file_path == "Calculator.java"
        assert embedding_obj.metadata["complexity"] == "low"
        assert isinstance(embedding_obj.embedding, np.ndarray)
    
    def test_code_embedding_serialization(self, encoder, java_samples):
        """Test CodeEmbedding serialization and deserialization."""
        code = java_samples["simple_method"]
        
        embedding_obj = encoder.create_code_embedding(
            code=code,
            code_id="test_method_001",
            code_type="method"
        )
        
        # Test serialization
        data = embedding_obj.to_dict()
        assert isinstance(data, dict)
        assert data["code_id"] == "test_method_001"
        assert data["code_text"] == code
        assert data["code_type"] == "method"
        assert isinstance(data["embedding"], list)
        
        # Test deserialization
        restored = CodeEmbedding.from_dict(data)
        assert restored.code_id == embedding_obj.code_id
        assert restored.code_text == embedding_obj.code_text
        assert restored.code_type == embedding_obj.code_type
        assert np.allclose(restored.embedding, embedding_obj.embedding)
    
    def test_caching(self, encoder, java_samples):
        """Test embedding caching."""
        code = java_samples["simple_method"]
        
        # Clear cache first
        encoder.clear_cache()
        
        # First encoding (should be cached)
        start_time = time.time()
        embedding1 = encoder.encode_single(code, "method", use_cache=True)
        time1 = time.time() - start_time
        
        # Second encoding (should use cache)
        start_time = time.time()
        embedding2 = encoder.encode_single(code, "method", use_cache=True)
        time2 = time.time() - start_time
        
        # Verify embeddings are identical
        assert np.allclose(embedding1, embedding2)
        
        # Second call should be faster (cached)
        assert time2 <= time1
        
        # Check cache stats
        stats = encoder.get_cache_stats()
        assert stats["cache_size"] > 0
        assert stats["cache_enabled"] is True
    
    def test_cache_management(self, encoder):
        """Test cache management functions."""
        # Test clear cache
        encoder.clear_cache()
        stats = encoder.get_cache_stats()
        assert stats["cache_size"] == 0
        
        # Test get cache stats
        assert isinstance(stats, dict)
        assert "cache_size" in stats
        assert "cache_enabled" in stats
        assert "embedding_dimension" in stats
        assert "model_name" in stats
        assert "device" in stats
    
    def test_preprocess_code(self, encoder):
        """Test code preprocessing."""
        # Test with messy code
        messy_code = """
        
        public    int   add(int a,    int b) {
            
            return a + b;
            
        }
        
        """
        
        processed = encoder._preprocess_code(messy_code)
        
        # Should normalize whitespace
        assert "  " not in processed  # No double spaces
        assert processed.strip() == processed  # No leading/trailing whitespace
        
        # Test with very long code
        long_code = "public void method() { " + "a = 1; " * 1000 + "}"
        processed_long = encoder._preprocess_code(long_code)
        
        # Should be truncated
        assert len(processed_long) < len(long_code)
        assert processed_long.endswith("...")
    
    def test_semantic_understanding(self):
        """Test semantic understanding capabilities."""
        encoder = CodeBERTEncoder(device="cpu", max_length=256)
        
        # Similar methods (should have high similarity)
        method1 = "public int add(int a, int b) { return a + b; }"
        method2 = "public int sum(int x, int y) { return x + y; }"
        
        # Different methods (should have lower similarity)
        method3 = "public String getName() { return this.name; }"
        
        # Encode all methods
        emb1 = encoder.encode_single(method1, "method")
        emb2 = encoder.encode_single(method2, "method")
        emb3 = encoder.encode_single(method3, "method")
        
        # Calculate similarities
        sim_similar = encoder.get_similarity(emb1, emb2)
        sim_different = encoder.get_similarity(emb1, emb3)
        
        # Similar methods should have higher similarity than different methods
        assert sim_similar > sim_different
        
        # Both similarities should be valid values
        assert 0 <= sim_similar <= 1
        assert 0 <= sim_different <= 1


class TestCodeEmbedding:
    """Test suite for CodeEmbedding class."""
    
    def test_code_embedding_creation(self):
        """Test CodeEmbedding object creation."""
        embedding = np.random.rand(768)
        
        code_emb = CodeEmbedding(
            code_id="test_001",
            code_text="public void test() {}",
            embedding=embedding,
            code_type="method",
            file_path="Test.java",
            metadata={"lines": 1}
        )
        
        assert code_emb.code_id == "test_001"
        assert code_emb.code_text == "public void test() {}"
        assert np.array_equal(code_emb.embedding, embedding)
        assert code_emb.code_type == "method"
        assert code_emb.file_path == "Test.java"
        assert code_emb.metadata["lines"] == 1
        assert code_emb.created_at is not None
    
    def test_code_embedding_defaults(self):
        """Test CodeEmbedding with default values."""
        embedding = np.random.rand(768)
        
        code_emb = CodeEmbedding(
            code_id="test_002",
            code_text="public void test2() {}",
            embedding=embedding,
            code_type="method"
        )
        
        assert code_emb.file_path is None
        assert code_emb.created_at is not None
        assert isinstance(code_emb.metadata, dict)
        assert len(code_emb.metadata) == 0


# Integration test
def test_end_to_end_workflow(java_samples):
    """Test complete workflow from code to similarity search."""
    # Initialize encoder
    encoder = CodeBERTEncoder(device="cpu", max_length=256, batch_size=2)
    
    # Create code embeddings
    embeddings = []
    for code_id, code in java_samples.items():
        emb = encoder.create_code_embedding(
            code=code,
            code_id=code_id,
            code_type="method" if "method" in code_id else "class",
            file_path=f"{code_id}.java"
        )
        embeddings.append(emb)
    
    # Test similarity search
    query_embedding = embeddings[0].embedding
    candidate_embeddings = [emb.embedding for emb in embeddings[1:]]
    
    similar = encoder.find_similar_codes(query_embedding, candidate_embeddings, top_k=2)
    
    assert len(similar) <= 2
    assert all(0 <= score <= 1 for _, score in similar)
    
    # Test serialization roundtrip
    for emb in embeddings:
        data = emb.to_dict()
        restored = CodeEmbedding.from_dict(data)
        assert restored.code_id == emb.code_id
        assert np.allclose(restored.embedding, emb.embedding)
