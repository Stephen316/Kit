<!--
This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Assemblies and occurrences

[Fusion feature index](../README.md)

See [SDK assembly readers](../../../src/convert/formats/Fusion/Assembly) and [public assembly tests](../../../tests/convert/api/ApiFusionAssemblyTests.py).

## SDK coverage

Kit reads local assembly definitions and occurrences from qualified `.f3d`
archives. Repeated instances share one component definition. Nested instances
retain their parent definition, native sibling order, and local rigid placement,
with translations expressed in millimetres. Kit binds the top-level timeline
through native component and history references and retains the empty child
history identities. The SDK validated 32 definitions, 23 native instances,
and 24 expanded paths across 12 tracked archives. Three Fusion 2705.1.30
captures independently verified 11 composed placements. Sixteen archives with
joint, pin, or stale occurrence records required explicit history selection.
Component geometry, external references, and joint-solved assemblies require
further decoding.

The reader also qualifies the saved B-rep body inventory through typed
component links and reciprocal, repeated native collection membership. It
preserves native body IDs, order, and stored custom names, including Unicode.
Removal, consumption, suppression, and rollback can leave historical records
outside the active collection. The inventory uses the saved membership lists
to distinguish those records. Geometry and terminal feature ownership remain
separate. A previously reconstructed solid retains its Kit body ID when the
same native body and collection are proven. The native reader qualified
1,093 body memberships across 766 component collections in 712 tracked
archives. Saved Fusion API controls corroborate interleaved body names,
component ownership, and membership after timeline edits.

Kit also reconstructs local solids in qualified assemblies. Root bodies stay
on the root document. Other bodies are stored once in their component
definition's embedded document and placed by every occurrence of that
definition. A paired native dependency graph verifies creator and sketch
ownership. For a rotated authoring frame, the creation snapshot and its parent
scope establish the occurrence path at the time of the Extrude. This preserves
the original local geometry when a later copy creates another path. Two saved
assemblies verified seven unique solids, including three reusable component
bodies placed five times in the repeated design. Local topology and measures
matched the saved body records. Unsupported active operations leave the
assembly graph and body inventory available for inspection. Later modeling
operations, joint-driven assemblies, and native writing require further
coverage.

## Saved study coverage

Saved evidence includes [`component-creation-decoding.json`](../Study/component-creation-decoding.json).

| Area             | Observed support                                                                                                                                                                                                                                                                                                                                              | Open work                                                                                                                                                                    |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Move             | Free rigid matrix; XYZ component/design-space translation, axis/sketch-line translation, axis rotation, construction-point-to-point and point-to-position controls including its component/design flag                                                                                                                                                        | Other selected entities/face moves, context interpretation and regeneration                                                                                                  |
| Local assemblies | Component definitions, repeated/native occurrences, explicit CreateComponent/snapshot and same-definition CopyPaste links, historical placement matrices, Pin occurrence provenance, parent collections, nested rigid transforms, explicit sketch ownership and world sketch coordinates                                                                      | Copy/paste and external feature schemas, flexible components, joint-solved placement, current grounding state and replay                                                     |
| Joints           | Ordinary point-origin rigid/revolute/slider/cylindrical/pin-slot/planar/ball types, flip/alignment bindings and enabled limits; observed root AsBuilt rigid/revolute/slider definitions, ordered occurrence routes and point-geometry caches using shared motion parsing; type11 RigidGroup expanded membership, including one explicitly routed nested child | Other AsBuilt/group variants, includeChildren control encoding, arbitrary origins, custom/ball frame directions, locked/suppressed state, joint solving and solved placement |

### Saved study findings

Study scripts, reports and capture paths in this section are relative to [the Study directory](../Study/README.md).

`component-body-proxy-decoding.json` resolves both populated-context proxies in the Boundary Fill component sample. Body IDs 275/354 match `ToolA`/`ToolB`; independent descriptor-context body leaves agree with the typed anchors. Ordered frame routes match occurrence 410 through its stored UUID without assigning source/target or transformation meanings. Two ordinary-proxy controls and five corruption checks support the observed variant. The main reader merges these recovered proxies into `body_selections`, removing only their superseded unresolved entries. General context semantics and current body lifecycle remain unresolved.

`move-decoding.json` checks nine exports in `movemodes-34cba3ced135`, covering six Move definitions and rotated-component coordinate contrasts. A bounded backend parser retains its optional reference slots, explicit parameter roles, owned selected entities and rigid transform. Translation/rotation/point controls and input body names match the API; transforming the original box corners reproduces each exported result's bounds. Two prior free-move matrices still match saved API transforms, and three malformed mode/matrix/owner cases are rejected. Point-to-position coordinate-space encoding remains unknown, with a null flag rather than an assumed API value. `GenerateMoveHoldouts.py` contains two proposed contrasts that were not captured because the foreground guard stopped dispatch; they add no coverage. Context frames, B-rep edge/vertex selections, face moves and regeneration remain partial. Existing body caches already include the move and must not have its matrix applied again.

`move-coordinate-decoding.json` supersedes the initial point-to-position flag limitation: the two prepared holdouts are now captured in `movemodes-0dd2f72dd9a7`. Component mode has a zero coordinate byte and no header frame; design mode has a one byte and an explicit frame. The reader validates both fields together. The two holdouts and original design-space example pass 18 API/control/transformed-bounds comparisons, including a rotated nested component. Three malformed flag/frame combinations are rejected. General frame interpretation, selected B-rep vertices and regeneration remain unsupported.

`joint-decoding.json` compares eight exports in `jointmodes-20d3aef2a07d`, covering seven point-origin joint types and a flipped/aligned rigid case. Native motion codes differ from API enums. Six bounded degree-of-freedom slots retain current/minimum/maximum/rest values, enable flags and explicit self references; enabled parameter bindings agree with those values. Typed origin/component links and ordered route UUIDs establish the two occurrence contexts independently of the native joint's differently ordered member list. Six malformed cases and two no-joint controls are checked. The initial grounded-first API failures remain in `jointmodes-3b967cafd7ca`.

The joint fixtures also expose an optional empty attribute table in their root occurrence collection; parsing it restores two reciprocal cached occurrence paths per file. Main-reader comparisons cover all eight joints and sixteen cached body placements. **Stored occurrence/context matrices differ from joint-solved placement.** Whenever the known native joint class is present, derived sketch/body/path coordinates use explicit occurrence-cache keys and status instead of solved-world labels, including when a joint layout is unresolved. A prior non-joint assembly retains its verified world-coordinate output. Successful native joint-definition chains are classified as `Joint` features; unknown definitions remain unsupported. Arbitrary joint geometry, as-built variants, custom directions, state flags, kinematic solving and regeneration remain unfinished.

`assembly_decoding.occurrence_paths` expands native occurrences through their parent components. Repeated instances share component definitions but have separate world transforms. A modeling feature's input-sketch component is recorded as source context. Its parent component is resolved separately through an explicit dependency-scope edge and typed component datum when that layout is recognized. Sketch ownership provides an independent consistency check.

`component-creation-decoding.json` recovers 27 CreateComponent associations across sixteen existing archives through typed scope datums, reciprocal internal snapshots and occurrence datums. The snapshot has an identity shortcut or an explicit rigid parent-local matrix; repeated datum references and a counted self/creation/scope table must agree. Forty-one comparisons use independent saved occurrence getters in the assembly and joint captures, and four malformed-reference guards pass. The eight Moving joint examples preserve a decisive counterexample: their creation snapshot differs from the later saved API transform after joint solving. Historical placement is therefore kept separate from a current solved state. Native structural evidence covers the other archives. The main reader exposes `component_creations`, classifies only successful CreateComponent records and annotates each related internal snapshot without claiming its whole schema is supported. `validate_component_creation.py` reproduces the focused report.

`pin-provenance-decoding.json` resolves the eight existing Pin features through reciprocal frames/links and an explicit UUID route to the native Fixed occurrence. Actual saved occurrence names and the joint's second occurrence corroborate that identity; four malformed route/owner guards reject. The main reader exposes `pin_provenance` and classifies successful Pin records. The generator requested grounding but did not save an `isGrounded` getter, so `verified_current_is_grounded` remains null. Suppression effects, lifecycle state, other route/frame variants and joint solving remain unresolved.

`copy-paste-occurrence-decoding.json` recovers the existing same-definition ComponentA:1 to ComponentA:2 copy through an explicit source UUID route, its independently decoded creation snapshot and a reciprocal created-occurrence datum. The nested ComponentB graph instance is reused, not inferred as a separate native copy target. Nine API comparisons, eight native checks, eight malformed guards and two historical-cache mismatch controls pass. Stored source-cache times first-feature-matrix equals the stored created cache in this sample; the reverse order does not. These arithmetic facts are retained without assigning a general transformation role or claiming current solved placement. Main output matches the report and annotates only successful CopyPaste IDs; component duplication, external links, other copying variants and replay remain unresolved.

`recipe-component-decoding.json` corrects the observed reference grammar: a count0/1/2 is followed by that many 32-bit components and a mandatory zero terminator. Count2 accounts for 184 formerly rejected recipes across eleven existing archives (178 edge and six face). All 184 framed records reencode byte-for-byte; five malformed guards reject, and output is independent of numeric record lookups. Components can be negative, and positive components can coincide with unrelated records or have no matching record. They remain opaque numeric tuples. The old `matching_primary_record` diagnostic is renamed `numeric_record_collision`, explicitly without an object-reference claim; the surface-constraint field likewise becomes `recipe_stored_numeric_reference_value`. Existing 0/1 parser fields remain as legacy framing, while the opt-in counted reader supports all three observed counts. Main output merges the new frames into `recipe_decoding` and exposes `recipe_reference_components`. Payload operation meanings, chosen cells, persistent face/edge identity and regeneration remain unresolved.

`occurrence-gate-attribute-decoding.json` recovers the imported expanded-timeline root. Three literal stored attributes add 132 bytes before the standard occurrence suffix; the earlier reader assumed an empty table. The strict callback admits only the captured parentless identity root with the exact ordered false/empty/false attributes, then reuses canonical occurrence framing in memory. Removing just that attribute table yields the exact complete root payload of the independently saved grouped import source. Thirty-seven focused checks include reciprocal component/root references, three restored root sketches/body placements, six unchanged ordinary occurrence controls and four malformed guards. The expanded API truth has timeline/group getters, without occurrence path/transform getters; that missing evidence is explicit. Gating, visibility, resolution-time meaning, nonempty HString encoding and active attribute combinations remain unresolved. Ordinary occurrence output stays unchanged.

`GenerateComponentColorContrast.py` imported an owned contrast into a fresh document, set the root component's display color to `(17,83,201,255)`, captured actual getters and exported one new file. `component-display-color-decoding.json` qualifies nine component prefixes across six archives, including three assembly children, through thirteen typed reciprocal references per component. The bounded prefix replays exactly; the controlled change alters only its three float32 RGB fields. The four same-document parameter exports keep that prefix unchanged. A stored-red rounding counterexample yields181 while the actual getter returns180, so no general RGB8 conversion is published. Eight malformed guards pass. `component_display_colors` exposes the raw float32 channels and opaque adjacent bytes; alpha, color space, display-mode enablement and material appearance are not inferred.

`asbuilt-joint-decoding.json` adds actual root AsBuilt Rigid, Revolute and Slider definitions with two independently owned component occurrences. Typed feature/context routes establish API occurrence order Moving/Fixed separately from the native joint's Fixed/Moving member list. Native collection backlinks, repeated inputs, fresh component scopes and enabled parameter bindings are checked. The common six-slot motion parser is shared with ordinary joints; the observed nonrigid matrix-marker variant retains forty prefix bytes and a shorter footer without assigning meanings to incidental numeric values. Two explicit native origin-point/provider/backend routes corroborate API geometry transforms. Rigid geometry stays null; `[-1,-1,-1]` in the provider is retained as a sentinel rather than a point. Actual rounded limit getters, not requested values, corroborate the decoded native values. Nine malformed guards, six placement snapshot comparisons and all eight ordinary-joint goldens pass. Main `as_built_joints` classifies only successful AsBuilt features, updates their timeline names/kinds and clears only their newly resolved common-native-joint lookup diagnostic. Joint or AsBuilt class presence keeps placement labels unsolved even if definition decoding fails. Suppression remains null because only unsuppressed getters were captured; no solver or solved world placement is inferred.

`rigid-group-decoding.json` identifies native constraint type11 inside the existing As-built/common-JOINT classes, without treating it as an ordinary API rigid joint. Three actual groups establish seven expanded occurrence associations, four copied relative matrices and one typed reciprocal parent/child route. Shared AsBuilt context readers preserve their default output and reject the nested route unless explicitly opted in. Seven malformed guards and all three prior AsBuilt golden summaries pass. The nested capture retains eight token getter failures rather than using tokens to choose native identities. A requested suppressionTrue setter completes but the actual getter remainsFalse, so suppression and `includeChildren` encoding remain null. Main `rigid_groups` classifies only qualified groups and clears only their resolved generic native-joint lookup failures. Existing strict AsBuilt diagnostics and unsolved placement labels remain separately scoped.
