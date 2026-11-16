# Start the owned Fusion installation before Phase A

Use the separately provisioned signed-in macOS owner session and its reviewed
[startup profile](../FusionStartupProvision.md). Keep the supervisor running
independently. Use a durable receipt for a pair queued with `--owner-lifecycle`
on the configured capacity-one installation. The first Phase A should be
unattempted and waiting for its initially unavailable resource.

```sh
python3 re/automation/ApplicationWorkers/FusionOwnerColdStart.py \
  --config /private/fusion/Supervisor.json \
  --installation /private/fusion/Installation.json \
  --lifecycle /private/fusion/Lifecycle.json \
  --profile /private/fusion/StartupStage/startup-profile.json \
  --queue-receipt /private/fusion/QueuePair.json
```

The command records a private request and reserves the exact Phase A in A03
before it asks AppKit to launch the reviewed local bundle. It checks for any
live counterpart and an empty endpoint, including no acknowledgement, restart
fence, or retained spool. The request carries a random value passed by AppKit
to a newly launched instance. The exact observed process must prove that
value through the reviewed add-in's vendor startup callback before A03
opens the resource. [Apple launch environment](https://developer.apple.com/documentation/appkit/nsworkspace/openconfiguration/environment)

An interruption before the physical launch request can resume the same
draft. A sealed attempt without exact launch evidence stays parked. An exact
launch receipt resumes startup observation without relaunch. The final
startup evidence and A03 admission reference are durable. The first-claim
reservation admits only the exact Phase A while it is outstanding. Its
accepted result transitions to the [normal restart reservation](../FusionRestartResourceReservation.md).
Existing quarantines, timeout holds, phase deadlines and healthy controls
retain their existing procedures.

AppKit checks the reviewed bundle, attempts no duplicate instance, and
disables activation and substitution. Its new-instance environment binding
keeps admission parked if the selected Fusion version does not deliver it
to the pinned add-in. The result attests to owner startup and initial
admission. Licensed Fusion startup, capture, and native acceptance still
require a signed-in host witness.

The hosted case uses a disposable AppKit bundle, the actual pinned
bootstrap, and A03. It checks interrupted owner launch, missing launch
evidence, observed-peer resume, and an older competing Phase A. Hosted
execution is pending.
