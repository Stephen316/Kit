# Bound Fusion batch source lifetime

The pinned Fusion research reader now loads one committed archive at a time.
Previously, it retained every selected archive before decoding started.
The 1000-asset and 256 MiB per-asset limits could therefore admit an excessive aggregate source allocation.

The loop releases each source payload after decoding it and before loading the next asset.
This bounds retained source archives; it does not measure or bound every SDK allocation or final run artifact.
Receipt fields, fingerprints, per-file outcomes, output limits, and CLI statuses remain unchanged.

A pin failure after an earlier successful decode still aborts the complete run.
The staging directory is removed, and no output directory is published.
A new real-process CLI case exercises that late-pin rollback alongside the existing full pinned corpus gate.
No local decoding or tests ran.
Remote execution evidence is recorded on PR #94.
