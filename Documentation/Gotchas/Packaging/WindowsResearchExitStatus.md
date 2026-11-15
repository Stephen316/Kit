# Windows research commands must wait for their child

A launcher using `os.execv` can appear to preserve the selected tool's lifetime and exit status on every platform.
The Windows execution model does not provide the POSIX process replacement contract expected by this launcher.
Returning before the research tool finishes can lose failure statuses consumed by scripts and CI.

On Windows, the CLI now uses [Popen](https://docs.python.org/3.14/library/subprocess.html#subprocess.Popen), inherits terminal streams, waits for completion, and exits with the child's return code.
An interrupt in the launcher continues waiting instead of invoking `subprocess.run`'s exception path, which would kill a still-running child during cleanup.
Linux and macOS now use a separate child session with explicit signal forwarding and matching signal termination.
The supervisor itself still requires Linux or macOS.

Windows process coverage exercises pinned readers, artifact identity, failed batches, stale leases, and explicit supervisor refusal.
An installed-entry-point process case interrupts the waiting launcher and checks that its real child finishes cleanup and retains exit status 37.
This behavior was identified during source review; accepted-head Windows execution evidence belongs to remote CI.
No local commands or decoding runs were used to reproduce it.
