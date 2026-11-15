# Pre-claim tool versions are unknown

## Expectation

A memory estimate learned for one runner version can appear suitable for the next job with the same kind.

## Actual behavior

The controller's `ClaimJob` operation returns the job's `tool_version` only after creating its lease.
The preceding admission check knows the pool and runner kind, but cannot identify the next job's version.
Using a small learned estimate at that point can admit a larger, previously unmeasured version.
The source boundary is [the controller adapter](../../../../re/automation/Adapters.py).

## Workaround

Keep histories separate by kind and tool version.
Use an exact-version learned estimate only after that version is known.
For pre-claim admission, retain the registry estimate and any higher learned estimate across recorded versions.
Do not claim and hold a job merely to discover that it cannot fit.
A future version-aware selection interface can remove this conservative reservation.

See [the memory-estimate change entry](../../../Changes/Research/Supervisor/VersionedMemoryEstimates.md).
