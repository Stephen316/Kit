# Fusion XML stream dump failure

## Expectation

`Segment.Save` appears to expose native XML persistence when `Options.BinaryPersistence` is off.
Its help also advertises a `/Binary` flag.

## Actual behavior

On Fusion 2706.1.17, the first save produced a ZIP containing `BulkStream.dat` and `MetaStream.dat`, despite an `.xml` filename.
The command reads the persistence option; the inspected implementation does not select its format from the advertised flag.

A second experiment imported a controlled archive, disabled binary persistence, and called `Segment.Save`.
It entered the crash handler without writing an XML file or completing its Python `finally` block.
A process sample located the interrupted path at `Ns::SegmentTestor::SegmentTestor` plus 104 bytes, before the XML serializer branch.
The stack also contained an earlier script-error message box and a nested script task.
Cached segment lifetime and reentrancy are possible explanations, not established causes.

## Workaround

Do not use this failed sequence as an XML-export recipe.
Use the successful document-schema dump and controlled archive exports for current research.
Recover the application and verify its persistence option after a native failure; Python cleanup cannot recover a process-level fault.
The application contained only task-created transient documents during this experiment.
After restart, the [recovery record](../../../../re/Fusion/LocalOracle/Restore.json) confirmed binary persistence was on and no documents were open.

See the [oracle command reference](../../../Reference/Research/FusionOracleCommands.md).
