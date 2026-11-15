# Recover interrupted supervisor acknowledgements

The [application runner binding](SupervisedApplicationAcceptance.md) records a private acknowledgement intent in the supervisor state directory before it calls the A03 finish command.
The accepted result carries a SHA-256 of that intent, including its nonce.
The intent identifies the job, claim generation, input fingerprint, attempt, session, controller store and exact installation configuration bytes.
A03 still checks the active lease and current supervisor owner when it accepts the result.

When the supervisor starts again, it acquires its locks, installs a new controller owner and recovers abandoned sessions.
It then checks outstanding intents against A03 and requeues acknowledgement for a corresponding completed claim.
These checks run alongside normal supervision and retry one failed controller status request.
A rejected supervisor owner stops the check immediately.
The acknowledgement checks the content-addressed result and its supervisor session against the intent before changing the retained application spool.
It uses the current owner and the installation selected by the registry.
The intent contains neither the lease token nor the old owner's credential.

Restart the supervisor with its original state directory, A03 store, runner registry and installation configuration.
An intent from an unaccepted or superseded attempt is discarded after a successful controller check.
An unavailable controller, changed owner configuration or refused cleanup leaves the intent available for investigation.
The existing [owner recovery command](ApplicationAcceptance.md) can reconcile an already accepted spool using the exact configuration.
The application endpoint journal still protects interrupted spool deletion, and a required CAD restart remains fenced.
This change covers supervisor process interruption and subsequent restart.

Remote process cases interrupt the supervisor before A03 finish and after its durable response.
They verify the digest in the accepted result and recovery after spool cleanup, as well as a transient controller status failure.
Tampered intent bytes, changed installation bytes and a removed registry binding preserve accepted controller evidence and the original application fence.
The licensed Windows P04 job verified recovery after a real controller-accepted readback, including immutable result and receipt identity through supervisor restart. Remote results for the other process cases remain pending. [Licensed job evidence](SolidWorksQueuedReadback.md#licensed-job-evidence)
