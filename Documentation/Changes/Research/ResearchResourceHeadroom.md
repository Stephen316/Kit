# Research resource headroom

## Admission

A08b checks machine headroom before the supervisor claims a job.
The supervisor configuration accepts `reserved_cpus` from 0 to 65,536, with a default of 2.
It accepts `reserved_memory_mib` from 0 to 1,048,576, with a default of 4,096 MiB.
The host measurement refreshes every five seconds.
Running sessions reserve their configured thread counts across all pools.
Their growth reservation uses the larger of each initial estimate and its currently observed resident memory.
It subtracts only the resident memory already reflected in the latest host measurement.
New sessions reserve their full estimate until that host measurement refreshes.
New sessions require the configured CPU and memory reserves to remain available.
The controller continues to enforce its concurrency limit and counted resources.

Admission uses the largest thread count and initial memory estimate of every runner registered in a pool.
This conservative rule can leave small jobs queued behind an inadmissible large runner.
Use separate pools for runners with materially different resource estimates.
A denied admission leaves the job queued without an attempt or lease.
The `admission` event records the measured host resources, estimates, reserves, and blocking reason.
The supervisor emits this event when a pool's blocking reason changes.
It does not emit repeated unchanged denial events.

## Memory stops

Runner registry entries accept `max_memory_mib` from 1 to 1,048,576 MiB.
The default is twice `initial_peak_memory_mib`, capped at 1,048,576 MiB.
Each supervision pass samples resident memory across the runner's process group.
When the group exceeds its limit, the supervisor stops it through the existing signal and retry protocol.
The stop reason is `memory_limit`.
Receipts retain `memory_limit_bytes` and `sampled_group_peak_memory_bytes` alongside the existing `wait4` peak.
The sampled group value is distinct from the operating system's per-process high-water measurement.

## Measurements and limits

Linux uses `MemAvailable` from `/proc/meminfo` and CPU affinity when available.
macOS reads the page size and free, inactive, and purgeable counts from `vm_stat`.
Its admission estimate uses free pages plus the larger of inactive or purgeable pages.
That lower-bound calculation avoids assuming that inactive and purgeable sets are disjoint.
Process-group resident sizes come from `ps` and are converted from KiB to bytes.
Shared resident pages can be counted in more than one process, which makes the group sum conservative.
These host measurements do not establish container or cgroup quota enforcement.

Missing host measurements fail startup before claims begin.
A later measurement failure stops existing sessions and exits with an error after cleanup.
A naturally exited leader is reaped before a missing group measurement is treated as an error.
Memory enforcement is sampled, so short-lived peaks and growth between samples can exceed the configured threshold.
It is not an operating-system allocation limit or containment of children that leave the process group.
Adaptive limits, calibration, grouped jobs, and Windows support remain separate work.

## Verification

New remote process scenarios use the actual supervisor and A03 controller.
CPU and memory denial scenarios check that no lease or attempt is consumed.
The CPU scenario restores headroom and verifies that the queued job subsequently completes.
The memory scenario allocates 96 MiB in a child with a 64 MiB group limit.
It checks the stop reason, stored measurements, and child cleanup.
The existing process fixture explicitly reserves zero CPUs and zero MiB on small CI runners.
This fixture configuration does not change the production defaults.

Local verification is limited to static syntax, formatting, and whitespace checks.
No local test or reproduction ran.
Exact-revision remote results are pending when this entry is introduced.
See the [supervisor guide](../../Reference/Research/ResearchSupervisor.md) and [step register](../../Reference/Research/AutomationSteps.md).
