# Grouped crash stderr

A grouped runner writes one physical `stderr.log` in the session root.
Each member has a separate result directory under `jobs/NN/` and has no separate stderr log.
Reading a crash tail relative to that member directory returns an empty tail, then session cleanup removes the only diagnostic log.

Pass the physical session's stderr path into each member's result construction.
The bounded tail then persists in each affected attempt result before cleanup.
The process receipt, memory observation and adaptive outcome remain physical-session records.

The real-process crash fixture writes distinct stderr bytes, lets the supervisor retry jobs singly, and reads each first attempt's immutable result through its controller receipt.
Remote execution remains pending for this repair; local checks cover source and fixture validation only.
See [the grouped-session change](../../../Changes/Research/Supervisor/GroupedSmallFileSessions.md).
