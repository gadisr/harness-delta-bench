"""Tests for harness_delta_bench.cli module."""

import json
import sys
from pathlib import Path

import pytest

from harness_delta_bench.cli import cmd_compare, main


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class Args:
    """Mock argparse.Namespace for testing."""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_cmd_compare_success(capsys):
    """Test successful comparison command."""
    args = Args(
        baseline=str(FIXTURES_DIR / "baseline.json"),
        treatment=str(FIXTURES_DIR / "treatment.json"),
        json=False,
    )
    
    exit_code = cmd_compare(args)
    
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "gpt-4" in captured.out
    assert "baseline-harness" in captured.out
    assert "improved-harness" in captured.out


def test_cmd_compare_json_output(capsys):
    """Test JSON output format."""
    args = Args(
        baseline=str(FIXTURES_DIR / "baseline.json"),
        treatment=str(FIXTURES_DIR / "treatment.json"),
        json=True,
    )
    
    exit_code = cmd_compare(args)
    
    assert exit_code == 0
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    
    assert result["model_id"] == "gpt-4"
    assert result["task_count"] == 3
    assert "aggregate" in result


def test_cmd_compare_model_mismatch(capsys):
    """Test that model mismatch returns exit code 2."""
    args = Args(
        baseline=str(FIXTURES_DIR / "baseline.json"),
        treatment=str(FIXTURES_DIR / "different_model.json"),
        json=False,
    )
    
    exit_code = cmd_compare(args)
    
    assert exit_code == 2
    captured = capsys.readouterr()
    assert "Model mismatch" in captured.err


def test_cmd_compare_file_not_found(capsys):
    """Test that missing file returns exit code 1."""
    args = Args(
        baseline=str(FIXTURES_DIR / "nonexistent.json"),
        treatment=str(FIXTURES_DIR / "treatment.json"),
        json=False,
    )
    
    exit_code = cmd_compare(args)
    
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err.lower()


def test_main_no_args(capsys):
    """Test main with no arguments shows help."""
    sys.argv = ["harness-delta-bench"]
    
    exit_code = main()
    
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "usage:" in captured.out.lower() or "usage:" in captured.err.lower()


def test_main_compare_command(capsys):
    """Test main with compare command."""
    sys.argv = [
        "harness-delta-bench",
        "compare",
        "--baseline", str(FIXTURES_DIR / "baseline.json"),
        "--treatment", str(FIXTURES_DIR / "treatment.json"),
    ]
    
    exit_code = main()
    
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "gpt-4" in captured.out
