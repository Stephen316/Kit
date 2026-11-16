# Ambient memory reserve crossing

The Linux supervisor process gate has an opt-in witness for host available memory crossing a configured reserve while two workers are running.
The existing natural increase, deadline, worker memory limit, and kernel OOM cases remain independent.

The witness selects the reserve before starting the supervisor. It starts with four eligible slots and an active limit of two. A dedicated child touches 384 MiB of anonymous memory. The supervisor reads the real `MemAvailable` field before, during and after the allocation.
The allocator is enabled only on the disposable GitHub-hosted Linux workflow. It checks at least 8 GiB of headroom beyond the allocation and at least 2 GiB beyond it at any finite cgroup limit it encounters. The allocator has a 512 MiB address-space cap and releases its pages on command, on parent exit, or after its time bound. No cgroup configuration or memory counter is changed by the fixture.

The expected observation is one active-limit change from two to one while two workers remain alive. A second low sample must keep the same revision. After the pages are released, the calculated capacity must return to four while the adaptive target stays at one. Both original jobs must finish on their first attempts. CI prints the admission records and allocation receipt on success.

Unsupported host or cgroup conditions before startup leave the observation unmeasured. Hosted verification is pending.
