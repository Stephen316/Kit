# Verify archived SOLIDWORKS rearm evidence

The verifier reads a retained A03 artifact store after the Windows listener exits. Supply the trusted archive manifest SHA-256 and the exact controller receipt SHA-256 for each of the two attempts. The command follows the receipt to the settled result and immutable job definition, checks each archived object and verifies the first request, launch and canonical owner ticket against the retained listener disposition. It checks that attempt two used a distinct request under the same controller fingerprint and reached the configured limit of two attempts. The report records discovery evidence. [Rearm command](../../../../../re/automation/ApplicationWorkers/SolidWorksRearmEvidence.py), [Live rearm](TimeoutRearm.md)

```powershell
python -B re/automation/ApplicationWorkers/SolidWorksRearmEvidence.py `
  --store <retained-controller-store> `
  --manifest-sha256 <archive-manifest-pin> `
  --first-receipt-sha256 <attempt-one-pin> `
  --second-receipt-sha256 <attempt-two-pin>
```

The archive-only report marks `retained_history.status` as `not_supplied`. Provide `--history-root`, `--history-pins` and `--history-pins-sha256` together to bind the retained event sequence, supervisor outcome and second native spool. Use the SHA-256 of a separately retained pin document. Its fields are `schema` with value `1`, `events_sha256` for `ControllerEvents.json`, `supervisor_sha256` for `supervisor.stdout`, `fence_sha256` for `endpoint/fence.json`, and `second_files`. The last field maps five relative names to SHA-256 values from `endpoint/jobs/<verified-queue-id>`.

- `native-timeout-request.json`
- `phase.done`
- `native-recovery.json`
- `readback/native-launch.json`
- `readback/native-owner.json`

With those pins, the verifier checks the rearm event between the two accepted claims, the supervisor's recovery marker and intervening owner rotation, the second canonical native ticket and the retained final quarantine. It reports listener equality and native process distinction without publishing their IDs or installation paths. The legacy P04 witness predates the recovery marker and reports a null replacement verdict. [Controller receipt semantics](../../../../Reference/Research/ResearchController.md), [Windows queue identities](../../../../Gotchas/Research/Workers/WindowsQueueClientIdentity.md)

The command uses read-only file access and opens no controller database, native process handle or CAD session. On Windows, use the existing research environment with pinned pywin32 for the protected file reads. The reported exit disposition comes from the archived listener attestation. A supplied pin mismatch, missing object or contradictory relationship makes the command exit with status 1.

## Recorded verification

The verifier read four licensed Windows runs after their listeners exited. It verified 94 archived objects and checked separately pinned history for each run. Every run used the same listener across two distinct native processes, exhausted its two-attempt budget and retained the second quarantine. The four reports have UTF-8 and LF bytes.

| Licensed source revision | Scope | Archived objects | Replacement replay | Report SHA-256 |
| --- | --- | ---: | --- | --- |
| `41c963c5` | P04 | 22 | Legacy marker absent | `2a5b2c12273149594f4cbd13b7eb169628f08ae4f7c9c56e1362a3a461676724` |
| `5770f1b3` | P04 | 22 | Verified | `45824832149971816a362c0b1ca3620555691dfcd19d705bb1fc8015b2be852d` |
| `0d527bb9` | P01 and P03 | 25 | No replacement recorded | `41c2d412b4ab8b23521d2cede7c0c035fdd23dcd888675def578116c7e3d4671` |
| `60fb1c73` | P01 and P03 | 25 | No replacement recorded | `e3ad36e7c4f9661b1c68168073b619ddfd597600414e67e766f669ef7b4e1936` |

The `5770f1b3` history pins have SHA-256 `3a93961178df227db6894d746620c150e312bf002e5808fac21094818a321cb7`. Its archive-only report has SHA-256 `a7efeadafd36ca6eec64323198c62ffa420ea34a55f729fdddb3dac452485f9c` and records the optional history as absent. Supplying that run's second receipt as its first receipt exited with status 1 and identified the mismatched attempt. Supplying its archive manifest hash as the history-pin hash also exited with status 1 and identified the SHA-256 mismatch. [Licensed restart witness](TimeoutRearmReplay.md#licensed-restart-witness), [Principal timeout runs](../SolidWorksQueuedReadback.md#p01-and-p03-rectangle-readback)
