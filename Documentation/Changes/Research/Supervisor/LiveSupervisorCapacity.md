# Live supervisor capacity status

The research supervisor adds a `capacity` field to each pool in the existing `status` response.
The configured maximum, running sessions, pause record and optional A03 claim occupancy retain their existing fields.

When a live decision is available, `capacity.decision` contains the active limit, calculated capacity, limiting factors and reservation estimate per registered kind.
The CPU, memory and configured slot limits come from the real admission check.
The adaptive factor applies when it reduces the calculated capacity.
The estimate for each kind is its pre-claim reservation, including any applicable learned estimate and kernel OOM floor.
A03 independently decides whether to issue a claim.

`capacity.state` records an evaluated pool, a full pool, a pause, an application settlement in progress or unavailable information.
A pool with a current pause loses its decision view immediately.
The supervisor needs a new admission evaluation after a pause change before it can display numeric limits again.
A full pool can show its last decision until that decision or its host measurement ages out.

The owner publishes one private status file with atomic replacement.
The reader checks the running process identity, the effective configuration and the registry used by that process.
The snapshot, decision and host sample each have a 20-second freshness limit.
The command reads the snapshot without acquiring the supervisor lock or reevaluating adaptive policy.
Publication failures leave scheduling and controller settlement to their existing paths.

## Verification

The hosted POSIX pause case compares live status with the actual admission event and checks configuration mismatch, pause, and normal exit.
It passed in the 59-case Linux and 143-case macOS supervisor suites at PR head `648ddf5c` and tested merge `7d662f29`. [Hosted Linux evidence](https://github.com/TryUniCAD/Kit/actions/runs/43774889237/job/132998931871), [hosted macOS evidence](https://github.com/TryUniCAD/Kit/actions/runs/43774889237/job/132998931836)
The hosted Windows recovery case checks a live decision and refusal of the retained snapshot after forced owner exit.
It passed with all 92 Windows supervisor cases at PR head `648ddf5c` and tested merge `7d662f29`. [Hosted Windows evidence](https://github.com/TryUniCAD/Kit/actions/runs/43774889237/job/132998931881)

See [supervisor commands](../../../Reference/Research/ResearchSupervisor.md#commands).
