# Link queued SOLIDWORKS timeouts to their controller attempts

When a dispatched P04 request runs past its queue deadline, the worker retains its queue job ID, nonce, request SHA-256 and requester process identity in the controller result.
The record identifies the installation, source revision, resource roster, job, session, generation, input fingerprint and attempt.
A03 still settles that result through its normal lease and owner checks as `waiting_application`.
Other application waits, including refusal before a request was dispatched, carry no timeout claim.
The [cancellation publication](../SingleTimeoutCancellation.md) completes before the worker emits a linked timeout.

The listener keeps the exact timed-out request in `native-timeout-request.json` in the failed spool.
The `native-recovery.json` version 2 record ties its disposition to that request and to the listener's Windows process identity.
A confirmed native exit carries the matching owner ticket SHA-256 and the held process identity.
A recovery refusal carries the quarantine reason and no confirmed owner ticket hash.

The job and resource stay parked and the failed spool stays in quarantine.
The links provide input for a later compare-and-set rearm that can verify both records and the accepted controller receipt.
Older timeout records lack these links and remain parked.

Remote Windows process cases cover the real supervisor and controller timeout with no serving application, and confirmed-exit and refusal outcomes with a disposable Windows process handle.
Verification of this revision remains pending.
