"""Conversation history manager for chat sessions."""

from typing import List, Dict, Optional
from text_manager import TextManager


class ConversationHistory:
    """Manages conversation history for a chat session."""

    # Token limits for context management
    MAX_CONTEXT_TOKENS = 30000  # Gemini model limit
    SAFE_THRESHOLD = 25000      # Start warning at 80%
    KEEP_RECENT_MESSAGES = 5    # Number of recent messages to keep full
    MAX_INPUT_TOKENS = 800      # Maximum tokens for single input message (compress if longer)

    def __init__(self):
        """Initialize empty conversation history."""
        self.history: List[Dict] = []
        self.total_tokens = 0
        self.message_tokens: List[int] = []  # Token count per message
        self.compressed = False  # Track if history was compressed

    def add_user_message(self, text: str, tokens: Optional[int] = None):
        """Add user message to history.

        Args:
            text: User message text
            tokens: Token count (if None, will estimate)
        """
        self.history.append({
            "parts": [{"text": text}],
            "role": "user"
        })

        # Track tokens for this message
        if tokens is None:
            tokens = TextManager.estimate_tokens(text)
        self.message_tokens.append(tokens)

    def add_assistant_message(self, text: str, tokens: Optional[int] = None):
        """Add assistant message to history.

        Args:
            text: Assistant message text
            tokens: Token count (if None, will estimate)
        """
        self.history.append({
            "parts": [{"text": text}],
            "role": "model"
        })

        # Track tokens for this message
        if tokens is None:
            tokens = TextManager.estimate_tokens(text)
        self.message_tokens.append(tokens)

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
        self.message_tokens.clear()
        self.compressed = False

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

    def should_compress(self) -> bool:
        """Check if history should be compressed.

        Returns:
            True if approaching token limit
        """
        return self.total_tokens > self.SAFE_THRESHOLD

    @staticmethod
    def should_compress_input(text: str) -> bool:
        """Check if input text should be compressed before sending.

        Args:
            text: Input text to check

        Returns:
            True if text exceeds MAX_INPUT_TOKENS
        """
        tokens = TextManager.estimate_tokens(text)
        return tokens > ConversationHistory.MAX_INPUT_TOKENS

    def get_compression_stats(self) -> Dict:
        """Get current compression statistics.

        Returns:
            Dictionary with token usage stats
        """
        return {
            "total_tokens": self.total_tokens,
            "max_tokens": self.MAX_CONTEXT_TOKENS,
            "percentage": (self.total_tokens / self.MAX_CONTEXT_TOKENS * 100),
            "should_compress": self.should_compress(),
            "message_count": len(self.history),
            "compressed": self.compressed
        }

    def compress_history(self, client) -> Dict:
        """Compress old messages using hierarchical summarization.

        Keeps recent messages intact, summarizes older ones.

        Args:
            client: GeminiApiClient instance for summarization

        Returns:
            Dictionary with compression results:
                - messages_compressed: Number of messages compressed
                - tokens_before: Token count before compression
                - tokens_after: Token count after compression
                - tokens_saved: Number of tokens saved
        """
        # Need at least 2 messages to compress (1 to compress, 1 to keep)
        if len(self.history) < 2:
            return {
                "messages_compressed": 0,
                "tokens_before": self.total_tokens,
                "tokens_after": self.total_tokens,
                "tokens_saved": 0,
                "message": "Need at least 2 messages to compress"
            }

        tokens_before = self.total_tokens

        # Split history into old and recent
        # Keep recent messages, compress the rest
        num_to_keep = min(self.KEEP_RECENT_MESSAGES, len(self.history) - 1)
        old_messages = self.history[:-num_to_keep] if num_to_keep > 0 else self.history[:-1]
        recent_messages = self.history[-num_to_keep:] if num_to_keep > 0 else self.history[-1:]

        recent_tokens = self.message_tokens[-num_to_keep:] if num_to_keep > 0 else self.message_tokens[-1:]

        # Combine old messages into text for summarization
        old_text_parts = []
        for msg in old_messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            text = msg["parts"][0]["text"]
            old_text_parts.append(f"{role}: {text}")

        old_text = "\n\n".join(old_text_parts)

        # Summarize old messages with short timeout to prevent hanging
        summary_result = TextManager.summarize_text(
            text=old_text,
            client=client,
            max_tokens=500,  # Use 500 tokens for summary
            language="mixed",
            timeout=15  # 15 second timeout for compression (faster failure)
        )

        # Create summary message
        summary_message = {
            "parts": [{
                "text": f"[Previous conversation summary: {summary_result['summary']}]"
            }],
            "role": "model"
        }

        # Rebuild history with summary + recent messages
        self.history = [summary_message] + recent_messages
        self.message_tokens = [summary_result['summary_tokens']] + recent_tokens

        # Recalculate total tokens
        self.total_tokens = sum(self.message_tokens)
        self.compressed = True

        tokens_after = self.total_tokens
        tokens_saved = tokens_before - tokens_after

        return {
            "messages_compressed": len(old_messages),
            "tokens_before": tokens_before,
            "tokens_after": tokens_after,
            "tokens_saved": tokens_saved,
            "compression_ratio": summary_result['compression_ratio']
        }
