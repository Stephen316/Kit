# A Fusion kernel watch ends with its owner

The saved watch intent identifies the exact commissioned Fusion process
and the owner that registered its kernel watch. The kernel descriptor
belongs to that owner process. A replacement owner can register a new
watch while the same Fusion process is still live.

After an observer outage, a missing PID and old watch intent supply no
exit event. Recovery needs a matching durable exit receipt. Keep the
installation parked when that proof is missing.
[Commissioned exit observation](../../../Changes/Research/Workers/FusionLifecycle/FusionCommissionedExit.md)
