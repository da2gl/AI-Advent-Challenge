"""
SQuAD dataset loader for RAG comparison.
"""

from dataclasses import dataclass
from typing import List, Optional
from datasets import load_dataset


@dataclass
class SquadExample:
    """Single example from SQuAD dataset."""
    context: str
    question: str
    answers: List[str]
    title: str
    id: str


class SquadLoader:
    """Loads and manages SQuAD dataset for RAG experiments."""

    def __init__(self, cache_dir: str = "data/squad_cache"):
        """Initialize SQuAD loader.

        Args:
            cache_dir: Directory to cache downloaded dataset (default: data/squad_cache)
        """
        self.dataset = None
        self.examples: List[SquadExample] = []
        self.cache_dir = cache_dir

    def load(self, split: str = "validation", limit: Optional[int] = None) -> List[SquadExample]:
        """
        Load SQuAD dataset.

        Args:
            split: Dataset split ('train' or 'validation')
            limit: Maximum number of examples to load

        Returns:
            List of SquadExample objects
        """
        # Load dataset with local cache
        if limit:
            self.dataset = load_dataset(
                "squad",
                split=f"{split}[:{limit}]",
                cache_dir=self.cache_dir
            )
        else:
            self.dataset = load_dataset(
                "squad",
                split=split,
                cache_dir=self.cache_dir
            )

        # Convert to SquadExample objects
        self.examples = []
        for item in self.dataset:
            example = SquadExample(
                context=item['context'],
                question=item['question'],
                answers=item['answers']['text'],
                title=item['title'],
                id=item['id']
            )
            self.examples.append(example)

        return self.examples

    def get_contexts(self) -> List[str]:
        """Get all unique contexts from loaded examples."""
        contexts = set()
        for example in self.examples:
            contexts.add(example.context)
        return list(contexts)

    def get_example(self, index: int) -> Optional[SquadExample]:
        """Get example by index."""
        if 0 <= index < len(self.examples):
            return self.examples[index]
        return None

    def __len__(self) -> int:
        """Return number of loaded examples."""
        return len(self.examples)
