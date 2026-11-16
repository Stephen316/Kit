# A Fusion probe archive identifies the requesting worker

The untouched probe archive records a hostless quarantine and links to
the original supervisor worker and its transport request. The worker
can exit before any Fusion add-in claims the request. That exit supports
archiving the untouched probe while keeping the controller parked.

Native restart and retry admission require independent evidence of the
owned application process and a verified ready peer. Keep that evidence
bound to the exact installation and request before marking it available.
[Continuous owner archival](../../../Changes/Research/Workers/FusionLifecycle/FusionOwnerProbeArchive.md)
