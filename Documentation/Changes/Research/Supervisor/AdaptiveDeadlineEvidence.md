# Adaptive deadline backoff evidence

When an `adaptive_backoff` event has `adaptive_reason: "deadline_pair"`, `deadline_sessions` contains both physical session IDs in controller settlement order.
`deadline_elapsed_seconds` measures the interval between the supervisor's accepted stop observations with its monotonic clock.
The existing top-level `session` and `job` fields still identify the settlement that triggered the event.
Use the session IDs to find the corresponding `finished` events and process receipts in the same supervisor output.

The decision still requires two accepted deadline stops in the same pool within 600 seconds.
A physical session cannot supply both observations.
The supervisor consumes the pair when it reduces the limit.
Pending observations remain in memory for the current supervisor process.
Earlier logs lack these two fields.

## Verification

The existing process case stops two workers for real deadlines and matches the emitted pair to both non-stale finish events and their process receipts.
It checks the monotonic interval against the declared window and retains the limit and durable job outcome checks.
Exact-revision verification in hosted Linux and macOS remains pending.

See [resource admission and adaptive capacity](../../../Reference/Research/ResearchSupervisor.md#versioned-memory-learning).
