# Imported stderr bypasses later host redirection

A host can import the CLI entry point before using contextlib.redirect_stderr to capture structured diagnostics.
Importing sys.stderr as a module binding retains the original stream, so diagnostics bypass the host's replacement.

The queue-only isolated-wheel case observed the expected research refusal on the process's real stderr while its redirected StringIO remained empty.
Read sys.stderr when emitting each diagnostic, including interruption messages, so the active host stream receives them.
The installed-process regression imports MainEntry before redirecting stderr and verifies both the returned status and captured JSON.
The existing isolated-wheel assertions and runtime blockers remain unchanged.

See [the failed acceptance job](https://github.com/TryUniCAD/Kit/actions/runs/43731847195/job/132865977145).
