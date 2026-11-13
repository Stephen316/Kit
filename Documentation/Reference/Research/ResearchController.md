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

| Field          | Meaning                                                                             |
| -------------- | ----------------------------------------------------------------------------------- |
| `id`           | Stable job label; submitting changed content updates that job's definition          |
| `kind`         | Worker operation identifier; the controller does not execute this string            |
| `inputs`       | Object mapping semantic roles to named evidence bindings                            |
| `rule_version` | Explicit rule version; actual integrations must use an immutable version identifier |
| `tool_version` | Explicit worker build/version identifier                                            |

Optional fields are `depends_on`, `resources`, `options`, `max_attempts`, `lease_seconds`, `timeout_seconds` and `retry_base_seconds`.
Unknown top-level fields are rejected.
Dependencies and resources are arrays of labels; `options` is a JSON object.
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
   Status pages contain at most 100 jobs; supply the returned `next_after` label through `--after` to read the next page.
   `artifact <sha256>` verifies an object and reports its path and byte count.
   Replace angle-bracket values with actual labels or hashes.

Commands emit bounded JSON and return `0` on success.
Invalid records, unavailable stores, corrupted evidence and stale leases return `1`.
No runnable job is a successful claim response with `job: null`; it does not consume an attempt or create a claim file.
Existing claim files are not overwritten.
Lease secrets are written to the private claim file and omitted from status, events and command arguments.
Do not publish claim files or reuse one for a different execution.

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
CI semantics are supplied by later workers and evidence bindings; A03 does not poll GitHub or treat arbitrary JSON as a passed CI result.

## Leases, retries and resource recovery

Status and claim requests reconcile prerequisites and expired leases transactionally.
Each heartbeat is capped by the original execution deadline.
Expired attempts retain a receipt, consume their attempt budget and enter bounded backoff or failure.
A stale token cannot complete a replacement execution or publish a result as current.
The controller does not terminate an external process; it refuses that process's late result.

All resource labels are exclusive while a job is running.
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

The SQLite schema is version 3; versions 1 and 2 migrate transactionally to the queue, reverse indexes and quota counters they require.
The migration retains jobs, attempts, receipts and artifacts.
Version 1 migration seeds the queue; version 2 already has it and receives the maintained counters.
Unknown versions are rejected.
No distributed worker service, model provider, CAD adapter, neutral schema change or capability promotion is added.
Worker-reported completion and a valid receipt do not prove the worker's assertion.
Domain verification and native acceptance remain separate later steps.

See [artifact publication across rollbacks](../../Gotchas/Research/ArtifactPublicationOutlivesRollback.md), [the step register](AutomationSteps.md) and [the corpus guide](PinnedCorpus.md).
