# Preserve the audited SOLIDWORKS capture harness

Paired corpus intake hashes the retained SOLIDWORKS capture harness against the source that was audited for the original native files.

The two-pad draft changed the class declaration and constructor in that harness. The [Linux corpus gate at `d910429b`](https://github.com/TryUniCAD/Kit/actions/runs/43764700194/job/132967157070) rejected both intake scenarios because those bytes changed.

Keep the audited source byte-identical. Put new capture logic in a separate collector or retain the exact audited source at its expected path. The two-pad draft remains available at `df3ee5c511bc2b710424a6c0a2ae75c2f6007d7c` for the later phase.
