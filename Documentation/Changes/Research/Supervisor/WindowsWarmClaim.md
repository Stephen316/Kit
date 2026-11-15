# Warm Windows A03 claim helper

The built-in Windows supervisor starts one controller helper on its first single-job claim. The helper runs inside a dedicated kill-on-close Windows Job Object, with only its private request, response and error handles inherited. Each bounded exchange has the existing 120-second controller deadline. One request is outstanding at a time. The supervisor checks admission before every claim, and exact resource and attempt selection still occurs in the ordinary A03 transaction. [Supervisor guide](../../../Reference/Research/ResearchSupervisor.md)

The controller command and helper share single-claim publication. Each claim checks the installed owner under the SQLite writer transaction. On Windows, the controller writes and synchronizes a private sibling stage before publishing the final claim without replacing an existing file. It commits the ledger before acknowledging success. The acknowledgement contains only claim identity. The adapter reads the final record privately and returns the established tokenless claim.

A missing or invalid acknowledgement stops admission and terminates the owned helper. The supervisor drains its active sessions through its ordinary shutdown path. On restart, the new owner removes interrupted stages and settles each complete orphan claim through the existing recovery path. A claim published before a rolled-back transaction is stale. The supervisor issues each submitted claim request once.

Group claims continue through the existing grouped transaction. Custom adapters and standalone controller callers retain their existing command paths. The controlled claim timing measured interpreter startup and repeated controller import as the largest typical cost on the Windows workstation. The same timing also observed durable file and transaction latency spikes. [Controlled timing](SixteenWorkerCalibration.md#controlled-claim-timing)

The existing Windows calibration observer includes the helper's working set in aggregate outer-job samples alongside eligible worker and controller processes. Each decoder retains its own measured interval and working-set metrics.

The Windows process cases cover helper reuse, ordinary close, stale ownership, and a committed claim whose reply is withheld by exit or timeout. They check recovery by a new supervisor process and absence of duplicate settlement. Remote execution and a matched throughput sweep are pending.
