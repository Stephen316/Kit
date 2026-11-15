# Retain the Fusion restart fence during replacement startup

The native Fusion endpoint can acquire its lock before its add-in verifies the installed bootstrap. Keep the existing `restart_required` fence during that interval. The replacement must present the bootstrap and protocol source pins loaded by its verified startup. Its subsequent queue check can release the matching fence once it confirms the old process has exited.

Configure the installation to pin the updated queue protocol and checkout revision using the existing add-in bootstrap. A replacement crash after its startup check can still interrupt the request. The fresh main-thread challenge and the existing deadline continue to govern that attempt.

Hosted startup fixtures use separate disposable provider processes. They verify byte-identical fence retention after unverified and stale-source startup, then verify release after the trusted pins are loaded. Hosted verification of this change is pending.
