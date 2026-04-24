# run_eval.py
# The main entry point for SE1 -- LLM Safety Eval Framework.
# Run this from the terminal: python run_eval.py
# Optional flags:
#   --config   path to YAML test suite (default: finance_eval.yaml)
#   --output   path to reports folder  (default: reports/)
#   --model    Claude model ID         (default: claude-haiku-4-5-20251001)

import argparse
import yaml
import time
from tqdm import tqdm
from rich.console import Console
from rich.table import Table
from rich import box

from src.eval_engine import run_single_eval
from src.evaluator import evaluate
from src.reporter import generate_reports

console = Console()


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def print_summary(report: dict, elapsed: float):
    summary = report["summary"]

    console.print("\n")
    console.rule("[bold blue]SE1 -- LLM Safety Eval Complete[/bold blue]")
    console.print("\n")

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="dim", width=25)
    table.add_column("Value", justify="right")

    table.add_row("Total test cases", str(summary["total"]))
    table.add_row("Passed", f"[green]{summary['passed']}[/green]")
    table.add_row("Failed", f"[red]{summary['failed']}[/red]")
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
    parser.add_argument(
        "--config",
        default="finance_eval.yaml",
        help="Path to YAML test suite (default: finance_eval.yaml)"
    )
    parser.add_argument(
        "--output",
        default="reports",
        help="Output directory for reports (default: reports/)"
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Claude model ID to evaluate (overrides YAML default)"
    )
    args = parser.parse_args()

    console.print(f"\n[bold blue]Loading test suite:[/bold blue] {args.config}")
    config = load_config(args.config)

    metadata = config.get("metadata", {})
    test_cases = config.get("test_cases", [])
    system_prompt = metadata.get("system_prompt", "You are a helpful banking assistant.")

    model = args.model or metadata.get("model_target", "claude-haiku-4-5-20251001")

    console.print(f"[bold blue]Model under evaluation:[/bold blue] {model}")
    console.print(f"[bold blue]Test cases loaded:[/bold blue] {len(test_cases)}")
    console.print(f"[bold blue]Output directory:[/bold blue] {args.output}\n")

    results = []
    start_time = time.time()

    console.print("[bold]Running evaluations...[/bold]\n")

    for test_case in tqdm(test_cases, desc="Evaluating", unit="test"):
        test_case["_system_prompt"] = system_prompt
        result = run_single_eval(test_case, model)
        evaluated = evaluate(result, judge_model=model)
        results.append(evaluated)
        time.sleep(0.3)

    elapsed = time.time() - start_time

    console.print("\n[bold]Generating reports...[/bold]")
    report = generate_reports(results, args.output, model)

    print_summary(report, elapsed)


if __name__ == "__main__":
    main()