# Hosted Linux supervisor OOM witness

The Linux kernel OOM witness job runs two supervised cases after its standalone measurements. Each case uses a fresh A03 store, one ordinary supervisor attempt and a new private cgroup v2 leaf. The checkout is pinned to the GitHub Actions candidate, with no stored checkout credentials. The privileged step reads the three witness scripts from root-owned copies whose Git blob IDs and SHA-256 values match that candidate. The supervisor, A03 controller and worker run as the existing unprivileged runner user.

Before the supervisor releases its launch gate, the observer checks the direct child PID, start ticks, UID, exact bootstrap command and expected worker command. It moves only that held worker into the leaf and records its local memory counters. The leaf has a 64 MiB memory cap, zero swap, one permitted process and no child cgroups. Each case is bounded to one attempt. The fixed memory worker touches at most 96 MiB in one MiB blocks. The ordinary kill worker checks the same containment and its own durable launch record before sending itself `SIGKILL`.

The observer reads the post-reap counters and filters the kernel log to the owned worker and leaf. The supervisor receipt must match the independent kernel record, and the accepted A03 result and controller receipt must match their stored digests. With four eligible slots the adaptive limit begins at two. The memory-cap case requires one `linux_memcg_oom` backoff to one. The ordinary kill case requires zero local counter changes, no matching kernel record, no OOM receipt and a final limit of two. The sampler-driven `memory_limit` case remains covered separately.

The job uploads only the bounded `LinuxSupervisorOomWitness` JSON. Missing host cgroup or kernel capabilities produce an explicit unmeasured report before any workload is released. A failure after release fails the gate. [Standalone witness](BoundedLinuxOomWitness.md) [Supervisor observation contract](LinuxSupervisorOomEvidence.md)

## Verified hosted result

The Linux kernel OOM witness job succeeded on PR head `5770f1b322688e55237172d7a6d57c983f334ce0`. The checked out candidate `fdb682757a3f8a8d3bf180dcee5c85fee2f1ddb4` has first parent `25588d8c15fbd85d7ec9ae9185477a09eead938f` on main and second parent `5770f1b322688e55237172d7a6d57c983f334ce0` on the PR. Kernel `7.0.0-1014-aws` reported both cases observed. [Workflow job](https://github.com/TryUniCAD/Kit/actions/runs/43706418832/job/132788439990)

| Case | Native wait | Independent cgroup evidence | Current A03 settlement | Adaptive limit |
| --- | --- | --- | --- | --- |
| Ordinary signal | `SIGKILL`, PID 2333 | All local counter deltas zero, no matching kernel record | Generation 1, attempt 1, accepted retry, no OOM proof | 2 → 2 |
| 64 MiB memory cap | `SIGKILL`, PID 2353 | 64 MiB peak, local `max +35`, `oom +1`, `oom_kill +1`, one `CONSTRAINT_MEMCG` record for UID 1001 and the same leaf in both kernel fields | Generation 1, attempt 1, accepted retry, durable matching OOM proof | 2 → 1, one `linux_memcg_oom` backoff |

Both attempts had no supervisor stop reason, both leaves were removed, and all four host available-memory samples exceeded 15.2 GB. The accepted OOM result SHA-256 is `fb4d7d30811d25ed697f0880d83cf835622b3092887c77078d855d86898866ee` and its A03 receipt SHA-256 is `d91729d055822e2d2075a78e8bfb0a7f6d0859e6f90fb0de85b339540fafecc9`.

Artifact `14158468995` ZIP SHA-256 is `127733859ba0dbe981db89de7ffe6900923290c16b4cba08799b2ba459b9d23a`. The single `LinuxSupervisorOomWitness.json` member has SHA-256 `902a0352bc7bc9f15d4ff161696ab165ad03ad786f9b51ba960e323a0e0d0387`. The downloaded artifact digest, candidate ancestry, Git blob IDs and SHA-256 values were verified independently. [Sanitized artifact](https://github.com/TryUniCAD/Kit/actions/runs/43706418832/artifacts/14158468995)

| Source | Candidate Git blob | SHA-256 |
| --- | --- | --- |
| `LinuxOomGuest.py` | `992b3f617305d411d8bea1c2c6053249ced50d90` | `6406b5ce07ecb39a09e1e5c51b0df9c6697430bfb0689e4f8d6bc85c8717a824` |
| `LinuxOomSupervisor.py` | `cd16e1b16d8c3f7b38ba599c2bb5918cfb031065` | `837d9efaf4353d5acd8707ac50e9c7875add0ec2b4fab997e63793a16fb69c1e` |
| `LinuxOomWitness.py` | `5722c93ae7146ac46344d0537dfa4dd08cba26ae` | `7f2fe98439304779234205dd91458fc1ba43bec793800223b7a6cc24f33cf08a` |
