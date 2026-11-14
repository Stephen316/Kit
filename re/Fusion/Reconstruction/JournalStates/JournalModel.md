# Linear ASM history with archived revisions

This research separates complete byte framing, semantic record decoding, state materialization and native acceptance. These are different claims. The current research reader fully frames 69 histories and interprets every record of the three exceptional controls. The research serializer derives a complete stream from named field values. Both original-allocation and independently permuted reconstructions passed native rollback, edit, rebuild and save/reopen. The new production `BrepCodec/Journal` path promotes the bounded semantic model; its acceptance is tracked separately from the research serializer.

## Evidence and scope

- [Inventory.json](Inventory.json) is the compact source/digest index. `Inventory.json.xz` contains its complete 69-history framing evidence.
- An earlier version also cited static inspection of installed Fusion libraries for stream counters, board status, the hidden flag, the merged-state reference and the tracked attribute payload. That material was removed. Field names that came only from it are marked below as not confirmed by a black-box experiment.
- [Materialization.json](Materialization.json) records each historical live-entity set and reference result. `SemanticHistory.json.xz` contains complete named geometry/attribute values, journal states, revision aliases and materialized state maps.
- [DesignStatesSummary.json](DesignStatesSummary.json) binds `DesignStates.json.xz` to complete research decoding of the source Design records.

Read-only sources are the frozen corpus Draft, offset-cylinder and rolled-back archives. No application calls, production codec execution or tests participate in these analyses. Native files are used as format evidence, not as opaque writer blocks.

## Namespaces

| Namespace | Meaning | Scope |
| --- | --- | --- |
| Entity table ordinal | Serialized active geometry/attribute identity | One ASM stream |
| Archived revision ordinal | Serialized prior entity version, allocated after active entries | One ASM stream |
| Stable entity slot | Logical entity represented by an active or archived version | One materialized state lineage |
| State node ordinal | Position of a `delta_state` in its stream list | One state table |
| State ID | Kernel identity joined by Design `startModelHS`/`endModelHS` | One history stream |
| Entity tag | History allocator identity stored on a tagged entity, including the body key | One history stream |
| Tracking tag | Native `tracked_tag_id` carried by a custom tracking attribute | Explicit caller identity; source-specific Design join verified below |
| Operation/secondary tag IDs | Persistent generic-tag identities | Design/progenitor contract, separate from state IDs |

The source physical state order is `14, 2, 9`, while chronological rollback walks `14 → 9 → 2`. The source physical node ordinals are therefore `0 → 2 → 1`. A node ordinal is not a state ID and the partner reference is not inherently the node's own identity: it happens to be self-linked in this qualified linear profile.

## Stream framing

The qualified header is `ASM BinaryFile8`, native save version 23200, stored-count zero, two roots including `asmheader`, flags three, and explicit product/version/date strings. Unit metadata is 50 with absolute tolerance `1e-6` and normal tolerance `1e-10`. Geometric coordinates in the embedded records remain centimetres.

The sections are:

1. The complete active entity table.
2. The identifier chain `Begin-of-ASM-History-Data`, immediately followed by `history_stream`, its scalar/reference fields and a record terminator.
3. Every `delta_state`, including boards, changes, optional name and the final counted state list.
4. `End-of-ASM-History-Section`, immediately followed by the first archived entity name, without an intervening record terminator.
5. Every archived entity in its allocated revision order.
6. `End-of-ASM-data`, followed by EOF without a record terminator.

The archive section contains complete prior entity records, not deltas within individual records. Active entities are numbered `0..N−1`; archived revisions follow at `N..N+A−1`. The bulletin changes reference these entities. The serializer does not retain original stream bytes, token arrays or unidentified tail spans.

## History-stream fields

The four signed integers are read as `currentStateId`, `maxStateId`, `maxStatesToKeep`, and `nextEntityTag`. The BinaryFile8 wire uses tagged signed 64-bit slots. The retained-state limit is qualified zero. A `−1` entity-tag value is rejected by this profile. The names came from removed static evidence. Saved documents support the first, second and fourth readings: the rolled-back source below stores current 3 and maximum 10 while Design still references state 10, and the next entity tag is one more than the highest body tag in both controls.

Four references follow: the working delta node, active node, initial node, and an entity reference. These roles came from removed static evidence and are not confirmed by a black-box experiment. The qualified model permits a null working node and null final entity reference. The general role of the final entity reference is not yet established. Its non-null form is rejected.

Current and maximum state IDs differ in a rolled-back source: `[3, 10, 0, 6, −1, 0, 1, −1]`. Design retains later extrusion intervals `3→9` and `9→10`, even though their geometry states are absent from the saved rolled-back stream. Thus neither serialized state count nor active geometry can reconstruct the maximum allocated state ID.

## Delta-state fields

| Wire order | Semantic field | Qualified value |
| --- | --- | --- |
| 0 | State ID | Nonnegative signed 32-bit ID |
| 1 | Rolls backward | Integer true (`1`) |
| 2 | Hidden | Integer false (`0`) |
| 3 | Previous node | Toward current head, or null |
| 4 | Next node | Toward initial root, or null |
| 5 | Partner node | Self-linked ring for this linear profile |
| 6 | Merged-with node | Null |
| 7 | Owning history stream | Stream zero |
| 8 | Optional name | Tagged Boolean presence; absent here |
| After name | Board chain | Counted-by-presence linked boards |
| Final field | State list | Count and state references; empty here |

The names rolls backward, hidden, partner and merged-with came from removed static evidence. They are not confirmed by a black-box experiment. The general semantic role of the final state list is unknown. Empty-list qualification does not authorize nonempty opaque retention.

Each board begins with integer one, its owner-node reference and a status integer. Changes each begin with integer one, then old and new entity references. Integer zero ends changes, another zero ends boards. The last zero in the controlled state is the state-list count, not undifferentiated padding. The board status names `mainline=0`, `stacked=1`, `succeeded=2`, `failed=3` came from removed static evidence and are not confirmed by a black-box experiment. This multi-state serializer qualifies status 2 (succeeded) boards only.

## Revision materialization

A bulletin `(−1,new)` inserts an entity. `(old,−1)` deletes an entity. `(old,new)` replaces an entity version. Both references cannot be null.

Starting from the current table, rollback applies each board's changes in saved order:

- Undo insertion: remove the `new` stable slot.
- Undo deletion: reintroduce the `old` slot using its archived revision.
- Undo replacement: retain the `new` stable slot and select the archived `old` revision.

Replacement aliases map archived revision IDs back to stable entity slots. Archived entity references must be normalized through these aliases before checking liveness. Checking archived references directly against current ordinals would falsely reject valid historical links. The reader checks every non-null reference in every materialized state. The serializer additionally checks target record classes, state-link reciprocity, unique state IDs, complete archived revision coverage, and termination at the initial `{asmheader}` table.

| Source | Current state 14 | State 14 changes | State 9 | Archived records |
| --- | --- | --- | --- | --- |
| Draft | 35 entities, −5° frustum | 15 replacements, 7 deletions, 6 insertions | 36 entities, cylinder | 22 |
| Offset cylinder | 35 entities, larger cylinder | 16 replacements, 9 deletions, 8 insertions | 36 entities, original cylinder | 25 |

Both state-9 boards contain 35 insertions, so reversing them leaves only the ASM header at state 2. Every materialized state has zero dangling references. The additional historical entity is a tracked custom attribute on the selected face.

## Geometry and identity joins

Draft's state-9 cylinder has radius 10 mm and height 20 mm. The active state-14 frustum has base radius 10 mm, top radius approximately 8.25022672948152 mm, height 20 mm and signed sine `−0.08715574274765817`. Offset-cylinder state 9 has radius 10 mm; state 14 has radius 12.5 mm. Both are 20 mm high at base `(20,20,0)` mm.

Both Design graphs join extrusion entity 234 to state interval `2→9`; feature entity 267 joins Draft or OffsetFaces to `9→14`. Their BRep history serializer body maps use entity tag 1 for Draft and 3 for OffsetFaces, both mapping to Design body 260. The preamble next-entity-tag values are respectively 2 and 4.

`FPM_tracked_attrib_def` has qualified schema marker one and one signed 32-bit integer that Kit calls `trackedTagId`. The name came from removed static evidence. Both controls store value 271. Design entity 271 is a `BrepRefMetaType`, has recipe 274, and is a child of feature 267. This is direct source-specific linkage evidence. A universal tracking-tag allocation rule has not been established.

## Research writer and remaining qualification

`EmitEntities.py` derives each supported topology, analytic carrier and attribute record from named semantic fields. `EmitJournal.py` derives header, stream, states, changes and boundaries. `ValidateJournal.py` rejects unsupported branching/merged/named/state-list profiles and checks state/reference consistency. `PrepareNative.py` assembles each source-specific acceptance archive by replacing only the fully reconstructed history member; the source's own Design, snapshots, graphics and other members remain unchanged.

These controls cover cylinder/frustum topology, planes, circles, points, timestamp attributes, generic tags, sketch links and tracked attributes. They do not cover arbitrary surfaces, wire bodies, transforms, non-null reserved fields, multiple history streams, merged or branched execution, nonempty auxiliary state lists, or non-null history owner entities. Production promotion requires immutable typed models, strict field domains, remote archive integration and native load/rollback/rebuild/save/reopen acceptance. Independent construction of a new multi-state Design feature graph is separate from this complete same-source history read/write proof.

## Native acceptance

[NativeAcceptance.json](../../LocalOracle/JournalStates/NativeAcceptance.json), SHA-256 `673bb75a6a5431a2d6e95df6597f9c85abde820add6958a753e026473e56e7ac`, records successful source/control comparisons for complete original-allocation reconstruction. OffsetFaces volumes progressed from 9.817477 cm³ to the prior cylinder at 6.283185 cm³, then 11.290099 cm³ after height 23 mm and 13.168771 cm³ after offset 3.5 mm. Draft progressed from 5.247895 cm³ to 6.283185 cm³ in the prior state, then 5.869212 cm³ after height 23 mm and 5.377191 cm³ after angle 7°. Both saved and reopened successfully.

[NativePermutationAcceptance.json](../../LocalOracle/JournalStates/NativePermutationAcceptance.json), SHA-256 `99e57f2485630f128487820c4a8c0f32dbf4b30c5f5c57753109a70a514bf209`, repeats the full sequence with reversed active entity allocation and independently reversed archive allocation. Every declared entity reference and bulletin old/new reference was remapped; state-node ordinals and native Design identifiers were unchanged. This deliberately changes the stream bytes and establishes allocation-independent semantic serialization. Both acceptance runs closed all opened documents.

`PrepareProduction.py` uses only public production journal APIs to prepare an additional original/permuted pair for each source. [NativeProductionAcceptance.json](../../LocalOracle/JournalStates/NativeProductionAcceptance.json), SHA-256 `fdee08a175167a2d579905ac7084ecdf6f58cdcd26b4d0a3672c41bd7ef8dd66`, accepted all four public-codec candidates against the two source controls. Original histories were byte-exact; independently permuted histories changed bytes. All prior-state rollback, geometry restoration, parameter edits, rebuild and save/reopen observations matched, with zero documents open afterward. `ProductionPreparation.json` records the exact input and output hashes.

## External attribution

The framing and state-version model were compared with the [cadmpeg project](https://github.com/cadmpeg/cadmpeg), pinned at commit `de2726870ff728352163f601ab4e60bbd54fbade`, particularly `crates/cadmpeg-asm/src/history.rs` and `docs/formats/asm.md` §3. Its code is Apache-2.0 and its specification is CC-BY-4.0. Kit's reading differs from its duplicated-generation/size, board-number, state-version and partner-field interpretations. Complete framing of 69 histories and native acceptance of the reconstructions support Kit's framing. The field meanings behind those differences came from removed static evidence and are not confirmed by a black-box experiment. The Kit research serializer is independently implemented from explicit semantic fields; it does not adopt raw-byte record retention.
