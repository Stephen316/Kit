# Grouped leases and memory accounting

A group contains several logical jobs but only one process tree.
Treating every member as a physical session would multiply memory samples and count a single deadline as several failures.
Learning group peaks in the single-job history would also let small single jobs reduce a required batch memory floor.

The supervisor records adaptive outcomes once per physical identity and keeps memory history separate by actual group size.
It clamps every group estimate to the registry's explicit `group_peak_memory_mib` floor.
A failed group receives generation/fingerprint-scoped single-job retry markers in the controller store, so a restart cannot repeatedly expose the same files to the same bad batch.

Starting one controller interpreter for every heartbeat or output copy can consume a short lease before later members are processed.
Group protocol 1 renews leases in one controller invocation and renews remaining leases before each bounded member intake.
Every member still checks its token, current fingerprint and execution deadline.
A slow copy remains stale if it exceeds that deadline.

See [the change entry](../../../Changes/Research/Supervisor/GroupedSmallFileSessions.md) for configuration, process fixtures and the current evidence limit.
