# Artifact publication outlives a metadata rollback

## Expectation

A failed SQL transaction can appear to roll back the whole research operation, including files created beside the database.

## Actual boundary

The controller publishes immutable objects before committing metadata that refers to them.
A rejected cycle, interrupted command or failed transaction can therefore leave an unreferenced object.
SQLite rollback removes transactional metadata changes; it does not remove separately published filesystem objects.
The [store implementation](../../../re/automation/Ledger.py), [artifact publisher](../../../re/automation/Artifacts.py) and [remote integrity scenario](../../../tests/Research/ControllerIntegrityTests.py) expose this boundary.
See [SQLite transactions](https://www.sqlite.org/lang_transaction.html).

## Workaround

Treat committed metadata and receipts as the reference graph.
Ignore unreferenced objects when deciding whether a job completed.
Never infer success from the presence of an output file alone.
Keep object publication atomic and durable before metadata commit.
Do not delete objects automatically during rollback or introduce garbage collection without tracing historical receipts and definitions.
The initial controller intentionally has no garbage collector.
