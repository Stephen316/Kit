# Parallel merge-queue test shards

## Behavior

Each `Test suite / Shard (n)` job ran its tests in one serial pytest process.
The shard runner has 4 CPUs, so 3 CPUs stayed idle.
The first sharded queue run, [43371286350](https://github.com/TryUniCAD/Kit/actions/runs/43371286350), used 6 shards.
Their test steps took from 57 to 187 seconds.
After the plan finished, the shards waited 2.6 to 3.4 minutes for a runner.

The shard jobs now use every CPU of their runner:

1. `Test suite / Plan` puts at most 1,200 tests in each shard.
   This is 300 tests for each of the 4 CPUs.
   The current suite of about 1,700 tests uses 2 shards instead of 6.
2. The planner orders the tests of each shard for parallel dispatch.
   The slowest test is first, and the fastest test is second.
   The order then alternates between the slowest and the fastest remaining tests.
3. Each shard runs pytest-xdist with `--numprocesses logical --dist load --maxschedchunk 1`.
   One worker starts for each logical CPU.
   Each worker holds the test that runs and the next test.
   The controller sends a new test when a worker finishes one.
4. `uv sync --compile-bytecode` compiles the installed packages.
   A `compileall` step then compiles `src`, `tools`, and `tests` on all CPUs.
   The workers load the compiled files and do not each compile the same modules.
   The [queue build cache](QueueTestReuse.md) skips this step when it restores bytecode from `main`.
5. pytest runs with `-p no:cacheprovider` because the runner is discarded after the job.
6. The shard summary records the number of planned tests and the CPU count.

`pytest-reportlog` writes the report log only in the xdist controller.
The log contains the test reports of every worker, and each entry records its `worker_id`.
`Test suite / Report` verifies the logs with no change.
The plan collection also uses `-p no:cacheprovider`.

## Dispatch order

The xdist `load` scheduler starts each worker with consecutive tests from the collection order.
Without `--maxschedchunk`, the first chunk is a quarter of the worker's share.
For a 1,700-test shard on 4 workers, the first worker gets the first 106 tests.
With `--maxschedchunk 1`, each worker starts with 2 consecutive tests.
If the 2 slowest tests are adjacent, one worker runs both of them in sequence.
The alternating order puts a fast test after each slow test.
The [xdist chunk gotcha](../Gotchas/Ci/XdistLoadChunks.md) has the details.

## Runner choice

The TryUniCAD organization uses the GitHub Free plan.
Public repositories get 4-CPU standard runners at no cost.
The shards stay on `ubuntu-24.04`, which is the largest runner available to the organization.
The [Free-plan runner gotcha](../Gotchas/Ci/FreePlanRunners.md) describes the limits.

To move the shards to a larger runner, change `runs-on` of the `test-shard` job.
`--numprocesses logical` then uses all CPUs of that runner.
Set `--max-tests` in the plan step to 300 multiplied by the new CPU count.

## Expected effect

A scheduling model replayed the 1,719 measured durations from run 43371286350.
It uses the `load` scheduler with `--maxschedchunk 1` and 4 workers for each shard.
The model assumes that each worker runs at the speed of a single serial process.
It does not include runner wait, setup, or worker start time.
The values are model results, not measured runs.

| Shards | Order within each shard   | Slowest shard (s) |
| ------ | ------------------------- | ----------------- |
| 1      | Collection order          | 218.2             |
| 1      | Slowest first             | 184.2             |
| 1      | Alternating slow and fast | 145.8             |
| 2      | Collection order          | 163.9             |
| 2      | Alternating slow and fast | 145.8             |

With alternating order, the model reaches the 145.8-second lower limit that `CheckWheel` sets.
The queue requests 4 fewer shard jobs for each candidate.
Those jobs no longer compete for the 20 concurrent job slots of the Free plan.

## Limits

- `tests/convert/runtime/WheelRuntimeTests.py::CheckWheel` took 145.8 seconds in run 43371286350.
  It sets the lower limit for the slowest shard.
  More CPUs or more shards cannot make the test suite faster than that test.
- Each xdist worker collects all tests of its shard.
  The plan job collected the complete suite in 10 seconds.
- Module-scoped fixtures and `lru_cache` values exist once in each worker.
  The tests that use the 2 module-scoped fixtures took less than 1 millisecond each in run 43371286350.
- Parallel workers share a CPU, so the recorded durations can increase.
  The next plan uses those durations, and the shard count can change.
- Workers run in parallel processes in the same checkout.
  A search of `tests/` found no directory changes, fixed ports, or fixed output paths outside temporary directories.
  The first parallel merge-group run is the full check of that result.

## Usage

Plan shards for 4-CPU runners:

```sh
uv run python -m tools.TestShards.PlanShards --collected Collected.txt \
  --history TestDurations.json --max-tests 1200 --output ShardPlan.json
```

Run one shard with the xdist options of the queue.
The queue also loads the [dependency recorder](QueueTestReuse.md).

```sh
uv run pytest -p no:cacheprovider --numprocesses logical --dist load \
  --maxschedchunk 1 --report-log=ShardReport.jsonl @ShardTests.txt
```

## Verification

- Black, Ruff, Pyright, Mypy, full-repository steering, Zizmor, and Prettier passed locally on the changed files.
- No tests ran locally.
- [ShardPlanTests.py](../../tests/Policy/ShardPlanTests.py) runs each sample shard with the queue's xdist options and 2 workers.
  It checks that the report log contains reports from `gw0` and `gw1`.
  It also checks the alternating order of a planned shard.
  PR CI runs it in the workflow quality job.
  Both of its tests passed in [job 131717796021](https://github.com/TryUniCAD/Kit/actions/runs/43374527764/job/131717796021) on Python 3.11.
- The pytest 9.1.1 `normalize_collection_arguments` function keeps the argument order.
  The planned order therefore reaches xdist.
- The pytest-reportlog 1.0.0 `pytest_configure` hook registers the plugin only in the controller.
- `compileall` compiled every Python file in `src`, `tools`, and `tests` with Python 3.14 and exit code 0.
- The first live parallel run requires an authorized merge-group candidate.
