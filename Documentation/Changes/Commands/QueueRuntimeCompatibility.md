# Queue runtime and scope compatibility

The merge candidate exposed three defects that normal PR checks did not exercise.
The CI research root still resolved an environment-provided path before checking it against the fixed fixture directory.
The configuration policy expected the old three-root analyzer scope.
The isolated wheel command imported distribution metadata during parser construction, which transitively imported a blocked standard-library module before formats could run.

Research fixtures now compare the configured absolute path lexically before accessing only the repository-owned checkout.
They retain fixed-root and symlink guards; the developer command still accepts an explicitly trusted arbitrary checkout.
The strict analyzer scope and suppression scans explicitly include `Cli` alongside SDK sources, tools, and tests.
The CLI prepares the version text only for a top-level `--version` before a command, help, or the option terminator, then passes it to the standard argument-parser action.
Direct `BuildParser()` callers retain installed-version discovery independent from host arguments, including when they later parse an explicit argument list.
Ordinary CLI commands avoid that metadata dependency, including forwarded research arguments.

The existing isolated-wheel process case retains all blocked imports and operations and now also requires metadata to remain unloaded after formats.
Six installed module cases verify the package version, early version exit, and invalid version placement across the SDK and developer modules.
A hosted-parser process case also verifies explicit version parsing when the host process arguments request formats.
No source policy, diagnostic severity, security rule, or queue gate was relaxed.

Verification evidence: both [the first failed candidate](https://github.com/TryUniCAD/Kit/actions/runs/43718199570) and [the next failed candidate](https://github.com/TryUniCAD/Kit/actions/runs/43719461782) reported the same security and compatibility failures.
These corrections were reviewed from those logs and statically checked; no tests, reproductions, collection, or builds ran locally.
Remote verification on the repaired head and its merge candidate remains required.

The next candidate passed the earlier security and scope checks but exposed a diagnostic-stream defect in the isolated wheel case.
MainEntry had retained sys.stderr from import time, so the expected research refusal escaped a host's later redirect_stderr context.
Diagnostics now use the active sys.stderr, including interruption messages.
A lightweight installed-process case covers this import-before-redirect sequence in PR compatibility CI; the original wheel assertions and runtime restrictions remain intact.
Evidence: [the failed wheel acceptance job](https://github.com/TryUniCAD/Kit/actions/runs/43731847195/job/132865977145).
The repair was inspected statically; no tests, reproductions, collection, or builds ran locally.
