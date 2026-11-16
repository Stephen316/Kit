# Resumable Fusion lifecycle owner

Run one owner program for a reviewed macOS Fusion installation after configuring
its signed-in startup, pinned source checkout, capacity-one resource, and
automatic quit opt-in. The source pin must include the deadline-aware macOS
replacement provider. Use the same A03 supervisor configuration and exact
private installation and lifecycle profile used by the existing owner tools.
Run the supervisor independently so Phase A output acceptance and its spool
acknowledgement can finish during owner observation.
The [startup provisioning tool](FusionStartupProvision.md) stages and verifies
the opt-in add-in for a signed-in macOS owner session.

```sh
python3 re/automation/ApplicationWorkers/FusionLifecycleOwner.py \
  --config /private/path/supervisor.json \
  --installation /private/path/installation.json \
  --lifecycle /private/path/lifecycle.json \
  --queue-directory /private/path/queue-receipts
```

Point each `QueueFusionPhases.py --receipt` at a distinct JSON file in that
private directory. Its durable submission intent associates the exact
definitions and content-addressed plan with the configured installation. The
owner finds the pair from the retained Phase A fence and accepted A03 result,
recovers a missing receipt from the exact committed submission, and records
the immutable restart intent. The owner lock covers one continuing driver for
the endpoint. Restarting the same command resumes the active record.

Add `--owner-lifecycle` to a durable queue submission before either phase is
claimed to reserve the capacity-one installation across the automatic restart.
The installation source pin must include the reservation policy.
[Reservation requirements and recovery](FusionRestartResourceReservation.md)

The driver requires the exact Phase B lease and remaining deadline for a new
physical request. It rechecks admission while sealing authorization for the
armed Darwin watcher or the replacement request. The replacement provider
uses the sealed deadline immediately before calling LaunchServices. Phase B
can wait at its existing fence without blocking the acknowledgement executor.
Computing capacity and rearming parked resources remain under the existing
supervisor and owner controls.

The durable quit request, exact observed exit, replacement request, and
observed replacement process govern which step is eligible after interruption.
A sealed quit or launch without its conclusive receipt stays parked. In
particular, the absence of the old process does not establish a Darwin exit
receipt, and the presence of a process does not establish an authorized
replacement receipt. After the exact Phase B settlement, the read-only
replacement verifier checks the accepted output, new peer, and startup probe.
The owner persists the final evidence before clearing the active record and
starting any subsequent restart. A registered installation also waits for
[Phase B acknowledgement to drain](FusionLifecycle/FusionPhaseBAcknowledgement.md).
`--once` performs one reconciliation and emits an
evidence status suitable for checking a parked owner.
[Automatic archive of an unclaimed Phase A timeout](FusionLifecycle/FusionOwnerProbeArchive.md)
[Exact commissioned native exit evidence](FusionLifecycle/FusionCommissionedExit.md)

Use [the read-only completion report](FusionLifecycle/FusionResetEvidence.md)
to inspect confirmed work in the exact current Fusion process lifetime.

Hosted fixtures cover real A03 settling and acknowledgement, a disposable
Darwin exit, expired admission, and owner subprocess interruption around
sealed actions and final evidence. The fixture uses disposable providers for
replacement and Phase B, and the separate AppKit fixture exercises the
deadline-aware launch. These checks leave signed-in licensed Fusion lifecycle
verification open.
