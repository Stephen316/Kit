# Local application dispatch

The research application runner can dispatch pinned Fusion fresh-process phases
through the existing local `KitCaptureRunner` add-in queue. This implements a
bounded A08c slice. Automatic application launch/restart, batch scheduling,
utilization targets and native qualification remain open.

## Configure an installation

Create an owner-private endpoint directory. Keep installation configuration under
the host owner's control; a queued request cannot select its trusted revision.
Use this configuration shape, replacing the paths and revision:

```json
{
  "version": 1,
  "installation": "fusion:local",
  "application": "fusion",
  "endpoint": "/private/path/fusion-endpoint",
  "source_root": "/absolute/path/Kit",
  "source_revision": "0123456789abcdef0123456789abcdef01234567"
}
```

The revision must contain the dispatcher and all capture inputs. Keep that
trusted repository snapshot unchanged. Copy the `KitCaptureRunner` folder,
including its manifest, to the Fusion add-in location. Its existing `config.json`
keeps `allowed_root` pointing to `re/automation/PairedCaptures`; add `dispatch`
pointing to the installation configuration file. Reload the add-in after changing
the trusted revision. Startup rejects a stale bootstrap snapshot.

Register a runner with this argument list:

```text
python re/automation/ApplicationWorkers/FusionApplicationWorker.py --installation /absolute/Installation.json {session}
```

Use `re/automation/ApplicationWorkers/ApplicationResult.json` as its result schema.
Give each installation one counted controller resource with capacity 1. Jobs that
need this installation declare that resource. Resource availability permits a
claim; it does not establish application health.

## Submit a phase

Prepare a plan with the existing `FusionFreshProcess.py` tool at the same trusted
revision. Bind `plan.json` as the input role `plan`. The job takes exactly one
option, `phase`, whose value is `a` or `b`. Recipe selection is pinned inside the
prepared plan.

For phase B, also provide these exact input roles from the accepted phase A
artifacts:

- `phase-a.receipt` and `phase-a.measurements`.
- `phase-a.accepted`, containing the accepted controller result record. The phase B
  job must depend on that completed phase A job; its dependency result digest and
  accepted output manifest must bind every supplied phase A file.
- `phase-a.P01`, `phase-a.P02`, `phase-a.P03` or `phase-a.P04`, for each selected
  recipe's saved baseline A archive.

The existing artifact and binding operations can prepare those inputs. Automatic
publication of downstream input bindings is not implemented by this slice.

The worker submits a fresh random challenge. The add-in services it on Fusion's
main thread, opens and recomputes the pinned healthy control, and closes only its
owned documents. A phase requires that successful control from the same process
and plan, measured within 60 seconds. The challenge itself has a 30-second limit;
the complete dispatch uses the smaller of the remaining session budget and five
minutes. `runner.json` is never accepted as readiness evidence.

The counterpart invokes only the fixed `run_phase` entry point from
`FusionFreshProcess.py`. Protocol, counterpart, tool, helper, binding helper,
specification and control inputs must match the host's configured Git revision.
Executable helpers compile from freshly verified captured bytes. Dispatch proof
records loaded source hashes. Requests cannot supply script, code or module paths.

## Ownership, outputs and restart

Application output stays in a private installation spool while the request runs.
Completed files copy into the session's private `work` directory with verified
size/hash pins, then use durable output intake. Only a completed, copied spool is
removed. Cancellation and timeout quarantine the installation; late results expose
no accepted output references. Active or quarantined spool files survive session
cleanup for the external application owner's investigation.

Phase A emits a restart-required handoff containing the installation, plan hash
and old application process identity. The add-in then refuses more work in that
process. The external owner must exit and restart Fusion. Phase B checks a new
process identity and the actual old process exit; the existing fresh-process
helper also enforces its capture-specific restart checks.

The dispatcher never quits or kills externally owned CAD. Unknown-owner
quarantines require explicit owner recovery. A known old-process fence can clear
when a new counterpart starts after that old process exits. Automatic recovery,
50-job resets, native-process memory limits, 20-job batch invalidation, spool
retention policy and unattended pilot evidence remain open A08c work.

The native operation currently supports macOS Fusion. Windows Fusion and
SOLIDWORKS configurations return `waiting_application`. Missing, busy or fenced
hosts also park the application job. Independent jobs continue; dependent jobs
wait under the existing controller rules.

## Verification

`tests/Research/Applications` adds real process/file protocol cases for queue
exchange, exclusive counterparts, process-owned restart fences, dead clients,
late output, untrusted revisions, fixed entry points and independent-job progress.
The protocol fixture identifies itself as `fixture.transport`, emits
`native_qualified: false` and does not call CAD APIs. It cannot qualify native
application behavior. Windows exercises the absent/unsupported-host cases only.

Local execution was limited to AST, steering, Mypy, Pyright, formatting and
whitespace checks. Remote process execution and licensed native-host execution
remain pending. No captured native pair is qualified by this implementation.

See [the main-thread availability gotcha](../../../Gotchas/Research/Workers/FusionMainThreadAvailability.md).
