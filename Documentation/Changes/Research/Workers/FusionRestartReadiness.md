# Obtain fresh Fusion restart readiness evidence

After Phase A has been accepted and acknowledged, register the exact [owner restart intent](FusionOwnerRestart.md) and configure the pinned [macOS application peer](FusionRestartPeer.md). Load the add-in bootstrap, queue protocol and readiness handler from the same reviewed installation revision. Use this command from the owner account on the macOS Fusion host.

```sh
python3 re/automation/ApplicationWorkers/FusionRestartReadiness.py \
  --installation /private/fusion/Installation.json \
  --store /private/fusion/Store \
  --queue-receipt /private/fusion/QueueReceipt.json \
  --lifecycle /private/fusion/Lifecycle.json
```

The command holds the installation's dispatch lock and verifies the accepted A03 attempt, retained fence, exact intent and live macOS peer. It sends a private challenge to the loaded add-in in a separate mailbox. Fusion delivers its custom event on the main thread when idle. The handler checks the retained fence, installation configuration bytes, loaded provider source, prior process, exact Fusion version and empty document collection. [Autodesk custom events](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_Application_fireCustomEvent.htm), [Autodesk application documents](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_Application.htm)

The grant expires after at most 20 seconds. The requester rechecks A03 acceptance and the exact bundle and OS process before requesting consumption. A second main-thread callback requires the same challenge, provider, handoff and requester. It rechecks the application and atomically consumes the grant once. A newly opened document, expired grant, released dispatch lock or a different retained fence keeps the gate closed. The returned digests and process identity describe the completed observation. The endpoint's ordinary queue and restart fence remain under their existing owners.

This observation is a prerequisite for a separate authorized quit action. That action needs a fresh equivalent main-thread decision at the point of quit, an exact application-instance target, and observed exit under the same owner deadline. Relaunch must target the pinned physical bundle and show the new exact process loaded the trusted add-in. Phase B continues to require native startup and a fresh control under its existing fence and deadline.

The hosted macOS fixture runs the pinned add-in bootstrap in a separate disposable process with an event-source stand-in. It exercises issuance and one-use consumption, a document open during issuance or revalidation, owner-lock refusal, a changed fence and expiry. Hosted fixture execution and signed-in Fusion verification are pending.
