# Use accepted dependency outputs as job inputs

In an A03 job definition, an `inputs` entry can name a global evidence binding or select bytes from a job in its explicit `depends_on` list.
Use `{"dependency": "job:id"}` for the accepted A03 result record or add `"artifact": "role"` for a named entry in that result's accepted output manifest.
Use the same submit and supervisor commands as other jobs.

For example, submit Phase A as `capture:fusion:p01:a`, then submit this Phase B job with the runner and resource configured for the same [Fusion installation](../Workers/LocalApplicationDispatch.md).
Both jobs use the same `capture:plan:p01` binding.

```json
{
  "id": "capture:fusion:p01:b",
  "kind": "capture.fusion",
  "inputs": {
    "plan": "capture:plan:p01",
    "phase-a.accepted": { "dependency": "capture:fusion:p01:a" },
    "phase-a.receipt": {
      "dependency": "capture:fusion:p01:a", "artifact": "phase-a.receipt"
    },
    "phase-a.measurements": {
      "dependency": "capture:fusion:p01:a", "artifact": "phase-a.measurements"
    },
    "phase-a.P01": {
      "dependency": "capture:fusion:p01:a", "artifact": "phase-a.P01"
    }
  },
  "depends_on": ["capture:fusion:p01:a"],
  "resources": ["application:fusion:local"],
  "options": { "phase": "b" },
  "rule_version": "fresh-fusion@1",
  "tool_version": "fusion-dispatch@1"
}
```

Use the receipt and measurement roles and one baseline archive role for each recipe in the pinned plan.
A03 resolves the full input set and its dependency receipts in one controller transaction.
The claim's input descriptor retains the selector alongside the verified digest. The supervisor stages each digest as a private session file.
An incomplete dependency or a missing named output leaves the child waiting for evidence. Corrupted accepted bytes fail verification.
The child can reuse its completed result when the job definition and prerequisites remain identical.
A replacement or invalidated parent changes the child's prerequisite fingerprint and fences an active child lease.
The selector creates no global name and uses no additional binding command.

The Fusion runner still validates the accepted result, files, plan and installation and requires the old native process to exit.
The remote process cases cover exact staging, repeat submission, changing the parent generation, a missing output and an undeclared dependency.

A Windows consumer at `7e4c604b60568666287b61ce843eb5ac5ef10ce7` used a private copy of the completed [licensed SOLIDWORKS store](../Workers/SolidWorksQueuedReadback.md#licensed-job-evidence). It selected the accepted result plus its `readback.receipt` and `readback.measurements` artifacts. The supervisor staged those three exact digests even with a separate global `readback.measurements` binding present. The consumer verified the receipt and all eleven supporting-face observations. The original store digest and the completed parent record stayed unchanged.

The accepted parent result SHA-256 is `6fb3373a27b793ebdc5f66056a4cff93761ac31d77d522d7dc0b93e963fdc059`. The measurement artifact SHA-256 is `68a072c111f9a2e5d3334766fdaac7b3a0a3d1e43477f37325177bbeffc0e55c`. The accepted consumer result SHA-256 is `664523368640d00fbc1808589a57298ccd8af6a66e3e39c2fabaf51c1c683df5`. The licensed Fusion sequence and remote process verification remain pending.

The Windows in-process staging implementation at `927bbfd61236bc1bf3fabed2499ce04903808e37` delivered the same parent result, receipt and 4.7 MB measurement bytes to the analysis job. All eleven supporting-face observations matched. The accepted consumer result SHA-256 is `b695f784dac2511785845fed104bf7b903e65a1248d31a78aa001c52ca15875a`. [Windows staging](../Supervisor/WindowsArtifactStaging.md)
