"""
RAG comparison module for comparing responses with and without retrieval.
"""

from .koog_loader import KoogLoader
from .rag_comparator import RagComparator

__all__ = ['KoogLoader', 'RagComparator']
