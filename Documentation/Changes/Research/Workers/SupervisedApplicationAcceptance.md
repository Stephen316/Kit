# Acknowledge application spools after supervisor settlement

Set `application_installation` in an [application runner entry](../../../Reference/Research/ResearchSupervisor.md#runner-registry).
Its value is the same owner-controlled installation JSON file that the runner uses to dispatch.
Use an absolute path or a path relative to the registry directory.
Keep the installation file in a private directory controlled by the supervisor owner.
This option requires the built-in A03 adapter and a single-job runner.
Leave the option absent on runners that have no application spool.

After A03 accepts a completed attempt, the supervisor invokes the [owner acknowledgement](ApplicationAcceptance.md).
The acknowledgement checks the supervisor owner and exact job, generation, input fingerprint, and attempt against the current controller state.
It verifies the pinned installation source and compares the accepted dispatch and output hashes to the retained spool under the installation lock.
The registry supplies the installation path.
The supervisor continues supervising other sessions while the acknowledgement runs and defers new claims for the affected pool.

The `application_acknowledgement` event reports `acknowledged` after cleanup or `no_pending_acceptance` when there is no current acceptance fence to clear.
The event reports whether a restart fence was retained when it acknowledges a spool.
An `application_acknowledgement_failed` event records a refusal or interruption separately from the already accepted job.
Check the reported cause and use the owner command to resume any interrupted cleanup.
The acknowledgement journal and retained records protect pending cleanup across interruption.

See [interrupted acknowledgement recovery](ApplicationAckRecovery.md) for restart behavior.
Licensed application startup and restart and downstream input binding remain open.
The process cases exercise the supervisor, A03, and fixture application transport for accepted output, a mismatched installation binding, and a stale owner or attempt.
They are selected by remote Linux, macOS and Windows research CI.
Remote verification is pending.
