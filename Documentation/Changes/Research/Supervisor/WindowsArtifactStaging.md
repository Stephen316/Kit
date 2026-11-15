# Windows A03 artifact staging

The built-in Windows supervisor adapter resolves bound artifacts in its own process after the controller installs the supervisor owner. The lookup uses a read-only SQLite transaction on the initialized version-4 store and checks the owner with the same recovery fence used by the controller. The existing artifact path rules, 256 MiB byte ceiling, digest verification and verified copy apply. The store lookup creates no file or directory. The only new bytes go to the exclusive private session input file. [Session input contract](../../../Reference/Research/ResearchSupervisor.md#session-contract)

Direct A03 clients, including native application acknowledgement, use the controller command route. Other hosts and custom adapters continue to use their configured input paths. Owner installation, claims, lease renewal, settlement and recovery remain controller operations.

The Windows process check stages a valid bound input, replaces the owner through the controller, and verifies refusal for the old owner and for modified artifact bytes. It checks the contents of the staged file and the unchanged ledger bytes after a successful lookup. Its separate interpreter uses the built-in adapter loader with the artifact subprocess unavailable, so the exercise reaches the new path. Remote verification is pending.

## Matched Windows calibration

The Windows run at `86338a90516df8f1eef9d4495b65cec981f06aa2` used the prior 32-archive Fusion discovery manifest. The decoder sources, package inventory and resource limits were identical. The canonical manifest SHA-256 is `a86e1ecfa76b5ce8c9a5698dd0e034378644105695b6c594bc8369ba00591620`. Both runs completed 32 jobs per trial and returned identical decoded-output digests with complete CPU and working-set telemetry. Every trial verified ordinary shutdown and empty Job Object membership, claims and sessions. [Historical calibration baseline](WindowsOfflineCalibration.md)

| Requested workers | Baseline decodes per minute | In-process decodes per minute | In-process overlap in seconds |
| ---: | ---: | ---: | ---: |
| 1 | 15.48 | 15.26 | 8.292 |
| 2 | 32.52 | 33.18 | 2.725 |
| 4 | 53.81 | 53.05 | 2.372 |
| 8 | 68.22 | 73.48 | 1.976 |

The eight-way decoder overlap increased from 0.554 to 1.976 seconds, clearing the existing one-second requirement. All adjacent in-process trials were comparable. The four-to-eight throughput gain of 38.5% exceeded the existing 10% threshold for a plateau. The sweep produced no recommendation through eight workers. Independent operating-system OOM attribution remains open.

The first eight supervisor start records span 1.402 seconds, compared with 3.084 seconds in the baseline. Across the seven gaps, the sum of the session-construction-to-launcher-creation intervals fell from 1.456 to 0.084 seconds. The timings combine claim, staging and launch operations at their recorded boundaries. Host background load and run-to-run variation remain uncontrolled.

The calibration source digest is `bdfcc94936c34716fe59482fcdef4a8bb7479fa474789b52d90399d42b7b9634`. The private calibration report SHA-256 is `419b4c497181006b979825467a6c8ab016b8a52084b62583af7489de6fbcf24a`.
The shared read-only lookup also paged all 163 controller events from the optimized eight-worker calibration across two pages. The audit recovered 32 claim and 32 completion events in contiguous ID order with the source database digest unchanged.
