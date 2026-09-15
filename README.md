# harness-delta-bench

**Benchmark harness policies, not models.** Hold model and task constant, swap only the harness (policy, orchestration, environment), and measure outcome deltas. Answers the core question: did this harness change help or hurt?

## Use Cases

### 1. SWE-bench harness A vs B

You're developing a new SWE-bench evaluation harness with improved sandboxing. Does it change pass rates compared to the baseline harness when running the same model on the same tasks?

**Example baseline run** (`baseline.json`):

```json
[
  {
    "model_id": "gpt-4-turbo",
    "task_id": "django/django-11333",
    "harness_id": "swe-bench-baseline-v1",
    "metrics": {
      "pass": true,
      "score": 0.95,
      "cost_usd": 0.12
    }
  },
  {
    "model_id": "gpt-4-turbo",
    "task_id": "django/django-11422",
    "harness_id": "swe-bench-baseline-v1",
    "metrics": {
      "pass": false,
      "score": 0.45,
      "cost_usd": 0.08
    }
  }
]
```

**Example treatment run** (`treatment.json`):

```json
[
  {
    "model_id": "gpt-4-turbo",
    "task_id": "django/django-11333",
    "harness_id": "swe-bench-improved-sandbox",
    "metrics": {
      "pass": true,
      "score": 0.98,
      "cost_usd": 0.11
    }
  },
  {
    "model_id": "gpt-4-turbo",
    "task_id": "django/django-11422",
    "harness_id": "swe-bench-improved-sandbox",
    "metrics": {
      "pass": true,
      "score": 0.72,
      "cost_usd": 0.09
    }
  }
]
```

**Compare:**

```bash
harness-delta-bench compare --baseline baseline.json --treatment treatment.json
```

**Output:**

```
Model: gpt-4-turbo
Baseline harness: swe-bench-baseline-v1
Treatment harness: swe-bench-improved-sandbox
Tasks compared: 2

Aggregate statistics (treatment - baseline):

  pass:
    Mean delta: +0.5000
    Wins/Ties/Losses: 1/1/0
  score:
    Mean delta: +0.1500
    Wins/Ties/Losses: 2/0/0

Per-task deltas:
  django/django-11333:
    pass: +0.0000
    score: +0.0300
  django/django-11422:
    pass: +1.0000
    score: +0.2700
```

### 2. Meta-harness policy evolution

You maintain a meta-agent harness (retry budgets, tool policies, context limits). Compare two policy versions to see if the new one improves outcomes without changing the underlying model.

**Commands:**

```bash
# Human-readable summary
harness-delta-bench compare --baseline policy-v1.json --treatment policy-v2.json

# Machine-readable JSON for CI dashboards
harness-delta-bench compare \
  --baseline policy-v1.json \
  --treatment policy-v2.json \
  --json > delta-report.json
```

### 3. CI scoreboard harness regression detection

Your CI runs benchmarks with evolving harness code. Did a recent harness commit accidentally break pass rates?

```bash
# Compare last known good vs current
harness-delta-bench compare \
  --baseline runs-commit-abc123.json \
  --treatment runs-commit-def456.json
```

If deltas show unexpected losses, investigate the harness change—not the model.

## Installation

```bash
# From source (editable install)
git clone https://github.com/yourusername/harness-delta-bench.git
cd harness-delta-bench
pip install -e .

# Or directly from git
pip install git+https://github.com/yourusername/harness-delta-bench.git
```

**Requirements:** Python 3.11+, stdlib only (no external dependencies)

## CLI Reference

### `compare`

Compare baseline and treatment runs with fixed model and task IDs.

```bash
harness-delta-bench compare --baseline <path> --treatment <path> [--json]
```

**Arguments:**

- `--baseline`: Path to baseline runs JSON file (required)
- `--treatment`: Path to treatment runs JSON file (required)
- `--json`: Output results as JSON instead of human-readable text (optional)

**JSON Schema:**

Each input file must be a JSON array of runs:

```json
[
  {
    "model_id": "<model-identifier>",
    "task_id": "<task-identifier>",
    "harness_id": "<harness-identifier>",  // or "policy_id"
    "metrics": {
      "pass": true,              // boolean or numeric
      "score": 0.95,             // any numeric metric
      "custom_metric": 123.45    // arbitrary metrics supported
    }
  }
]
```

**Validations:**

- `model_id` must match across all baseline and treatment runs (exit code 2 if mismatch)
- `task_id` sets must match exactly between baseline and treatment (exit code 2 if mismatch)
- `harness_id` (or `policy_id`) must differ between baseline and treatment (exit code 2 if same)

**Exit Codes:**

- `0`: Success
- `1`: File not found, invalid JSON, or other error
- `2`: Validation failure (model mismatch, task mismatch, or same harness)

## Example Workflow

```bash
# 1. Install
pip install -e .

# 2. Run comparison
harness-delta-bench compare \
  --baseline tests/fixtures/baseline.json \
  --treatment tests/fixtures/treatment.json

# 3. Get JSON for further analysis
harness-delta-bench compare \
  --baseline tests/fixtures/baseline.json \
  --treatment tests/fixtures/treatment.json \
  --json | jq '.aggregate'
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=harness_delta_bench

# Test CLI directly
python -m harness_delta_bench compare --baseline a.json --treatment b.json
```

## With failstrata

`harness-delta-bench` can analyze failstrata policy evolution: hold model and task constant, compare orchestration outcomes across failstrata harness versions.

## License

MIT - see [LICENSE](LICENSE) for details.
