# Adaptive research pool limits

## Configuration and startup

A08b enables adaptive pool limits by default.
Set the supervisor configuration field `adaptive_limits` to `false` to retain the existing measured admission ceiling directly.
Only JSON boolean values are accepted for this field.
The controller's concurrency limit and counted resources remain additional constraints.

Each pool starts at half its calculated total capacity, rounded down, with a minimum of one when capacity is available.
Calculated total capacity includes already running sessions and the additional measured headroom.
The active limit never exceeds that capacity.
A lower active limit stops new claims while existing sessions drain normally.
It does not change their outcomes or revoke their leases.
Restarting the supervisor resets adaptive state conservatively.
The versioned memory history remains durable.

## Healthy increases

The first actual session starts that pool's healthy interval.
An empty queue cannot accumulate startup time before any work begins.
After 60 seconds without a failure, the supervisor can add one session when all applicable guards hold:

- The one-minute load average is below 85 percent of the measured logical CPU count.
- Available memory exceeds the reserve plus one session estimate.
- On Linux, memory PSI `some avg10` is below 10 percent.
- The calculated capacity permits another active session.

Each increase starts another 60-second interval.
Load and pressure observations refresh with the existing five-second host measurement.
Missing load or applicable PSI data blocks increases with an explicit reason.
Windows has no implemented load-average measurement, so this change does not qualify automatic upward ramps there.
Startup limits, measured admission, and explicit backoff remain available.

## Backoff

A recorded `memory_limit` stop halves the pool target immediately, with a minimum of one.
Two recorded deadline stops within 600 seconds halve the target once for that pair.
The pair is then consumed before another pair can trigger backoff.
Memory below the configured reserve halves the target once per below-reserve episode.
Continued below-reserve observations restart the healthy interval without repeating the backoff event.
Other failed or rejected sessions reset the healthy interval without inventing a memory-failure cause.
These decisions remain separate for each pool.

An unattributed signal is not an OOM diagnosis.
Automatic backoff specifically attributed to an operating-system OOM termination remains unqualified.
This change does not infer that cause from `SIGKILL` or a nonzero exit status.

## Events and verification

Admission events include `active_limit`, `calculated_capacity`, `adaptive_reason`, `adaptive_revision`, and `upward_blocked_reason`.
They also retain the actual host observations and resource reservations.
The adaptive reason identifies the last target adjustment, while the admission reason identifies the current blocker.
Accepted memory-limit and deadline-pair observations emit an `adaptive_backoff` event with the preceding and resulting targets.
Events report policy transitions instead of repeating unchanged decisions each poll.

Dedicated remote process scenarios exercise the default enabled policy.
A runner holds a real session for 65 seconds while another job waits.
The scenario checks half-capacity startup and refusal to start the second job before the 60-second boundary.
It verifies each observed increase against the real load, memory, and applicable pressure guards.
Its printed evidence explicitly states whether an upward branch was observed.
Two real deadline failures verify the backoff pair and its ten-minute window.
Additional cases verify measured memory-limit backoff, below-reserve admission, and strict boolean configuration.
The legacy exact-pool fixtures explicitly disable adaptation while retaining measured admission checks.

Local work used source inspection, formatting, static types, syntax, and repository policy checks only.
No local tests, native reader reproductions, application calls, or model calls ran.
Exact-revision remote adaptive execution remains pending when this entry is introduced.
Calibration batches, grouped jobs, and independently attributed OOM backoff remain open.
See the [supervisor guide](../../../Reference/Research/ResearchSupervisor.md) and [step register](../../../Reference/Research/AutomationSteps.md).
