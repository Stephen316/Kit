# Audit queued Fusion phase evidence

Save the JSON emitted by [queueing both phases](FusionPhaseQueue.md). The audit command reads that receipt and the corresponding private A03 store.

```sh
python3 re/automation/ApplicationWorkers/AuditFusionPhases.py \
  --store /absolute/path/ResearchStore \
  --queue-receipt /absolute/path/QueueReceipt.json
```

The command opens a read-only controller snapshot. It checks the stored plan digest, paired job definitions, and Phase B's exact dependency selectors. A pending report gives both job states, causes, attempt counts and current resource availability. Terminal job failure has a distinct report status.

For each completed phase the audit checks the same accepted receipt and artifact contract used by application acknowledgement. It verifies the stored bytes, dispatch identity, source revision, plan, measurements and process metadata. A verified pair requires Phase B's controller snapshot and measurements to refer to the accepted Phase A outputs, the same Fusion build and a later distinct process. The native runner records the original process exit during Phase B. The audit reports retained evidence and leaves the application, owner, queue and resource availability under their existing controls.

The hosted fixture checks an absent installation, pending states and byte-identical ledger contents after the audit. Hosted execution of that fixture is pending. Verification of a retained native pair requires the signed-in macOS Fusion host to finish both phases. [Fresh-process host procedure](../FusionFreshProcessEvidence.md)

A Phase A or Phase B attempt parked after a real dispatch timeout includes its verified queue request identity and the current controller receipt and result digests. Pass `--installation /absolute/path/Installation.json` to correlate that identity with the owner-private spool. The command checks the exact retained request bytes or the response's request digest, and reports each observed request, running or terminal state with its fence status. A terminal response may retain outputs behind an acceptance fence. This observation leaves archive and reactivation decisions with the installation owner.
