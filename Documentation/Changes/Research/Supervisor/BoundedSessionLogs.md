# Bounded research session logs

## Behavior

A08b bounds each supervisor session's standard-output and standard-error capture.
The optional `max_log_bytes` configuration field defaults to 1,048,576 bytes per stream.
It accepts integers from 1,024 to 67,108,864 bytes.
The supervisor retains the first bytes up to that limit and drains subsequent bytes without storing them.
Each stream uses a nonblocking pipe and a fixed-size read buffer.
Each supervision pass drains at most 256 KiB per stream.
The receipt records the configured limit and the seen, retained, and dropped byte counts under `logs`.
The existing failure diagnostic uses the tail of the retained standard-error prefix.
The existing session cleanup removes both log files after result publication.

## Process cleanup

Restart recovery checks the recorded process identifier and start time before sending a signal.
After `SIGTERM`, it checks the entire process group for non-zombie members.
A leader that exits no longer causes surviving children to be treated as stopped.
After the grace period, recovery sends `SIGKILL` to surviving group members.
If cleanup cannot establish that the group stopped, recovery preserves the session and fails before retrying its job.
Normal session completion continues to kill the process group before reaping its leader.

## Verification and limits

New remote process scenarios exercise two boundaries through the real supervisor and A03 controller.
One runner writes 2 MiB to each stream with an 8 KiB capture limit.
The scenario checks file sizes during execution and exact byte counters in the stored receipt.
Another runner leaves a child that ignores `SIGTERM` while the leader accepts it.
The scenario kills the supervisor, restarts it, and checks child cleanup and the orphan receipt.

Local verification is limited to source inspection and static checks.
No local tests, collection, native application work, or model calls ran.
[Remote workflow quality](https://github.com/TryUniCAD/Kit/actions/runs/43663022455/job/132656265358) passed eight supervisor process scenarios at `480d9d3a`, including both new boundaries.
Later resource-control changes require their own current-revision evidence.
This change does not complete A08b headroom, memory enforcement, calibration, or grouped sessions.
It does not add Windows support or terminate children that deliberately leave the session's process group.

See the [supervisor guide](../../../Reference/Research/ResearchSupervisor.md) and [step register](../../../Reference/Research/AutomationSteps.md).

The [macOS run at `6fb599a9`](https://github.com/TryUniCAD/Kit/actions/runs/43672428040/job/132685202111) exposed an empty PID file before the restart scenario could run. The fixture now publishes that identity atomically; the [PID publication gotcha](../../../Gotchas/Research/Supervisor/PidFilePublicationRace.md) records the race and unchanged cleanup assertions. Later process verification is recorded below.

At source checkpoint `22a59e68c839354f3e6672eec6f67aa647aa1dce`, the [Linux selection](https://github.com/TryUniCAD/Kit/actions/runs/43678423785/job/132703622509) passed all 57 supervisor cases and the [macOS selection](https://github.com/TryUniCAD/Kit/actions/runs/43678423785/job/132703622604) passed all 74 worker cases, including the repaired PID publication, actual worker-entry and live-orphan cleanup scenarios. Native application execution remains separate.
