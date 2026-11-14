# Fusion corpus import can fail after persistence loading

A corpus file is not a successful application acceptance control merely because its archive structure is valid or an earlier capture exists.

During a batch of native imports in Fusion 2706.1.17, three files returned successfully and the next import entered the native crash handler before returning.
The pending input was inferred from the ordered checkpoint as `embosstext-cd769aa41cdf/text_deboss.f3d`.
The crash did not identify a rejected persistence field.
The underlying invalid object or lifetime cause remains unproven.

The failed batch produced no schema snapshot; its three completed imports are not evidence that their runtime schemas were preserved.
The [crash record](../../../../re/Fusion/LocalOracle/Reflection/WarmCrash.json) retains their archive digests and the inferred pending file.
Only the task-era application and matching child/crash processes were terminated during recovery, and the same installed bundle was restarted.
No crash report was sent.

Continue native corpus research with one imported document per dispatched task, close only that task's document, and persist the results after every successful import.
This reduces evidence loss and avoids immediately repeating a multi-document batch.
It is not a demonstrated fix for the underlying native failure.
After recovery, the same first four files all opened when dispatched separately, including the inferred pending text-deboss file.
Their per-file snapshots reached 352 initialized schemas and 1,279 fields.
This makes a permanently unreadable text-deboss archive an unsupported explanation; session lifetime or activation state remains an unresolved possibility.
