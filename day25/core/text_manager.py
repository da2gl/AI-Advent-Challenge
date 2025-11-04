"""Text management utilities for token estimation and compression."""

from typing import Dict


class TextManager:
    """Manager for text compression and token estimation."""

    # Token estimation coefficients (empirical values)
    CHARS_PER_TOKEN_RUSSIAN = 3  # ~3 characters per token for Russian
    CHARS_PER_TOKEN_ENGLISH = 4  # ~4 characters per token for English

    @staticmethod
    def estimate_tokens(text: str, language: str = "mixed") -> int:
        """Estimate number of tokens in text.

        This is a rough estimation based on character count.
        For accurate counts, use the API response metadata.

        Args:
            text: Text to estimate
            language: Language hint ("russian", "english", or "mixed")

        Returns:
            Estimated number of tokens
        """
        if not text:
            return 0

        char_count = len(text)

        # Use conservative estimate for mixed content
        if language == "russian":
            chars_per_token = TextManager.CHARS_PER_TOKEN_RUSSIAN
        elif language == "english":
            chars_per_token = TextManager.CHARS_PER_TOKEN_ENGLISH
        else:
            # For mixed, use average
            chars_per_token = 3.5

        return max(1, int(char_count / chars_per_token))

    @staticmethod
    def summarize_text(
        text: str,
        client,
        max_tokens: int = 200,
        language: str = "english",
        timeout: int = 30
    ) -> Dict[str, any]:
        """Summarize text using Gemini API.

        Args:
            text: Text to summarize
            client: GeminiApiClient instance
            max_tokens: Maximum tokens for summary
            language: Target language for summary
            timeout: API request timeout in seconds (default: 30)

        Returns:
            Dictionary with:
                - summary: Summarized text
                - original_tokens: Estimated tokens in original
                - summary_tokens: Estimated tokens in summary
                - compression_ratio: How much was compressed (0.0-1.0)
        """
        # Estimate original tokens
        original_tokens = TextManager.estimate_tokens(text)

        # Create summarization prompt
        if language == "russian":
            prompt = f"""Создай краткое резюме следующего текста.
Максимальная длина резюме: {max_tokens} токенов.
Сохрани все ключевые моменты и важную информацию.

Текст:
{text}

Резюме:"""
        else:
            prompt = f"""You are summarizing a conversation history to preserve context for an AI assistant.

TASK: Create a comprehensive summary that captures all essential information needed to continue the
conversation naturally.

REQUIREMENTS:
- Maximum length: {max_tokens} tokens
- Preserve ALL key facts, names, numbers, dates, and specific details
- Maintain the chronological flow of the conversation
- Keep important questions asked and answers given
- Preserve any decisions made, problems identified, or solutions proposed
- Include technical details, code snippets, or file names if mentioned
- Maintain the context and relationship between topics discussed

CONVERSATION TO SUMMARIZE:
{text}

SUMMARY (preserve all critical details):"""

        # Get summary from Gemini with timeout handling
        try:
            response = client.generate_content(
                prompt=prompt,
                max_output_tokens=max_tokens * 2,  # Give some buffer
                timeout=timeout
            )

            summary = client.extract_text(response)
            summary_tokens = TextManager.estimate_tokens(summary)
        except Exception as e:
            # Re-raise with more context
            error_msg = str(e)
            if "timeout" in error_msg.lower():
                raise Exception(f"Compression timed out after {timeout}s - API response too slow")
            elif "connection" in error_msg.lower():
                raise Exception(f"Network error during compression: {error_msg}")
            else:
                raise Exception(f"Compression API failed: {error_msg}")

        # Calculate compression ratio
        compression_ratio = 1.0 - (summary_tokens / max(original_tokens, 1))

        return {
            "summary": summary,
            "original_tokens": original_tokens,
            "summary_tokens": summary_tokens,
            "compression_ratio": compression_ratio,
            "tokens_saved": original_tokens - summary_tokens
        }

    @staticmethod
    def format_token_usage(current: int, maximum: int) -> str:
        """Format token usage as a progress bar.

        Args:
            current: Current token count
            maximum: Maximum token limit

        Returns:
            Formatted string with progress bar
        """
        percentage = (current / maximum * 100) if maximum > 0 else 0
        bar_width = 20
        filled = int(bar_width * current / maximum) if maximum > 0 else 0
        bar = "█" * filled + "░" * (bar_width - filled)

        # Add warning emoji if usage is high
        warning = ""
        if percentage > 90:
            warning = " 🔴"
        elif percentage > 80:
            warning = " ⚠️"
        elif percentage > 60:
            warning = " 🟡"
        else:
            warning = " ✓"

        return f"[{current:,}/{maximum:,}] {bar} {percentage:.1f}%{warning}"
