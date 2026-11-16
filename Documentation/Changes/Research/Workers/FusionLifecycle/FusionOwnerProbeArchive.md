# Archive the exact unclaimed Fusion probe as the continuous owner

The macOS lifecycle owner now archives the first settled Phase A timeout
for an exact registered owner pair. The owner uses the existing private
inbox, capacity-one resource, and dispatch and host locks. The archive
requires the still-parked A03 attempt, its immutable receipt and result,
the exact request and cancellation bytes, the settled supervisor worker,
and the untouched hostless quarantine. A claimed or changed probe keeps
its quarantine.

The `phase_a_probe_archived` result carries the manifest SHA-256. Restarting
the owner after publication reconciles the same manifest. A03 keeps the
resource and Phase A parked. The archive establishes the end of the
requesting worker and preserves the request evidence. Native Fusion exit,
replacement readiness and retry still require their own evidence and
the existing owner admission.
[Explicit archive and retry commands](../FusionPhaseAudit.md)

The hosted macOS fixture uses a real A03 supervisor timeout with a
disposable hostless endpoint. It checks claimed-probe refusal, owner
archival, recovery in a separate owner process, and byte-identical A03
state before the existing explicit retry. Hosted execution is pending.
