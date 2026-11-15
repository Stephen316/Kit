# Audit queued Fusion phase evidence

Save the JSON emitted by [queueing both phases](FusionPhaseQueue.md). The audit command reads that receipt and the corresponding private A03 store.

```sh
python3 re/automation/ApplicationWorkers/AuditFusionPhases.py \
  --store /absolute/path/ResearchStore \
  --queue-receipt /absolute/path/QueueReceipt.json
```

The command opens a read-only controller snapshot. It checks the stored plan digest, paired job definitions, and Phase B's exact dependency selectors. A pending report gives both job states, causes, attempt counts and current resource availability. Terminal job failure has a distinct report status.

For each completed phase the audit checks the same accepted receipt and artifact contract used by application acknowledgement. It verifies the stored bytes, dispatch identity, source revision, plan, measurements and process metadata. A verified pair requires Phase B's controller snapshot and measurements to refer to the accepted Phase A outputs, the same Fusion build and a later distinct process. The native runner records the original process exit during Phase B. The audit reports retained evidence and leaves the application, owner, queue and resource availability under their existing controls.

The hosted fixture checks an absent installation, pending states and byte-identical ledger contents after the audit. Hosted execution of that fixture is pending. Verification of a retained native pair requires the signed-in macOS Fusion host to finish both phases. [Fresh-process host procedure](../FusionReadback/FusionFreshProcessEvidence.md)

A Phase A or Phase B attempt parked after a real dispatch timeout includes its verified queue request identity and the current controller receipt and result digests. Pass `--installation /absolute/path/Installation.json` to correlate that identity with the owner-private spool. The command checks the exact retained request bytes or the response's request digest, and reports each observed request, running or terminal state with its fence status. A terminal response may retain outputs behind an acceptance fence. This observation leaves archive and reactivation decisions with the installation owner.

## Archive an unclaimed Phase A probe

A macOS installation owner can archive a verified `request` observation whose sender exited and whose exact cancelled probe remains under a hostless quarantine.

```sh
python3 re/automation/ApplicationWorkers/ArchiveFusionProbe.py \
  --config /absolute/path/Supervisor.json \
  --queue-receipt /absolute/path/QueueReceipt.json
```

The command acquires the installation's dispatch and host locks. It verifies the still-parked A03 Phase A receipt and the untouched plan, request and cancellation bytes. It moves those files with an immutable manifest to the installation's private `failed-spools` directory, then releases that quarantine. An interrupted release can be retried with the same configuration and receipt.

An active host, a pending acknowledgement, an acceptance-required fence, any phase output or changes to the recorded request cause a refusal. The archive report contains its manifest SHA-256 and the timed-out request SHA-256. The A03 resource stays parked until the installation owner separately verifies readiness and marks it available.

After archival, the same audit with `--installation` verifies the archive manifest and retained file digests. It reports `archived`, the manifest SHA-256 and current fence status. It can read that evidence while the host lock is occupied. The owner still uses the normal host verification and resource reactivation procedure before another attempt.

## Request the exact archived probe retry

After verifying the macOS installation through its normal owner procedure, use the manifest SHA-256 reported by the audit to permit the original Phase A job to retry.

```sh
python3 re/automation/ApplicationWorkers/RetryFusionProbe.py \
  --config /absolute/path/Supervisor.json \
  --queue-receipt /absolute/path/QueueReceipt.json \
  --archive-manifest-sha256 <sha256>
```

The command verifies the current parked attempt and archived bytes under the dispatch lock. It requires an empty application queue, a released fence, remaining retry budget, and an installation resource with no unrelated unfinished jobs. One controller transaction records the archived receipt, reactivates the resource and queues Phase A at its normal retry time. Repeating the same command returns the recorded disposition.

Phase B still waits for accepted Phase A evidence. The next scheduled Phase A attempt must obtain a new main-thread readiness response from the pinned add-in before any native capture.
