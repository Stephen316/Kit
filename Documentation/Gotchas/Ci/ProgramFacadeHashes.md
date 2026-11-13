# Program facade hashes

A text-only edit to a generated `Program.py` facade might appear safe because PR CI passes.
The [program manifest](../../../re/tooling/ProgramDecomposition/ProgramManifest.py) stores a SHA-256 hash of each facade.
The generator check compares those hashes, and only the merge-queue test suite runs it.
After you edit a facade, update its manifest hash in the same PR.
See [the queue failure](https://github.com/TryUniCAD/Kit/actions/runs/43329927160/job/131571784596).
