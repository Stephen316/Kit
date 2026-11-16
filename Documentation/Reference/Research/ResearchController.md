# Durable research controller

## Purpose and scope

A03 adds a local evidence store and job controller under `re/automation/`.
It persists jobs across command processes, tracks exact prerequisites and fences stale worker results.
All work and current-step progress belong on [PR #94](https://github.com/TryUniCAD/Kit/pull/94).

The controller does not launch workers, run shell commands, call models or decode CAD files.
Later steps connect readers, comparison and investigation workers to this protocol.
Production conversion must not import this research code.
A02's missing native captures do not block this A03 metadata work.

## Store design

The store contains `ledger.sqlite3` and immutable files under `objects/<prefix>/<sha256>`.
SQLite owns job metadata, bindings, attempts, resources and an append-only event history.
Each command uses a parameterized, explicit write transaction.
Concurrent controller requests serialize through SQLite; workers return results through the controller commands instead of writing database tables.
See [SQLite transaction behavior](https://www.sqlite.org/lang_transaction.html).

This implementation selects SQLite's rollback journal and `synchronous=FULL`.
Objects are staged, flushed and published through an exclusive hard link before metadata refers to them.
Existing objects are verified and never overwritten silently.
Job definitions, input snapshots, execution receipts and worker result records have independent content hashes.
Hashes detect changes relative to the selected bytes; they do not authenticate the author or prove CAD correctness.

Use a private directory on one local filesystem with SQLite locking and hard-link support.
The initial remote verification target is Linux.
Windows and macOS process behavior still need independent compatibility evidence.
This is not a network service or a multi-host database protocol.
Back up a quiescent store together with its objects; copying a live database file alone is not a declared backup procedure.

## Job contract

Each submitted record must contain these fields:

| Field          | Meaning                                                                                          |
| -------------- | ------------------------------------------------------------------------------------------------ |
| `id`           | Stable job label; submitting changed content updates that job's definition                       |
| `kind`         | Worker operation identifier; the controller does not execute this string                         |
| `inputs`       | Object mapping semantic roles to named evidence bindings or accepted dependency output selectors |
| `rule_version` | Explicit rule version; actual integrations must use an immutable version identifier              |
| `tool_version` | Explicit worker build/version identifier                                                         |

Optional fields are `depends_on`, `resources`, `options`, `max_attempts`, `lease_seconds`, `timeout_seconds` and `retry_base_seconds`.
Unknown top-level fields are rejected.
Dependencies and resources are arrays of labels; `options` is a JSON object.
An input selector identifies a job in `depends_on` and can select its accepted result or a named artifact.
The controller resolves the full input set in the same snapshot transaction that checks the dependencies.
Use [a candidate fingerprint selector](../../Changes/Research/Controller/PendingCandidateDependencies.md) for research jobs that can run while a selected candidate is awaiting CI.
See [accepted dependency inputs](../../Changes/Research/Controller/DependencyOutputInputs.md) for the syntax and the Phase B example.
Forward dependencies are allowed, but cycles roll back the submission.
Use `submit-batch <file>` with a JSON object containing only `jobs`, an array of job records, to submit a group atomically.
Duplicate identifiers within a batch are rejected.
The same record-size and store limits apply; split large catalogues into bounded batches.

| Limit                                          | Value                                                           |
| ---------------------------------------------- | --------------------------------------------------------------- |
| Label                                          | 1–128 ASCII identifier characters                               |
| JSON record                                    | 1 MiB                                                           |
| Normalized job definition                      | 64 KiB                                                          |
| Input roles, dependencies or resources per job | 64 each                                                         |
| Named artifact                                 | 256 MiB                                                         |
| Stored jobs                                    | 10,000                                                          |
| Aggregate job-definition text                  | 16 MiB                                                          |
| Concurrent running jobs                        | Initialized once, default 4, maximum 64                         |
| Attempts per prerequisite generation           | Default 3, maximum 20                                           |
| Lease                                          | Default 60 seconds, range 1–3,600 seconds                       |
| Execution deadline                             | Default 300 seconds, range 1–86,400 seconds                     |
| Retry delay                                    | Default base 1 second; exponential growth capped at 300 seconds |
| Reason                                         | 1–2,048 characters                                              |

Metadata limits bound accepted records and collections.
They are not a memory limit for an external worker process.

## Commands

Use Python 3.11 or later with standard-library SQLite support.
No package installation, CAD installation, model credential or network connection is required for controller operation.
The remote controller process checks use Python 3.14.
Choose an existing private parent directory on a persistent local disk for real research.
The `/tmp/KitResearchState` path below is an example and can be removed by operating-system cleanup.

1. Initialize a store:

   ```shell
   python3 re/automation/Controller.py --store /tmp/KitResearchState init --max-running 2
   ```

2. Bind the existing recipe bytes as evidence:

   ```shell
   python3 re/automation/Controller.py --store /tmp/KitResearchState bind recipe:initial re/automation/PairSpecs.json
   ```

3. Save this illustrative request as `/tmp/KitResearchJob.json`:

   ```json
   {
     "id": "request:paired-captures",
     "kind": "research.capture-request",
     "inputs": { "recipe": "recipe:initial" },
     "rule_version": "paired-recipes@1",
     "tool_version": "manual-evidence-request@1",
     "max_attempts": 3,
     "lease_seconds": 60,
     "timeout_seconds": 300
   }
   ```

4. Submit and claim the request using an unused claim-file path:

   ```shell
   python3 re/automation/Controller.py --store /tmp/KitResearchState submit /tmp/KitResearchJob.json
   python3 re/automation/Controller.py --store /tmp/KitResearchState claim --worker operator:research --claim-file /tmp/KitResearchClaim.json
   ```

5. Renew the lease during actual work, or park this illustrative request while captures are missing:

   ```shell
   python3 re/automation/Controller.py --store /tmp/KitResearchState heartbeat --lease /tmp/KitResearchClaim.json
   python3 re/automation/Controller.py --store /tmp/KitResearchState finish --lease /tmp/KitResearchClaim.json --result re/automation/PairSpecs.json --outcome waiting_evidence --reason "independent native captures required"
   ```

   This records a request and its evidence, not a successful CAD experiment.
   A03 does not supply an authoring worker for `research.capture-request`.

6. Inspect jobs, events or a verified artifact:

   ```shell
   python3 re/automation/Controller.py --store /tmp/KitResearchState status
   python3 re/automation/Controller.py --store /tmp/KitResearchState events
   ```

   Use `status --job <job-label>` for one job.
   Each status record includes the job `kind`.
   Status pages contain at most 100 jobs; supply the returned `next_after` label through `--after` to read the next page.
   Use `events --after 0` to capture committed event history in ascending pages.
   For subsequent pages, use the returned `next_after` as `--after` and retain the first page's `through` as `--through`.
   A null continuation marks the end of the window. [Controller event windows](../../Changes/Research/Controller/ControllerEventWindows.md)
   `artifact <sha256>` verifies an object and reports its path and byte count.
   Replace angle-bracket values with actual labels or hashes.

Commands emit bounded canonical UTF-8 JSON followed by LF and return `0` on success.
Controller diagnostics also use UTF-8; subprocess clients must decode both output streams explicitly as UTF-8.
The [transport repair](../../Changes/Research/Controller/ControllerUtfEightTransport.md) preserves Unicode paths and reasons under restrictive host encodings without changing record hashes or transaction semantics.
Invalid records, unavailable stores and corrupted evidence return `1`.
A stale lease from `heartbeat` or `finish` returns `3` with a `controller stale lease` message.
A lease is stale when it was replaced, revoked or finished, when it expired, or when its inputs changed.
`finish` checks the lease before reading the worker's result JSON and checks the deadline again before storing the result.
The [session supervisor](ResearchSupervisor.md) stops a session at once when its renewal returns `3`.
No runnable job is a successful claim response with `job: null`; it does not consume an attempt or create a claim file.
Existing claim files are not overwritten.
Lease secrets are written to the private claim file and omitted from status, events and command arguments.
Do not publish claim files or reuse one for a different execution.

## Pools and counted resources

Schema version 4 adds pools and counted resources for the [session supervisor](ResearchSupervisor.md).

1. Assign job kinds to a pool:

   ```shell
   python3 re/automation/Controller.py --store /tmp/KitResearchState pool decode --kind decode.sldprt
   ```

2. Claim only jobs whose kind belongs to that pool:

   ```shell
   python3 re/automation/Controller.py --store /tmp/KitResearchState claim --worker operator:research --pool decode --claim-file /tmp/KitResearchClaim.json
   ```

3. Set a resource capacity, then mark the resource available:

   ```shell
   python3 re/automation/Controller.py --store /tmp/KitResearchState resource provider:example --capacity 2
   python3 re/automation/Controller.py --store /tmp/KitResearchState resource provider:example --available
   ```

A `pool` command replaces the kinds of that pool.
A kind belongs to at most one pool; a second assignment is rejected.
A pool holds 1–64 kinds, and the store holds at most 1,024 pool assignments.
A pool claim for a pool without kinds is rejected rather than reported as an empty queue.
A claim without `--pool` still selects from every kind, so do not mix plain claims with a running supervisor.
Capacity is 1–64 and defaults to 1, which keeps the earlier exclusive behavior.
Setting a capacity on an unknown resource creates it as unavailable.

The procedure is source-reviewed; it was not run locally as a test.
Actual remote evidence is recorded on the PR and in the step register.

## States, reuse and invalidation

| State                 | Behavior                                                                               |
| --------------------- | -------------------------------------------------------------------------------------- |
| `queued`              | Runnable once prerequisites, capacity, resources and retry delay permit                |
| `running`             | An attempt owns a unique lease token and an absolute execution deadline                |
| `waiting_evidence`    | Missing inputs/dependency results, or an explicit parked evidence request              |
| `waiting_ci`          | A worker explicitly parked the job for CI evidence                                     |
| `waiting_application` | Required resources are unavailable, or the worker reported an application wait         |
| `completed`           | A worker returned a result for the current fingerprint; this is not product acceptance |
| `rejected`            | A counterexample or unsupported proposal is parked until prerequisites change          |
| `failed`              | Retry budget exhausted for the current prerequisite generation                         |

A fingerprint binds the full job definition, selected input digests and dependency receipt/result digests.
Definition changes check newly added edges that can close a cycle, using indexed reachability over their affected ancestor region.
Appending a new leaf and resubmitting unchanged edges require no ancestor search.
Quota counters update transactionally instead of scanning every stored definition.
Execution uses a persistent queue of affected jobs and indexed reverse bindings/resources/dependencies.
Claims, heartbeats and completions do not rebuild or traverse the full graph.
Unchanged targeted status and heartbeat responses report `reconciled_jobs: 0`.
The counter records prerequisite evaluations in that command's transaction, not CAD coverage.
`cycle_searches` records changed-edge ancestor searches, not a general format-coverage metric.
An unchanged definition and unchanged bindings reuse the completed result.
Changing evidence, options, a rule/tool version or a dependency result invalidates affected jobs transitively.
Old attempt receipts and their immutable definitions/snapshots remain available after invalidation.
New prerequisites reset the per-generation attempt budget; unchanged prerequisites do not.

Explicit waits and rejections do not spin.
They resume when a relevant fingerprint changes.
An unavailable-to-available resource transition can also resume a parked application job that requires that resource.
For a bound SOLIDWORKS timeout, a fresh resource decision advances the [application hold epoch](../../Changes/Research/Controller/ApplicationHoldEpoch.md).
CI semantics are supplied by later workers and evidence bindings; A03 does not poll GitHub or treat arbitrary JSON as a passed CI result.

## Leases, retries and resource recovery

Status and claim requests reconcile prerequisites and expired leases transactionally.
Each heartbeat is capped by the original execution deadline.
Heartbeat renewal checks the current token, deadline and prerequisite digests in SQLite without reading artifact contents.
It reports `artifact_bytes_hashed: 0` and does not reconcile unrelated jobs.
Claims, result submission, status and explicit artifact reads retain content-integrity verification.
A heartbeat is a control-plane renewal, not artifact validation or result acceptance.
Use `finish` to validate and submit a result, even after successful heartbeats.
Expired attempts retain a receipt, consume their attempt budget and enter bounded backoff or failure.
A stale token cannot complete a replacement execution or publish a result as current.
The controller does not terminate an external process; it refuses that process's late result.

A resource admits as many running jobs as its capacity; the default capacity of 1 is exclusive.
Lowering a capacity does not stop running jobs; it blocks new claims until the running count falls below it.
Unknown resources begin unavailable; offline jobs can continue.
Use `resource <name> --available` or `--unavailable` to record actual worker availability.
An expired or invalidated resource-owning attempt, or an application-wait outcome, makes its resources unavailable.
Do not re-enable an installation until an isolated worker verifies that the previous execution has stopped and its controls are healthy.
Worker transport, process termination and physical application control belong to A08.

## Evidence and remaining scope

A03 adds remote process checks for restart persistence, idempotent reuse, transitive invalidation, stale-result fencing, competing claims, global capacity, exclusive resources, expiry/backoff limits, parked jobs, changed rule versions, cycle rollback and corrupt objects.
The scaling scenario submits a 10,000-job chain in bounded batches and completes 250 steps through the real command interface.
It checks that idle targeted reads and heartbeats reconcile no unrelated jobs and each completion updates only its direct dependent.
They execute through the real CLI and filesystem/database boundaries.
No local tests or collection run under repository policy.
The large-input scenario renews a lease over a 64 MiB input without payload hashing and rejects corrupted evidence at result submission.

The SQLite schema is version 4; versions 1–3 migrate transactionally.
Versions 1 and 2 receive the queue, reverse indexes and quota counters they require.
Version 3 receives the resource `capacity` column, the indexed job `kind` column filled from each stored definition, and the pool table.
The migration retains jobs, attempts, receipts and artifacts.
Version 1 migration seeds the queue; version 2 already has it and receives the maintained counters.
Unknown versions are rejected.
No distributed worker service, model provider, CAD adapter, neutral schema change or capability promotion is added.
The A08a supervisor is the first local process that drives these commands.
Worker-reported completion and a valid receipt do not prove the worker's assertion.
Domain verification and native acceptance remain separate later steps.

See [artifact publication across rollbacks](../../Gotchas/Research/ArtifactPublicationOutlivesRollback.md), [the step register](AutomationSteps.md) and [the corpus guide](PinnedCorpus.md).

## Declared worker output files

The supervisor's A03 adapter can submit a completed result with declared files under its private `work` directory. The research `finish --output-root` option derives from the adjacent finish record; it does not create global input bindings. The controller verifies at most 64 files and 256 MiB in aggregate, stages their bytes, rechecks the lease, and records durable output hashes only for an accepted completion. Status and dependency checks verify the accepted output objects. Existing finish calls without outputs keep their protocol.

See [durable worker outputs](../../Changes/Research/Workers/DurableWorkerOutputs.md) for schema, path protections, adapter capability and unverified concurrency cases.

The [semantic comparison worker](../../Changes/Research/Controller/SemanticComparisonWorker.md) applies this protocol to pinned neutral documents and a separately pinned tolerance profile.
It retains large correspondence reports as immutable artifacts and keeps a compact records receipt.
See the [comparison guide](SemanticComparison.md#run-through-the-controller) for the job contract and its unverified research scope.
The [native reader worker](../../Changes/Research/Readers/Comparison/NeutralReaderWorker.md) produces complete neutral-document and reader-evidence artifacts for these comparisons.
The [reader-to-comparison batch](SemanticComparison.md#connect-native-reader-jobs) uses accepted dependency output selectors without manual exports.
