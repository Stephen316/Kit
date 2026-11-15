# Versioned memory estimates

## Behavior

A08b now learns memory estimates from successfully completed supervisor sessions.
The controller must accept the completion on the current lease before a sample enters the history.
Rejected, retried, stale, and unmeasured sessions do not contribute samples.
A fast session with no positive process-group observation remains unmeasured.

The history groups samples by job `kind` and `tool_version`.
Each group retains its last 50 successful observations in completion order.
Before five observations, the estimate remains the registry's `initial_peak_memory_mib` value.
After five observations, it uses the nearest-rank 95th percentile with a 25 percent margin.
The result rounds up to a whole byte.
A new tool version starts from the registry estimate and an empty sample group.
Change the job's `tool_version` when its tool implementation changes.

## Persistence

The supervisor writes `memory-history.json` privately under its configured state directory.
Publication uses the existing atomic record writer.
The history retains at most 128 recently updated kind-and-version groups.
Its format and all sample bounds are validated before a supervisor starts claiming jobs.
An unknown format, duplicate identity, invalid sample, or symbolic link prevents startup.
The reader keeps the existing 1 MiB metadata limit.

Each accepted observation emits a `memory_estimate` event.
The event names the job, session, kind, version, sample count, estimate, and calculation source.
A write failure preserves the previous history and emits one `memory_history_error` event.
Further learning stays disabled until the supervisor restarts.
The already accepted job result remains accepted.

## Admission limits

Running-session growth reservations use the estimate for that session's exact kind and tool version.
The pre-claim controller interface does not expose the next job's tool version.
Pre-claim admission therefore retains the registry estimate and any larger learned estimate across that kind's recorded versions.
It never admits an unknown version using another version's smaller learned footprint.
This conservative guard can reduce concurrency until a version-aware claim interface is available.
The runner's configured `max_memory_mib` stop threshold remains unchanged.

## Verification

New remote process scenarios use the real supervisor, A03 controller, memory sampler, and stored receipts.
One scenario checks the five-observation transition, restart persistence, and isolation of a second tool version.
A 55-session scenario checks the retained 50-observation window and its percentile calculation.
An invalid-format scenario verifies failure before a queued job consumes an attempt.
Local work used source inspection, syntax parsing, formatting, and whitespace checks only.
No local tests, reproductions, native applications, or model calls ran.
Exact-revision remote execution remains pending when this entry is introduced.

This substep does not implement adaptive concurrency ramps, calibration batches, or grouped jobs.
It supplies measured estimates for those later steps.
See the [supervisor guide](../../../Reference/Research/ResearchSupervisor.md) and [step register](../../../Reference/Research/AutomationSteps.md).
