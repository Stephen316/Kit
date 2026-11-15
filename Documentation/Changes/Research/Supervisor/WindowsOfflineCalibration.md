# Windows offline decoder calibration

The research calibration command accepts Windows 10 and newer with Python 3.14 or newer and the repository's locked development environment. The manifest, fixed runner, sweep, overlap threshold and recommendation rules follow the existing operator guide. [Offline calibration operator guide](../../../Reference/Research/OfflineCalibration.md)

The calibration observer owns a noninherited outer Windows Job Object. The supervisor launches its usual nested worker jobs inside it. The observer can sample the aggregate worker working set without opening the worker job objects. It verifies the supervisor interpreter's exact creation time and outer job membership before excluding that interpreter and its launcher from the sample. The nested job list includes descendants even when their session record has yet to appear. [Windows job members](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_process_id_list), [Windows launcher identity](../../../Gotchas/Research/WindowsCalibrationLauncher.md)

The worker reports user and system CPU time and measures its own `PeakWorkingSetSize` through result preparation. The underlying supervisor receipt retains the launcher peak and the sampled session working set. The observer's trial aggregate sums resident working sets at each sample and can count shared pages more than once. [Process CPU times](https://docs.python.org/3.14/library/os.html#os.times), [Working set counters](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-process_memory_counters)

On stop, calibration pauses admission in the trial's private pool and lets the supervisor settle the active workers. If the grace period expires or a dead supervisor leaves a running member, calibration terminates the owned outer job. It verifies the job is empty before recovery proceeds in a separate contained launch. Observer death closes its handle and terminates the entire outer job. A host job that rejects nesting causes the trial launch to fail. [Nested Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/nested-jobs)

The Windows process selection covers the real fixed offline reader sweep, a decoder rejection, explicit termination of a nested worker tree, and abrupt observer exit with a held worker and descendant. The Windows research job passed all 29 selected process cases at `cdf53e1f`. [Windows research job](https://github.com/TryUniCAD/Kit/actions/runs/43693322495/job/132748412625)

## First Windows discovery sweep

On November 15, 2026, the calibration implementation at `b0f223ef` ran on Windows with Python 3.14.6 and pywin32 312. It read 25 receipt-pinned SOLIDWORKS discovery captures at each of four requested concurrency levels. The manifest covers P01, P03 and P04. P02 qualification and P05 holdout inputs were excluded. The worker used one thread per job with a 120-second deadline and the observer reserved two CPUs and 4 GiB of memory.

| Requested workers | Decodes completed | Decodes per minute | Sustained overlap in seconds | Comparable |
| ---: | ---: | ---: | ---: | --- |
| 1 | 25 | 17.03 | 5.807 | Yes |
| 2 | 25 | 32.04 | 2.369 | Yes |
| 4 | 25 | 49.39 | 1.649 | Yes |
| 8 | 25 | 69.69 | 0.210 | No |

All four trials produced the same decoded-output digest `69a83ff3138bd794dfef16aa97d1e1ae8aef57afd74002f5dadf29b9a2d0c8a6`. Job, session and claim cleanup passed with zero forced terminations. CPU and memory telemetry was complete for all 100 decodes. The eight-way run fell short of the one-second overlap requirement. The sweep produced no concurrency recommendation. A comparable saturated trial and independent attribution of an operating-system OOM termination remain open.

The canonical manifest SHA-256 is `31cfa5d61538e6488ab968e3c9e9e31cde4be0b573203bb64aa1d0bad548c2c2`. The private calibration report SHA-256 is `72e0707142d2614263e7666a70c53f48d0cfbd2ae722ffdd16657f02a5a645d4`. The speed and cleanup measurements describe execution of the fixed research reader. Native conversion qualification needs separate evidence.

## Fusion discovery sweep

On November 15, 2026, the Windows calibration at `68181ec830b0b1e4eb3cc8e7e72a2d08b577bf5c` measured 25 distinct receipt-pinned Fusion archives from the P01, P03 and P04 discovery captures. Input sizes ranged from 34,781 to 91,326 bytes. Each job used the fixed `decode.fusion` reader with partial fallback enabled after a strict rejection. It ran with Python 3.14.6 and pywin32 312. Resource settings retained one thread per job, a 120-second job deadline, a 1 GiB sampled worker limit and host reserves of two CPUs and 4 GiB.

| Requested workers | Decodes completed | Decodes per minute | Peak simultaneous decodes | Requested overlap in seconds | Trial meets overlap and measurement criteria |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 25 | 15.82 | 1 | 6.802 | Yes |
| 2 | 25 | 29.09 | 2 | 2.739 | Yes |
| 4 | 25 | 46.58 | 4 | 2.167 | Yes |
| 8 | 25 | 52.67 | 7 | 0 | No |

All 100 jobs supplied CPU and working-set telemetry. Each trial returned decoded-output digest `e5557411b7d15f018cb0db1c4ed5796bc1f153d87b6a5fa4d60888151883c384`. Every trial verified empty sessions, claims and Job Object membership after orderly shutdown. The host retained at least 14.49 GiB of available physical memory, with a peak sampled aggregate worker working set of 375 MiB at the eight-worker request.

The one-to-two and two-to-four comparisons met the existing criteria and improved measured throughput by 83.9% and 60.1%. The eight-worker request held eight active supervisor sessions, but its decoder intervals peaked at seven for 0.149 seconds. The four-to-eight comparison is noncomparable because the trial never reached the eight-way decode overlap required for the one-second window. The sweep returned no concurrency recommendation. Sustained eight-way decoding and independently attributed operating-system OOM backoff remain open.

The calibration source digest is `ff601a0e22e2eb674d5fd84eda80ff3eb9db36b335beaaead838e3c940d327c0`. The canonical manifest SHA-256 is `56236c41ee096c69abc644144a12dd38322a94e4860d068bf18ae9724bb124bc`. The private calibration report SHA-256 is `3d1e6a73af30decb315c4601cb1a0c69811123ef750685eaaee024b59cd770ff`.
