# A Fusion exit observation carries its collection time

The continuous observer can collect a queued Darwin exit event after the
peer has already exited. Preserve the recorded collection time when
joining it to a timed-out probe. If collection occurs after the original
probe deadline, the exit receipt cannot establish that the peer was
observed gone by that deadline.

Keep that recovery parked and retain the exit and archive evidence for
review. [Joined recovery custody](../../../Changes/Research/Workers/FusionLifecycle/FusionArchivedRecoveryBasis.md)
