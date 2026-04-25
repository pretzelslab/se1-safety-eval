from abc import ABC, abstractmethod


class BaseAdapter(ABC):
    """
    Every adapter must implement call().
    Input:  prompt (str) + system_prompt (str)
    Output: dict with keys: response, input_tokens, output_tokens, error
    """

    @abstractmethod
    def call(self, prompt: str, system_prompt: str) -> dict:
        raise NotImplementedError