import os
import time
from dotenv import load_dotenv
from .base import BaseAdapter

load_dotenv()


class OpenAIAdapter(BaseAdapter):
    """Calls OpenAI API. Requires OPENAI_API_KEY in .env."""

    def __init__(self, model: str):
        try:
            from openai import OpenAI, RateLimitError, APIError
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")

        self.model = model
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.RateLimitError = RateLimitError
        self.APIError = APIError

    def call(self, prompt: str, system_prompt: str, max_retries: int = 3) -> dict:
        attempt = 0
        while attempt < max_retries:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=512,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": prompt}
                    ]
                )
                return {
                    "response": response.choices[0].message.content,
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                    "error": None
                }
            except self.RateLimitError:
                time.sleep(2 ** attempt)
                attempt += 1
            except self.APIError as e:
                return {"response": None, "input_tokens": 0, "output_tokens": 0, "error": str(e)}

        return {"response": None, "input_tokens": 0, "output_tokens": 0, "error": "Max retries exceeded"}