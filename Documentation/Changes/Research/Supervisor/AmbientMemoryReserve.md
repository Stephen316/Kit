# Ambient memory reserve crossing

The Linux supervisor process gate has an opt-in witness for host available memory crossing a configured reserve while two workers are running.
The existing natural increase, deadline, worker memory limit, and kernel OOM cases remain independent.

The witness selects the reserve before starting the supervisor. It starts with four eligible slots and an active limit of two. A dedicated child touches 384 MiB of anonymous memory. The supervisor reads the real `MemAvailable` field before, during and after the allocation.
The allocator is enabled only on the disposable GitHub-hosted Linux workflow. It checks at least 8 GiB of headroom beyond the allocation and at least 2 GiB beyond it at any finite cgroup limit it encounters. The allocator has a 512 MiB address-space cap and releases its pages on command, on parent exit, or after its time bound. No cgroup configuration or memory counter is changed by the fixture.

The expected observation is one active-limit change from two to one while two workers remain alive. A second low sample must keep the same revision. After the pages are released, the calculated capacity must return to four while the adaptive target stays at one. Both original jobs must finish on their first attempts. CI prints the admission records and allocation receipt on success.

Unsupported host or cgroup conditions before startup leave the observation unmeasured.

At PR head `14f4a1f2` and tested merge `1198983e`, the hosted child measured available memory falling from 14,848 to 14,455 MiB across the 14,621 MiB reserve. The live assertions observed one reduction from two workers to one, followed by restored headroom. Both jobs completed on their first attempts. The final reporting assertion raised a key error on the terminal summary record. The report now distinguishes that summary from an event. [Earlier hosted Linux run](https://github.com/TryUniCAD/Kit/actions/runs/43788486237/job/133041436819)

At PR head `5605c58f` and tested merge `c4f34448`, all 63 hosted Linux supervisor cases passed. The allocator observed 14,614 MiB of available memory before the allocation and 14,220 MiB afterward. The supervisor sampled about 14,626, 14,200 and 14,595 MiB before, during and after the crossing of its 14,405 MiB reserve. The active limit changed from two to one at revision 2 with both workers running. It held that revision through a second low sample and recovery to four calculated slots. Both jobs completed their first attempts. The same run measured a separate healthy increase after 61.26 seconds and a separate two-deadline reduction from two to one. [Passing hosted Linux evidence](https://github.com/TryUniCAD/Kit/actions/runs/43794606581/job/133060521405)
