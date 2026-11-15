# Acknowledge accepted application outputs

The [owner command](../../../../re/automation/ApplicationWorkers/AcknowledgeApplication.py) releases one completed application spool after it verifies durable A03 acceptance.
The command uses the existing owner-controlled installation configuration and controller store.
Invoke it with the application job ID after that job completes.

```sh
python re/automation/ApplicationWorkers/AcknowledgeApplication.py \
  --installation /private/Kit/Installation.json \
  --store /private/Kit/Store \
  --job capture:p01
```

Supply the job ID from the controller.
The command reads the current completed attempt, its receipt, and its exact accepted result from A03.
It compares the accepted dispatch artifact and complete output manifest with the retained phase.
It checks the copied-file journal and verifies the original spool file hashes.
A stale, failed, unavailable, or mismatched attempt leaves the spool fenced.
An older spool from a different installed source revision remains with the owner for recovery.

The command holds the installation dispatch lock and writes a recovery journal before it deletes the accepted spool.
The journal keeps admission fenced if deletion stops partway through.
Rerun the same command after correcting a filesystem failure.
It checks the same accepted controller identity and any remaining spool files before it resumes.
It refuses a spool with a different directory identity.
A repeated command after completion leaves a newer spool untouched.

If the accepted phase requires a restart, the command restores the old-process restart fence before it releases the journal.
A new application process must still verify the previous process exited.
The command does not launch or stop a CAD application.

If automatic recovery refuses an acknowledgement, an agent can invoke the owner command with the existing trusted configuration.
See [supervised application acceptance](SupervisedApplicationAcceptance.md) for optional automatic invocation after the controller finishes an attempt.
Downstream input binding remains open.

The remote application process selection includes checks for completed acceptance, stale and tampered output, repeated acknowledgement, retained restart ownership, and recovery after a filesystem refusal.
The cases call the real supervisor, controller, and application transport with a fixed fixture.
Native execution and remote results remain pending.
No product tests ran locally.
