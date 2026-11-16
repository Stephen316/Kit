# Observe resident memory in the exact Fusion process

The [Fusion lifecycle reset report](FusionResetEvidence.md) now includes
`native_resident_bytes` for its live macOS peer. It samples the task's
resident set using the system `ps` after reading the A03 completion
snapshot. It verifies the pinned executable, PID, UID and kernel process
birth immediately around the sample, and refuses a Darwin exit or executable
change during the read. If the exact peer stays live while the reading is
unavailable, the field is `null`. The measurement covers one application process.
Launcher and worker group accounting stays separate. The sample carries no
memory limit, history, or restart action.
[Apple's Darwin ps manual](https://github.com/apple-oss-distributions/adv_cmds/blob/main/ps/ps.1#L2064-L2066)

The existing hosted macOS fixture compares the reported bytes with an
independent system reading of its disposable AppKit process. It also checks
that the fixture's Python process cannot stand in for the pinned peer.
The fixture passed in the 164-case hosted macOS run at PR head `27cb8d54`.
Licensed Fusion measurements remain open.
[Hosted macOS job](https://github.com/TryUniCAD/Kit/actions/runs/43797562452/job/133069853452)
