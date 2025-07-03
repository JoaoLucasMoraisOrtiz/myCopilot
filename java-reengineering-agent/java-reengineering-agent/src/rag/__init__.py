"""
RAG (Retrieval-Augmented Generation) module for the Java Reengineering Agent.

This module provides the foundation for code understanding through:
- CodeBERT encoder for Java code embeddings
- Vector store for efficient similarity search
- Graph-based RAG for understanding code relationships
- Context assembly for AI generation
"""

from .codebert_encoder import CodeBERTEncoder

__all__ = [
    'CodeBERTEncoder'
]
