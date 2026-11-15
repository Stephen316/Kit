# Research session supervisor

## Purpose

A08a adds a local supervisor under `re/automation/`.
It claims jobs for named pools, runs each attempt in a private session directory and finishes the job through a controller adapter.
Use this page to configure the supervisor, register runners and read its receipts.
The [parallel-session design](ParallelSessions.md) explains the full architecture.
The [step register](AutomationSteps.md) records the status of A08a and the later A08b and A08c steps.

The supervisor does not decode CAD files, launch CAD applications or call models.
Registered runner programs do that work.
Production conversion must not import this research code.

## Before you start

You need Python 3.11 or later on Linux or macOS.
The supervisor uses `fcntl`, process groups and `os.wait4`, so Windows is not supported.
A08e plans Windows support for a single Windows host that runs both CAD applications.
Initialize an [A03 controller store](ResearchController.md#commands), or supply another adapter.
Choose a private state directory on a local disk.

## Configuration

The configuration is one JSON object.
Relative paths resolve against the directory of the configuration file.
This example uses example paths:

```json
{
  "state": "/var/tmp/KitSupervisor",
  "controller": { "adapter": "a03", "store": "/var/tmp/KitResearchState" },
  "registry": "Runners.json",
  "worker": "supervisor:workstation",
  "pools": { "decode": { "max_sessions": 4 } },
  "resources": { "provider:fixture": 2 },
  "stop_grace_seconds": 10,
  "poll_seconds": 0.2
}
```

| Field                 | Required | Meaning                                                                              |
| --------------------- | -------- | ------------------------------------------------------------------------------------ |
| `state`               | Yes      | Private state directory with the lock, sessions, claims and pause file               |
| `controller`          | Yes      | `{"adapter": "a03", "store": ...}`, or `module`, `class` and `options`               |
| `registry`            | Yes      | Runner registry file                                                                 |
| `pools`               | Yes      | Each pool's `max_sessions`, 1–64; must match the pools in the registry               |
| `worker`              | No       | Worker label recorded on each claim; default `supervisor:local`                      |
| `resources`           | No       | Counted controller resources and their capacity, 1–64, set at each start             |
| `stop_grace_seconds`  | No       | Time between `SIGTERM` and `SIGKILL`, 0.1–60 seconds; default 10                     |
| `poll_seconds`        | No       | Time between supervision passes, 0.05–5 seconds; default 0.2                         |
| `reserved_cpus`       | No       | Logical CPUs kept outside the session budget, 0–65,536; default 2                    |
| `reserved_memory_mib` | No       | Available memory kept outside the session budget, 0–1,048,576 MiB; default 4,096 MiB |
| `max_log_bytes`       | No       | Retained bytes per output stream, 1 KiB–64 MiB; default 1 MiB                        |

The supervisor sets only the capacity of a configured resource.
Mark a resource available with the controller command after you verify it.

## Runner registry

The registry maps each job kind to one runner.

```json
{
  "runners": {
    "decode.fixture": {
      "pool": "decode",
      "argv": ["python3", "re/automation/runners/Example.py", "{session}"],
      "result_schema": "re/automation/schemas/Example.json",
      "threads": 1,
      "initial_peak_memory_mib": 2048
    }
  }
}
```

The runner and schema paths in this example are placeholders.
The repository does not ship a registry, because no production runner exists yet.

| Field                     | Required | Meaning                                                                                                         |
| ------------------------- | -------- | --------------------------------------------------------------------------------------------------------------- |
| `pool`                    | Yes      | Pool that runs this job kind                                                                                    |
| `argv`                    | Yes      | 1–64 arguments; a whole `{session}` argument is the only substitution                                           |
| `result_schema`           | Yes      | JSON Schema for the `records` value; relative paths resolve from the root                                       |
| `threads`                 | No       | Threads per session, 1–256; recorded for A08b capacity limits                                                   |
| `max_memory_mib`          | No       | Sampled group-memory stop threshold, 1–1,048,576 MiB; default twice the initial estimate, capped at the maximum |
| `initial_peak_memory_mib` | No       | First memory estimate, 1–1,048,576 MiB; recorded for A08b capacity limits                                       |

The schema checker accepts `type`, `properties`, `required`, `additionalProperties`, `items`, `enum`, `const`, `minLength`, `maxLength`, `minimum`, `maximum`, `minItems` and `maxItems`.
It refuses a schema that uses any other keyword.
Model runners such as Codex and Claude are not registry entries yet; they belong to A10.

## Session contract

The supervisor starts each runner without a shell, in a new process group, with the repository root as its working directory.
The environment contains only `PATH`, the locale variables, `TZ`, `KIT_SESSION`, and `HOME` and `TMPDIR` set to `work/`.

| Path           | Writer     | Content                                                                |
| -------------- | ---------- | ---------------------------------------------------------------------- |
| `job.json`     | Supervisor | Job definition, attempt, generation, fingerprint, inputs and `stop_at` |
| `inputs/`      | Supervisor | Copies of the bound input artifacts, named by SHA-256 and verified     |
| `work/`        | Runner     | Temporary files                                                        |
| `result.json`  | Runner     | `outcome`, `reason` and `records`                                      |
| `stdout.log`   | Supervisor | Standard output of the runner                                          |
| `stderr.log`   | Supervisor | Standard error of the runner                                           |
| `session.json` | Supervisor | Process identifier and process start time for restart fencing          |
| `receipt.json` | Supervisor | Exit status, signal, stop reason, duration and peak memory             |
| `finish.json`  | Supervisor | The receipt, the validated result, the error and the `stderr` tail     |

`job.json` never contains the lease token.
Claim files stay in the private `claims/` directory, which runners do not receive.
The runner selects `completed`, `rejected`, `waiting_evidence`, `waiting_ci` or `waiting_application`.

| Runner end                   | Controller outcome | Reason                                   |
| ---------------------------- | ------------------ | ---------------------------------------- |
| Exit `0` with a valid result | Runner's outcome   | Runner's reason                          |
| Exit `0` with a bad result   | `retry`            | `invalid result: ...`                    |
| Exit status other than `0`   | `retry`            | `runner exited with status N`            |
| Signal                       | `retry`            | `runner ended by signal N`               |
| Stopped by the supervisor    | `retry`            | `session stopped: deadline`, for example |
| Stale lease                  | No finish          | The controller has already requeued it   |

`finish.json` becomes the controller result for every finished attempt.
After the controller accepts it, the supervisor removes the session directory and the claim file.

Each output stream retains its first `max_log_bytes` bytes.
The supervisor continues draining additional output so a full log does not block the runner.
Receipts record each stream's limit, observed bytes, retained bytes and dropped bytes.
These counters measure drained output, not bytes a killed process never wrote.
See [bounded session logs](../../Changes/Research/BoundedSessionLogs.md).

## Resource admission and memory stops

The supervisor checks CPU and memory headroom before claiming a job.
Running sessions reserve their configured threads across all pools.
New and growing sessions reserve memory beyond the last host measurement.
The largest registered runner estimate determines admission for each pool.
Use separate pools for runners with materially different estimates.
Denied jobs stay queued without consuming a lease or attempt.
An `admission` event records changes to a pool's blocking reason.

Linux uses `MemAvailable` and available CPU affinity.
macOS uses free pages plus the larger of inactive or purgeable pages from `vm_stat`.
These measurements do not enforce container quotas.
Each supervision pass samples resident memory for the whole process group.
An exceeded `max_memory_mib` stops that group with reason `memory_limit` through the existing retry protocol.
Receipts retain `sampled_group_peak_memory_bytes` and `memory_limit_bytes`.
This sampled threshold is not an operating-system allocation limit.
A missing required measurement stops active sessions and exits after cleanup.
See [resource headroom](../../Changes/Research/ResearchResourceHeadroom.md) for bounds and remaining limits.

## Stops, pauses and stale leases

The supervisor renews each lease at one third of `lease_seconds`.
It stops a session at the execution deadline minus the smaller of `stop_grace_seconds` + 2 and half of `timeout_seconds`.
That margin lets the job finish before the controller deadline.
A stop sends `SIGTERM` to the process group, then `SIGKILL` after the grace period.

A renewal that returns a stale lease stops the session at once and does not finish the job.
The A03 controller reports a stale lease with exit status `3`.

Pause a pool with `pause <pool> --reason <text>`.
The supervisor stops that pool's sessions, finishes them with `retry` and claims no new jobs for the pool.
A stopped attempt counts against the job's attempt budget.
Use `resume <pool>` to remove the pause.

## Restart fencing

The supervisor takes an exclusive lock on `state/supervisor.lock` and on the adapter's lock path.
For A03 that path is `supervisor.lock` in the store.
A second supervisor exits with status `4` and a `supervisor busy` message.

At startup, the supervisor reads each remaining session directory.
It stops the recorded process group only when the process identifier and the process start time both match.
On Linux the start time comes from `/proc/<pid>/stat`; on macOS it comes from `ps -o lstart=`.
It writes an orphan receipt and finishes the job with `retry` if the claim file is still present.
A stale lease is accepted, because the controller has already expired or replaced that attempt.

## Commands

Replace `Supervisor.json` with your configuration file.

```shell
python3 re/automation/Supervisor.py --config Supervisor.json run --idle-seconds 30
python3 re/automation/Supervisor.py --config Supervisor.json status
python3 re/automation/Supervisor.py --config Supervisor.json pause decode --reason "operator hold"
python3 re/automation/Supervisor.py --config Supervisor.json resume decode
python3 re/automation/Supervisor.py --config Supervisor.json submit Batch.json
python3 re/automation/Supervisor.py --config Supervisor.json bind evidence:example Example.bin
python3 re/automation/Supervisor.py --config Supervisor.json jobs --job example
```

`run` prints one JSON event per line and a final `summary`.
Without `--idle-seconds` or `--max-seconds`, it runs until it receives `SIGTERM` or `SIGINT`.
At shutdown it stops its sessions and finishes them with `retry`.
`submit`, `bind` and `jobs` go through the configured adapter, so they work with any adapter.

## Controller adapters

The supervisor calls only these adapter operations: `LockPath`, `DefinePool`, `DefineResource`, `SubmitJobs`, `BindInput`, `ClaimJob`, `RenewLease`, `FinishJob`, `FetchInput` and `ReadStatus`.
`RenewLease` and `FinishJob` return `{"stale": true}` for a stale lease instead of raising an error.
`ClaimJob` writes the lease to the claim file and returns the claim without its token.
The `a03` adapter calls the [controller commands](ResearchController.md#commands) as argument lists.
Another adapter is a Python class loaded from `module` and `class`, with `options` passed to its constructor.
Load only an adapter module that you trust, because the supervisor executes it.

## Limits

These limits are intentional for A08a:

- Adaptive limits, calibration and grouped small-file sessions remain A08b work.
- Output files are bounded. Memory stops use sampled process-group RSS and cannot contain children that leave the group.
- Restart cleanup checks surviving process-group members after leader termination. Failed cleanup prevents releasing the job.
- An expired A03 attempt still marks its resources unavailable, also for counted provider resources.
- Application workers belong to A08c, and model runners belong to A10.

## If the task fails

| Symptom                                   | Action                                                                       |
| ----------------------------------------- | ---------------------------------------------------------------------------- |
| Exit status `4`, `supervisor busy`        | Stop the other supervisor for this state directory or store                  |
| `registry and configuration pools differ` | Make the `pools` keys match the registry pools                               |
| `pool has no registered job kinds`        | Start `run` once, or define the pool with the controller `pool` command      |
| A job stays `queued`                      | Check that a registry pool includes its kind and that the pool is not paused |
| Repeated `renew_error` events             | Check the controller store; the lease expires if renewals keep failing       |

## Related information

- [Parallel research sessions](ParallelSessions.md)
- [Durable research controller](ResearchController.md)
- [Step register](AutomationSteps.md)
