# Queue licensed SOLIDWORKS discovery readback

This Windows application worker submits a fixed discovery operation to the local application queue. The owner process starts a fresh SOLIDWORKS session. The collector verifies both healthy controls and measures the selected capture set before and after rebuild. The controller retains the plan, measurements, receipt and dispatch record as immutable artifacts. [P04 collector and retained evidence](SolidWorksCutFaceReadback.md)

Use the [application installation configuration](LocalApplicationDispatch.md#configure-an-installation) with `application` set to `solidworks`, an owner-private local endpoint and a Git checkout at the exact configured `source_revision`. Start the listener in the licensed Windows desktop with SOLIDWORKS closed. Use the existing Windows supervisor Python environment with pywin32 and supply the installed interop assembly for build `34.4.1.1011`.

```powershell
python re/automation/ApplicationWorkers/SolidWorksReadbackWorker.py --installation <installation.json> listen --interop <SolidWorks.Interop.sldworks.dll>
```

Register a single-session runner with `ApplicationResult.json` as its result schema and the same installation path as `application_installation`. Use the registered runner kind for the job, an empty `inputs` mapping and one `source_revision` option equal to the configured full Git SHA. The revision is part of the controller job fingerprint. Allow enough job time for native startup, eleven rebuilds and application exit. The worker caps the session dispatch at five minutes.

```text
python re/automation/ApplicationWorkers/SolidWorksReadbackWorker.py --installation <installation.json> dispatch {session}
```

Give the installation a counted controller resource with capacity one. Once the listener owns the endpoint, mark the resource available with the controller's `resource <name> --available` command. The listener and native collector still verify each request and application session. [Resource availability](../../../Reference/Research/ResearchController.md)

The listener stages the launcher from Git-verified bytes. The launcher verifies its own copy and the collector, specification, control and discovery archive bytes against the pinned checkout. The listener and registered runner agree on the fixed operation. The [direct launch](SolidWorks/OwnedReadback.md) binds the collector's COM session to the process created by the listener. The collector closes that process before the host returns a successful phase.

An unavailable listener, stuck COM call or failed native control parks the job behind the application fence. A dedicated unattended desktop can enable [bounded timeout cleanup](SolidWorks/OwnedReadback.md#bound-timeout-recovery) and separately opt into [cleanup after a collector failure](SolidWorks/CollectorFailure.md). Inspect the retained disposition before retrying. On success the supervisor can acknowledge the exact accepted attempt using its configured installation. [Controller acceptance](SupervisedApplicationAcceptance.md)

The readback records its source and native executable hashes. Broader native Windows dispatch, failed COM recovery and paired conversion qualification remain open.

## P01 and P03 rectangle readback

For this discovery set, add `--readback-operation p01-p03-readback` before `listen` in the owner command and before `dispatch` in the runner command. The job has empty inputs and options for the same `source_revision` and `"readback_operation": "p01-p03-readback"`. The fixed roster comes from the six P01 and eight P03 receipt entries. The collector records the principal datum, native sketch transform, four world edges, dimensions and constraint operands. For P03 it also records the selected Boss profile, blind length and direction, and solid measurements. Both before- and after-rebuild observations come from read-only copies.

The licensed job at `e73200e83bf1456767595a8a92910fee5f21f9bc` used build `34.4.1.1011`. It observed all fourteen profiles, passed both healthy controls, and verified unchanged input bytes and owned process exit. A03 accepted the job on its first attempt and acknowledged its spool. The accepted result SHA-256 is `ee200894ec059271e434f1a99f059d6d84067bf1dc2b6bb4567fef5247415e91`. The readback receipt SHA-256 is `54a4a653c457ea2a749c37aec07de9ab6cbfcafbbbd379cd18f721cc7612e1bb`. The paired qualification still needs a fresh Fusion process.

The same revision also completed the default P04 job. It observed all eleven support faces before and after rebuild and acknowledged the owned spool. The accepted result SHA-256 is `8d5f91a81ce96de4008f62dd76d25e71c6e102749d9f5b8057c576787f7b5df8`. The [body comparison](../Readers/Comparison/HistoricalCutBodyEvidence.md) verified the fresh measurements against the historical Fusion observations. All eleven pairs matched within the declared tolerances before and after rebuild. The comparison report SHA-256 is `e16ad320d939ae1a0ce8de9036d16b6b681405906579ebc89fdb35c6b1577eeb`.

The principal rerun at `0d527bb9ec59f7728545cd6aacfa98eb5951549b` tied every P03 blind depth to its owned driving display dimension before and after rebuild. The observed values were 10 mm and the 12 mm edit, including 10 mm in the inch-display and reversed variants. The accepted result SHA-256 is `389b6ab976b47c5f10f36e867844b65244d701526b4db993b524c60ffc00b230`. The readback receipt SHA-256 is `4ecb6df6818c6d3d194c326e0bb10ddfc7cdf0947f975a2749444eb44e249ffe`. [Principal readback comparison](SolidWorks/PrincipalReadback.md)

At that revision a separate 25-second deadline run verified principal-scope timeout recovery. The worker confirmed exit on the first owned process handle, A03 archived the failed request, and the supervisor issued exactly one further attempt. The second deadline exhausted the retry budget and preserved the quarantine. The first archive manifest SHA-256 is `c86b44fe62a4e68f94cd828c99e3517a30c34610e732c6198de11f4f0adb5025`.

The run at `60fb1c73d83fdd62cd93f1e8271a94fb2ea55c02` repeated that sequence with the single-cancellation change. It confirmed owned exit and preserved 25 files in the first archive. The second attempt exhausted the configured budget and retained its quarantine. The first archive manifest SHA-256 is `dfc8a653899a14ae5f9ddc083f91301aaeaf10418b20f089276bd37a2172adaf`. [Application timeout cancellation](SingleTimeoutCancellation.md)

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
