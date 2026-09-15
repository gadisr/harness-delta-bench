"""Tests for harness_delta_bench.compare module."""

import json
from pathlib import Path

import pytest

from harness_delta_bench.compare import Run, compare_runs, load_runs


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_load_runs():
    """Test loading runs from JSON file."""
    runs = load_runs(FIXTURES_DIR / "baseline.json")
    assert len(runs) == 3
    assert all(run.model_id == "gpt-4" for run in runs)
    assert runs[0].task_id == "swe-bench-1"
    assert runs[0].harness_id == "baseline-harness"


def test_valid_comparison():
    """Test valid comparison between baseline and treatment."""
    baseline = load_runs(FIXTURES_DIR / "baseline.json")
    treatment = load_runs(FIXTURES_DIR / "treatment.json")
    
    result = compare_runs(baseline, treatment)
    
    assert result.model_id == "gpt-4"
    assert result.baseline_harness == "baseline-harness"
    assert result.treatment_harness == "improved-harness"
    assert len(result.deltas) == 3
    
    task_1_delta = next(d for d in result.deltas if d.task_id == "swe-bench-1")
    assert task_1_delta.deltas["pass"] == 0.0
    assert task_1_delta.deltas["score"] == pytest.approx(0.03)
    assert task_1_delta.deltas["latency_ms"] == pytest.approx(-134.0)
    
    task_2_delta = next(d for d in result.deltas if d.task_id == "swe-bench-2")
    assert task_2_delta.deltas["pass"] == 1.0
    assert task_2_delta.deltas["score"] == pytest.approx(0.27)


def test_aggregate_statistics():
    """Test aggregate statistics calculation."""
    baseline = load_runs(FIXTURES_DIR / "baseline.json")
    treatment = load_runs(FIXTURES_DIR / "treatment.json")
    
    result = compare_runs(baseline, treatment)
    stats = result.aggregate_stats()
    
    assert "pass" in stats
    assert "score" in stats
    
    pass_stats = stats["pass"]
    assert pass_stats["wins"] == 1
    assert pass_stats["ties"] == 2
    assert pass_stats["losses"] == 0
    
    score_stats = stats["score"]
    assert score_stats["count"] == 3
    assert score_stats["mean_delta"] > 0


def test_model_mismatch_refuses():
    """Test that model mismatch is rejected with exit code 2."""
    baseline = load_runs(FIXTURES_DIR / "baseline.json")
    different_model = load_runs(FIXTURES_DIR / "different_model.json")
    
    with pytest.raises(ValueError, match="Model mismatch"):
        compare_runs(baseline, different_model)


def test_task_mismatch_refuses():
    """Test that task mismatch is rejected."""
    baseline = load_runs(FIXTURES_DIR / "baseline.json")
    different_task = load_runs(FIXTURES_DIR / "different_task.json")
    
    with pytest.raises(ValueError, match="No common tasks|Task mismatch"):
        compare_runs(baseline, different_task)


def test_same_harness_refuses():
    """Test that same harness IDs are rejected."""
    same_harness = load_runs(FIXTURES_DIR / "same_harness.json")
    
    with pytest.raises(ValueError, match="Harness IDs must differ"):
        compare_runs(same_harness, same_harness)


def test_empty_runs_refuses():
    """Test that empty run lists are rejected."""
    baseline = load_runs(FIXTURES_DIR / "baseline.json")
    
    with pytest.raises(ValueError, match="at least one run"):
        compare_runs([], baseline)
    
    with pytest.raises(ValueError, match="at least one run"):
        compare_runs(baseline, [])


def test_to_dict_serialization():
    """Test JSON serialization of results."""
    baseline = load_runs(FIXTURES_DIR / "baseline.json")
    treatment = load_runs(FIXTURES_DIR / "treatment.json")
    
    result = compare_runs(baseline, treatment)
    result_dict = result.to_dict()
    
    assert result_dict["model_id"] == "gpt-4"
    assert result_dict["task_count"] == 3
    assert "per_task_deltas" in result_dict
    assert "aggregate" in result_dict
    
    json_str = json.dumps(result_dict)
    assert json_str


def test_policy_id_alias():
    """Test that policy_id is accepted as alias for harness_id."""
    run_data = {
        "model_id": "gpt-4",
        "task_id": "test-task",
        "policy_id": "test-policy",
        "metrics": {"pass": True}
    }
    
    run = Run.from_dict(run_data)
    assert run.harness_id == "test-policy"


def test_boolean_to_numeric_conversion():
    """Test that boolean pass values are converted to numeric deltas."""
    baseline = [Run(
        model_id="gpt-4",
        task_id="task-1",
        harness_id="baseline",
        metrics={"pass": False}
    )]
    treatment = [Run(
        model_id="gpt-4",
        task_id="task-1",
        harness_id="treatment",
        metrics={"pass": True}
    )]
    
    result = compare_runs(baseline, treatment)
    assert result.deltas[0].deltas["pass"] == 1.0
