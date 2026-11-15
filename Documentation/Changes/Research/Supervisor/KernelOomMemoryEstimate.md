# Kernel OOM memory estimate

An accepted retry with verified Linux memory-cgroup OOM evidence doubles the current reservation estimate for that job kind and tool version.
The estimate starts from the larger of the registry value and the previously learned estimate.
The supervisor retains the result as a minimum alongside the existing successful samples.
Pre-claim admission includes the minimum when it selects the conservative estimate across versions.
The configured worker stop limit remains the fixed execution threshold.

The change applies once per physical session.
A group uses its own size-specific history and requires a current settlement for at least one member.
Ordinary process signals and supervisor-requested stops continue through their existing paths.
The minimum saturates at the signed 64-bit byte limit, so admission refuses a session when that reservation exceeds usable memory.

The supervisor reads version 1 histories as before.
Version 2 stores the minimum and its contributing session IDs, including cases with zero successful samples.
The supervisor publishes the replacement history after controller settlement using the same private atomic file update as ordinary observations.
A process interruption between settlement and the history write can leave that observation absent.
The existing history write error event reports failures without reversing controller settlement.

## Verification

The existing hosted Linux witness checks the actual 64 MiB cgroup OOM and the ordinary SIGKILL control.
The OOM case checks the reservation increase from 64 to 128 MiB, reload from the private file and duplicate-session refusal.
The ordinary kill control checks the original 64 MiB estimate.
The existing adaptive limit and exact controller receipt checks remain part of both cases.
At PR head `47de6ad0`, the hosted witness passed on tested merge `b008c6a82a1556c0e0018bfb5fa0e47e2dcc4f8e`. The accepted kernel OOM increased the recorded admission estimate from 64 to 128 MiB. The ordinary `SIGKILL` control stayed at 64 MiB, and cleanup passed in both cases. The downloaded JSON SHA-256 is `a56ea85b2b843a4e8518b97b838ff1a94046b9f647bd37ea580545dd7a165302`. [Hosted job](https://github.com/TryUniCAD/Kit/actions/runs/43772995626/job/132992935388), [Witness artifact](https://github.com/TryUniCAD/Kit/actions/runs/43772995626/artifacts/14185416716)

See [supervisor memory learning](../../../Reference/Research/ResearchSupervisor.md#versioned-memory-learning) and [the hosted Linux witness](HostedSupervisorOom.md).
