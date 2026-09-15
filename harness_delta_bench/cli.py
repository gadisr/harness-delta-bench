"""Command-line interface for harness-delta-bench."""

import argparse
import json
import sys
from pathlib import Path

from .compare import compare_runs, load_runs


def format_human_readable(result) -> str:
    """Format comparison result as human-readable text."""
    lines = []
    lines.append(f"Model: {result.model_id}")
    lines.append(f"Baseline harness: {result.baseline_harness}")
    lines.append(f"Treatment harness: {result.treatment_harness}")
    lines.append(f"Tasks compared: {len(result.deltas)}")
    lines.append("")
    
    stats = result.aggregate_stats()
    if stats:
        lines.append("Aggregate statistics (treatment - baseline):")
        lines.append("")
        for metric, data in sorted(stats.items()):
            lines.append(f"  {metric}:")
            lines.append(f"    Mean delta: {data['mean_delta']:+.4f}")
            lines.append(f"    Wins/Ties/Losses: {data['wins']}/{data['ties']}/{data['losses']}")
        lines.append("")
    
    lines.append("Per-task deltas:")
    for delta in result.deltas:
        lines.append(f"  {delta.task_id}:")
        for metric, value in sorted(delta.deltas.items()):
            lines.append(f"    {metric}: {value:+.4f}")
    
    return "\n".join(lines)


def cmd_compare(args: argparse.Namespace) -> int:
    """Handle 'compare' command."""
    try:
        baseline_runs = load_runs(Path(args.baseline))
        treatment_runs = load_runs(Path(args.treatment))
        
        result = compare_runs(baseline_runs, treatment_runs)
        
        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print(format_human_readable(result))
        
        return 0
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except FileNotFoundError as e:
        print(f"Error: File not found: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="harness-delta-bench",
        description="Compare benchmark results with fixed model+task, varying harness policy.",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    compare_parser = subparsers.add_parser(
        "compare",
        help="Compare baseline and treatment runs",
    )
    compare_parser.add_argument(
        "--baseline",
        required=True,
        help="Path to baseline runs JSON file",
    )
    compare_parser.add_argument(
        "--treatment",
        required=True,
        help="Path to treatment runs JSON file",
    )
    compare_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    
    args = parser.parse_args()
    
    if args.command == "compare":
        return cmd_compare(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
