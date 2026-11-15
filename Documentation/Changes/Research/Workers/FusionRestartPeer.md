# Verify the macOS peer for a Fusion restart

After the [owner restart intent](FusionOwnerRestart.md) has been recorded for an acknowledged Phase A, the installation owner can verify which live macOS process the handoff names. Run the command from the unprivileged login that owns both Fusion and the installation endpoint.

```sh
python3 re/automation/ApplicationWorkers/FusionRestartPeer.py \
  --installation /private/fusion/Installation.json \
  --store /private/fusion/Store \
  --queue-receipt /private/fusion/QueueReceipt.json \
  --lifecycle /private/fusion/Lifecycle.json
```

Keep `Lifecycle.json` in an owner-private directory and pin the exact installation configuration and reviewed physical application bundle. Use lowercase SHA-256 values of the named files.

```json
{
  "version": 1,
  "installation_sha256": "SHA256_OF_INSTALLATION_JSON",
  "bundle": "/absolute/physical/path/Autodesk Fusion.app",
  "info_sha256": "SHA256_OF_CONTENTS_INFO_PLIST",
  "executable_sha256": "SHA256_OF_CONTENTS_MACOS_BUNDLE_EXECUTABLE"
}
```

The `CFBundleExecutable` value in the pinned `Contents/Info.plist` identifies the executable under `Contents/MacOS`. A path alias, different bundle copy, changed plist or executable pin, different process owner, or process born after the accepted handoff fails verification. Darwin's process metadata supplies the executable path, real and effective UID, and process creation time in microseconds. The command compares the creation second with the accepted host record and verifies that the process existed at the handoff time. It rechecks the peer, intent, accepted attempt and file pins before returning. [Darwin process metadata](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/sys/proc_info.h), [Darwin process library](https://github.com/apple-oss-distributions/xnu/blob/main/libsyscall/wrappers/libproc/libproc.h)

The result binds the observed process to the installation and intent digests. It reports the PID, owner UID, creation time, bundle identifier and bundle file digests. Any later automated quit requires owner authorization and a fresh main-thread idle and empty-document check. Relaunch also requires verified graceful exit and proof from the replacement add-in before Phase B admission. Apple exposes normal quit and separate termination observation through its per-application instance object. [Apple application instance lifecycle](https://developer.apple.com/documentation/appkit/nsrunningapplication)

A macOS hosted fixture compiles a disposable process into a temporary bundle. It covers stable kernel identity, a creation time later than the handoff and rejection of a second bundle with identical executable bytes. Hosted execution and signed-in Fusion verification are pending. Use the [restart readiness command](FusionRestartReadiness.md) to request a fresh main-thread observation after verifying the peer.
