# Keep completed SOLIDWORKS scope cases during collection

Run the existing [through-all scope campaign](ThroughAllScopeControl.md), directly or under the [Windows watchdog](ScopeWatchdog.md). The collector writes `automatic.authoring.checkpoint.json` and the corresponding files for `explicit_a`, `explicit_ab`, and the reopen phase. Each record contains the exact source pins, process identity, archive hash, and measurements available for that case.

The authoring checkpoint follows the save, document close, and archive hash. The reopen checkpoint follows read-only open, both native measurements, rebuild, document close, and confirmation that the archive hash still matches. The collector flushes each record and moves it to its final name inside the private output directory. The checkpoint remains available if a later case fails or the watchdog stops the campaign. The complete `report.json` still requires all three cases and both observed native process exits.

When a case raises an error, the private `failure.json` names its case and last collector step, alongside the original HRESULT and message. A document close error during that failure has its own HRESULT. The diagnostics distinguish input selection, Cut creation, rebuild, save, and native reopen. A hard timeout can leave only the checkpoints already published and the watchdog receipt.

The .NET Framework collector compiled against installed SOLIDWORKS `34.4.1.1011` interop with warnings treated as errors. Windows PowerShell 5.1 parsed the pinned launcher. The licensed collection and failure paths still require native execution.
