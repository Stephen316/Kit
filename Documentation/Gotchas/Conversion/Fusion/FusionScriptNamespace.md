# Fusion native script namespace

## Expectation

A script dispatched by a native command might run like a registered Fusion API script.
The dispatched script would then have its file path in `__file__` and receive a call to `run(context)`.

## Actual behavior

The installed `RunScriptCommand` queues `RunPythonTask`.
It evaluates the file's top-level source in the shared `__main__` namespace.
It does not initialize `__file__` or invoke `run(context)`.
An initial probe failed when it used `__file__`; an explicit-path probe reached the API and recorded Fusion version 2706.1.17.
An unhandled error can leave a native modal dialog while later queued tasks run inside its nested event loop.

## Workaround

The research dispatcher now creates a task-owned wrapper that calls `runpy.run_path` in a separate script namespace.
The wrapper catches exceptions and writes a completion file.
Do not infer completion from the JavaScript command's return value.
Do not queue another experiment while an earlier task has an unresolved error dialog.

See the [oracle command reference](../../../Reference/Research/FusionOracleCommands.md).
