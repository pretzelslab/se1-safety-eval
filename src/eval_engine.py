# eval_engine.py
import time
import anthropic
from dotenv import load_dotenv

load_dotenv()


def run_single_eval(test_case: dict, model: str, max_retries: int = 3) -> dict:
    client = anthropic.Anthropic()
    system_prompt = test_case.get("_system_prompt", "You are a helpful banking assistant.")

    attempt = 0
    while attempt < max_retries:
        try:
            response = client.messages.create(
                model=model,
                max_tokens=512,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": test_case["prompt"]}
                ]
            )
            response_text = response.content[0].text
            return {
                **test_case,
                "response": response_text,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "error": None
            }
        except anthropic.RateLimitError:
            wait_time = 2 ** attempt
            time.sleep(wait_time)
            attempt += 1
        except anthropic.APIError as e:
            return {
                **test_case,
                "response": None,
                "input_tokens": 0,
                "output_tokens": 0,
                "error": str(e)
            }

    return {
        **test_case,
        "response": None,
        "input_tokens": 0,
        "output_tokens": 0,
        "error": "Max retries exceeded"
    }


def run_all_evals(test_cases: list, model: str, system_prompt: str) -> list:
    results = []
    for test_case in test_cases:
        test_case["_system_prompt"] = system_prompt
        result = run_single_eval(test_case, model)
        results.append(result)
        time.sleep(0.5)
    return results