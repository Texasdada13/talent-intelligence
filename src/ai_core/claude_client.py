"""Claude Client - Talent Intelligence"""
import os
import logging
from typing import Optional, Generator, Dict, Any, List
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class ClaudeClient:
    DEFAULT_MODEL = "claude-sonnet-4-20250514"
    MAX_TOKENS = 4096

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = Anthropic(api_key=self.api_key) if self.api_key else None

    def is_available(self) -> bool:
        return self.client is not None

    def generate_response(self, messages: List[Dict[str, str]], system_prompt: str, max_tokens: int = MAX_TOKENS, temperature: float = 0.7) -> str:
        if not self.client:
            return "AI assistant is not available. Please configure the Anthropic API key."
        try:
            response = self.client.messages.create(model=self.DEFAULT_MODEL, max_tokens=max_tokens, system=system_prompt, messages=messages, temperature=temperature)
            return response.content[0].text if response.content else "Unable to generate response."
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return f"Error: {str(e)}"

    def stream_response(self, messages: List[Dict[str, str]], system_prompt: str, max_tokens: int = MAX_TOKENS, temperature: float = 0.7) -> Generator[str, None, None]:
        if not self.client:
            yield "AI assistant is not available."
            return
        try:
            with self.client.messages.stream(model=self.DEFAULT_MODEL, max_tokens=max_tokens, system=system_prompt, messages=messages, temperature=temperature) as stream:
                for text in stream.text_stream:
                    yield text
        except Exception as e:
            yield f"Error: {str(e)}"
