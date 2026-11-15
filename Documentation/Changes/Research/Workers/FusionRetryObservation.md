# Observe whether an archived Fusion probe can retry

Add `--check` to the [archived Phase A retry command](FusionPhaseAudit.md#request-the-exact-archived-probe-retry) using the same supervisor configuration, queue receipt and archive manifest SHA-256.

The observation opens a read-only A03 snapshot and verifies the exact parked pair, released quarantine, archived bytes, empty endpoint, exclusive resource and retry budget. It reports `eligible_at_snapshot` when these checks pass, `already_requested` when the exact archive has a recorded retry, or `blocked_or_unverified` with a named check stage and exit status 1. Its status and evidence fields omit local paths and private request details.

Physical host readiness is always reported separately as `unverified`. Verify the signed-in installation and pinned add-in through the regular owner procedure. The observation leaves the store and endpoint untouched. The owner retry command rechecks admission under its dispatch lock and controller transaction.

The hosted macOS fixture observes an eligible archive and a rejected digest while the dispatch lock is held, compares the ledger and endpoint bytes and roster, and observes a previously recorded retry. Hosted verification of this change is pending.
