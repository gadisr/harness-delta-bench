"""Core comparison logic for harness delta benchmarking."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Run:
    """A single benchmark run."""
    
    model_id: str
    task_id: str
    harness_id: str
    metrics: dict[str, Any]
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Run":
        """Create Run from dictionary."""
        return cls(
            model_id=data["model_id"],
            task_id=data["task_id"],
            harness_id=data.get("harness_id") or data.get("policy_id", ""),
            metrics=data.get("metrics", {}),
        )


@dataclass
class Delta:
    """Delta between treatment and baseline for a single task."""
    
    task_id: str
    baseline_metrics: dict[str, Any]
    treatment_metrics: dict[str, Any]
    deltas: dict[str, float]
    
    def get_numeric_delta(self, metric: str) -> float | None:
        """Get numeric delta for a metric, handling booleans."""
        baseline_val = self.baseline_metrics.get(metric)
        treatment_val = self.treatment_metrics.get(metric)
        
        if baseline_val is None or treatment_val is None:
            return None
        
        if isinstance(baseline_val, bool):
            baseline_val = float(baseline_val)
        if isinstance(treatment_val, bool):
            treatment_val = float(treatment_val)
            
        try:
            return float(treatment_val) - float(baseline_val)
        except (TypeError, ValueError):
            return None


@dataclass
class ComparisonResult:
    """Result of comparing baseline and treatment runs."""
    
    model_id: str
    baseline_harness: str
    treatment_harness: str
    deltas: list[Delta]
    
    def aggregate_stats(self) -> dict[str, Any]:
        """Compute aggregate statistics across all deltas."""
        all_metric_names = set()
        for delta in self.deltas:
            all_metric_names.update(delta.deltas.keys())
        
        stats = {}
        for metric in sorted(all_metric_names):
            values = [d.deltas[metric] for d in self.deltas if metric in d.deltas]
            if not values:
                continue
                
            stats[metric] = {
                "mean_delta": sum(values) / len(values),
                "count": len(values),
            }
            
            wins = sum(1 for v in values if v > 0)
            losses = sum(1 for v in values if v < 0)
            ties = sum(1 for v in values if v == 0)
            
            stats[metric]["wins"] = wins
            stats[metric]["losses"] = losses
            stats[metric]["ties"] = ties
            
        return stats
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON output."""
        return {
            "model_id": self.model_id,
            "baseline_harness": self.baseline_harness,
            "treatment_harness": self.treatment_harness,
            "task_count": len(self.deltas),
            "per_task_deltas": [
                {
                    "task_id": d.task_id,
                    "baseline": d.baseline_metrics,
                    "treatment": d.treatment_metrics,
                    "deltas": d.deltas,
                }
                for d in self.deltas
            ],
            "aggregate": self.aggregate_stats(),
        }


def load_runs(path: Path) -> list[Run]:
    """Load runs from JSON file."""
    with open(path) as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return [Run.from_dict(item) for item in data]
    else:
        return [Run.from_dict(data)]


def compare_runs(
    baseline_runs: list[Run],
    treatment_runs: list[Run],
) -> ComparisonResult:
    """Compare baseline and treatment runs.
    
    Validates that:
    - All runs have the same model_id
    - All runs have consistent task_ids (can be paired)
    - Harness IDs differ between baseline and treatment
    
    Returns ComparisonResult with per-task deltas and aggregates.
    
    Raises:
        ValueError: If validation fails
    """
    if not baseline_runs or not treatment_runs:
        raise ValueError("Both baseline and treatment must have at least one run")
    
    baseline_model = baseline_runs[0].model_id
    treatment_model = treatment_runs[0].model_id
    
    if baseline_model != treatment_model:
        raise ValueError(
            f"Model mismatch: baseline={baseline_model}, treatment={treatment_model}. "
            "Cannot compare different models."
        )
    
    for run in baseline_runs:
        if run.model_id != baseline_model:
            raise ValueError(f"Inconsistent model_id in baseline: {run.model_id} != {baseline_model}")
    
    for run in treatment_runs:
        if run.model_id != treatment_model:
            raise ValueError(f"Inconsistent model_id in treatment: {run.model_id} != {treatment_model}")
    
    baseline_harness = baseline_runs[0].harness_id
    treatment_harness = treatment_runs[0].harness_id
    
    if baseline_harness == treatment_harness:
        raise ValueError(
            f"Harness IDs must differ (both are '{baseline_harness}'). "
            "This benchmark compares harness policies only."
        )
    
    baseline_by_task = {run.task_id: run for run in baseline_runs}
    treatment_by_task = {run.task_id: run for run in treatment_runs}
    
    common_tasks = set(baseline_by_task.keys()) & set(treatment_by_task.keys())
    if not common_tasks:
        raise ValueError("No common tasks found between baseline and treatment")
    
    baseline_only = set(baseline_by_task.keys()) - common_tasks
    treatment_only = set(treatment_by_task.keys()) - common_tasks
    
    if baseline_only or treatment_only:
        raise ValueError(
            f"Task mismatch: baseline_only={sorted(baseline_only)}, "
            f"treatment_only={sorted(treatment_only)}. "
            "All task_ids must match."
        )
    
    deltas = []
    for task_id in sorted(common_tasks):
        baseline_run = baseline_by_task[task_id]
        treatment_run = treatment_by_task[task_id]
        
        all_metrics = set(baseline_run.metrics.keys()) | set(treatment_run.metrics.keys())
        
        delta_dict = {}
        for metric in all_metrics:
            delta_obj = Delta(
                task_id=task_id,
                baseline_metrics=baseline_run.metrics,
                treatment_metrics=treatment_run.metrics,
                deltas={},
            )
            numeric_delta = delta_obj.get_numeric_delta(metric)
            if numeric_delta is not None:
                delta_dict[metric] = numeric_delta
        
        deltas.append(
            Delta(
                task_id=task_id,
                baseline_metrics=baseline_run.metrics,
                treatment_metrics=treatment_run.metrics,
                deltas=delta_dict,
            )
        )
    
    return ComparisonResult(
        model_id=baseline_model,
        baseline_harness=baseline_harness,
        treatment_harness=treatment_harness,
        deltas=deltas,
    )
