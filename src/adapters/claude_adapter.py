import time
import anthropic
from dotenv import load_dotenv
from .base import BaseAdapter

load_dotenv()


class ClaudeAdapter(BaseAdapter):
    """Calls Anthropic Claude API. Default adapter."""

    def __init__(self, model: str):
        self.model = model
        self.client = anthropic.Anthropic()

    def call(self, prompt: str, system_prompt: str, max_retries: int = 3) -> dict:
        attempt = 0
        while attempt < max_retries:
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=512,
                    system=system_prompt,
                    messages=[{"role": "user", "content": prompt}]
                )
                return {
                    "response": response.content[0].text,
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "error": None
                }
            except anthropic.RateLimitError:
                time.sleep(2 ** attempt)
                attempt += 1
            except anthropic.APIError as e:
                return {"response": None, "input_tokens": 0, "output_tokens": 0, "error": str(e)}

        return {"response": None, "input_tokens": 0, "output_tokens": 0, "error": "Max retries exceeded"}