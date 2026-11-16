# Drain accepted Phase B before releasing the installation

For a registered macOS Fusion owner lifecycle, accepted Phase B evidence and
the application spool acknowledgement are separate durable transitions. The
owner still saves the exact Phase B result as soon as it verifies it. It waits
for the matching supervisor intent to be retired and verifies a clear endpoint
while holding the installation's dispatch lock. Then it releases that
installation's A03 reservation and clears the active lifecycle record.

The running supervisor can retry the same accepted Phase B acknowledgement
after one second and then three seconds. It rechecks the current A03 owner,
exact registered pair, accepted result and durable intent binding. During
backoff the acknowledgement worker remains available to service other work.
If the application already removed its spool before the reply was lost,
reconciliation recognizes the exact accepted result and consumes the old
intent without removing another spool. An unresolved acknowledgement keeps
the resource reserved. The durable intent remains available to the existing
supervisor restart recovery procedure.

The same [continuous owner command](../FusionLifecycleOwner.md) advances the
next durable pair after the handoff. The hosted witness queues two pairs,
runs one supervisor and one continuing owner, and uses disposable application
processes. It exercises Phase B1 reply loss before and after physical spool
cleanup, checks that Phase A2 receives no claim before the intent drains,
and verifies both pairs' accepted attempts and process identities. Hosted
execution and signed-in Fusion verification are pending.
