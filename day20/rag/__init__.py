"""
RAG comparison module for comparing responses with and without retrieval.
"""

from .squad_loader import SquadLoader
from .rag_comparator import RagComparator

__all__ = ['SquadLoader', 'RagComparator']
