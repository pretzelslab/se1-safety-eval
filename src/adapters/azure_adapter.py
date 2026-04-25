import os
from dotenv import load_dotenv
from .base import BaseAdapter

load_dotenv()


class AzureAdapter(BaseAdapter):
    """
    Calls Azure OpenAI API.
    Requires in .env:
        AZURE_OPENAI_ENDPOINT    e.g. https://my-resource.openai.azure.com/
        AZURE_OPENAI_API_KEY
        AZURE_OPENAI_DEPLOYMENT  e.g. gpt-4o (your deployment name in Azure)
        AZURE_OPENAI_API_VERSION e.g. 2024-02-01 (optional, defaults below)
    """

    def __init__(self, model: str):
        try:
            from openai import AzureOpenAI, RateLimitError, APIError
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")

        # Azure ignores the --model flag — deployment name comes from .env
        # We keep model param in signature to match the factory interface
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", model)
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
        )
        self.RateLimitError = RateLimitError
        self.APIError = APIError

    def call(self, prompt: str, system_prompt: str, max_retries: int = 3) -> dict:
        import time
        attempt = 0
        while attempt < max_retries:
            try:
                response = self.client.chat.completions.create(
                    model=self.deployment,
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