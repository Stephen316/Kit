# Queue the licensed SOLIDWORKS P04 readback

This Windows application worker submits one fixed operation to the local application queue. The owner process runs the existing licensed P04 collector in a fresh SOLIDWORKS session. The collector verifies both healthy controls and all eleven discovery captures before and after rebuild. The controller retains the plan, measurements, receipt and dispatch record as immutable artifacts. [P04 collector and retained evidence](SolidWorksCutFaceReadback.md)

Use the [application installation configuration](LocalApplicationDispatch.md#configure-an-installation) with `application` set to `solidworks`, an owner-private local endpoint and a Git checkout at the exact configured `source_revision`. Start the listener in the licensed Windows desktop with SOLIDWORKS closed. Use the existing Windows supervisor Python environment with pywin32 and supply the installed interop assembly for build `34.4.1.1011`.

```powershell
python re/automation/ApplicationWorkers/SolidWorksReadbackWorker.py --installation <installation.json> listen --interop <SolidWorks.Interop.sldworks.dll>
```

Register a single-session runner with `ApplicationResult.json` as its result schema and the same installation path as `application_installation`. Use the registered runner kind for the job, an empty `inputs` mapping and one `source_revision` option equal to the configured full Git SHA. The revision is part of the controller job fingerprint. Allow enough job time for native startup, eleven rebuilds and application exit. The worker caps the session dispatch at five minutes.

```text
python re/automation/ApplicationWorkers/SolidWorksReadbackWorker.py --installation <installation.json> dispatch {session}
```

Give the installation a counted controller resource with capacity one. Once the listener owns the endpoint, mark the resource available with the controller's `resource <name> --available` command. The listener and native collector still verify each request and application session. [Resource availability](../../../Reference/Research/ResearchController.md)

The listener stages the launcher from Git-verified bytes. The launcher verifies its own copy and the collector, specification, control and P04 archive bytes against the pinned checkout. The job supplies no executable path, CAD path or case selector. The [direct launch](SolidWorks/OwnedReadback.md) binds the collector's COM session to the process created by the listener. The collector closes that process before the host returns a successful phase.

An unavailable listener, stuck COM call or failed native control parks the job behind the application fence. A dedicated unattended desktop can enable [bounded timeout cleanup](SolidWorks/OwnedReadback.md#bound-timeout-recovery) and separately opt into [cleanup after a collector failure](SolidWorks/CollectorFailure.md). Inspect the retained disposition before retrying. On success the supervisor can acknowledge the exact accepted attempt using its configured installation. [Controller acceptance](SupervisedApplicationAcceptance.md)

The readback records its source and native executable hashes. Broader native Windows dispatch, failed COM recovery and paired conversion qualification remain open.

## Licensed job evidence

Two Windows runs used source revision `195d45c7a6a0660dbd633e85872988171f32fd8d` and licensed SOLIDWORKS `34.4.1.1011`. Each run verified both healthy controls, unchanged source bytes and supporting-face identity before and after rebuild for all eleven discovery captures. Each observed its owned SOLIDWORKS process exit. A03 accepted all four output roles and the verification driver read every artifact back from the controller by SHA-256 and size.

| Run | Accepted A03 result SHA-256 | Native measurements SHA-256 |
| --- | --- | --- |
| Uninterrupted | `0118bbe8c36e9e6c063fce955c5f56050c56ce47745237ddcda1026d2d6728c5` | `9c13a5017d39e073266662391c657eaba9a8d70ceb8ec710066ac150e6361f31` |
| Supervisor interrupted after durable finish | `6fb3373a27b793ebdc5f66056a4cff93761ac31d77d522d7dc0b93e963fdc059` | `68a072c111f9a2e5d3334766fdaac7b3a0a3d1e43477f37325177bbeffc0e55c` |

The uninterrupted run acknowledged the spool automatically after controller acceptance. In the interruption run, the initial supervisor exited after the real `FinishJob` accepted the job and before acknowledgement began. The private intent and acceptance fence remained present. The replacement supervisor reported `recovered: true` and `status: acknowledged`, cleared the spool and left the accepted receipt, result, generation, fingerprint and attempt unchanged. It issued zero additional claims. [Restart recovery contract](ApplicationAckRecovery.md)

## Direct native process ownership

A separate Windows prototype starts the exact installed executable without arguments and keeps the process handle returned by creation. An STA client waits for passive `GetActiveObject` attachment, reads `ISldWorks.GetProcessID`, and confirms the same PID, creation FILETIME, canonical executable and desktop session. The licensed build reported revision `34.4.1` and zero initial documents. The attached client opened and rebuilt the pinned healthy control in read-only mode with zero open errors or warnings, closed it, and requested application exit. The launch handle signaled exit. The control and scratch copy retained their original SHA-256. [Passive attachment](https://learn.microsoft.com/en-us/windows/win32/api/oleauto/nf-oleauto-getactiveobject), [Windows process handles](https://learn.microsoft.com/en-us/windows/win32/procthread/process-handles-and-identifiers), [Creation time](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes)

The executable SHA-256 is `200ac2597814daaead89c1de698a45341850fa2fe0d8c094debb316009e7ea7f`. The control SHA-256 is `d1bbca099ccac1330024619390df3c6b76320a6a6c281a5009578b2fb63e7408`. The queued implementation binds the ownership ticket to the request and uses the retained launch handle for bounded timeout recovery. A licensed normal run and a short-deadline run verified both paths. [Licensed queue verification](SolidWorks/OwnedReadback.md#licensed-queue-verification)
