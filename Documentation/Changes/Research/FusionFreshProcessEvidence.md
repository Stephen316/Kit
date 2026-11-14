# Fusion fresh-process baseline evidence

The [paired capture audit](PairedCaptureLineageAudit.md) verified the bytes of the existing Fusion artifacts and identified a same-process repeat-save limitation. The [fresh-process capture tool](../../../re/automation/PairedCaptures/FusionFreshProcess.py) prepares two independent launchers for the already-authorized macOS Fusion oracle host. It accepts P01–P04. P05 and its descendants remain reserved for holdout.

## Run on the Fusion host

Use a signed-in Fusion installation on macOS, an exclusive application session without open documents, and a complete Git checkout of a revision containing this tool. Use Python 3.11 or later in the terminal to prepare the run. Use a new local output directory outside the checkout, with its parent already present.

```shell
capture_dir="$HOME/KitFusionEvidence/paired-run-01"
python3 re/automation/PairedCaptures/FusionFreshProcess.py \
  --output "$capture_dir" --recipe P01 --recipe P02 --recipe P03 --recipe P04 --read-existing
```

The preparation command pins the committed specification, control, tool and capture helper. With `--read-existing`, it also verifies both original baseline archives against their committed receipts. Archive inputs and outputs remain local.

1. In the running Fusion process, open **File > View > Show Text Commands**, select **Txt** and run `Python.RunScript "/absolute/path/to/paired-run-01/phase-a.py"`. Phase A measures the control, independently authors and exports each baseline A through the Fusion API, closes owned documents, and measures the control again.
2. Confirm `phase-a/receipt.json` reports `complete`. Quit Fusion normally, confirm its process has exited, then start it again. Use the same Fusion build. If there is an unowned document or a modal dialog, stop to preserve the user's work and capture context.
3. Run `Python.RunScript "/absolute/path/to/paired-run-01/phase-b.py"` in the restarted Fusion session. Phase B requires a different PID, a later OS process start time, and no active phase A PID. It reopens the exact A bytes, measures before and after recompute, exports a separate B, and closes and reopens B for a second readback. The optional original A and B readbacks are separate observations and never update the recorded originals.
4. Check `phase-b/receipt.json` and the corresponding `measurements.json`. The receipt hashes the full report. The report binds the exact phase A measurement hash, source revision, recipe hashes, app build, process identities, controls, archive hashes and sizes, and errors. Save both phase directories and the original plan together. A missing or failed receipt leaves the run incomplete. Start a new output directory after diagnosing a failed run.

The same generated launchers can be run through the [local oracle dispatcher](../../Reference/Research/FusionOracleCommands.md) on a host where its existing Fusion localhost bridge is available:

```shell
node re/Fusion/LocalOracle/RunNative.mjs "$capture_dir/phase-a.py"
# Quit Fusion, confirm exit, and restart the same build.
node re/Fusion/LocalOracle/RunNative.mjs "$capture_dir/phase-b.py"
```

The checked-in queue add-in only dispatches `GenerateFusion.py` scripts with its existing allowed directory layout. Use the Text Commands or localhost path for these generated launchers. The PR's offline Fusion CI does not provide a vendor process.

## Recorded signals and limits

- Each readback records the exact archive hash, whether the archive import returned a document, and any exception. On import failure, the tool also attempts to capture Fusion's last-error code and message. Autodesk's archive import method has no aggregate warning list. The report leaves that field null with the source limitation. If a modal warning is visible, preserve it as a separate dated observation tied to the phase, file hash and process. [Autodesk archive import API](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_ImportManager_importToNewDocument.htm)
- Recompute completion and per-item timeline health are checked separately. The observations include enum states and messages when available, feature order and suppression, units, sketch geometry, constraints and dimensions reported by the shared capture helper, and physical properties. Analytic comparisons are labeled separately. [Autodesk timeline health API](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_TimelineObject_healthState.htm)
- The new A/B artifacts establish a cross-process repeat-save sequence only when both phases succeed. The optional readbacks of recorded originals can establish open and recompute observations for those exact bytes in a new process. Their historical save sequence remains same-process. The tool does not collect complete constraint participants, dimension targets or the exact P04 parent-face identity.

Verification is limited to static syntax, package paths and source inspection. No Fusion application ran on the implementation host. This tool adds a path to capture the missing evidence. Qualification and native conversion acceptance require separate adjudication of the recorded observations.
