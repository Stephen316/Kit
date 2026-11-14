# Reference-driven native rectangle projection

## Scope and evidence

Extend the strict public adapter to complete native rectangular extrusion documents whose decoded Design graph has one root component, one planar rectangular sketch and one ordinary additive distance extrusion. The first two qualified controls are:

| Source | Source SHA-256 | Native Design identities | Geometry |
| --- | --- | --- | --- |
| `re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d` | `09980af5a2c9e03e0fc9246ed0b20e796c8f5574c8838d255c85bdd08ea1aa9c` | Component 3, sketch 202 / DcSketch 207, extrude 279, body 311 / DcBody 317 | 40 × 30 × 25 mm |
| `re/Fusion/LocalOracle/RectangleAuthoring/vendor_ProductionCuboid37mm.f3d` | `62c03b7aa11ce2c79193e51376e4405e6bbfd34aa5ab8097b72043ad49f38683` | Component 1002, sketch 1089 / DcSketch 1106, extrude 1121, body 1140 / DcBody 1143 | 17 × 23 × 37 mm |

Read-only inspection used `EntityGraph/DecodeGraph.py::read_graph` on each source; no product parser execution, native calls or local tests were used for this plan. Parent-coordinated complete native acceptance is recorded in `LocalOracle/NativeDocuments/NativeAcceptance.json`: the original and fully typed re-emitted documents both survived native rollback, regeneration, height edits and save/reopen. These are full archives with graphics, snapshots, empty configuration parts and material aliases; their accepted lower codec is `ReadDocument` / `EmitParsed`.

The ordinary control has 347 total segment records and the saved cuboid 246. Their respective graphics scenes have 39 and 41 objects. Both have one BRep history, one prism snapshot, one material package and two empty configuration payloads. These counts are observations, not eligibility constants.

## Why the existing constructor qualification is insufficient

The ordinary control has **zero user parameters**. Its extrusion owns `d1` (25 mm, expression `25.00 mm`) and `d2` (zero taper, expression `0.0 deg`). The saved cuboid has the user parameter `authoredLength` (37 mm, expression `37 mm`), owned distance `d2` referring to it, and taper `d3`. A projector must not manufacture a user-height parameter for the ordinary control or rename these actual parameter names into generic role labels.

The ordinary history serializer maps body key 0 to Design body 311; the saved control maps body key 1 to Design body 1140. Their extrusion start/end history states are 2/4 and 2/7. Both feature-id managers map sketch operation 300 and extrusion operations 301/302 to their actual feature identities. These joins must be derived from references and checked against the typed BRep history; authored defaults such as body key 0 and end state 4 are not native-format invariants.

Native UI and bookkeeping differences include additional units and choices, cameras, named views, render settings, image serializers, texture mappings, cache records, populated update timestamps, and changed visibility. These do not justify comparing against a newly authored archive or erasing source identities.

## Index and ownership

Build an immutable index keyed by `(segment_id, object_id)`. Merge primary and continuation groups without losing the original records or frames. Resolve class identities through the production schema vocabulary; ancestry identifies persistent feature and geometry families. A local reference is resolved in its owning segment. A cross-segment reference must resolve to its declared target kind.

Find the root `ComponentInstance` and its `rTargetComponent`, then the component's `DcDesignFragment`, node container and creation-order controller. Reject more than one component occurrence, external references, nonidentity occurrence placement, derived ownership, unmodeled body collections, or actual assembly relationships. Entity IDs are never assumed to start at 1000, occur in creation order, or have a particular gap pattern.

`DcCreationOrderFeatures.representationFeatures` is the authoritative feature ordering for this profile: exactly the referenced `DcSketch` followed by `DcExtrudeFeature`. Enumerate every entity derived from a feature-bearing base and every component feature collection; no extra active, suppressed, eliminated, orphaned or grouped feature is silently discarded. Known structural/helper entities are separately classified and retained in the native state. Unknown classes or unclassified semantic records reject qualification.

## Sketch projection

Follow `DcSketch.rSketch` and reciprocal `MSketch.rDcNode`, then `MSketch.UCS` and its `CoordinateSystem.transform`. Initially qualify the XY plane and identity occurrence/coordinate placement; validate the referenced `DRMatrix` and plane source consistently. Preserve the actual support reference and native identities in the versioned native state.

Inspect the actual `MSketch.children`: five `Point3D` records and four `Line3D` records in both controls. The fixed origin is distinct from the rectangle corner at the same position. Expose all five points and all four lines in the neutral sketch rather than conflating equal coordinates or inventing a coincident constraint. Resolve each line's `rStartPoint` / `rEndPoint`; verify its saved start/displacement, direction and plane normal against the referenced points. Build the closed profile by traversing endpoint incidence, independently of record or recipe-list order. Require one simple rectangle, four distinct corner identities, positive side lengths, perpendicular adjacent edges and no interior loop, arc, spline, projected curve, construction edge or offset.

For the two initial vendor profiles, dimensions and constraints are empty, and the four corners/lines are unfixed. The separately fixed origin is allowed. Actual constraints or driving dimensions require their own qualified projector; do not convert their presence into free geometry. Existing independently authored constrained profiles retain their current route until their reference-driven constraint handling is added.

## Parameter and extrusion projection

Follow `rAlongDistance` / `rTaperAngle` to their `DcDoubleParameter` objects and then `parameter` to actual `Parameter` records. Require reciprocal `dcParameter`, `rrOwnerFeature`, `rParentFeature` and compatible numeric values. Preserve `userName`, native expression text, comment, owned/user distinction and actual IDs. Use mm for neutral lengths and radians for angles; the native numeric quantities are cm and radians. Expression support initially includes dimensionally checked literals and a direct reference to one existing compatible user parameter. Reject other formulas until their dependencies and semantics are implemented; never use Python evaluation.

Emit a neutral `DistanceExtrude` whose owned parameter IDs are the real projected distance/taper IDs. User parameters have no artificial feature owner. All ParameterTable entries must be accounted for, including unused user parameters; external, text, Boolean, orphan or unsupported parameter forms reject the initial scope.

Validate every geometric option in `DcExtrudeFeature`: `booleanOperation=4`, `directionType=1`, solid operation, positive Z normal, one distance extent, no reversal, start offset, second side, thin wall, from/to entity, target-body modification, removed bodies or taper. Require active, healthy, unsuppressed sketch/extrusion status. Follow the single `profileDataRefs` through `ModelDataRef.dataRefs` to `SketchRegionRef`, its scope and `SketchRegionRecipe`. Resolve scope IDs by their declared kind: native controls use an entity-id scope (`scopeIdType=1`, `scopeEntityIdentifier` equal to the actual sketch ID); persistent-UUID scope (`scopeIdType=2`) is resolved through the actual component/sketch persistent identities when explicitly supported.

Validate the region recipe's referenced sketch primary tags and loop polarity against the four consumed edges. Its saved tag list order is retained exactly and is not treated as geometric perimeter order: the ordinary control stores 107,106,108,105 whereas the saved authored control stores 105,106,107,108. Do not sort or rewrite that native list.

## Body, identity and history joins

Follow the extrusion's sole `dcBodies` reference and verify `DcBody.rOwnFeature`, `rBody`, fragment membership and component body-container membership. Resolve `BRepHistorySerializer.partName` to the typed history part, and `mapBodyId` from its saved body key to this exact Design body. Validate BodyKey against the history identity; validate OperationId through `DcFeatureIdManager` and body/sketch progenitors, not a hardcoded operation number. Validate the applicable secondary tag/progenitor role and body UUID relationships. Require history current/initial states to agree with the feature's actual end/start states.

The typed prism BRep must match the extruded rectangle's placement, side lengths and bound distance. Build neutral analytic topology from those actual dimensions using `BuildPrism`, and preserve the source's typed carrier/rim/tag/history representation in native state. Do not use display meshes to derive the solid. The source body's empty `userName` is distinct from a synthesized label: retain the stored name and creation index, with a documented display-label fallback only if required by neutral UI presentation.

Preserve the complete prism snapshot and validate its solid/profile/sketch geometry and tags against the corresponding current model and input rectangle. Snapshot presence does not add a hidden modeling operation. Empty table/rule configuration payloads are already semantically checked by `ReadConfigPart` / `CheckDocConfig` and remain exact typed parts; nonempty configurations remain rejected by the lower codec.

## Materials, appearance and graphics

Resolve the body's physical/visual material references through its actual ProteinAssetManager and material package. Use `ResolveMatAsset` for the native `_Post2015` appearance alias and retain both original and effective asset records. Physical name selection uses the nonempty `physmat_Label`, otherwise the stored definition `UIName`; a library localization key remains a key. Follow physical aspect connections to the actual structural density. Project a typed neutral material record containing the physical name, density and effective appearance's floating-point `metal_f0` RGBA channels; keep all other definition/property/connection values in decoded native state. Do not flatten all asset properties into one dictionary or conflate density from unrelated instances. The source Steel appearance is not the authored generic material, and its raw color channels must not be rounded to UI bytes.

The graphics scene is typed `GraphicScene`, not `GraphicsData` or an opaque stream. Extend the static state registry only with the dataclasses reachable from `GraphicScene`; raw stream carrier classes are excluded. Validate scene entity references against the same segment index. Keep graphics as derived display state and preserve all typed mesh/texture/node fields. No new modeled body or timeline feature may be accepted solely because it appears in graphics. Preview images remain the already explicit image parts.

## Exhaustive field accounting

Use declarative policies per class/group: each saved member is either projected, validated as a supported modeling condition, resolved as a graph reference, or explicitly retained as non-modeling UI/cache/provenance state. Inherited member groups are included. Unknown members and unknown semantic classes reject; there is no catch-all 'retain arbitrary feature' policy and no class-name prefix heuristic.

Allow variations in explicitly non-modeling values such as compute timings, birthdays, native persistent identities, source labels, cached topology and UI visibility without treating them as source-template deviations. Modeling-affecting flags, feature lists, relations, transforms and dependencies are independently validated. These policies are schema-based and semantic; they must not embed complete source records, source hashes, captured entity IDs, or an authored graph template.

## Contract and dispatch

Keep semantic authoring contract version 1 unchanged. Introduce native-state version 2 for reference-projected native documents, with the complete typed model and no archive/segment payload retention. Preserve decoding and consistency checking for already-created native-state version 1 documents.

Dispatch by explicit decoded graph signature and supported feature semantics, not by attempting one parser and falling back on its error. The new ordinary native rectangle-extrusion route accepts both controls and arbitrary valid entity allocations satisfying the invariants above. The already qualified constructor routes remain separately identified until migrated. Prefer version 2 for vendor auxiliary-bearing rectangle graphs; do not change the meaning of an existing version-1 contract silently. Writer version 2 decodes the model, independently emits and rereads it, runs the reference projector, and compares the complete neutral document before mutation. It does not compare source records with freshly authored records.

Source identities in neutral records should be stable textual `(segment, entity)` IDs. Preserve actual parameter names, feature/geometry identities and dependency links. A full native round trip retains the exact decoded semantic model even when ordinary ZIP framing differs. Changed neutral fields without a corresponding supported semantic update are rejected, as in the existing writer contract.

## Implementation and validation boundaries

Own only the adapter subtree, new public API integration tests, the new change/gotcha entries and research artifact preparation. Do not modify the shared neutral model, lower codecs, evidence matrix or workflows. Add focused modules for indexing, semantic eligibility, rectangle topology, parameter binding, extrusion/body joins, material resolution, native-state version routing and field-disposition policies.

Remote integration cases should cover both complete source archives through strict public read, neutral JSON and native write; actual parameter inventories and identity preservation; arbitrary entity-ID remapping through typed references where the generic encoder supports it; and adversarial mismatches in feature ordering, unmodeled features, suppressed state, line endpoints, geometry, parameter owner/value/expression, profile scope, BRep body/operation/secondary identities, history state, material alias/library joins and auxiliary scene references. Verify rejected operations leave path and stream destinations unchanged. Retain the existing 26 public adapter cases.

Prepare new public-route native re-emissions from each controlled source after implementation. Parent owns Fusion load/rollback/edit/rebuild/save/reopen acceptance, commits, PR checks and configured review evidence. No native calls or local tests are authorized to this agent.

## Implemented qualification

The implementation uses the narrower counterclockwise, axis-aligned, unconstrained rectangle profile described in `Documentation/Changes/Fusion/Adapter/FusionNativeRectangleProjection.md`. Native-state version 2 requires auxiliary-bearing documents and rejects nonempty mesh parts. Parameter references target literal user parameters; dependency chains are rejected. The two public re-emissions have SHA-256 values `0203674063f58504d037a51236a1aff9cc3283ed1b8b107cc8307e1e73f10e92` and `49f92bbe4f33fc7c1413ca8a8d433ff3ba948c1822c6513363934425f626ec31`, matching the prior accepted typed re-emissions. The former broad proposal does not expand these implemented eligibility conditions.
