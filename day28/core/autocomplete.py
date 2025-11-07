"""Autocomplete for @ file mentions with fuzzy search."""

from typing import Iterable
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from fuzzywuzzy import fuzz


class FileMentionCompleter(Completer):
    """Completer for @ file mentions with fuzzy matching."""

    def __init__(self, files: list, folders: list):
        """
        Initialize completer.

        Args:
            files: List of file paths
            folders: List of folder paths
        """
        self.files = files
        self.folders = folders
        self.all_paths = files + folders

    def get_completions(
        self,
        document: Document,
        complete_event
    ) -> Iterable[Completion]:
        """
        Generate completions for current input.

        Args:
            document: Current document
            complete_event: Completion event

        Yields:
            Completion objects
        """
        text_before_cursor = document.text_before_cursor

        # Check if we're in @ mention context
        if '@' not in text_before_cursor:
            return

        # Find the last @ and text after it
        last_at = text_before_cursor.rfind('@')
        if last_at == -1:
            return

        # Get the partial path after @
        partial = text_before_cursor[last_at + 1:]

        # Don't complete if user already finished the mention
        if len(partial) > 0 and (
            partial[-1] == ' '
            or (last_at + 1 + len(partial)) < len(document.text)
        ):
            return

        # Generate fuzzy matches
        matches = self._fuzzy_match(partial)

        # Yield completions
        for path, score in matches[:20]:  # Limit to top 20
            # Calculate start position (negative = characters to replace)
            start_position = -len(partial)

            # Add metadata to display
            display_meta = self._get_display_meta(path)

            yield Completion(
                text=path,
                start_position=start_position,
                display=path,
                display_meta=display_meta
            )

    def _fuzzy_match(self, partial: str, threshold: int = 50):
        """
        Perform fuzzy matching on paths.

        Args:
            partial: Partial path to match
            threshold: Minimum score to include

        Returns:
            List of (path, score) tuples sorted by score
        """
        if not partial:
            # No partial - return all paths sorted alphabetically
            return [(p, 100) for p in sorted(self.all_paths)[:20]]

        matches = []

        for path in self.all_paths:
            # Try different fuzzy matching strategies
            ratio = fuzz.ratio(partial.lower(), path.lower())
            partial_ratio = fuzz.partial_ratio(partial.lower(), path.lower())
            token_sort = fuzz.token_sort_ratio(partial.lower(), path.lower())

            # Boost score if starts with partial
            if path.lower().startswith(partial.lower()):
                score = max(ratio, partial_ratio, token_sort) + 20
            else:
                score = max(ratio, partial_ratio, token_sort)

            # Boost score for file name match (not just path)
            filename = path.split('/')[-1]
            if filename.lower().startswith(partial.lower()):
                score += 15

            if score >= threshold:
                matches.append((path, score))

        # Sort by score (descending)
        matches.sort(key=lambda x: x[1], reverse=True)

        return matches

    def _get_display_meta(self, path: str) -> str:
        """
        Get metadata to display next to completion.

        Args:
            path: File/folder path

        Returns:
            Metadata string
        """
        if path.endswith('/'):
            return 'folder'
        else:
            # Get file extension
            if '.' in path:
                ext = path.split('.')[-1]
                return f'{ext} file'
            return 'file'

    def update_paths(self, files: list, folders: list):
        """
        Update available paths.

        Args:
            files: New list of files
            folders: New list of folders
        """
        self.files = files
        self.folders = folders
        self.all_paths = files + folders
