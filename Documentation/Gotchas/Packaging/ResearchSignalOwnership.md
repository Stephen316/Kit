# Detached research processes need signal ownership before spawning

Installing relay handlers after a child starts leaves a cancellation window where only the launcher terminates.
A separate child session also does not receive terminal quit or suspension signals delivered to its launcher.
The initial research launcher exposed both behaviors during review.

Install one queueing dispatcher before spawning, bind the child into its shared state, then consume queued signals without replacing handlers.
Continuation must remove a queued suspension before replay.
For terminal suspension, explicitly stop the child with `SIGSTOP` because an orphaned process group may ignore `SIGTSTP`; stop the launcher afterward and relay `SIGCONT` on resume.
Restore prior handlers even if process creation fails.
Uncatchable launcher termination remains outside this catchable-signal contract and requires the existing research recovery controls.

See [the startup finding](https://github.com/TryUniCAD/Kit/pull/119#discussion_r4578452192), [the signal finding](https://github.com/TryUniCAD/Kit/pull/119#discussion_r4578452247), and [the change entry](../../Changes/Commands/ResearchRuntimeBoundary.md).
