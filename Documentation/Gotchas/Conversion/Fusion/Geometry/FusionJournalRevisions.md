# Fusion history references use separate namespaces

A history with 35 current records can still contain older geometry and more than two states. Treating the initial record count as a complete cylinder or frustum discriminator loses the archived revisions and replacement/deletion bulletins. The native Draft and OffsetFaces controls both start with 35 records but each contains three states and a complete older cylinder.

State IDs and state-node ordinals also differ. Both controls serialize IDs `14, 2, 9` in physical node order `0, 1, 2`; rollback follows nodes `0 → 2 → 1`. The node's partner reference is self-linked only within the qualified linear profile. Kit names the other reference a merged-with node. That name comes from earlier binary inspection and is not confirmed by a black-box experiment.

Old/new bulletin references address the entity table, whose archived revisions follow the active records. An archived entity may refer to another archived revision that aliases an active logical slot. Checking raw reference ordinals only against the current table falsely reports dangling references. Reusing state-node remapping for these references instead corrupts the journal.

Use the typed journal reader to materialize each state's logical-slot-to-revision map. Resolve replacement aliases before checking entity liveness and target class. Preserve state IDs, Design identities, tracking tags and allocation counters independently. A record permutation must remap entity links and bulletin old/new slots while leaving the state graph in its own namespace.

The complete control streams end at an initial state containing only the ASM header. Their intermediate cylinders have 36 live records because an additional tracked face attribute joins Design entity 271. The active bodies have 35 records. Neither this count difference nor tracking value 271 is a universal construction rule.

The [research data model](../../../../../re/Fusion/Reconstruction/JournalStates/JournalModel.md) includes the Design joins. [Native permutation acceptance](../../../../../re/Fusion/LocalOracle/JournalStates/NativePermutationAcceptance.json) verifies rollback, edit, rebuild and save/reopen with changed physical allocation. See the [typed API entry](../../../../Changes/Fusion/History/FusionLinearJournals.md) for the bounded supported profile and remaining unsupported histories.
