"""Conversation history manager with SQLite persistence."""

from typing import List, Dict, Optional
from .text_manager import TextManager
from .storage import SQLiteStorage


class ConversationHistory:
    """Manages conversation history with persistent SQLite storage."""

    # Token limits for context management
    MAX_CONTEXT_TOKENS = 30000  # Gemini model limit
    SAFE_THRESHOLD = 25000      # Start warning at 80%
    KEEP_RECENT_MESSAGES = 5    # Number of recent messages to keep full
    MAX_INPUT_TOKENS = 800      # Maximum tokens for single input message (compress if longer)

    def __init__(self, storage: SQLiteStorage, dialog_id: Optional[int] = None):
        """Initialize conversation history with storage.

        Args:
            storage: SQLiteStorage instance
            dialog_id: Dialog ID to load (if None, starts empty)
        """
        self.storage = storage
        self.dialog_id = dialog_id
        self.history: List[Dict] = []
        self.total_tokens = 0
        self.message_tokens: List[int] = []
        self.compressed = False

        # Load dialog from storage if dialog_id is provided
        if dialog_id:
            self.load_from_storage(dialog_id)

    def load_from_storage(self, dialog_id: int):
        """Load conversation history from storage.

        Args:
            dialog_id: Dialog ID to load
        """
        messages = self.storage.load_dialog(dialog_id)
        self.dialog_id = dialog_id
        self.history.clear()
        self.message_tokens.clear()
        self.total_tokens = 0

        # Reconstruct history from stored messages
        for msg in messages:
            role = msg['role']
            content = msg['content']
            tokens = msg['tokens']

            # Add to in-memory history
            self.history.append({
                "parts": [{"text": content}],
                "role": role
            })
            self.message_tokens.append(tokens)
            self.total_tokens += tokens

    def add_user_message(self, text: str, tokens: Optional[int] = None):
        """Add user message to history and save to storage.

        Args:
            text: User message text
            tokens: Token count (if None, will estimate)
        """
        if tokens is None:
            tokens = TextManager.estimate_tokens(text)

        # Add to in-memory history
        self.history.append({
            "parts": [{"text": text}],
            "role": "user"
        })
        self.message_tokens.append(tokens)

        # Save to storage if dialog is active
        if self.dialog_id:
            self.storage.save_message(self.dialog_id, "user", text, tokens)

            # Auto-generate title from first user message
            dialog_info = self.storage.get_dialog_info(self.dialog_id)
            if dialog_info and dialog_info['title'] == 'Untitled':
                # Use first 50 chars of first message as title
                title = text[:50] + "..." if len(text) > 50 else text
                self.storage.update_dialog_title(self.dialog_id, title)

    def add_assistant_message(self, text: str, tokens: Optional[int] = None):
        """Add assistant message to history and save to storage.

        Args:
            text: Assistant message text
            tokens: Token count (if None, will estimate)
        """
        if tokens is None:
            tokens = TextManager.estimate_tokens(text)

        # Add to in-memory history
        self.history.append({
            "parts": [{"text": text}],
            "role": "model"
        })
        self.message_tokens.append(tokens)

        # Save to storage if dialog is active
        if self.dialog_id:
            self.storage.save_message(self.dialog_id, "model", text, tokens)

    def get_history(self) -> List[Dict]:
        """Get conversation history without the last user message.

        Returns:
            List of conversation messages
        """
        # Return all messages except the last one (current user prompt)
        return self.history[:-1] if len(self.history) > 0 else []

    def clear(self):
        """Clear in-memory conversation history (does not delete from storage)."""
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

    def add_message(self, role: str, text: Optional[str], function_calls=None, function_results=None):
        """Add a message to history (generic method for all message types).

        Args:
            role: Message role ('user', 'model', 'function')
            text: Message text (optional for function messages)
            function_calls: List of function calls (for model messages)
            function_results: List of function results (for function messages)
        """
        if role == "user":
            self.add_user_message(text)
        elif role == "model":
            if function_calls:
                # Model message with function calls
                self.history.append({
                    "parts": [{"functionCall": fc} for fc in function_calls],
                    "role": "model"
                })
                tokens = len(str(function_calls)) // 4
                self.message_tokens.append(tokens)
            elif text:
                self.add_assistant_message(text)
        elif role == "function":
            # Function results message
            if function_results:
                parts = []
                for result in function_results:
                    parts.append({
                        "functionResponse": result["functionResponse"]
                    })
                self.history.append({
                    "parts": parts,
                    "role": "function"
                })
                tokens = len(str(function_results)) // 4
                self.message_tokens.append(tokens)

    def add_token_usage(self, usage: Dict):
        """Add token usage from API response.

        Args:
            usage: Dictionary with token usage info (prompt_tokens, response_tokens, total_tokens)
        """
        if usage and "total_tokens" in usage:
            self.add_tokens(usage["total_tokens"])

    def get_token_stats(self) -> Dict:
        """Get token usage statistics.

        Returns:
            Dictionary with token statistics
        """
        return {
            "total_tokens": self.total_tokens,
            "prompt_tokens": sum(self.message_tokens[::2]) if len(self.message_tokens) > 0 else 0,
            "response_tokens": sum(self.message_tokens[1::2]) if len(self.message_tokens) > 1 else 0,
            "max_context_tokens": self.MAX_CONTEXT_TOKENS,
            "remaining_tokens": self.MAX_CONTEXT_TOKENS - self.total_tokens,
            "message_count": len(self.history)
        }

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
            Dictionary with compression results
        """
        # Need at least 2 messages to compress
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

        # Summarize old messages
        summary_result = TextManager.summarize_text(
            text=old_text,
            client=client,
            max_tokens=500,
            language="mixed",
            timeout=15
        )

        # Create summary message
        summary_text = f"""[CONVERSATION HISTORY COMPRESSED]
This is a summary of the previous conversation to preserve context while reducing token usage.

{summary_result['summary']}

[Compression stats: {len(old_messages)} messages compressed, {summary_result['tokens_saved']:,} tokens saved]
"""
        summary_message = {
            "parts": [{
                "text": summary_text
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

        overall_compression_ratio = (tokens_saved / tokens_before) if tokens_before > 0 else 0

        return {
            "messages_compressed": len(old_messages),
            "tokens_before": tokens_before,
            "tokens_after": tokens_after,
            "tokens_saved": tokens_saved,
            "compression_ratio": overall_compression_ratio,
            "summary_tokens": summary_result['summary_tokens'],
            "messages_kept": len(recent_messages),
            "efficiency_percent": overall_compression_ratio * 100
        }
