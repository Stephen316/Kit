# Queue the licensed SOLIDWORKS P04 readback

This Windows application worker submits one fixed operation to the local application queue. The owner process runs the existing licensed P04 collector in a fresh SOLIDWORKS session. The collector verifies both healthy controls and all eleven discovery captures before and after rebuild. The controller retains the plan, measurements, receipt and dispatch record as immutable artifacts. [P04 collector and retained evidence](SolidWorksCutFaceReadback.md)

Use the [application installation configuration](LocalApplicationDispatch.md#configure-an-installation) with `application` set to `solidworks`, an owner-private local endpoint and a Git checkout at the exact configured `source_revision`. Start the listener in the licensed Windows desktop with SOLIDWORKS closed. Supply the installed interop assembly for build `34.4.1.1011`.

```powershell
python re/automation/ApplicationWorkers/SolidWorksReadbackWorker.py --installation <installation.json> listen --interop <SolidWorks.Interop.sldworks.dll>
```

Register a single-session runner with `ApplicationResult.json` as its result schema and the same installation path as `application_installation`. Use the registered runner kind for the job, an empty `inputs` mapping and one `source_revision` option equal to the configured full Git SHA. The revision is part of the controller job fingerprint. Allow enough job time for native startup, eleven rebuilds and application exit. The worker caps the session dispatch at five minutes.

```text
python re/automation/ApplicationWorkers/SolidWorksReadbackWorker.py --installation <installation.json> dispatch {session}
```

The listener stages the launcher from Git-verified bytes. The launcher verifies its own copy and the collector, specification, control and P04 archive bytes against the pinned checkout. The job supplies no executable path, CAD path or case selector. SOLIDWORKS startup identifies the process by canonical executable, Windows desktop session and creation time. The collector closes the owned process before the host returns a successful phase.

An unavailable listener, stuck COM call or failed native control parks the job behind the application fence. Inspect the retained spool and have the installation owner recover the app process before retrying. On success the supervisor can acknowledge the exact accepted attempt using its configured installation. [Controller acceptance](SupervisedApplicationAcceptance.md)

The readback records its source and native executable hashes. Broader native Windows dispatch, failed COM recovery and paired conversion qualification remain open.
