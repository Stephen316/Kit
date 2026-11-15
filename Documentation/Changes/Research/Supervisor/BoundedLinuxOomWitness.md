# Bounded Linux kernel OOM witness

The standalone witness uses a disposable Linux VM with a host-root cgroup v2 mount, existing memory and PID controllers, and sudo access to the host kernel message device. Its preflight requires at least 4 GiB of available memory and `panic_on_oom=0`. It creates two new child groups in sequence with a 64 MiB memory ceiling, zero swap, one process and no descendants. After confirming singleton membership, the observer releases the unprivileged child with a one-byte gate. The child rechecks its group and hard limit before touching pages. The active case stops after at most 96 one-MiB allocations. [Linux cgroup v2 memory controls](https://docs.kernel.org/admin-guide/cgroup-v2.html#memory-interface-files)

Run the checked-in witness on the disposable VM using a new output file in its private temporary directory.

```sh
sudo -n -- /usr/bin/python3 -I -S re/automation/LinuxOomWitness.py \
  --source-revision "$(git rev-parse HEAD)" \
  --output "$RUNNER_TEMP/LinuxOomWitness.json"
```

The ordinary-signal control sends `SIGKILL` through the held child's PID file descriptor. Its local memory counters and matching kernel event list must stay empty of OOM evidence. The capped case requires the exact victim PID and UID, matching `oom_memcg` and `task_memcg` paths, a kernel-origin `CONSTRAINT_MEMCG` record and one local OOM kill. The observer checks identity and counters at both boundaries, reaps both children and removes both private groups before writing the report. Its output retains only matching kernel fields, process identity, configured limits, counters, host headroom and source identities. [Kernel log ABI](https://kernel.org/doc/html/latest/admin-guide/abi-testing.html#dev-kmsg), [Linux victim record](https://raw.githubusercontent.com/torvalds/linux/v6.14/mm/oom_kill.c)

The Windows implementation host verified source syntax. A hosted Linux execution is pending preflight verification of its cgroup controllers and kernel-log access. Supervisor integration and numeric adaptive backoff remain separate evidence requirements.
