"""
CodeBERT Encoder for Java Code Embeddings

This module implements a CodeBERT-based encoder that transforms Java code
into high-dimensional vector representations for semantic search and similarity.

Features:
- Pre-trained CodeBERT model for code understanding
- Efficient batching and caching
- Preprocessing and tokenization for Java code
- Support for different code granularities (method, class, file)
"""

import torch
import numpy as np
from typing import List, Dict, Optional, Tuple, Union
from transformers import (
    RobertaTokenizer, 
    RobertaModel, 
    AutoTokenizer, 
    AutoModel
)
from pathlib import Path
import logging
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json

# Import logger with fallback
try:
    from ..utils.logger import AgentLogger
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    try:
        from utils.logger import AgentLogger
    except ImportError:
        # Final fallback - use basic logging
        class AgentLogger:
            def info(self, msg): print(f"INFO: {msg}")
            def debug(self, msg): print(f"DEBUG: {msg}")
            def error(self, msg): print(f"ERROR: {msg}")
            def warning(self, msg): print(f"WARNING: {msg}")

# Configure logger
logger = AgentLogger()


@dataclass
class CodeEmbedding:
    """Represents a code embedding with metadata."""
    
    code_id: str
    code_text: str
    embedding: np.ndarray
    code_type: str  # 'method', 'class', 'file', 'snippet'
    file_path: Optional[str] = None
    created_at: Optional[datetime] = None
    metadata: Optional[Dict] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'code_id': self.code_id,
            'code_text': self.code_text,
            'embedding': self.embedding.tolist(),
            'code_type': self.code_type,
            'file_path': self.file_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CodeEmbedding':
        """Create from dictionary."""
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
            
        return cls(
            code_id=data['code_id'],
            code_text=data['code_text'],
            embedding=np.array(data['embedding']),
            code_type=data['code_type'],
            file_path=data.get('file_path'),
            created_at=created_at,
            metadata=data.get('metadata', {})
        )


class CodeBERTEncoder:
    """
    CodeBERT-based encoder for transforming Java code into embeddings.
    
    This encoder uses the Microsoft CodeBERT model, which is pre-trained on
    code and natural language pairs, making it particularly effective for
    understanding code semantics.
    """
    
    def __init__(
        self,
        model_name: str = "microsoft/codebert-base",
        device: Optional[str] = None,
        max_length: int = 512,
        batch_size: int = 16,
        cache_embeddings: bool = True
    ):
        """
        Initialize the CodeBERT encoder.
        
        Args:
            model_name: HuggingFace model identifier
            device: Device for computation ('cpu', 'cuda', 'auto')
            max_length: Maximum sequence length for tokenization
            batch_size: Batch size for encoding
            cache_embeddings: Whether to cache computed embeddings
        """
        self.model_name = model_name
        self.max_length = max_length
        self.batch_size = batch_size
        self.cache_embeddings = cache_embeddings
        
        # Setup device
        if device == "auto" or device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        logger.info(f"Initializing CodeBERT encoder on device: {self.device}")
        
        # Initialize model and tokenizer
        self._load_model()
        
        # Cache for embeddings
        self._embedding_cache: Dict[str, np.ndarray] = {}
        
        logger.info(f"CodeBERT encoder initialized successfully")
    
    def _load_model(self):
        """Load the CodeBERT model and tokenizer."""
        try:
            logger.info(f"Loading model: {self.model_name}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # Load model
            self.model = AutoModel.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            
            # Get embedding dimension
            self.embedding_dim = self.model.config.hidden_size
            
            logger.info(f"Model loaded successfully. Embedding dimension: {self.embedding_dim}")
            
        except Exception as e:
            logger.error(f"Failed to load CodeBERT model: {str(e)}")
            raise
    
    def _preprocess_code(self, code: str) -> str:
        """
        Preprocess Java code for better encoding.
        
        Args:
            code: Raw Java code
            
        Returns:
            Preprocessed code
        """
        # Remove excessive whitespace
        code = " ".join(code.split())
        
        # Truncate if too long (leave room for special tokens)
        max_chars = self.max_length * 4  # Rough estimate
        if len(code) > max_chars:
            code = code[:max_chars] + "..."
            
        return code
    
    def _get_cache_key(self, code: str) -> str:
        """Generate cache key for code."""
        return hashlib.md5(code.encode()).hexdigest()
    
    def encode_single(
        self, 
        code: str, 
        code_type: str = "snippet",
        use_cache: bool = True
    ) -> np.ndarray:
        """
        Encode a single piece of code into an embedding.
        
        Args:
            code: Java code to encode
            code_type: Type of code ('method', 'class', 'file', 'snippet')
            use_cache: Whether to use cached embeddings
            
        Returns:
            Code embedding as numpy array
        """
        # Preprocess code
        processed_code = self._preprocess_code(code)
        
        # Check cache
        if use_cache and self.cache_embeddings:
            cache_key = self._get_cache_key(processed_code)
            if cache_key in self._embedding_cache:
                logger.debug(f"Using cached embedding for {code_type}")
                return self._embedding_cache[cache_key]
        
        try:
            # Tokenize
            inputs = self.tokenizer(
                processed_code,
                max_length=self.max_length,
                padding=True,
                truncation=True,
                return_tensors="pt"
            )
            
            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate embedding
            with torch.no_grad():
                outputs = self.model(**inputs)
                
                # Use [CLS] token embedding (first token)
                embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()
                embedding = embedding.squeeze()
                
            # Cache if enabled
            if use_cache and self.cache_embeddings:
                self._embedding_cache[cache_key] = embedding
                
            logger.debug(f"Generated embedding for {code_type}, shape: {embedding.shape}")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to encode {code_type}: {str(e)}")
            raise
    
    def encode_batch(
        self, 
        codes: List[str], 
        code_types: Optional[List[str]] = None,
        use_cache: bool = True
    ) -> List[np.ndarray]:
        """
        Encode multiple pieces of code efficiently in batches.
        
        Args:
            codes: List of Java code strings
            code_types: List of code types (optional)
            use_cache: Whether to use cached embeddings
            
        Returns:
            List of code embeddings
        """
        if not codes:
            return []
            
        if code_types is None:
            code_types = ["snippet"] * len(codes)
            
        logger.info(f"Encoding batch of {len(codes)} code snippets")
        
        embeddings = []
        
        # Process in batches
        for i in range(0, len(codes), self.batch_size):
            batch_codes = codes[i:i + self.batch_size]
            batch_types = code_types[i:i + self.batch_size]
            
            batch_embeddings = []
            
            # Check cache first
            cached_embeddings = {}
            codes_to_process = []
            indices_to_process = []
            
            if use_cache and self.cache_embeddings:
                for j, code in enumerate(batch_codes):
                    processed_code = self._preprocess_code(code)
                    cache_key = self._get_cache_key(processed_code)
                    
                    if cache_key in self._embedding_cache:
                        cached_embeddings[j] = self._embedding_cache[cache_key]
                    else:
                        codes_to_process.append(processed_code)
                        indices_to_process.append(j)
            else:
                codes_to_process = [self._preprocess_code(code) for code in batch_codes]
                indices_to_process = list(range(len(batch_codes)))
            
            # Process uncached codes
            if codes_to_process:
                try:
                    # Tokenize batch
                    inputs = self.tokenizer(
                        codes_to_process,
                        max_length=self.max_length,
                        padding=True,
                        truncation=True,
                        return_tensors="pt"
                    )
                    
                    # Move to device
                    inputs = {k: v.to(self.device) for k, v in inputs.items()}
                    
                    # Generate embeddings
                    with torch.no_grad():
                        outputs = self.model(**inputs)
                        
                        # Use [CLS] token embeddings
                        batch_embs = outputs.last_hidden_state[:, 0, :].cpu().numpy()
                        
                    # Cache new embeddings
                    if use_cache and self.cache_embeddings:
                        for idx, code in enumerate(codes_to_process):
                            cache_key = self._get_cache_key(code)
                            self._embedding_cache[cache_key] = batch_embs[idx]
                    
                    # Map back to original indices
                    processed_embeddings = {}
                    for idx, orig_idx in enumerate(indices_to_process):
                        processed_embeddings[orig_idx] = batch_embs[idx]
                        
                except Exception as e:
                    logger.error(f"Failed to process batch: {str(e)}")
                    # Fallback to individual processing
                    processed_embeddings = {}
                    for idx, code in zip(indices_to_process, codes_to_process):
                        try:
                            emb = self.encode_single(code, batch_types[idx], use_cache=False)
                            processed_embeddings[idx] = emb
                        except Exception as inner_e:
                            logger.error(f"Failed individual encoding: {str(inner_e)}")
                            # Use zero embedding as fallback
                            processed_embeddings[idx] = np.zeros(self.embedding_dim)
            else:
                processed_embeddings = {}
            
            # Combine cached and processed embeddings
            for j in range(len(batch_codes)):
                if j in cached_embeddings:
                    batch_embeddings.append(cached_embeddings[j])
                elif j in processed_embeddings:
                    batch_embeddings.append(processed_embeddings[j])
                else:
                    # Fallback to zero embedding
                    logger.warning(f"No embedding available for code {i+j}, using zero vector")
                    batch_embeddings.append(np.zeros(self.embedding_dim))
            
            embeddings.extend(batch_embeddings)
            
            logger.debug(f"Processed batch {i//self.batch_size + 1}/{(len(codes)-1)//self.batch_size + 1}")
        
        logger.info(f"Completed batch encoding: {len(embeddings)} embeddings generated")
        return embeddings
    
    def create_code_embedding(
        self,
        code: str,
        code_id: str,
        code_type: str,
        file_path: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> CodeEmbedding:
        """
        Create a complete CodeEmbedding object.
        
        Args:
            code: Java code to encode
            code_id: Unique identifier for the code
            code_type: Type of code ('method', 'class', 'file', 'snippet')
            file_path: Path to the source file (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            CodeEmbedding object
        """
        embedding = self.encode_single(code, code_type)
        
        return CodeEmbedding(
            code_id=code_id,
            code_text=code,
            embedding=embedding,
            code_type=code_type,
            file_path=file_path,
            metadata=metadata or {}
        )
    
    def get_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Cosine similarity score
        """
        # Normalize embeddings
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        normalized1 = embedding1 / norm1
        normalized2 = embedding2 / norm2
        
        # Calculate cosine similarity
        similarity = np.dot(normalized1, normalized2)
        return float(similarity)
    
    def find_similar_codes(
        self,
        query_embedding: np.ndarray,
        candidate_embeddings: List[np.ndarray],
        top_k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Find most similar code embeddings to a query.
        
        Args:
            query_embedding: Query embedding
            candidate_embeddings: List of candidate embeddings
            top_k: Number of top results to return
            
        Returns:
            List of (index, similarity_score) tuples
        """
        similarities = []
        
        for i, candidate in enumerate(candidate_embeddings):
            similarity = self.get_similarity(query_embedding, candidate)
            similarities.append((i, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def clear_cache(self):
        """Clear the embedding cache."""
        self._embedding_cache.clear()
        logger.info("Embedding cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        return {
            "cache_size": len(self._embedding_cache),
            "cache_enabled": self.cache_embeddings,
            "embedding_dimension": self.embedding_dim,
            "model_name": self.model_name,
            "device": self.device
        }
    
    def save_cache(self, file_path: str):
        """Save embedding cache to file."""
        cache_data = {
            "embeddings": {k: v.tolist() for k, v in self._embedding_cache.items()},
            "metadata": {
                "model_name": self.model_name,
                "embedding_dim": self.embedding_dim,
                "created_at": datetime.now().isoformat()
            }
        }
        
        with open(file_path, 'w') as f:
            json.dump(cache_data, f, indent=2)
            
        logger.info(f"Cache saved to {file_path}")
    
    def load_cache(self, file_path: str):
        """Load embedding cache from file."""
        try:
            with open(file_path, 'r') as f:
                cache_data = json.load(f)
            
            # Validate metadata
            metadata = cache_data.get("metadata", {})
            if metadata.get("model_name") != self.model_name:
                logger.warning("Cache model name mismatch, clearing cache")
                return
                
            if metadata.get("embedding_dim") != self.embedding_dim:
                logger.warning("Cache embedding dimension mismatch, clearing cache")
                return
            
            # Load embeddings
            self._embedding_cache = {
                k: np.array(v) for k, v in cache_data["embeddings"].items()
            }
            
            logger.info(f"Cache loaded from {file_path}: {len(self._embedding_cache)} embeddings")
            
        except Exception as e:
            logger.error(f"Failed to load cache: {str(e)}")
