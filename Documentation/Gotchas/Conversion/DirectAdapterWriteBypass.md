# Direct adapter writes can bypass registry safeguards

## Expectation

A caller can expect `JsonAdapter.write` and registry-based document writing to enforce the same unqualified-document restrictions.

## Observed behavior

The [review finding](https://github.com/TryUniCAD/Kit/pull/94#discussion_r4576561310) identified that the checks were only in `RegistryWriteApi.WriteDocument`.
Direct JSON writing called `JsonWriter.EmitTarget` and could publish a document carrying unresolved or unqualified evidence.
The direct Fusion, CATIA, and FreeCAD methods also omitted those checks.
Structural model validation does not establish semantic qualification and does not replace these safeguards.

## Workaround

Apply the existing checks at each concrete writer before serialization or destination mutation.
Keep the registry checks for custom writers that implement the registry protocol.
Keep the checks independent of `WriteOptions.validate`.
Verify that nested documents, existing files, and streams receive the same rejection behavior.
The [safeguard change](../../Changes/Research/DirectAdapterWriteSafeguards.md) records the affected methods and verification scope.
