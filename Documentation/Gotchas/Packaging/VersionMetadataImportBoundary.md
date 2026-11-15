# Version lookup imports dependencies during parser construction

Using `version=importlib.metadata.version(...)` in the parser factory reads distribution metadata for every command.
On the queue's Python interpreter, that lookup imports email utilities and then `urllib.parse`, which the isolated runtime blocks.
The result was a wheel formats command failing before argument parsing completed.

Have the CLI prepare version text only for a top-level version request and inject it into parser construction.
Keep the direct parser factory's default installed-version discovery independent from process arguments so callers can parse explicit argument lists later.
Keep argparse responsible for output, placement validation, and exit status, using its [documented version action](https://docs.python.org/3.11/library/argparse.html#action).
Stop version discovery at commands, help, and the option terminator so forwarded arguments and filename operands do not trigger it.
Keep the runtime import guard unchanged.

See [the queue correction](../../Changes/Commands/QueueRuntimeCompatibility.md) and [the failed wheel process](https://github.com/TryUniCAD/Kit/actions/runs/43719461782/job/132828247820).
