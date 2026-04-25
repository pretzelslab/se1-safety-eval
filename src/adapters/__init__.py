from .base import BaseAdapter
from .claude_adapter import ClaudeAdapter
from .openai_adapter import OpenAIAdapter
from .azure_adapter import AzureAdapter
from .vendor_http_adapter import VendorHttpAdapter
from .output_only_adapter import OutputOnlyAdapter


def get_adapter(adapter_name: str, model: str, input_file: str = None) -> BaseAdapter:
    """Factory — returns the right adapter for the --adapter flag."""
    adapters = {
        "claude":      lambda: ClaudeAdapter(model),
        "openai":      lambda: OpenAIAdapter(model),
        "azure":       lambda: AzureAdapter(model),
        "vendor-http": lambda: VendorHttpAdapter(),
        "output-only": lambda: OutputOnlyAdapter(input_file),
    }
    if adapter_name not in adapters:
        raise ValueError(
            f"Unknown adapter '{adapter_name}'. "
            f"Choose from: {', '.join(adapters.keys())}"
        )
    return adapters[adapter_name]()