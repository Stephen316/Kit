# Successful supervisor sessions remove worker directories

A runner can appear to publish a document by returning a path within its session's `work/` directory.
The supervisor removes that directory after the controller accepts the result.
The returned path would then refer to a deleted artifact.
The result record also has a 1 MiB bound and cannot carry arbitrary decoded files inline.

Use the pinned reader commands for persistent document and receipt output.
Define verified persistent artifact ingestion before adding a scheduled decode runner.
Do not treat a generic registry as an implemented unattended decoding pipeline.
See [session completion](../../../re/automation/Sessions.py), [supervisor settlement](../../../re/automation/Supervisor.py), and [the supervisor guide](../../Reference/Research/ResearchSupervisor.md).
