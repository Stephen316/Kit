# Request the pinned Fusion replacement

Use a signed-in macOS owner session and a reviewed installation revision containing the restart tools and add-in. A working Swift toolchain must already be selected. Start with the immutable intent and exit receipt from the [exact Fusion exit observer](FusionQuitObserver.md).

```sh
python3 re/automation/ApplicationWorkers/FusionReplacementLaunch.py \
  --installation /private/fusion/Installation.json \
  --store /private/fusion/Store \
  --queue-receipt /private/fusion/QueueReceipt.json \
  --lifecycle /private/fusion/Lifecycle.json \
  --quit-intent-sha256 QUIT_INTENT_SHA256 \
  --quit-exit-sha256 QUIT_EXIT_RECEIPT_SHA256 \
  --request-launch
```

The command verifies both artifact hashes, the accepted controller attempt, the unchanged restart fence, the pinned physical bundle and the prior process exit. It checks add-in ownership and seals one launch request before calling LaunchServices. It releases the dispatch lock before launch so the replacement's normal startup and Phase B can proceed. A separate owner lock serializes launch requests. [Dispatch lock timing](../../../Gotchas/Research/Workers/FusionLaunchDispatchLock.md)

The reviewed Swift helper rechecks the plist, executable, sealed request and retained fence before using the exact application URL. A live AppKit counterpart with that bundle identifier or path prevents launch. AppKit substitution and duplicate-instance requests are disabled. The reply must identify a new same-owner process whose exact executable and kernel creation time match the request. An uncertain launch leaves the sealed request available for owner inspection. [Apple exact-URL launch](https://developer.apple.com/documentation/appkit/nsworkspace/openapplication%28at%3Aconfiguration%3Acompletionhandler%3A%29), [AppKit substitution control](https://developer.apple.com/documentation/appkit/nsworkspace/openconfiguration/allowsrunningapplicationsubstitution)

The provider compares Darwin physical paths with the supplied bundle, executable and custody pins. This keeps canonical paths under `/private` comparable between Python and the provider, with caller-supplied symbolic links refused. [Foundation path aliases](../../../Gotchas/Research/Workers/FoundationPrivatePathAlias.md)

Save the returned `launch_receipt_sha256`. To inspect native completion, run the same command with `--observe-phase-b --launch-receipt-sha256 LAUNCH_RECEIPT_SHA256` in place of `--request-launch`. This read-only observation reads the existing Phase B result. It checks the same live kernel peer, the accepted native readiness probe digest, exact bootstrap and queue protocol source pins, same Fusion version, and the Phase A dependency. A pending or parked Phase B reports its controller state. The launch receipt by itself records process identity. Existing application readiness, deadlines and resource recovery still govern the queued phase.

The hosted macOS fixture uses a disposable AppKit bundle to exercise normal launch, changed byte pins, a linked launch request, a changed retained fence, duplicate refusal and observed natural cleanup. Its refusal controls require the intended provider exit and reason. Failed fixture launches include the exit status and a bounded stderr excerpt. The exit fixture also checks the exact artifact pins used by replacement intake. The first hosted run reached an unspecified provider failure on the positive case. A subsequent hosted result and signed-in Fusion acceptance are pending. [Initial hosted job](https://github.com/TryUniCAD/Kit/actions/runs/43770822331/job/132986201023), [Provider failure detail](../../../Gotchas/Research/Workers/MacLaunchProviderRefusal.md)
