# Queue admission needs the job directory before checking retention

## Expectation

A client can queue a request in an owner-private endpoint before the counterpart starts.

## Actual behavior

The one-retained-spool admission check enumerated `endpoint/jobs` before the client created that directory. When the endpoint existed but the counterpart had never started, the client exited before publishing a request.
The [macOS run at `6fb599a9`](https://github.com/TryUniCAD/Kit/actions/runs/43672428040/job/132685202111) failed both pre-counterpart cases with no request published; source inspection identified the premature enumeration.

## Workaround

Create and validate the private job directory while holding the client dispatch lock, then check for existing spools and allocate one request directory.
This preserves the one-spool bound and does not treat a queued request as application health.
The dead-client and untrusted-revision process cases retain their original refusal requirements; exact-head remote verification remains required.
See [local application dispatch](../../../Changes/Research/Workers/LocalApplicationDispatch.md).
