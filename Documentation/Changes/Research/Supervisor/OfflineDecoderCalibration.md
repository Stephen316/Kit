# Offline decoder calibration

The standalone research command `python3 re/automation/Calibration.py --manifest <file> --output <unused-directory>` measures one explicit offline decode workload at requested concurrency 1, 2, 4, and 8.
It does not add an installed CLI command or a supervisor subcommand.
Linux and macOS require Python 3.14 or newer. Windows calibration is unavailable.

The immutable manifest selects the fixed SOLIDWORKS or Fusion offline reader, lists every independent job and input digest, and declares its resources and positive CPU and memory reserves.
Dependencies, application or model kinds, arbitrary commands, grouping options, missing resources, and mismatched input hashes are rejected.
The tool never reads or clones a live queue and never removes job dependencies or resources.

Each requested step gets a fresh controller database, artifact store, supervisor state, runner registry, and memory history.
Job IDs, options, resource capacities and availability, rule versions, and tool versions remain the same across steps.
The private controller maximum and pool maximum equal the requested step.
Adaptive limits are disabled.
The generated registry has no grouping fields, and its actual runtime interpretation must retain `group_protocol=None` and the fixed single-job argument list.
The report records that contract and registry hash.

The worker records monotonic decoder intervals, process CPU time, a neutral serialization hash, and model counts.
Existing supervisor receipts supply physical process peak RSS and sampled process-group RSS.
The observer records host headroom and sampled aggregate active-group RSS.
Requested concurrency is reported separately from actual decoder overlap.
Scheduler start and finish timestamps do not establish measured overlap.

A trial is complete for comparison only when every explicit job completes once, its physical measurements are present, no resource limit or interruption invalidates the trial, and the requested decoder overlap is sustained for at least one second.
That duration is a declared policy threshold; it is not native CAD acceptance or proof that every CPU is fully occupied.
Only complete adjacent steps with matching input, source, environment, registry, host-topology, and decoded-output fingerprints can be compared.
If measured throughput improves by less than ten percent, the previous measured step can be recommended.
No recommendation extrapolates beyond a measured step.
Resource-constrained and insufficient-workload trials remain incomplete.

Reserve loss, child failure, measurement failure, interruption, or timeout stops the active trial.
Graceful supervisor cleanup runs first.
The forced POSIX fallback freezes only the owned supervisor, records descendant group creation identities, stops that supervisor group, and stops residual owned groups through the existing identity-checked cleanup.
Private state and receipts remain available for inspection.
Cleanup failures cannot produce a completed calibration or recommendation.
When a recorded group leader has disappeared, a refused identity-checked stop is accepted only if the existing conservative group probe proves that no running descendants remain; an unverified surviving group is not signaled or declared cleaned.

No calibration, decoder experiment, collection, or test ran locally for this addition.
Static syntax, formatting, and source checks provide local evidence only.
New remote process/file cases cover private-store isolation, fixed runner interpretation, actual decode counters, resource-limited non-recommendation, refused manifests, a decoder rejection, timeout, interruption, and forced cleanup after stopping the owned supervisor.
An additional real process case reaps a group leader while retaining its child and requires cleanup refusal without signaling the unverified group.
At source checkpoint `2ff967671c20758d56131d37708f9812aabbef40`, the [macOS process gate](https://github.com/TryUniCAD/Kit/actions/runs/43676632437/job/132698100852) passed all 74 selected cases in 501.85 seconds, including these 14 calibration cases.
Linux and current-head reruns remain required.
No comparable saturated performance trial has been established by those fixtures.

This is an A08b implementation slice.
It does not qualify captured native pairs, reader semantics, conversion, native application loadability, grouped runtime behavior, or Windows measurement support.
See [the operator guide](../../../Reference/Research/OfflineCalibration.md) and [the measurement gotcha](../../../Gotchas/Research/CalibrationConcurrency.md).
