# A08a research session supervisor and A03 schema version 4

## Behavior

A08a adds a local session supervisor under `re/automation/` on PR #94.
The [supervisor guide](../../Reference/Research/ResearchSupervisor.md) describes its configuration, runner registry, session contract, stops, pauses and restart fencing.

The supervisor claims jobs for named pools through a controller adapter.
Each attempt runs in a private session directory, without a shell, in its own process group and with an allowlisted environment.
The supervisor copies and verifies the bound inputs, renews the lease at one third of its duration and validates `result.json` against the runner's schema.
It stops a session at the deadline, on a stale lease or when an operator pauses its pool.
A stop sends `SIGTERM` to the process group and `SIGKILL` after the grace period.
At startup, it fences orphaned sessions by process identifier and process start time, so it does not stop a reused identifier.
One exclusive lock for each state directory and each controller store prevents a second supervisor.

The [A03 controller](../../Reference/Research/ResearchController.md) moves to schema version 4.
Version 3 stores migrate transactionally.
Resources have a capacity, so a shared provider can admit more than one session.
`claim --pool` selects only jobs whose kind belongs to the pool.
`heartbeat` and `finish` return exit status `3` for a stale lease, separate from other errors.

The supervisor reaches A03 only through the `a03` adapter.
A minimal file-based controller in `tests/Research/MiniController.py` is the alternate adapter.

## Usage and limits

Follow [the supervisor guide](../../Reference/Research/ResearchSupervisor.md#commands).
The repository ships no runner registry, because no production runner exists yet.
Headroom, adaptive limits, calibration, memory stops, bounded logs and grouped small-file sessions belong to A08b.
Application workers belong to A08c, and model runners belong to A10.
The supervisor supports Linux and macOS, not Windows.
A loaded adapter module is executed, so use only a trusted module.

## Verification

Source inspection, Python syntax, `black`, `ruff`, `pyright` and `mypy` are checked on the new process coverage before publication.
No local tests, test collection, CAD experiments or model calls run.

The new remote process scenarios run in the workflow-quality job:

| Gate                 | Scenario                                                                                         |
| -------------------- | ------------------------------------------------------------------------------------------------ |
| Schema migration     | A version 3 store without capacity, kind or pool data migrates to version 4 and keeps its jobs   |
| Counted resources    | Capacity 2 admits two claims, blocks a third, and follows capacity changes                       |
| Pool-filtered claims | Pool claims return only member kinds, and a kind cannot join two pools                           |
| Stale outcomes       | Changed inputs and expired leases return exit status `3` from `heartbeat` and `finish`           |
| Session outcomes     | Valid, rejected, invalid, schema-violating, crashing and unpooled jobs reach the expected states |
| Deadline stop        | A runner that ignores `SIGTERM` is killed and its job finishes with `retry` before the deadline  |
| Pause and lock       | A paused pool stops its session, a second supervisor exits with status `4`, and resume completes |
| Stale lease          | Rebinding an input stops the running session without a finish, and the new generation completes  |
| Restart fencing      | A restarted supervisor stops a matching orphan, spares a reused identifier and reruns the job    |
| Alternate adapter    | The supervisor completes, retries and fences stale leases through the minimal controller         |

Exact-revision results are recorded in the step register and PR comments after CI completes.
No result is recorded here yet.
