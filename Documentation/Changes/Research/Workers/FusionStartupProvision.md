# Provision and observe the Fusion startup add-in

From the signed-in macOS owner account, stage a private copy of the pinned
`KitCaptureRunner` add-in. Use the same installation and lifecycle records that
pin the owner, source revision, and physical Fusion bundle.

```sh
python3 re/automation/ApplicationWorkers/FusionStartupProvision.py \
  --installation /private/fusion/Installation.json \
  --lifecycle /private/fusion/Lifecycle.json \
  prepare --output /private/fusion/StartupStage \
  --installed-addin "/absolute/owner/AddIns/KitCaptureRunner"
```

The stage contains the exact Git-pinned bootstrap and a manifest with only
`runOnStartup` enabled. The command leaves the selected install folder untouched.
During one-time owner installation, copy the staged `KitCaptureRunner` folder to
the declared location with owner-private permissions. Point the add-in runner's
existing `config.json` `startup` field at the absolute path of the staged
`startup-profile.json`. For an existing Fusion registration, verify that
**Run on Startup** is enabled for this add-in in **Scripts and Add-Ins**.
[Autodesk add-in installation and startup settings](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/WritingDebugging_UM.htm)

From a separate process under the same unprivileged account, run the tool with
`observe --profile /private/fusion/StartupStage/startup-profile.json --pid PID`
in place of the prepare arguments. The observer verifies the installed source
and manifest, checks the live physical bundle peer, and publishes a bounded
challenge in the private endpoint. The add-in can answer through its real
main-thread event only after a vendor startup invocation and completed
application startup. The immutable response binds the nonce request, exact
Darwin peer, profile, provider, and source revision. A stale receipt cannot
answer a later request. [Autodesk add-in run context](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/WritingDebugging_UM.htm)

The receipt attests to add-in startup and event delivery. The ordinary phase
worker still performs its pinned healthy control and native acceptance checks.
The tracked manifest remains manual by default. The tool leaves CAD launch,
license sign-in, controller availability and restart custody under their
existing owner procedures.
The [owner cold-start command](FusionStartup/FusionOwnerColdStart.md) uses the provisioned
profile to start an unavailable installation before Phase A.

At PR head `14f4a1f2` and tested merge `1198983e`, the hosted fixture ran the
actual pinned bootstrap and Darwin peer checks across disposable processes.
It verified the vendor startup callback, refusal of manual or incomplete
startup, refusal of a wrong peer or changed manifest, and two fresh challenges.
A signed-in Fusion run is still required. [Hosted macOS evidence](https://github.com/TryUniCAD/Kit/actions/runs/43788486237/job/133041436716)
