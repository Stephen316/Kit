# A01: Neutral contract and capability audit

## Decision and scope

Use Kit interchange JSON as the neutral file format.
The document is the existing typed `CadDocument`, serialized with the existing wire codec and UTF-8 JSON adapter.
Use the existing `.json` suffix and `interchange.json` format identifier.
Do not introduce another neutral schema, custom binary format, or source-specific intermediate document.

This completes the A01 design deliverable: contract inventory, demonstrated gaps, version boundaries and independent acceptance requirements.
It does not implement a decoder, comparator, controller, schema extension or native writer.
Conversion support remains unqualified until the later route-specific gates pass.

The audit inspects main `52dbbe55ea1410b6bcf0ac153975b8c35fe37a3d`.
PR #94 supplies the [plan](AutomationPlan.md) and [step register](AutomationSteps.md).
The separate Fusion comparison uses unmerged PR #92 at `be3220e3fb2e07ef33ee264f300a20f2c7a4a137`.
Results from that branch are not main capabilities.

## Artifact design

| Artifact         | Contract                                                                                   | Purpose                                                                                                           |
| ---------------- | ------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| Neutral document | Existing `CadDocument` JSON with registered wire records and `schema_version`              | Portable design information consumed by native writers                                                            |
| Native evidence  | Existing source identity, provenance spans, diagnostics and explicitly classified payloads | Explain source observations and undecoded information                                                             |
| Research receipt | Separate versioned JSON evidence record, to be implemented in A03                          | Bind a document digest to source hashes, decoder revision, options, field-level observations and acceptance scope |

The receipt is not a replacement document or a new `CadDocument` field.
Its implementation belongs to A03, not this audit.
Its required information is source/document digests, native versions, decoder revision, options, profile, requirements, unresolved items and evidence links.
Statuses distinguish syntax, semantic interpretation, reference resolution, native writing and application acceptance.
The receiver must verify that its document digest matches the neutral file before using its claims.
Digest agreement binds the receipt to bytes; it does not establish the truth or authorship of its evidence.

Native payloads remain useful evidence but cannot replace portable feature definitions.
A destination writer must work from understood neutral semantics without needing the opposite-format source file or proprietary application.
Retaining a source archive in `$bytes` does not complete decoding.
Source evidence can contain private design information and requires the same handling as the original model.

Use existing serialization functions and registered types, including their historical wire-name mappings.
Do not infer wire keys from Python identifiers or change `$type`, `$enum` and collection markers manually.
Source inspection shows deterministic key ordering and explicit type registration.
It does not establish semantic equivalence between documents with different identities.
Run model/reference validation separately from JSON reconstruction.

The root model defaults to schema `1.0`; that label alone does not enumerate adapter or feature coverage.
Record exact SDK and contract-profile revisions in research receipts.
Any later field or type addition requires registered serialization, compatibility/migration evidence and its own reviewed change.

## Existing contract inventory

“Represented” below means a model type exists, not that every native reader or writer implements it.

| Domain                   | Existing representation                                                                        | Limitation or required check                                                                                     |
| ------------------------ | ---------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Document and source      | `CadDocument.source`, `schema_version`, diagnostics, metadata                                  | A source digest is integrity evidence, not source authentication                                                 |
| Units                    | Document `UnitSystem`; `ParameterValue.kind` and `.unit`                                       | Document unit choices are mm, m and in; parameter units remain explicit strings                                  |
| Parameters and formulas  | `Parameter.value`, role, owner, expression and referenced parameter IDs                        | Retaining expression text does not establish execution in another CAD application                                |
| Sketch geometry          | `Sketch`, lines, circles, arcs, splines, conics and support plane                              | `NativeGeometry` retains unresolved source semantics and cannot qualify a portable sketch                        |
| Constraints              | `SketchRelation.kind`, entity/point references, parameter binding, driving and suppression     | Kind is a string; each relation still needs source meaning and target support                                    |
| Planes and placement     | `SupportPlane`, transform basis/origin, support selection and offset parameter                 | Validate orientation, reference ownership and units independently                                                |
| Feature history          | `FeatureStep.order`, inputs, sketch/parameter/selection IDs, operation and definition          | Feature labels and dependency validity do not prove complete definitions                                         |
| Extrusion                | `ExtrudeFeature`; linked `DistanceExtrude` and `PlaneExtrude` definitions                      | Legacy inline values and parameter-linked definitions require semantic mapping, not literal equality             |
| Revolution               | `RevolveFeature`; linked `AngularRevolve` and `PlaneRevolve`                                   | Preserve actual axis, extent, direction, plane limits and driving bindings                                       |
| Finishing and body tools | Typed fillet, chamfer, shell, hole, patterns, scale, move, combine and reference-plane records | A type does not cover every vendor option or operation sequence                                                  |
| Configurations           | `Configuration`, parameter overrides, feature suppression and per-feature configuration states | Variant selection and suppression relationships need explicit paired evidence                                    |
| Bodies and geometry      | Design bodies, neutral B-rep topology/curves/surfaces, meshes and payload roles                | Cached geometry cannot substitute for editable source history                                                    |
| Tolerances               | B-rep vertex, edge and face tolerance fields                                                   | No root-wide comparison tolerance policy; define quantity-specific criteria separately                           |
| Assemblies               | Definitions, instances, linked documents, transforms, mates, groups and entity references      | Complete component bundles and constraint behavior remain independent obligations                                |
| Materials                | Main has `DesignBody.material_id` and an inferred materials capability                         | No root typed material collection on this main revision; identity alone cannot represent density/color semantics |
| Provenance               | Optional entity-level `Provenance` with stream spans, native ID and attributes                 | No enforced per-field evidence coverage or requirement that every record provides provenance                     |

### Source anchors

- [Root document](../../../src/interchange/document/models/DocumentModel.py)
- [Parameters, roles and expressions](../../../src/interchange/records/RecordParameter.py)
- [Sketches and relations](../../../src/interchange/geometry/models/Sketch.py)
- [Feature step](../../../src/interchange/features/FeatureStep.py)
- [Inline feature definitions](../../../src/interchange/features/FeatureKinds.py)
- [Inline extrusion](../../../src/interchange/features/FeatureExtrude.py)
- [Linked distance extrusion](../../../src/interchange/features/FeatureDistExt.py)
- [Linked angular revolution](../../../src/interchange/features/FeatureAngleRev.py)
- [Configuration records](../../../src/interchange/records/RecordConfig.py)
- [Bodies](../../../src/interchange/features/FeatureBody.py)
- [B-rep tolerance fields](../../../src/interchange/brep/topology/BrepTopology.py)
- [Provenance records](../../../src/interchange/records/RecordProvenance.py)
- [JSON codec](../../../src/interchange/serialization/JsonCodec.py), [wire encoding](../../../src/interchange/serialization/EncodeData.py), [registered type reconstruction](../../../src/interchange/serialization/Deserialize.py)

## Reader and writer capability boundaries

| Path                     | Inspected main behavior                                                                         | A01 disposition                                                                        |
| ------------------------ | ----------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| SOLIDWORKS → neutral     | Registered part/assembly reader combines available native records, geometry and source evidence | Reuse it; A04 must qualify each feature variant and every required source relationship |
| Fusion → neutral         | Explicit research reader requires `strict=False`; production discovery excludes `Fusion`        | Reuse its evidence carefully; A05 must establish the intended supported read boundary  |
| Neutral → SOLIDWORKS     | Recovered native families, source replay/edit paths and preservation paths coexist              | A12 must prove portable-source writing without relying on same-format replay           |
| Neutral → Fusion         | No production registered Fusion writer on main                                                  | A11 remains open; the unmerged writer is not a general portable-graph translator       |
| Neutral → JSON → neutral | Registered model serialization and reconstruction exist                                         | Reuse them; JSON roundtrip alone does not prove native semantic preservation           |
| FreeCAD and CATIA        | Registered adapters have native subsets and preservation/replay representations                 | Future per-route qualification, not automatic support for all new neutral concepts     |

The SOLIDWORKS container implementation accepts versions 3 and 4.
That is a physical-container scope, not support for every SOLIDWORKS application release or feature grammar.
Recorded SOLIDWORKS native evidence includes controlled 2025 families.
The saved Fusion study identifies captures from 2705.1.30 and 2706.1.17 and implemented version-8 stream framing.
These are evidence anchors, not a blanket supported-version matrix.
A02 must bind each candidate pair to actual files and application builds before qualification.

The historical FreeCAD → SOLIDWORKS structural audit records 44 accepted files out of 165, with zero accepted assemblies out of five.
It neither qualifies SOLIDWORKS → Fusion nor establishes native application acceptance for every counted part.

The pinned [unmerged Fusion adapter description](https://github.com/TryUniCAD/Kit/blob/be3220e3fb2e07ef33ee264f300a20f2c7a4a137/Documentation/Changes/Fusion/Adapter/FusionPublicAdapter.md) adds qualified authoring/native-state contracts and typed materials.
It expressly rejects arbitrary changed neutral graphs outside those contracts.
Do not resolve the main material gap by adding a competing type before reconciling that work.

Source evidence: [SOLIDWORKS adapter](../../../src/convert/adapters/solidworks/core/Adapter.py), [container versions](../../../src/convert/adapters/solidworks/container/Format.py), [Fusion discovery exclusion](../../../src/convert/adapters/registry/AdapterDiscovery.py), [partial-reader options](../../../src/convert/adapters/Fusion/ReaderOptions.py), [corpus scope](../../../re/Fusion/Notes/Corpus.md), [measured writer scope](../../../re/solidworks/CorpusCoverage.md).

## Demonstrated gaps and owning steps

| ID  | Gap established by inspection                                                                                                             | Resolution owner                                                                                     |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| G01 | Capability inference detects category presence, including native-only timeline records; it is not semantic coverage                       | A03/A04/A05: retain a separate evidence receipt and unresolved census                                |
| G02 | Main Fusion discovery/read policy is research-only and no native writer is registered                                                     | A05/A11: reconcile the pinned Fusion work and qualify the actual route                               |
| G03 | Legacy inline and linked feature definitions represent related semantics differently                                                      | A04/A05/A06/A11/A12: map roles and dependencies explicitly; do not compare serialized field spelling |
| G04 | Unsupported SOLIDWORKS records can become `NativeFeature` definitions; typed extrusion termination can also remain `native:<code>`        | A04: classify both opaque and partially interpreted definitions as unresolved                        |
| G05 | Labels exist for sweep, loft, draft, mirror, helix and offset without complete dedicated typed definitions in the inspected feature model | A16: add only source-demonstrated contracts and qualified mappings                                   |
| G06 | Per-field evidence and semantic matching are not enforced by existing entity provenance or JSON serialization                             | A03/A06: implement field-path receipts and explainable graph correspondence                          |
| G07 | Main materials retain an identity but not a root typed density/color contract                                                             | A01 follow-up/A11: reconcile PR #92 before qualifying inputs requiring those semantics               |
| G08 | Generic reference validation does not establish all vendor constraint meanings or regenerate geometry                                     | A04/A05/A13/A14: use independent source inventories and native observations                          |
| G09 | Reader strictness and carrier policy are independent, and target-limit carriers can remain permissible                                    | A11/A12/A13: apply the full required-capability gate in addition to public options                   |

The SOLIDWORKS `BuildExtrude` path derives its `reversed` field from the cut operation and can retain a native termination code.
This is a mapping observation, not a measured direction defect.
A04 must verify direction, frame and operation independently before treating those values as portable source semantics.

Source evidence: [feature construction and fallback](../../../src/convert/adapters/solidworks/core/Adapter.py), [feature-kind labels](../../../src/interchange/enums/EnumFeatures.py), [definition-specific checks](../../../src/interchange/document/validation/DocumentDefValidate.py), [capability inference](../../../src/interchange/document/models/DocumentCaps.py), [write policy](../../../src/convert/adapters/base/WritePolicy.py).

## Initial contract profiles

These are requirements for A02–A13, not declarations of current conversion support.
Each profile has independent source inventories, required concepts, allowed variants and explicit failure cases.

| Profile                    | Required portable meaning                                                                                                                | Initial limits                                                                              |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| P01: dimensioned rectangle | Four connected lines, support frame, anchored position, horizontal/vertical relations, driving width/depth and actual parameter bindings | One planar sketch; no unresolved relations or expression dependencies                       |
| P02: dimensioned circle    | Center, radius, support frame, position constraint and driving radius/diameter meaning                                                   | One full planar circle; do not conflate radius and diameter                                 |
| P03: additive extrusion    | P01 or P02, driving depth, direction, start condition, operation, dependency order and resulting body                                    | Qualified one-sided blind case first; reject unresolved termination, draft or second extent |
| P04: cut                   | Qualified parent body, profile, driving extent, direction and explicit cut operation                                                     | Qualify blind first; through-all remains a separate variant                                 |
| P05: revolution            | Profile, axis origin/direction/ownership, angular extent, operation and driving parameter                                                | Axis/angle/direction variants require independent evidence                                  |

For these comparison profiles, express normalized lengths in millimeters and angles in radians while preserving source unit evidence.
Treat inline and linked values as equivalent only when their source relationships and driving roles are independently established.
Do not synthesize missing dimensions, constraints or dependency edges merely to make documents match.
Inputs requiring custom materials, assemblies, additional configuration variants or other unqualified semantics fail until those semantics are covered.
A selected single active configuration still retains its source identity and required state.
This is a qualified profile boundary, not permission to discard input information.

## Independent acceptance contract

1. Bind each source to its exact file hash, authoring recipe and application version.
2. Independently enumerate required parameters, sketches, constraints, formulas, features, references and applicable variants.
3. Require every source requirement to have a portable interpretation or an explicit unresolved disposition.
4. Reconstruct the neutral JSON through registered types and validate its model references.
5. Compare source roles and graph relationships using declared numeric tolerances; retain uncertain matches.
6. Prove each native writer uses understood neutral information without opposite-format source replay, donor blocks or CAD runtime dependencies.
7. Check native output body count, volume, center of mass, geometry and feature history against independent source observations.
8. Exercise every independent driving parameter, restore it, rebuild, save and reopen the result.
9. Verify all required constraints, expression dependencies, feature states and assembly relationships independently.
10. Require healthy controls and exact-revision remote evidence for each claimed route.

Both SOLIDWORKS → neutral → Fusion and Fusion → neutral → SOLIDWORKS must pass for the bidirectional milestone.
A successful JSON reconstruction, same-format fixed point or matching pair cannot replace those observations.
No native application or test execution was performed for A01.

## Verification and handoff

The audit used read-only source inspection and AST field enumeration without importing or executing SDK modules.
It traced the model, serialization, reference validation, capability inference and relevant adapter boundaries.
New documents receive Markdown formatting, source-link inspection and Git whitespace checks before publication.
Remote PR checks and configured review remain separately reported evidence.
Full rendered documentation assessment and language-standard conformance remain unverified.

A01 decides the existing neutral format and qualified profile design without changing schema `1.0`.
No code, migrations, command, runtime selection or persistence implementation is introduced.
A02 is the next step: pin actual paired examples and independently measured expected observations for P01–P05.
G01–G09 remain tracked implementation/qualification gaps, not claims that A01 repaired them.
