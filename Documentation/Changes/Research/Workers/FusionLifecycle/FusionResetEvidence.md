# Observe verified completions in one Fusion process lifetime

Use the existing macOS lifecycle owner entry point with the exact live
process ID from the owner session.

```sh
python3 re/automation/ApplicationWorkers/FusionLifecycleOwner.py \
  --config /private/fusion/Supervisor.json \
  --installation /private/fusion/Installation.json \
  --lifecycle /private/fusion/Lifecycle.json \
  --reset-evidence-pid PID
```

The command verifies the live exact Darwin peer and physical bundle. It reads
historical A03 completions for the counted installation from one controller
snapshot. A completion counts when the historical job definition and receipt,
accepted result, exact dispatch bytes, phase and plan agree. Its dispatch
must name this installation and process and finish within that process
lifetime. It deduplicates the native request digest. If the same A03 job runs
again with a different native request, that execution can contribute another
completion. Previously accepted generations remain observable while their
immutable attempts and artifacts are retained.

The report separates duplicate dispatches, other process lifetimes, and
completions with missing attribution. `--reset-evidence-limit` changes the
numeric comparison from its default of 50. The comparison covers only
corroborated completed native requests. Failed, incomplete, and currently
running attempts have no completed dispatch proof in this count. A figure
below the comparison limit therefore leaves the general reset obligation
unresolved. This command reads controller evidence and observes a process.
It leaves resource availability, native startup and restart decisions under
the existing owner workflow.

The hosted fixture starts a disposable macOS application and settles real
A03 attempts. It checks a replaced job generation, duplicated request
identity, another process lifetime, an unattributed completion, and both
comparison limits. The controller database bytes must remain unchanged.
Hosted execution is pending.
