# Windows A03 artifact staging

The built-in Windows supervisor adapter resolves bound artifacts in its own process after the controller installs the supervisor owner. The lookup uses a read-only SQLite transaction on the initialized version-4 store and checks the owner with the same recovery fence used by the controller. The existing artifact path rules, 256 MiB byte ceiling, digest verification and verified copy apply. The store lookup creates no file or directory. The only new bytes go to the exclusive private session input file. [Session input contract](../../../Reference/Research/ResearchSupervisor.md#session-contract)

Direct A03 clients, including native application acknowledgement, use the controller command route. Other hosts and custom adapters continue to use their configured input paths. Owner installation, claims, lease renewal, settlement and recovery remain controller operations.

The Windows process check stages a valid bound input, replaces the owner through the controller, and verifies refusal for the old owner and for modified artifact bytes. It checks the contents of the staged file and the unchanged ledger bytes after a successful lookup. Its separate interpreter uses the built-in adapter loader with the artifact subprocess unavailable, so the exercise reaches the new path. Remote verification is pending.

The larger 32-archive Fusion baseline measured 3.084 seconds between its first and eighth supervisor start records. The new lookup removes a controller subprocess from input staging. The same frozen manifest and concurrency policy govern the performance comparison. [Windows calibration](WindowsOfflineCalibration.md)
