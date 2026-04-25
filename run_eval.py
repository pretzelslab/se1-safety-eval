# run_eval.py
# Entry point for SE1 — LLM Safety Eval Framework.
# Usage:
#   python run_eval.py                                          # Claude (default)
#   python run_eval.py --adapter openai --model gpt-4o         # OpenAI
#   python run_eval.py --adapter azure                         # Azure OpenAI (creds from .env)
#   python run_eval.py --adapter vendor-http                   # Generic REST API
#   python run_eval.py --adapter output-only --input resp.csv  # No API — pre-collected responses

import argparse
import yaml
import time
from tqdm import tqdm
from rich.console import Console
from rich.table import Table
from rich import box

from src.adapters import get_adapter
from src.evaluator import evaluate
from src.reporter import generate_reports

console = Console()


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def print_summary(report: dict, elapsed: float, adapter_name: str, model: str):
    summary = report["summary"]

    console.print("\n")
    console.rule("[bold blue]SE1 -- LLM Safety Eval Complete[/bold blue]")
    console.print("\n")

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="dim", width=25)
    table.add_column("Value", justify="right")

    table.add_row("Adapter", adapter_name)
    table.add_row("Model under test", model)
    table.add_row("Total test cases", str(summary["total"]))
    table.add_row("Passed",    f"[green]{summary['passed']}[/green]")
    table.add_row("Failed",    f"[red]{summary['failed']}[/red]")
    table.add_row("Uncertain", f"[yellow]{summary['uncertain']}[/yellow]")
    table.add_row("Pass rate", f"[bold]{summary['pass_rate']}%[/bold]")
    table.add_row("Total tokens used", f"{summary['total_tokens']:,}")
    table.add_row("Time elapsed", f"{elapsed:.1f}s")

    console.print(table)

    if summary["failures_by_category"]:
        console.print("\n[bold red]Failures by category:[/bold red]")
        for cat, count in summary["failures_by_category"].items():
            console.print(f"  - {cat}: {count} failure(s)")

    if summary["failures_by_severity"]:
        console.print("\n[bold red]Failures by severity:[/bold red]")
        severity_order = ["critical", "high", "medium", "low"]
        for sev in severity_order:
            count = summary["failures_by_severity"].get(sev, 0)
            if count > 0:
                colour = {"critical": "red", "high": "orange3",
                        "medium": "yellow", "low": "green"}.get(sev, "white")
                console.print(f"  [{colour}]{sev.upper()}: {count}[/{colour}]")

    console.print(f"\nReports saved to:")
    console.print(f"  {report['json_report']}")
    console.print(f"  {report['markdown_report']}")
    console.print("\n")


def main():
    parser = argparse.ArgumentParser(
        description="SE1 -- LLM Safety Eval Framework for Financial Services"
    )
    parser.add_argument("--config",  default="finance_eval.yaml",
                        help="Path to YAML test suite (default: finance_eval.yaml)")
    parser.add_argument("--output",  default="reports",
                        help="Output directory for reports (default: reports/)")
    parser.add_argument("--model",   default=None,
                        help="Model ID to evaluate (default from YAML or claude-haiku-4-5-20251001)")
    parser.add_argument("--adapter", default="claude",
                        choices=["claude", "openai", "azure", "vendor-http", "output-only"],
                        help="Model adapter to use (default: claude)")
    parser.add_argument("--input",   default=None,
                          help="Path to pre-collected responses CSV/JSON (required for --adapter output-only)")
    args = parser.parse_args()

    console.print(f"\n[bold blue]Loading test suite:[/bold blue] {args.config}")
    config = load_config(args.config)

    metadata   = config.get("metadata", {})
    test_cases = config.get("test_cases", [])
    system_prompt = metadata.get("system_prompt", "You are a helpful banking assistant.")
    model = args.model or metadata.get("model_target", "claude-haiku-4-5-20251001")

    console.print(f"[bold blue]Adapter:[/bold blue]          {args.adapter}")
    console.print(f"[bold blue]Model under test:[/bold blue] {model}")
    console.print(f"[bold blue]Test cases loaded:[/bold blue] {len(test_cases)}")
    console.print(f"[bold blue]Output directory:[/bold blue] {args.output}\n")

    # Build the adapter — this is the only line that knows which API we're talking to
    adapter = get_adapter(args.adapter, model, input_file=args.input)

    results = []
    start_time = time.time()
    console.print("[bold]Running evaluations...[/bold]\n")

    for test_case in tqdm(test_cases, desc="Evaluating", unit="test"):
        # Call the model (or read pre-collected response)
        adapter_result = adapter.call(test_case["prompt"], system_prompt)

        # Merge adapter result into the test case dict — same shape as before
        result = {**test_case, **adapter_result, "_system_prompt": system_prompt}

        # Judge always runs on Claude — model under test ≠ judge model
        evaluated = evaluate(result, judge_model="claude-haiku-4-5-20251001")
        results.append(evaluated)
        time.sleep(0.3)

    elapsed = time.time() - start_time

    console.print("\n[bold]Generating reports...[/bold]")
    report = generate_reports(results, args.output, model)
    print_summary(report, elapsed, args.adapter, model)


if __name__ == "__main__":
    main()