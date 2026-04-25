import os
import time
import requests
from dotenv import load_dotenv
from .base import BaseAdapter

load_dotenv()


class VendorHttpAdapter(BaseAdapter):
    """Generic HTTP adapter for any REST-based model API."""

    def __init__(self):
        self.url = os.getenv("VENDOR_API_URL")
        self.api_key = os.getenv("VENDOR_API_KEY")
        self.response_path = os.getenv(
            "VENDOR_RESPONSE_PATH", "choices.0.message.content"
        )
        if not self.url:
            raise ValueError("VENDOR_API_URL not set in .env")

    def call(self, prompt: str, system_prompt: str, max_retries: int = 3) -> dict:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": prompt}
            ],
            "max_tokens": 512,
        }
        attempt = 0
        while attempt < max_retries:
            try:
                resp = requests.post(self.url, json=payload, headers=headers, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                text = self._extract(data, self.response_path)
                return {
                    "response": text,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "error": None
                }
            except requests.exceptions.Timeout:
                time.sleep(2 ** attempt)
                attempt += 1
            except requests.exceptions.RequestException as e:
                return {"response": None, "input_tokens": 0, "output_tokens": 0, "error": str(e)}

        return {"response": None, "input_tokens": 0, "output_tokens": 0, "error": "Max retries exceeded"}

    def _extract(self, data: dict, path: str) -> str:
        """Drills into nested JSON using dot notation e.g. choices.0.message.content"""
        parts = path.split(".")
        val = data
        for part in parts:
            val = val[int(part)] if part.isdigit() else val[part]
        return str(val)