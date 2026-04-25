import json
import csv
import os
from .base import BaseAdapter


class OutputOnlyAdapter(BaseAdapter):
    """
    Evaluates pre-collected model responses — no API call made.
    Reads from a CSV or JSON file supplied via --input flag.

    CSV format expected:
        id, prompt, response
        (extra columns ignored)

    JSON format expected:
        [{"id": "...", "prompt": "...", "response": "..."}, ...]

    Usage:
    python run_eval.py --adapter output-only --input my_responses.csv"""

    def __init__(self, input_file: str):
        if not input_file:
            raise ValueError(
                "--input is required when using --adapter output-only\n"
                "Example: python run_eval.py --adapter output-only --input responses.csv"
            )
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")

        self.responses = self._load(input_file)

    def _load(self, path: str) -> dict:
        """Returns a dict keyed by prompt text → response text."""
        responses = {}
        if path.endswith(".json"):
            with open(path, "r", encoding="utf-8") as f:
                rows = json.load(f)
            for row in rows:
                responses[row["prompt"].strip()] = row["response"]
        else:
            # treat as CSV
            with open(path, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    responses[row["prompt"].strip()] = row["response"]
        return responses

    def call(self, prompt: str, system_prompt: str, **kwargs) -> dict:
        """Looks up the pre-collected response for this prompt."""
        response = self.responses.get(prompt.strip())
        if response is None:
            return {
                "response": None,
                "input_tokens": 0,
                "output_tokens": 0,
                "error": f"No pre-collected response found for prompt: {prompt[:60]}..."
            }
        return {
            "response": response,
            "input_tokens": 0,   # no API call made
            "output_tokens": 0,
            "error": None
        }