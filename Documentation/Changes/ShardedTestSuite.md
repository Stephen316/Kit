# Sharded merge-queue test suite

## Behavior

The merge queue previously ran the complete pytest suite in one serial job.
That job was the longest queue job.
It took about nine minutes, and CodeQL for Python took about five minutes.

The queue now plans shards when it runs.
It does not use a fixed shard list.

1. `Test suite / Plan` collects the candidate with `pytest --collect-only -q`.
   It sets the shard count to the collected count divided by 300, rounded up.
2. The planner assigns the slowest tests first.
   Each test goes to the shard with the lowest estimated load that has fewer than 300 tests.
   Each shard keeps the collection order of its tests.
3. `Test suite / Shard (n)` runs its node IDs through a pytest argument file.
   It writes a `pytest-reportlog` record of every test phase.
4. `Test suite / Report` merges the shard records.
   It fails when a planned test did not run, ran more than once, or was not planned.
   It also fails when a shard record is missing or incomplete.

`Merge queue acceptance` requires the plan, every shard, and the report.
It also requires `Run the complete test suite`.
That compatibility job succeeds only when the plan, every shard, and the report succeed.
The merge-group `CI Agg` loads its allowlist from the trusted base commit.
The base before this change requires `Run the complete test suite`, so the first sharded candidate needs that check.
To remove the job, first make the name optional in the allowlist, then remove the job in a later PR.
`CI Agg` requires the plan and the report by name.
It matches `Test suite / Shard (n)` checks by pattern.
On pull requests, GitHub reports the skipped shard job with its expression text.
The allowlist defers that name with the other heavy jobs.

## Duration history

The report job publishes `TestDurations` for 30 days.
The next plan downloads the newest unexpired copy from a same-repository merge-group run.
The planner uses the median recorded duration for a new test.
Without history, every test has the same weight, and the shards are balanced by count.
History changes only the assignment.
It cannot remove a collected test from the plan.

## Usage

Run the planner and the verifier as modules:

```sh
uv run python -m tools.TestShards.PlanShards --collected Collected.txt \
  --history TestDurations.json --max-tests 300 --output ShardPlan.json
uv run python -m tools.TestShards.MergeReports --plan ShardPlan.json \
  --reports ShardReports --output TestDurations.json
```

Change the limit with `--max-tests` in [MergeQueue.yml](../../.github/workflows/MergeQueue.yml).
GitHub limits one matrix to 256 jobs.

## Limits

- Each shard repeats checkout, environment synchronization, and module-scoped fixture setup.
- The slowest single test sets the lower limit for the slowest shard.
  The wheel runtime test took about 106 seconds in the last observed run.
- A node ID that pytest cannot select again fails its shard with `not found`.
- The first plan after this change has no history and balances by count.
- Shard report and plan artifacts are kept for seven days.

## Verification

- Queue run [43166611149](https://github.com/TryUniCAD/Kit/actions/runs/43166611149) collected 1689 tests and passed in 467 seconds.
- Queue run [43329927160](https://github.com/TryUniCAD/Kit/actions/runs/43329927160) collected 1673 tests in a 514-second test step.
  Its test job was the longest job in the run.
- Log timestamps in run 43166611149 put `SwapsTests.py` at about 117 seconds and `WheelRuntimeTests.py` at about 106 seconds.
- A synthetic 1673-test plan with that duration shape gave six shards.
  The largest estimate was 107 seconds.
- Black, Ruff, Pyright, Mypy, steering, Zizmor, and Prettier passed locally on the changed files.
- No tests ran locally.
- Pedantic Zizmor fails with exit code 12 when the `actions: read` permission has no comment.
  The comment on that permission stays for this reason.
- [ShardPlanTests.py](../../tests/Policy/ShardPlanTests.py) runs real pytest collection, planning, shard runs, and verification as separate processes.
  PR CI runs it in the workflow quality job.
- [QueueAggregationTests.py](../../tests/Policy/QueueAggregationTests.py) checks that a failed plan, shard, or report fails `CI Agg`.
- The first live sharded run requires an authorized merge-group candidate.
