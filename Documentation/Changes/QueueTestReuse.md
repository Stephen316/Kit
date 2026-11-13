# Merge-queue test reuse and build cache

## Behavior

The merge queue no longer runs a test module again when nothing that the module used has changed.
It reuses the passing result that an accepted ancestor candidate recorded for that module.
The queue jobs also restore the Python install, the uv cache, and the compiled bytecode from `main`.

### Dependency recording

Each `Test suite / Shard (n)` job loads the `tools.TestShards.Reuse.Track.TrackHooks` pytest plugin.
The `--test-deps` option enables the plugin and names the output folder.
The plugin records these items for each test module during collection and during each test:

- Each repository module that an `import` statement or `importlib.import_module` call gives.
  This includes modules that an earlier test in the same worker already loaded.
- Each repository file that the code opens for reading.
- Each repository folder that the code lists.
- Each process start, for example `subprocess.Popen`, `os.system`, `os.fork`, or an `exec` or `spawn` function.

The plugin also records which repository file did each import, read, listing, or process start.
It ignores the folder scans of the Python import system.
Each xdist worker writes `Deps-<worker>.json` next to the shard report log.

### Cache records

`Test suite / Report` runs `tools.TestShards.Reuse.Cache.BuildCache` after the completeness check passes.
It uses only modules whose tests all passed or were skipped.
For each module, it follows the recorded links from the test file, the files that the module used, and its `conftest.py` files.
The result is the set of files and folders that can change the module's result.

`BuildCache` does not record a module in these conditions:

- The module or a linked file started a process.
- The module used a file or folder that git does not track.
- A test of the module failed or did not run.

`BuildCache` writes no cache in these conditions:

- A worker that ran tests did not write its `Deps-<worker>.json` file.
- The plugin could not record an import, read, listing, or process start in a worker.
  The plugin counts each such error and does not stop the test.
- The workers ran different Python versions.

For each recorded module, the cache stores the git blob ID of each file.
It also stores a SHA-256 digest of the tracked entry names of each listed folder.
The cache stores a guard with the Python version and the blob IDs of these files:

- `pyproject.toml`, `uv.lock`, `pytest.ini`, `setup.cfg`, and `tox.ini`
- Every `conftest.py` file
- Every file in `tools/TestShards/`
- `.github/workflows/MergeQueue.yml`

The report publishes the cache as the `TestCache` artifact for 8 days.
It publishes the artifact only when every shard and the completeness check succeeded.

### Reuse in the plan

`Test suite / Plan` looks for the newest usable `TestCache` artifact:

1. It lists at most 20 unexpired artifacts from same-repository runs on `gh-readonly-queue/` refs.
2. It accepts a run only if the run is a `merge_group` run of `.github/workflows/MergeQueue.yml`.
3. It accepts a run only if the compare API reports the candidate as `ahead` of the run's head commit or `identical` to it.

The plan reuses the results of a test module only when all of these conditions are true:

- The guard is equal to the guard of the candidate.
- Every collected test of the module has a stored `passed` or `skipped` result.
- Every stored blob ID and folder digest is equal to the candidate's value.
- The record is at most 7 days old.

The plan puts all other collected tests into shards.
If every collected test can reuse a result, the plan runs every test.
The shard matrix needs at least one test.
The plan writes the reused records to `Carried.json` in the `ShardPlan` artifact.
The report copies those records into the next cache with their original age.

`Test suite / Report` checks that the planned and reused tests together equal the collected tests.
It also checks that no test is both planned and reused, and that each reused result passed or was skipped.
The report summary states the number of reused tests and the run that verified them.
`TestDurations` keeps the last measured duration of each reused test.

A failure in the cache fetch step or in `BuildCache` does not fail the queue.
The next plan then runs every test.

### Build cache

The `Queue cache` workflow runs for each push to `main`.
It installs the locked dev environment with Python 3.14.
It compiles `src`, `tools`, and `tests` with `--invalidation-mode checked-hash`.
It saves the bytecode as the `queue-bytecode-<commit>` cache.
`astral-sh/setup-uv` saves the uv cache and the managed Python install with the `queue-python-3.14` suffix.

The queue plan, shard, and report jobs use the same setup-uv suffix and `cache-python: true`.
The plan and shard jobs restore the bytecode of the candidate's base commit, or else the newest bytecode from `main`.
The shard job skips its `compileall` step when it restores bytecode.
Python checks the source hash of each restored file and compiles the changed files again.

## Usage

Record the dependencies of a test run:

```sh
uv run python -m pytest -p tools.TestShards.Reuse.Track.TrackHooks \
  --test-deps=Reports/1 --report-log=Reports/1/ShardReport.jsonl tests/Policy
```

Build a cache from the plan and the shard reports:

```sh
git ls-tree -r -z HEAD > Tree.bin
uv run python -m tools.TestShards.Reuse.Cache.BuildCache --plan ShardPlan.json \
  --carried Carried.json --reports Reports --tree Tree.bin --run 1 --output TestCache.json
```

Plan with reuse:

```sh
uv run python -m tools.TestShards.PlanShards --collected Collected.txt \
  --cache TestCache.json --tree Tree.bin --carried Carried.json \
  --max-age-days 7 --max-tests 1200 --output ShardPlan.json
```

To stop reuse, remove the `--cache` argument from the `Plan test shards` step.

## Limits

- Reuse works on whole test modules.
  A change to one file runs every test in each module that can reach that file.
- A package `__init__.py` that imports many modules links all of them to each test that imports the package.
  Most `convert` tests import `convert`, so a change to most `convert` sources runs most `convert` tests.
- Modules that start a process never reuse results.
  `tests/convert/runtime/WheelRuntimeTests.py::CheckWheel` is one of them and still sets the shortest test path.
- The plugin does not see `os.stat` and existence checks, environment variables, network access, the time, or files that native code reads.
  A test that depends on these items can reuse an old result until the record is 7 days old or the guard changes.
- The guard does not include the runner image.
- Code in a background thread counts for the module that runs at that time.
- A candidate can use only results that an ancestor recorded.
  A new candidate cannot use the results of a candidate that is still running.
- Each import statement and each file read, listing, or process start calls the plugin once.

## Verification

- Black, Ruff, Pyright, Mypy, full-repository steering, explicit imports, Zizmor, and Prettier passed locally on the changed files.
- No tests ran locally.
- [ShardPlanTests.py](../../tests/Policy/ShardPlanTests.py) `TestShardReuse` runs the complete flow in a temporary git repository.
  It runs a sample suite with the plugin on 2 xdist workers and builds a cache.
  It then changes a helper module and adds a file to a listed folder.
  The next plan reuses only the modules that did not use either change.
  A third plan reuses every module except the module that starts a process.
  PR CI runs it in the workflow quality job.
  It passed on Python 3.11 in [job 131741615869](https://github.com/TryUniCAD/Kit/actions/runs/43381981299/job/131741615869).
- The first live reuse requires an authorized merge-group candidate after the `Queue cache` workflow ran on `main`.

See the [cache scope gotcha](../Gotchas/Ci/QueueCacheScope.md), the [import cache gotcha](../Gotchas/Ci/ImportCacheDependencies.md), the [bytecode timestamp gotcha](../Gotchas/Ci/CheckoutBytecodeTimestamps.md), and the [setup-uv cache gotcha](../Gotchas/Ci/SetupUvQueueCache.md).
