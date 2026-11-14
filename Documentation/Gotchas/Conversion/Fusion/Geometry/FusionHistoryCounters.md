# Fusion history counters are distinct identities

A newly authored history often begins with equal integers, such as `4, 4`. It is tempting to treat them as a duplicated generation or size. A rolled-back native history instead stores `3, 10`. Requiring equality rejects that valid journal; writing the current value twice loses the maximum allocated state ID.

Kit names the four values current state, maximum allocated state, retained-state limit and next entity tag. These names come from earlier binary inspection and are not confirmed by a black-box experiment. The saved rollback does show that the first two values are distinct, so they are not one duplicated value. The present typed profile requires a nonnegative fourth value.

Kit reads the integer within a bulletin board as a status from 0 to 3, not as a board ordinal. The status names `mainline`, `stacked`, `succeeded` and `failed` also come from earlier binary inspection and are not confirmed by a black-box experiment. Do not write an arbitrary larger number there.

Use `CurrentStateId`, `MaxStateId`, `NextEntityTag` and `BoardStatus` independently. The optional maximum defaults to the current value only for callers that omit it. Preserve explicit maxima from parsed journals. Keep body keys, Design operation IDs and body generic-tag secondary IDs in their own namespaces.

The [read-only inventory](../../../../../re/Fusion/Reconstruction/JournalStates/Inventory.json) frames all 69 histories, including the rolled-back one. The [feature entry](../../../../Changes/Fusion/FusionHistoryStates.md) records compatibility and the qualified two-state boundary. Current production support does not infer complete multi-state history support from a familiar initial topology count.
