"""Conversation history manager for chat sessions."""

from typing import List, Dict


class ConversationHistory:
    """Manages conversation history for a chat session."""

    def __init__(self):
        """Initialize empty conversation history."""
        self.history: List[Dict] = []
        self.total_tokens = 0

    def add_user_message(self, text: str):
        """Add user message to history.

        Args:
            text: User message text
        """
        self.history.append({
            "parts": [{"text": text}],
            "role": "user"
        })

    def add_assistant_message(self, text: str):
        """Add assistant message to history.

        Args:
            text: Assistant message text
        """
        self.history.append({
            "parts": [{"text": text}],
            "role": "model"
        })

    def get_history(self) -> List[Dict]:
        """Get conversation history without the last user message.

        Returns:
            List of conversation messages
        """
        # Return all messages except the last one (current user prompt)
        return self.history[:-1] if len(self.history) > 0 else []

    def clear(self):
        """Clear conversation history."""
        self.history.clear()
        self.total_tokens = 0

    def add_tokens(self, count: int):
        """Add to total token count.

        Args:
            count: Number of tokens to add
        """
        self.total_tokens += count

    def get_message_count(self) -> int:
        """Get total number of messages.

        Returns:
            Number of messages in history
        """
        return len(self.history)
