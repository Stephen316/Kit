# Record the exact Fusion process exit

After A03 has accepted and acknowledged Phase A, record the [restart intent](FusionOwnerRestart.md) and use the installation's pinned [macOS lifecycle profile](FusionRestartPeer.md). Run this command under the unprivileged owner account on the licensed Fusion host.

```sh
python3 re/automation/ApplicationWorkers/FusionQuitObserver.py \
  --installation /private/fusion/Installation.json \
  --store /private/fusion/Store \
  --queue-receipt /private/fusion/QueueReceipt.json \
  --lifecycle /private/fusion/Lifecycle.json \
  --wait-seconds 60
```

The command holds the installation's dispatch lock, consumes a [fresh main-thread readiness grant](FusionRestartReadiness.md), and checks the exact macOS peer immediately before and after registering its kernel exit watch. Once the command reports that the watch is armed, confirm that the owned Fusion session is still idle and use its normal Quit command. Leave the restart fence intact until the watch finishes. A process that disappeared before registration is refused. A watched executable replacement also fails observation. [Darwin process event filters](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/kqueue.2.html)

The private endpoint retains `quit-intent-<digest>.json`, with the exact grant and its consumption response. A matching `quit-exit-<digest>.json` records the exact process, kernel exit observation, accepted restart intent and retained fence. The command rechecks the accepted A03 attempt and endpoint custody before it publishes the receipt. The receipt records the cause as unverified. Expiry leaves the intent and returns `exit_unobserved` with status code 2. An interrupted watch cannot be restored retroactively after that process is gone.

An owner can separately opt into the [guarded Cocoa quit](FusionArmedCocoaQuit.md) on a dedicated reviewed installation. The hosted and licensed acceptance boundaries are tracked there.

Autodesk's public Fusion `Application` API provides main-thread custom events and document inspection. The vendor API does not expose a normal quit method. Apple's AppKit quit API implements a normal application request, while the corresponding Fusion application-instance invocation and its delegate behavior still require a signed-in witness. The operator performs the quit in this checkpoint. An unattended follow-up needs a guarded quit request at the fresh main-thread decision, verified exit, a launch of the pinned bundle under the same owner, and replacement add-in startup plus the existing Phase B admission checks. [Autodesk Application API](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_Application.htm), [Apple normal app quit](https://developer.apple.com/documentation/appkit/nsapplication/terminate%28_%3A%29)

The hosted macOS fixture starts separate disposable target and observer processes. The cases cover live exit, a disappeared or mismatched peer, deadline expiry, executable replacement and a changed fence after arming. The [owner-directed replacement command](FusionReplacementLaunch.md) consumes the verified exit when requesting the pinned bundle.

At PR head `445b4e78`, the hosted macOS job passed the disappeared and mismatched peer cases. Four other cases failed before the fixture reported its armed marker. The fixture now checks the durable marker when the observer exits and includes the observer's bounded output on early failure. Signed-in Fusion verification is pending. [Hosted macOS results](https://github.com/TryUniCAD/Kit/actions/runs/43767713654/job/132976461568)
