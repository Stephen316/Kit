# Bound the standalone SOLIDWORKS scope campaign

On the dedicated licensed Windows desktop, run the existing pinned scope collector under the research watchdog. Use the Windows supervisor Python environment with pinned `pywin32`, a clean checkout at the chosen revision, an owner-private output parent, and SOLIDWORKS closed.

```powershell
python -B re/automation/ScopeWatchdog.py `
  --source-revision <full-commit> `
  --output-directory <new-private-run-directory> `
  --timeout-seconds 300
```

The watchdog checks the source pins, preserves the signed-in owner's Windows profile, and launches the existing Windows PowerShell 5.1 command inside one private no-breakaway Job Object. The authoring and reopen phases launch their native processes directly, so their children inherit this job. The job handle stays in the watchdog. On timeout, the watchdog terminates its job and verifies that the kernel reports zero members. Existing CAD processes outside that job stay untouched. Use the watchdog only when all descendants of this scratch campaign can be stopped at the deadline. [Windows Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)

The campaign writes its original artifacts under `scope/`. The outer `launch.json` records the exact collector and named job. `watchdog.json` records the outcome, exit status, job-drain observation, bounded logs, and the sealed report digest on a completed run. A confirmed timeout exits with status `124`. An unconfirmed drain exits with status `1` and retains its diagnostic. Partial output remains private and supplies no completed result. If the watchdog itself is stopped before settlement, the kill-on-close job still provides containment and the launch record may be the only receipt.

The hosted disposable fixture exercises the same watchdog with a blocked process and a direct child. Its assertions require both to drain while an identical executable outside the private job stays alive. Hosted execution and a licensed scope campaign remain pending.
