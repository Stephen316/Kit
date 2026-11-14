# Fusion reader and writer acceptance evidence

This matrix records what the production codecs have demonstrated, which input is independently constructed, and which surrounding data remains supplied by the caller. The detailed wire and semantic model is [FusionDataModel.md](FusionDataModel.md). Acceptance does not extend automatically from one row to another.

## Complete documents

| Production operation                             | Construction and observed result                                                                                                                                                                                                      | Evidence and boundary                                                                                                                                                                                                                                                         |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Parameter-only F3D authoring                     | Fresh complete archive, new identities, typed Design/ACT/Browser segments and generated previews. Fusion changed the length from 17.25 to 31.5 mm, saved and reopened it, then created native sketch/extrusion features.              | [Native report](../../../re/Fusion/LocalOracle/Authored/ProductionParameterAcceptance.json). No source archive or CAD runtime in the writer.                                                                                                                                  |
| Circle-sketch F3D authoring                      | Fresh complete document with a radius-12.5 mm circle. Native radius edit to 18 mm survived save/reopen, and Fusion subsequently extruded the sketch.                                                                                  | [Native report](../../../re/Fusion/LocalOracle/Authored/ProductionCircleAcceptance.json). The qualified sketch profile does not imply arbitrary constraint-system generation.                                                                                                 |
| Circular-extrusion F3D authoring                 | Fresh document, two healthy timeline features and independently constructed solved history. Initial height 17.25 mm was correct before recomputation. Rollback, restoration, rebuild, height edit to 23 mm and save/reopen succeeded. | [Native material/geometry report](../../../re/Fusion/LocalOracle/Authored/ProductionMaterialDocumentAcceptance.json). The generated package also supplies valid density, mass and center. No source records, template archive, donor geometry or vendor runtime in the codec. |
| Complete typed read and re-emission              | All three entity segments and supported body history are decoded. The independently authored 61,439-byte extrusion archive reconstructs exactly.                                                                                      | [Re-emission report](../../../re/Fusion/LocalOracle/Authored/ProductionReemitted.json). Exact reconstruction is demonstrated for the qualified authored envelope, not every corpus container.                                                                                 |
| Semantic edit through a complete parsed document | A parameter comment changed in the typed entity graph. The re-emitted archive passed native load, rollback, rebuild, distance edit, save and reopen.                                                                                  | [Native report](../../../re/Fusion/LocalOracle/Authored/ProductionEditedAcceptance.json). This changes a decoded field rather than patching an offset or replaying an unchanged bulk block.                                                                                   |

The additional [rectangle/cuboid acceptance](../../../re/Fusion/LocalOracle/RectangleAuthoring/NativeAcceptance.json) establishes independent complete 17×23 mm sketches and 17×23×31 mm solids. The cuboid has valid material identity, density 1000 kg/m³, volume 12.121 cm³, mass 0.012121 kg and center (0.85,1.15,1.55) cm before recomputation. A 31-to-37 mm height edit produces volume 14.467 cm³ and mass 0.014467 kg; rollback, rebuild, save and reopen preserve the expected results. Width/depth in that default profile are authoring inputs.

The optional [fully constrained rectangle profile](../../Changes/Fusion/FusionConstrainedRectangles.md) adds actual driving width/depth dimensions, four orientation constraints and a fixed corner. Both sketch and cuboid [pass native dimension edits and save/reopen](../../../re/Fusion/LocalOracle/DimensionAuthoring/NativeAcceptance.json); the cuboid also passes rollback/rebuild and an independent height edit. Its 19×29×37 mm final dimensions produce volume 20.387 cm³ and mass 0.05851069 kg at 2870 kg/m³. Both complete accepted files [reconstruct byte exactly](../../../re/Fusion/LocalOracle/DimensionAuthoring/TypedReemission.json), including all dimension, parameter, observer and continuation records.

The complete 108,583-byte cuboid [reconstructs exactly](../../../re/Fusion/LocalOracle/RectangleAuthoring/TypedReemission.json) through typed entity, history and material models. A separate density edit to 2870 kg/m³ [passes native acceptance](../../../re/Fusion/LocalOracle/RectangleAuthoring/EditedMaterialNativeAcceptance.json) with mass 0.03478727 kg initially and 0.04152029 kg after the height edit. Historical initial solids had undefined materials and zero mass; [the diagnosis and correction](../../Gotchas/Conversion/Fusion/Materials/UndefinedBodyMaterial.md) distinguish earlier geometry-only proof from this expanded acceptance.

Material families have [held-out acceptance](../../../re/Fusion/LocalOracle/MaterialFamilies/Accept/Summary.json) on 10 × 20 × 30 mm cuboids. Nineteen cases cover the Basic, Gas, Generic, Liquid, Metal, Plastic and Wood structural families and the Opaque, Metal and Transparent appearances. Kit chose the same schemas as Fusion's own document each time. Name, appearance, mass and all 456 appearance values match. 945 of 1043 material values match, including every listed physical value; the rest are descriptive text. See [material families](../../Changes/Fusion/Materials/FusionMaterialFamilies.md).

All native reports above identify Fusion version `2706.1.17`, the exact input SHA-256 and the saved output SHA-256. The production writer does not import `adsk`; the separate research acceptance scripts use the installed application as the target consumer.

## Component-level semantics

| Production operation                        | Observed result                                                                                                                                                                                                              | Evidence and boundary                                                                                                                                                                                                                                                                              |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Full corpus Design entity graphs            | All 712 indexed Design segments reconstruct exactly through production schema selection, typed decode and encode: 261,141 records and 25,458,293 record bytes.                                                               | [Schema catalog](../../Changes/Fusion/FusionNativeSchemaCatalog.md), [corpus evidence](../../../re/Fusion/Reconstruction/CorpusSemantics/ProductionCompatibility.json). This covers Design segment records, not all geometry, auxiliary assets or historical migration paths.                      |
| Native cylinder history read/write          | Complete native history retained its closed-circle vertex owner indices and other semantic fields. Re-emission passed native rollback/rebuild, a 7-to-23 mm depth edit and save/reopen.                                      | [Native report](../../../re/Fusion/LocalOracle/Authored/NativeHistoryAcceptance.json). The acceptance archive retains its own non-history members.                                                                                                                                                 |
| Cuboid history read/write                   | Complete 102-record history and 101-insertion journal reconstructed with canonical record allocation. Native import, rollback/rebuild, 25-to-37 mm depth edit and save/reopen succeeded; volume changed from 30 to 44.4 cm³. | [Native report, `HistoryReemitted`](../../../re/Fusion/LocalOracle/PrismHistory/NativeAcceptance.json). Semantic carrier frames, ownership, identities and journal states are retained; source record numbers need not be.                                                                         |
| Independent cuboid history authoring        | Dimensions, explicit naming identities and journal states generated fresh topology and carriers without a history payload input. The same native lifecycle succeeded.                                                        | [Native report, `HistoryAuthored`](../../../re/Fusion/LocalOracle/PrismHistory/NativeAcceptance.json). Surrounding Design and selection snapshot still belong to that acceptance source; independent rectangular document authoring is established separately above, not by this history-only row. |
| Material definition/instance reconstruction | Nested material storage was reconstructed with fresh unused allocation bytes; density changed to 6300 and RGBA to 51/102/153/255. Native rebuild and save/reopen preserved the values.                                       | [Native report](../../../re/Fusion/LocalOracle/Features/ProductionMaterialAcceptance.json). The owning document remains a controlled input.                                                                                                                                                        |
| F3Z dependency envelope read/write          | Nine complete document members, eight references and the root dependency graph survived reconstructed JSON/ZIP framing, native upload and resolution. Rebuild and a 2-to-4 mm parameter edit survived cloud save/reopen.     | [Native report](../../../re/Fusion/LocalOracle/Bundles/NativeBundleAcceptance.json). All nine supplied document members are preserved explicitly; the bundle codec does not semantically convert their contents.                                                                                   |

## Standalone geometry

| Independently authored format | Native measurements                                                                                                                | Evidence                                                                          |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Cylinder SMT                  | Radius 15 mm, height 11 mm, base `(20,-30,5)` mm, volume 7.7754418176350715 cm³, correct topology and native save/reopen.          | [SMT report](../../../re/Fusion/LocalOracle/Brep/ProductionAcceptance.json)       |
| Cylinder SMB                  | The same dimensions and measurements through the native temporary-BRep binary import API, then document ownership and save/reopen. | [SMB report](../../../re/Fusion/LocalOracle/Brep/ProductionBinaryAcceptance.json) |
| Cuboid SMT                    | Dimensions 17×23×31 mm, base `(-7,13,5)` mm, volume 12.121 cm³, six faces, twelve edges and eight vertices, native save/reopen.    | [SMT report](../../../re/Fusion/LocalOracle/Brep/CuboidAcceptance.json)           |
| Cuboid SMB                    | The same measurements through binary import, document ownership and native save/reopen.                                            | [SMB report](../../../re/Fusion/LocalOracle/Brep/CuboidBinaryAcceptance.json)     |

These geometry writers derive their records from analytic dimensions and provenance inputs. Standalone geometry acceptance does not establish a parametric feature timeline.

Six [frustum SMT/SMB artifacts](../../../re/Fusion/LocalOracle/Frustums/NativeAcceptance.json) additionally cover expanding, shrinking and equal-radius solids. Native volume, area, center, bounds, topology and save/reopen all passed. These remain standalone geometry profiles.

Four [complete frustum history replacements](../../../re/Fusion/LocalOracle/TaperedHistory/NativeAcceptance.json) separately passed native load, rollback, restoration, rebuild, height and taper edits, save and reopen. They cover source and fresh geometry frames, a longitudinal parameter scale of 3.125 cm and a five-degree holdout. Their own source Design and other parts are preserved. Independent tapered document synthesis is established separately by [three generated complete files](../../../re/Fusion/LocalOracle/TaperedAuthoring/NativeAcceptance.json). The files have expanding, contracting and zero-angle profiles with fresh materials. The files also cover correct initial geometry/mass/inertia, rollback/rebuild, height and taper edits, and native save/reopen. All three complete archives [read/re-emit byte exactly](../../../re/Fusion/LocalOracle/TaperedAuthoring/TypedReemission.json).

## Remote compatibility and remaining boundaries

PR compatibility run [43229332005](https://github.com/TryUniCAD/Kit/actions/runs/43229332005), on revision `ad3c764fbd778a2f1a2a30a7fc047d7d0fc49c39`, passed all 828 cases in 38.16 seconds. That includes the complete 712-file Design reconstruction set and all five cuboid-history compatibility/rejection cases. A later conical-solid run [43233457278](https://github.com/TryUniCAD/Kit/actions/runs/43233457278) on revision `2fbad758d47c38a69ecbfb9756e5dccf333e5759` passed all 853 cases in 51.84 seconds. The rectangle/material revision ran 868 cases with 864 passing; the four failures identified incorrect helper assumptions about direct material objects and local manager references. After those corrections, revision `9f6753ce885eff64fdcc907361175ff65253fb6d` passed all 885 cases in [run 43237855649](https://github.com/TryUniCAD/Kit/actions/runs/43237855649), including all material-document and new tapered-history cases. Revision `223781e4a066ef5cc3bcedb05cac61ca3868e738` then passed all 897 cases in [run 43239432056](https://github.com/TryUniCAD/Kit/actions/runs/43239432056), including twelve complete tapered-document cases. Revision `d673214fb134e099ddcd7e187fdf640135b99520` passed all 906 cases in 41.46 seconds in [run 43241250257](https://github.com/TryUniCAD/Kit/actions/runs/43241250257), including nine snapshot/configuration cases. Revision `53ad933e3ca32d70985a7d543d66c9766021ae07` passed all 920 cases in 40.53 seconds in [run 43242480290](https://github.com/TryUniCAD/Kit/actions/runs/43242480290), including fourteen constrained rectangle/cuboid cases. General tests run remotely only. Native application acceptance is separately recorded above; a green codec round-trip alone does not establish target-application acceptance.

Full arbitrary Fusion interoperability remains unproven. Open boundaries include arbitrary constraint systems and part feature families beyond the 18 accepted suites. They also include Form cages that the general cage rules refuse, and configured designs. A DWG written entirely by Kit does not open in Fusion. The reason is that Fusion waits on header values and a trusted-file text that Kit does not reproduce. Slanted base views, view edges of fillets, partial arcs and split edges, procedural surface evaluation and 7 unread saved documents remain open too. Unsupported production forms are rejected instead of being presented as semantic conversion. Native merge-group acceptance and current-head configured reviewer approvals are independent PR requirements. No merge or queue enrollment is authorized by this work.

## Complete native snapshot parts

Two [typed cuboid/profile/sketch snapshot replacements](../../../re/Fusion/LocalOracle/PrismSnapshot/NativeAcceptance.json) passed native load, rollback, restoration, rebuild, height edits and save/reopen. The ordinary rectangle changed height 25→37 mm and volume 30→44.4 cm³; the saved authored cuboid changed 37→43 mm and volume 14.467→16.813 cm³. The source-specific archives preserve their own remaining members. That part-level evidence is now complemented by complete native-envelope reconstruction below; it remains distinct from the whole-document proof.

## Rolled-back history state

The complete reconstructed history preserves distinct current/maximum state IDs 3/10 and next entity tag 6. [Native control and reconstructed-document observations match](../../../re/Fusion/LocalOracle/RolledHistory/NativeAcceptance.json) through initial marker 2, rollback to the sketch and restoration. The observations also match through regeneration of three cylinders at the timeline end, a 10→13 mm height edit and native save/reopen. The output retains its own source Design and other members; this is history qualification, not independent synthesis of that three-feature document. [The change entry](../../Changes/Fusion/History/FusionRolledHistoryAcceptance.md) records exact hashes and the migration of the obsolete rejection case to positive reconstruction coverage.

## Complete native archive reconstruction

The ordinary rectangle control and native-saved authored cuboid now pass complete typed document reconstruction, including graphics, material compatibility aliases, snapshots and configuration sidecars. [Preparation](../../../re/Fusion/LocalOracle/NativeDocuments/Preparation.json) records complete output hashes `0203674063f58504d037a51236a1aff9cc3283ed1b8b107cc8307e1e73f10e92` and `49f92bbe4f33fc7c1413ca8a8d433ff3ba948c1822c6513363934425f626ec31`. Both world/mesh pairs reconstruct byte exactly.

[Native acceptance](../../../re/Fusion/LocalOracle/NativeDocuments/NativeAcceptance.json), SHA-256 `f03ceae55edbefc2054edcadee6b9f579066bed3384a4879ac1f0cb01f942cfb`, compares each result against its own original native control. Every observed parameter, timeline/sketch state, topology, geometry, physical property, material/appearance identity and appearance color agrees through open, rollback, rebuild, edit and save/reopen. Steel volume/mass changes 30 cm³/0.2355 kg → 44.4 cm³/0.34854 kg. The generic-material cuboid changes 14.467 cm³/0.014467 kg → 16.813 cm³/0.016813 kg. This qualifies those complete native profiles; it does not imply arbitrary OGS callbacks or all native archives. See [the implementation and boundaries](../../Changes/Fusion/Graphics/FusionNativeGraphics.md).

## Public registry and neutral serialization

Six independently authored profiles passed public registry writing, default strict reading, neutral JSON serialization and public re-emission. Every re-emitted archive was byte-identical to its source, with complete parameters, sketches, feature history, analytic topology and typed materials retained. [Preparation](../../../re/Fusion/LocalOracle/PublicAdapter/Preparation.json) records each input/output hash; [native acceptance](../../../re/Fusion/LocalOracle/PublicAdapter/NativeAcceptance.json), SHA-256 `9a31b0bacc7d59449b3becdc96c77e5b51dccff269b716800ae353f2c601c4a5`, records all six successful Fusion lifecycles.

Fusion verified initial geometry, topology, volume, mass, density, center, bounds and RGBA 51/102/153/255. Height changed 17→21 mm, circle radius 12→14 mm, constrained rectangle/cuboid width 19→22 mm and depth 23→29 mm, and frustum taper +5→−3 degrees. Solid rollback, rebuild, save and reopen succeeded. The [public adapter entry](../../Changes/Fusion/Adapter/FusionPublicAdapter.md) documents the precise constructor and native-state contracts. This evidence does not claim recognition of arbitrary neutral documents or every post-edit native graph.

## Complete multistate history reconstruction

The production journal API reconstructed the Draft and OffsetFaces history members exactly. Then the API independently reversed both active and archived allocation partitions and regenerated every affected reference. [Production preparation](../../../re/Fusion/LocalOracle/JournalStates/ProductionPreparation.json) records all four candidates and their hashes. [Native production acceptance](../../../re/Fusion/LocalOracle/JournalStates/NativeProductionAcceptance.json), SHA-256 `fdee08a175167a2d579905ac7084ecdf6f58cdcd26b4d0a3672c41bd7ef8dd66`, compares each candidate against its own source control.

Every observed parameter, timeline health, topology, volume, area and bounding box agrees through initial load, prior-cylinder rollback and sketch-only rollback. The observations also agree through restoration/rebuild, height edit to 23 mm, final-feature edit and save/reopen. OffsetFaces changes to a 3.5 mm offset and final volume 13.168771005685585 cm³; Draft changes to 7° and final volume 5.377191140021575 cm³. All documents close afterward. Non-history source members remain explicitly supplied by their own original archive. This is semantic history replacement and allocation-independent serialization, not independent authoring of those full three-feature Design graphs.

## Native mesh component reconstruction

Five `.paramesh` components were independently emitted in two source-specific archives; compressed bytes changed while all typed scalar fields remained equal. [Preparation](../../../re/Fusion/LocalOracle/ParaMesh/Preparation.json) binds each component, semantic model and resulting archive hash. [Native acceptance](../../../re/Fusion/LocalOracle/ParaMesh/NativeAcceptance.json), SHA-256 `2a4257fd81b657ca33456754dc6cee62da2e56ca178206edf70c6768d529626a`, compares both reconstructions to original controls through load, feature rollback, rebuild, edit and save/reopen.

The grouped octahedron retains six vertices, eight triangles and volume 1.333333392937979 cm³. Its seven face groups restore to eight on rollback; editing the combine feature to select all eight yields one group. The hollowed tetrahedron starts with 2,745 vertices and 5,482 triangles and restores its four-vertex/four-triangle source on rollback. After a thickness edit 1→1.5 mm, the hollowed tetrahedron has 2,307 vertices, 4,606 triangles and volume 2.4168816259885424 cm³. Every observed geometry/normal/corner/group digest, physical measure, parameter, feature state and timeline state matches. Complete numerical arrays are bound by compressed observation digest `820a8f055753146857692183162f96dd237ac98b2f582c0b0a12a2a2091454a8`. Non-mesh source members remain supplied explicitly; this is complete mesh-component reconstruction, not full independent mesh-document synthesis.

## Complete mesh archives and arbitrary convex polyhedra

[Complete mesh document preparation](../../../re/Fusion/LocalOracle/MeshDocuments/Preparation.json) independently reconstructs every modeled part of the combine/shell controls. [Native acceptance](../../../re/Fusion/LocalOracle/MeshDocuments/NativeAcceptance.json), SHA-256 `9bd545054849e9b72a80e0edd9cbae386b1942fcdac146432fb72876aa2c9113`, matches all observations through load, rollback, rebuild, combine-selection/thickness edits and save/reopen. This supersedes the component-only boundary for these two specific native archives. It does not qualify public neutral mesh projection or arbitrary mesh document synthesis.

[Planar topology acceptance](../../../re/Fusion/LocalOracle/PlanarTopology/NativeAcceptance.json), SHA-256 `9974d4d3abb6305e21d3a843e8bbd19defbad1d4d49830de9b21fa4e95e0976d`, separately accepts four exact/permuted history replacements against two controls and three source-free SMB bodies. The tetrahedron history restores mesh-conversion stages without inventing nonexistent parameters; the triangular pipe accepts a 6→8 mm section edit. Independent tetrahedron and triangular prism volumes are 2.0201666666666673 and 4.5695 cm³. The transformed tetrahedron has volume 3.945638020833335 cm³, centroid `(0.38125,-0.16875,1.46875)` cm and bounds `(-1.775,-0.7,0.5)..(1.1,1.425,4.375)` cm after native save/reopen.

Revision `486ea6828e13ef816ee001155e1261f69e3de10d` passed all 1,087 remote compatibility cases in 77.04 seconds in [run 43253279187](https://github.com/TryUniCAD/Kit/actions/runs/43253279187). The complete mesh-document and planar additions above add further remote cases; their result must be read from the subsequent revision. All test execution remains remote.

## Reference-driven public native projection

[Native public preparation](../../../re/Fusion/LocalOracle/NativePublicAdapter/Preparation.json) now reads the ordinary rectangle and native-saved cuboid through the public registry, serializes the complete neutral model and writes native-state contract version 2. Their actual parameter names and entity identities survive. The resulting archive hashes are exactly `0203674063f58504d037a51236a1aff9cc3283ed1b8b107cc8307e1e73f10e92` and `49f92bbe4f33fc7c1413ca8a8d433ff3ba948c1822c6513363934425f626ec31`, already bound to the complete native acceptance report above. No additional native execution is claimed for identical bytes. Eighteen additional remote file/API-boundary cases cover both sources, semantic rejection and transactional writing.

## General document history and open geometry

[Complete document geometry acceptance](../../../re/Fusion/LocalOracle/DocumentGeometry/NativeAcceptance.json), SHA-256 `58ca80b5234e03ce15b9c7a2127d9491084a25c47529d0a69b698469503d5692`, covers six complete typed archive reconstructions against their originals. The reconstructions are closed/open base features, closed/open faceted conversion, two converted bodies and a triangular pipe. All observations agree through native load, every timeline rollback marker, rebuild and save/reopen. The pipe additionally accepts its section edit from 6 to 8 mm. Open sheets retain their area, topology, vertex coordinates and bounds; volume is undefined in the original native API and is not fabricated.

Revision `8a6122596348933b846bf8f9a2f27dcfb2272cd3` passed 1,168 remote compatibility cases and failed six in [run 43256167270](https://github.com/TryUniCAD/Kit/actions/runs/43256167270). Five failures exposed the missing general history/snapshot routes now implemented and accepted above. The sixth expected the wrong exception type at the public registry metadata rejection boundary; the expectation now matches its existing transactional rejection. These repairs and 26 further archive cases await subsequent remote CI; native acceptance does not substitute for that result.

## Native circular graphics and public projection

[Native acceptance](../../../re/Fusion/LocalOracle/RotationalDocuments/NativeAcceptance.json), SHA-256 `5950746b0d3601bcf3cb7bf798288aa5a894e2d410e875018ab67f0d95a62d1f`, matches three original circle/cylinder/frustum documents against their complete typed reconstructions through every rollback marker, rebuild, parameter edits and save/reopen. The circle changes radius 14→16 mm, all three change `publicHeight` 21→26 mm, and frustum taper changes −3→4°. The edited cylinder/frustum volumes are 11.762122895039681 and 13.634178374871233 cm³. All documents close afterward.

[Public registry preparation](../../../re/Fusion/LocalOracle/NativeRotationalPublic/Preparation.json) independently reads each source, serializes its complete neutral state and writes the same accepted candidate bytes. Their SHA-256 values are `1b2a7c2d57ca750030c75514ccb977c0cf8bb9dcfea7c0018de08716ef161610`, `29b666aa7afc20267e273bbd4d29f98143d3c2157af3ca2e353785724f2e4176` and `fa018c7ec54ae00ebbb0da84312eafb5915a3ce3ed90e57149cf78c8caa39e81`. Byte identity reuses that native acceptance without claiming a second native execution. The qualified public graph remains one unconstrained planar circle with zero or one additive circular extrusion.

## T-spline control surfaces

[Native acceptance](../../../re/Fusion/LocalOracle/TSplineCodec/NativeAcceptance.json), SHA-256 `c6f6973215fbb0f46cc454f2fc998132d988e2f76fc03ec002981e4c8551964d`, has status `accepted` in Fusion 2706.1.17. Zero documents remained open.

| Production operation           | Construction and observed result                                                                                         | Boundary                                   |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------ |
| TSM read and re-emission       | Twelve native plane, box, symmetric box, edited and crease-contrast controls re-emit byte for byte                       | Qualified `#TS0200` profile only           |
| Native lifecycle of re-emitted | Control and re-emission are equal after form import, conversion, control-point edit, save and reopen                     | Form-graph routing is not part of the test |
| Source-free closed cage        | 17 × 23 × 31 mm cage with explicit face, edge and vertex roots equals the native box primitive at every stage within 1e-8 | Closed quad cages only                     |
| Authored solved body           | Initial area 12.710567668877099 cm². Edited area 12.43421957296201 cm² and volume 3.8361736781260087 cm³, kept after reopen | Default and very-high accuracy agree       |

[Root](../../../re/Fusion/LocalOracle/TSplineCodec/RootVariants/Capture.json) and [edge](../../../re/Fusion/LocalOracle/TSplineCodec/EdgeVariants/Capture.json) variant captures show that the root links are orientation state. See the [T-spline codec entry](../../Changes/Fusion/TSpline/FusionTsplineCodec.md).

## Round bodies and trimmed round histories

[Native acceptance](../../../re/Fusion/LocalOracle/RoundBodies/NativeAcceptance.json), SHA-256 `7ce52b6fd762408fd9aa0fe98380ad9cd4e223588c26882ef1e285c0c6025b9f`, has status `accepted` in Fusion 2706.1.17. Zero documents remained open.

| Production operation       | Construction and observed result                                                                                          |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Authored sphere            | Radius 19 mm, volume 28.73091201462985 cm³, area 45.36459791783661 cm², `adsk::core::Sphere`, save and reopen              |
| Authored torus and tilted torus | 31/9 mm, volume 49.56515330227076 cm³, area 110.14478511615724 cm², `adsk::core::Torus`, save and reopen              |
| Native carrier re-emission | Sphere, torus, tilted torus and placed torus `.smb` regenerate byte for byte and equal the native control                  |
| Partial closed pipe        | Every rollback marker, rebuild, `d3` edit to 8 mm, volume 3.46423114478236 → 6.158633146279758 cm³, save and reopen        |
| Composite circular pipe    | Every rollback marker, rebuild, `d3` edit to 6 mm, volume 1.166559470517908 → 2.6247588086652924 cm³, save and reopen      |
| Rule-all-rounds fillets    | 454 records, 359 active, four states, `d7` edit to 0.8 mm, volume 37.96633332328521 → 37.97836761590841 cm³, save and reopen |

Authored round bodies are direct-design bodies. No parametric feature history is synthesized for them. See the [round body entry](../../Changes/Fusion/Geometry/FusionRoundBodies.md).

## Remote compatibility after circular, round and T-spline work

Revision `55aeed29b454d084ac23567f75c7b3602a9e5468` ran the extended archive compatibility job in [run 43288977523](https://github.com/TryUniCAD/Kit/actions/runs/43288977523). It passed 1,256 cases, failed three and had one collection error. The earlier history-dispatch failures from run 43256167270 did not recur.

| Remote failure                         | Cause                                                                                   | Repair                                          |
| -------------------------------------- | --------------------------------------------------------------------------------------- | ----------------------------------------------- |
| Circle scene, extrusion and frustum    | Extruded scenes consume the sketch profile fill mesh, so only the circle has a `RenderMesh` | Expect the mesh only for the circle document |
| History guard, body role               | General dispatch now rejects the corrupted body key in the journal allocator check first | Accept either rejection message               |
| `CheckRotaryBody` collection error     | The `Check*` collection pattern selected a helper function                              | Rename the helper                               |

Steering also rejected two test names over 15 letters and a four-letter variable. These repairs await subsequent remote CI. Native acceptance does not substitute for that result.

## Fusion-saved document coverage

[Native acceptance](../../../re/Fusion/LocalOracle/ReaderCoverage/NativeAcceptance.json), SHA-256 `503fdfc703b07842c25e0295b201ceb9754da6cd5338dfee68e840a4c09bcc43`, has status `accepted` in Fusion 2706.1.17. All 26 cases are `accepted`, and zero documents remained open. Each case compares a Fusion-saved control with its `ReadDocument` and `EmitParsed` re-emission through open, rebuild, rollback, restore, save and reopen. The saved outputs have 52 distinct SHA-256 values. The [preparation report](../../../re/Fusion/LocalOracle/ReaderCoverage/Preparation.json) has SHA-256 `bd80f77e02a096146857ddce9250895d8ffe42035b7098914291b2320100c381`.

The offline census in the [saved document coverage entry](../../Changes/Fusion/Records/FusionSavedDocumentCoverage.md) reads 159 of 159 vendor exports and 1,145 of 1,159 F3D and F3Z files. The 14 unreadable files are three older example files with 48 uncatalogued class versions and 11 Kit research files. See the [data model section](FusionDataModel.md#fusion-saved-document-coverage).

The [read gap change](../../Changes/Fusion/Records/FusionReadGaps.md) swept the 1,709 tracked files and their 1,725 design documents. `ReadDocument` reads 1,704 documents, against 1,690 before. Of these, 1,698 round-trip. `NativeMaterial` passes 1,656 documents, against 1,371 before. Of the 21 unread documents, 5 are Kit containers that Fusion rejected and 2 are cache rewrites that Fusion failed to import. The other unread documents are 4 Form files whose patch words are doubles and 10 bundle members that stop in the graphics cache. This census is offline. It adds no native acceptance run. See the [read gap rules](FusionDataModel.md#read-gap-rules). The [cache and package gaps change](../../Changes/Fusion/Records/FusionCacheGaps.md) fixes the 10 bundle members. `ReadDocument` then reads 1,714 documents, and 1,710 round-trip. `NativeMaterial` passes 1,666. The written graphics members of the 10 fixed documents equal the saved bytes. The 11 unread documents are the Kit containers, cache rewrites and Form files above. The Form patch word rule then reads the four Form interval files, so 1,718 documents read and 1,714 round-trip. The 7 unread documents are Kit containers and cache rewrites that Fusion rejected. This sweep is offline too. See the [cache and package gap rules](FusionDataModel.md#cache-and-package-gap-rules).

## Complex surface geometry

| Report                                                                                                 | SHA-256                                                            | Status     | Observed result                                                                                                  |
| ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------ | ---------- | ---------------------------------------------------------------------------------------------------------------- |
| [First pass](../../../re/Fusion/LocalOracle/ComplexGeometry/NativeAcceptance.json)                     | `6e9a616056ae539b3c6ee6caf22f3f0fc8ad35b6dfa68cec322da9291a55a4e4` | `accepted` | Three authored NURBS bodies, one pole edit, eight snapshots and six histories accepted                           |
| [Bounds](../../../re/Fusion/LocalOracle/ComplexGeometry/Bounds/NativeAcceptance.json)                  | `d44670ba057d49a737a3b2a53135367bcf84f8d4c0b0e7e1e38b9fedf16d3af8` | `accepted` | Nine re-emitted corpus histories equal their controls at every stage within 1e-8                                 |
| [Second pass subtypes](../../../re/Fusion/LocalOracle/ComplexGeometry/SecondPass/Runs/Subtypes.json)   | `b7e5f02c83cbf4b7a6d68b30c951d14f1ad5deb8e4ad4332df9f9bef9937a5dc` | `failed`   | Seven of nine subtype edits reflected. `StitchHint` failed at export, and `TolerantFormRefine` was not reflected |
| [Second pass diagnosis](../../../re/Fusion/LocalOracle/ComplexGeometry/SecondPass/Runs/Diagnose.json)  | `70c0540137ae0d490a3acf9ad2d5e34cb118829644d48a885c4d447c17ba1cd5` | `failed`   | The stitch hint survived export. The refined pcurve was reported with its inserted knot at full multiplicity     |
| [Second pass remainder](../../../re/Fusion/LocalOracle/ComplexGeometry/SecondPass/Runs/Remaining.json) | `04331a7d4b3f497dea32f9b2af296a6799e8a38d7f0430abb9ff94ba35af72fd` | `accepted` | Two `cyl_spl_sur` refinements reflected and five authored bodies accepted                                        |
| [Interrupted run](../../../re/Fusion/LocalOracle/ComplexGeometry/SecondPass/Runs/Crashed.json)         | `9ac76cd9316e73809c57a57653c94aa1eb66edaaaa6e57a8c68eec2f75b9de43` | None       | Fusion exited during the run, so the report has no final status or closing document count                        |

The first pass and the second pass remainder started and ended with zero open documents. Their authored and edited bodies measured as follows.

| Case               | Faces, edges, vertices | Area (cm²)         | Volume (cm³)       |
| ------------------ | ---------------------- | ------------------ | ------------------ |
| `AuthoredPatch`    | 1, 4, 4                | 7.366308780834109  | None               |
| `AuthoredRational` | 1, 4, 4                | 11.361644058057117 | None               |
| `AuthoredPillow`   | 6, 12, 8               | 25.0885564915581   | 10.501319359009246 |
| `EditedPatch`      | 1, 4, 4                | 6.782947284786066  | None               |
| `HoledPatch`       | 1, 8, 8                | 6.809012806990166  | None               |
| `CollapsedPatch`   | 1, 3, 3                | 4.429902308098689  | None               |
| `CappedTube`       | 3, 3, 2                | 19.80532565024299  | 6.96792035947401   |
| `DomedCylinder`    | 3, 3, 3                | 18.93842138073986  | 6.850844430134102  |
| `NurbsTorus`       | 1, 2, 1                | 39.47841761360506  | 9.869604403401263  |

The first four rows come from the first pass and the last five from the second pass remainder. The `RuleFillet` history had a control self-drift of 5.061870858686882e-05 and a re-emitted drift of 4.2369471785593015e-05. Fusion's own rebuilds of that rule fillet differ, as the [rule fillet gotcha](../../Gotchas/Conversion/Fusion/Geometry/RuleFilletRebuildDrift.md) describes.

The [first-pass preparation](../../../re/Fusion/LocalOracle/ComplexGeometry/Preparation.json) has SHA-256 `5a5de5583d81de989688909dbc08870cca8b9ac74542160f0aa009140ab8cad9`. The [second-pass preparation](../../../re/Fusion/LocalOracle/ComplexGeometry/SecondPass/Preparation.json) has `74cd0b937bad6350e28d2e49bd36b79f52988732179d193501b93a35a836e570`, and the [analysis](../../../re/Fusion/LocalOracle/ComplexGeometry/SecondPass/Analysis.json) has `4a311525eb1a710d6e8bb83c0856e03bbc5186847af1124475992020d570d52d`. Procedural surfaces are read and re-emitted but not evaluated. See the [data model section](FusionDataModel.md#complex-surface-geometry-and-explicit-nurbs-bodies).

## Form documents

| Report                                                                                                            | SHA-256                                                            | Cases             | Observed result                                                                                                      |
| ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | ----------------- | -------------------------------------------------------------------------------------------------------------------- |
| [Re-emitted controls](../../../re/Fusion/LocalOracle/FormDocuments/Acceptance/NativeAcceptance.json)              | `b018171b82ad933a65611f5e56b54f0b48b6660bae06bc936267544f876fa552` | 4 of 4 accepted   | Plane, creased plane, box and symmetric box equal their native controls through edit, save and reopen                |
| [Grid conversion](../../../re/Fusion/LocalOracle/FormDocuments/Grid/NativeAcceptance.json)                        | `ba7536f4cfed4b6cc60a50aed672d62bbcb96168571c3050527f4fd024266769` | 2 of 2 accepted   | Affine and warped plane grids equal Fusion's conversion within 1e-8 cm                                               |
| [Source-free bodies](../../../re/Fusion/LocalOracle/FormDocuments/Sourceless/NativeAcceptance.json)               | `acc43da40fa16f28a3441f719c43cf6608b0b56081e1606495e2a986fd646ee4` | 9 of 9 accepted   | `EmitFormDoc` with typed bodies, 175 comparisons with largest deviation 2.6645352591003757e-15                       |
| [Cage documents](../../../re/Fusion/LocalOracle/FormDocuments/CageDocuments/NativeAcceptance.json)                | `76d2a6a35c902f6776270584b1db9363b0f6ecb9c4c2e85c3e68e26822a7ad8f` | 14 of 14 accepted | `EmitFormDoc` with `ConvertForm` bodies within 1e-8 cm and zero recorded problems                                    |
| [Stencil swaps](../../../re/Fusion/LocalOracle/FormDocuments/StencilAccept/NativeAcceptance.json)                 | `f7455953a99fb482fa03054aa73e165a40cbf0d683c87a8139f6dae84e25a95d` | 8 of 8 accepted   | `SwapFormCage` into native documents within 1e-8 cm                                                                  |
| [General conversion](../../../re/Fusion/LocalOracle/FormDocuments/General/Accept/GeneralAcceptance.json)          | `4a8b000974e0c6007c7db4849e27954650fbdced4d00536088a60a4ce6b58a83` | 30 of 30 accepted | `EmitFormDoc` with `ConvertForm` from the general rules: 8 old layouts, 9 probe and 13 held-out cages within 1e-8 cm |
| [General stencil swaps](../../../re/Fusion/LocalOracle/FormDocuments/StencilAccept/General/NativeAcceptance.json) | `d9efa56868d16dd066c29111803fec97c59f554f5147bec061ce5bdd92431fdf` | 7 of 7 accepted   | `SwapFormCage` with the general rules within 1e-8 cm; Kit refuses the fresh creased plane swap                       |

Every Form report started and ended with zero open documents in Fusion 2706.1.17. The re-emitted controls report has top-level status `completed`, and each of its four cases has status `accepted`. Their edited areas are 3.75882224444742, 3.7597048123427688, 23.229292504382165 and 22.896262895240067 cm². The two boxes have edited volumes 9.339333654763482 and 9.137857029717933 cm³. The grid cases changed area from 3.981294020792737 to 3.9230459543150173 cm² and from 4.005512887961321 to 3.9455217633195576 cm².

Cage conversion follows general rules computed from the cage topology, with no per-layout table. It covers closed and creased quad cages with extraordinary points of valence 3 to 8. Cage conversion also covers crease ends, darts next to an extraordinary point or crease, weighted grips and one whole-number knot interval. Face line ties, two creases at one extraordinary point, uncovered darts, mixed or fractional intervals in capped cages and folded cages are rejected. See the [data model section](FusionDataModel.md#form-documents).

## Independently authored part features

All sixteen suites have status `accepted` in Fusion 2706.1.17, with zero open documents before and after each run. Each opened Kit documents without a recompute and compared them with native API controls built in the same session. It then walked every rollback marker, ran `computeAll`, applied the driving edits, exported, reopened and recomputed again. The whole set was re-run after the feature defaults were reduced to schema type defaults.

| Suite        | Report                                                                                                      | SHA-256                                                            | Cases |
| ------------ | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | ----- |
| Corners      | [Native report](../../../re/Fusion/LocalOracle/FeatureAuthoring/Authored/NativeAcceptance.json)             | `66793b7021e8228d4b3de1ab2e7cffbd3a6a0518b596e9baeab7c4e7472e40eb` | 5     |
| Extrusions   | [Native report](../../../re/Fusion/LocalOracle/FeatureAuthoring/Authored/NativeAcceptanceExtrudes.json)     | `73119817b8b2bea2ad197c14932ddeee003474f311c979bf6badceb72361763b` | 15    |
| Holes        | [Native report](../../../re/Fusion/LocalOracle/FeatureAuthoring/Authored/NativeAcceptanceHoles.json)        | `ae2d56cc65c601a0bf2ea5dbec26a86963dd6a365662a1d3bf1f7a1a45a78d07` | 4     |
| Patterns     | [Native report](../../../re/Fusion/LocalOracle/FeatureAuthoring/Authored/NativeAcceptancePatterns.json)     | `348edf0dfda685b68f836e48fc2681d50f1d9166fbba20680fa876502b186528` | 5     |
| Multi        | [Native report](../../../re/Fusion/LocalOracle/FeatureAuthoring/Authored/NativeAcceptanceMulti.json)        | `ea1d2499e13e916087e572229c063f972b22efb45362ec6674b2ea1ff605a2a5` | 2     |
| Edges        | [Native report](../../../re/Fusion/LocalOracle/FeatureAuthoring/Authored/NativeAcceptanceEdges.json)        | `34ad556949fe13a72128616c7ff6893fffb1f1e00aeb37ea5cef1e8ceb568e60` | 5     |
| Construction | [Native report](../../../re/Fusion/LocalOracle/FeatureAuthoring/Authored/NativeAcceptanceConstruction.json) | `4dc1ffe3dfffc78817927649fc76eb05d0794cb2988d22b5dd346c6bdd33e8ac` | 2     |
| Revolves     | [Native report](../../../re/Fusion/LocalOracle/FeatureAuthoring/Authored/NativeAcceptanceRevolves.json)     | `a1bd67d0d59a2646bd4cfb4f800b85fe2b452b36806ca7c622fddeff5d22e883` | 4     |
| Countersinks | [Native report](../../../re/Fusion/LocalOracle/FeatureAuthoring/Authored/NativeAcceptanceCountersinks.json) | `4dce6033dffc3aa10e81155f43d8776a2885f77e9f4c9e1859af8928e198f3e7` | 2     |
| Shells       | [Native report](../../../re/Fusion/LocalOracle/FeatureAuthoring/Authored/NativeAcceptanceShells.json)       | `4b3ad4110e8868d204a723faf45fed1db989f674701a120588ade2caa2e97097` | 2     |
| Moves        | [Native report](../../../re/Fusion/LocalOracle/FeatureAuthoring/Authored/NativeAcceptanceMoves.json)        | `082476dd2990dce0771ec62faba293dcd3d09b9ad8b61d30cf17bdec7ae8be13` | 2     |
| Offsets      | [Native report](../../../re/Fusion/LocalOracle/FeatureAuthoring/Authored/NativeAcceptanceOffsets.json)      | `334b720d512ba477b5a3d324ea52bab515dea1be2c29df0ba7ce44ff63deb30a` | 4     |
| Drafts       | [Native report](../../../re/Fusion/LocalOracle/FeatureAuthoring/Authored/NativeAcceptanceDrafts.json)       | `1cdad708a701c172160b3e89fc39917e8d5c0004df72092c13b20fda42ad93f4` | 3     |
| Bodies       | [Native report](../../../re/Fusion/LocalOracle/FeatureAuthoring/Authored/NativeAcceptanceBodies.json)       | `69eeb678d6f78001dbaa0e42a161c279a5ec5f7335f21e78565e27653aad7639` | 11    |
| Lofts        | [Native report](../../../re/Fusion/LocalOracle/FeatureAuthoring/Authored/NativeAcceptanceLofts.json)        | `c5d78aaf08bcd7be99f6ead2205e930bf6e3ef61b55b5d4516ed4e43dddf4e9d` | 3     |
| Sweeps       | [Native report](../../../re/Fusion/LocalOracle/FeatureAuthoring/Authored/NativeAcceptanceSweeps.json)       | `1f033a661fac2fe2c696c9f692377185310007dc519f0a2cc2f440eb4514b85a` | 4     |

The 73 cases matched their controls at open, at every marker, after recompute and after the edits. They also matched after reopen, with parameters preserved, and after the final recompute. `MultiPocketPart` has 19 faces, 43 edges and 30 vertices and changed from 22.62232750 to 22.59228325 cm³ across 10 marker positions. `MultiDiscPart` changed from 13.38318470 to 12.85539714 cm³. The fillet case changed from 23.96137167 to 23.93132741 cm³, the shell case from 7.152 to 10.128 cm³ and `ConstructionPart` from 23.39588499 to 30.54523896 cm³. With the paste and edge round cases added, the [authored file manifest](../../../re/Fusion/LocalOracle/FeatureAuthoring/Authored/Manifest.json) has SHA-256 `868e8b2e4b4ce6377410817df6e15bb8043ff63aaa648d3d507d539bb9d60517`. Every saved `vendor_*.f3d` was scrubbed, and each report records the scrubbed digest.

The paste suite has status `accepted` in Fusion 2706.1.17, with zero open documents before and after the run. Its [native report](../../../re/Fusion/LocalOracle/FeatureAuthoring/Authored/NativeAcceptancePastes.json) has SHA-256 `1816365683f7b9231c61d2c307c1999c3cd30942460f6d9f347a35ff8035fb42`. All 6 cases matched their controls at open, at every marker, after recompute and after the edits. The cases also matched their controls after reopen with parameters preserved and after the final recompute. [Body copy and paste](../../Changes/Fusion/Features/FusionBodyPaste.md) lists the cases.

The edge round suite has status `accepted` in Fusion 2706.1.17, with zero open documents before and after the run. Its [native report](../../../re/Fusion/LocalOracle/FeatureAuthoring/Authored/NativeAcceptanceRounds.json) has SHA-256 `a0856fc3368f36b4ec4fc43feba3b63fbacc1b9c43174131c25b0b4ccb347174`. All 30 cases matched their controls at open, at every marker, after recompute and after the edits. The cases also matched their controls after reopen with parameters preserved and after the final recompute. The 30 Fusion saves were scrubbed, and the report records their scrubbed digests. [Edge rounds](../../Changes/Fusion/Features/FusionEdgeRounds.md) lists the cases.

See the [data model section](FusionDataModel.md#independently-authored-part-features) for the authored families and their limits.

## External references and assemblies

| Report                                                                                | SHA-256                                                            | Observed result                                                                                                     |
| ------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| [Link evidence](../../../re/Fusion/LocalOracle/LinksConfigs/LinkEvidence.json)        | `01d61a8915733fe8ae2213abe13ab88d2c0cd8f5fb297849fad86752f538e45b` | 15 sanitized native controls, 14 replayed through `ReadDocument` and `EmitParsed`. Configuration controls `blocked` |
| [Link acceptance](../../../re/Fusion/LocalOracle/LinksConfigs/LinkAcceptance.json)    | `8d806ab1f7c11f8d18b8f9f32c893250bbdbdb6ed73123f80f5884b8ab7cfe58` | Uploaded Kit outputs opened with resolved references, updated and reopened at version 2                             |
| [Assembly acceptance](../../../re/Fusion/LocalOracle/LinksConfigs/AsmAcceptance.json) | `20eb2c161764e09ddea429bf79125fcb36c0fe7395b5f3a0ace18b46319c4ea6` | A root written by `EmitAssembly` opened, updated, saved as version 2 and reopened                                   |

Link acceptance run `Accept1` failed, because Fusion refuses a local import with external references: `New design cannot be created from a local file containing external references`. The `Accept2_upload` step recorded only status `started`. Run `Accept2` then completed three cases: a native root and the Kit outputs `KitLinkReplayR5` and `KitLinkMovedR1`. Each had a largest transform error of 0.0 and zero unhealthy items, and the reference update moved Part A to version 2. Run `Accept2_saves` completed both saved cases, and each reopened at version 2.

The assembly acceptance has status `completed` and started and ended with zero open documents. The root moved from version 1 to version 2. Part A changed from 5.0 mm to 8 mm through `updateAllReferences`, so its body height changed from 0.5 to 0.8 cm. Part B stayed 1.2 cm. At all four stages the occurrence paths were equal and the largest transform error was 0.0 for `KitAsmPartA:1`, `KitAsmSub:1` and `KitAsmSub:1+KitAsmPartB:1`. Joint `Rigid 1` had health 0, and the four timeline items had no unhealthy item. Kit read all three Fusion exports of the saved root, each with two links and a 17,946-byte Design stream.

Native probe `A` has status `failed` with a script `TypeError` on an unhashable `FusionDocument`, and it left two documents open. Its export was still recorded. Probes `B` and `Sub` completed. Configured designs could not be created: `Design.createConfiguredDesign` raised `Cannot create configuration top table as the user is restricted.` The plain-part export `C0_plain.f3d` has 48,973 bytes. See the [data model section](FusionDataModel.md#external-references-assemblies-and-configurations).

## Drawing documents

The [drawing acceptance report](../../../re/Fusion/Reconstruction/Drawings/NativeAcceptance.json), SHA-256 `41f06474033b311871996f7b076f5a93094fd69c3379e47f3aba52d39ba2e039`, records the first-pass variants below and the second-pass authoring variants in Fusion 2706.1.17. The historical bundle and the modern A1 control re-emit byte for byte. The report has no single status. Its status table records byte-exact round trip and typed DWG re-emission of the A0, A1, A2 and historical DWGs as `passed`. The table also records the open of a Kit-built F2D and the view update on the Kit-emitted A1 control as `passed`. It records the open of a Kit-authored DWG as `failed`.

| Variant          | Views | Dimensions | Result                                                |
| ---------------- | ----- | ---------- | ----------------------------------------------------- |
| `P0Control`      | 3     | 1          | Opened                                                |
| `H0Historical`   | 1     | 0          | Opened                                                |
| `M1Reemitted`    | 3     | 1          | Opened with the same measurements as `P0Control`      |
| `P4ViewsControl` | 3     | 0          | Opened                                                |
| `P5ReverseSwap`  | 3     | 1          | Opened with the dimension of its DWG                  |
| `P2NoDwg`        | None  | None       | `Cannot find the specified drawing file.` dialog      |
| `P3SwappedDwg`   | None  | None       | No drawing engine session header within 207 seconds   |
| `M2Reemitted`    | None  | None       | Uploads were read-only, so the edit was not attempted |

The edit run has status `failed`, because it timed out waiting for the drawing cloud save. Before that timeout it recorded a design volume change from 7.497345175425612 to 11.497345175425611 cm³. The reference moved from version 1, out of date, to version 2, not out of date. The base view x range moved from 100.47–260.47 mm to 60.47–300.47 mm. Both saved-edit attempts failed, so save and reopen after a model edit are not verified. Kit decodes every DWG object into typed values and builds F2D packages and drawing-root bundles. `N2AuthoredF2d`, a Kit-built F2D around a Fusion-saved DWG, opened in 4.3 s with 3 views and 1 dimension. No DWG that Kit authors has opened. Bisection traced the stall to two checks. The first check concerns four header values that depend on the header variables through a check no unkeyed checksum reproduces. The second check concerns Autodesk's trusted-file text, which Kit does not write because the text claims an Autodesk save. The [header tail gotcha](../../Gotchas/Conversion/Fusion/Drawing/FusionDrawingHeaderTail.md) and the [authored shell gotcha](../../Gotchas/Conversion/Fusion/Drawing/FusionDrawingAuthoredShell.md) record these checks. See the [data model section](FusionDataModel.md#drawing-documents).

### Drawing rule grafts

Kit-authored DWGs do not open, so the drawing rules are checked by graft in Fusion 2706.1.17.
An object graft keeps the A3 control's header and swaps in the objects a rule generates.
A container graft keeps the control's Fusion-saved DWG and re-emits the F2D with one rule applied.
Each graft below opened with views of 5, 4 and 4 curves, 1 dimension and a 420 × 297 mm sheet.

| Graft                | Replaced                                                                     | Report |
| -------------------- | ---------------------------------------------------------------------------- | ------ |
| `L1Lean` to `L4Core` | Removed save history, Fusion dictionary items and unused standard objects    | [G2](../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundG2.json) |
| `T1Tables`           | Kit's 8 layers, 6 line types, 2 text styles, dimension style, active viewport | [T3](../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundT3.json) |
| `T2Standard`         | Also materials, multiline style, view standard, layout plot fields           | [T3](../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundT3.json) |
| `T3Sheet`            | Also Kit's border block, title block, inserts and 15 title attributes        | [T4](../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundT4.json) |
| `C1NoTemplateThumbs` | No template sheet thumbnails                                                 | [T4](../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundT4.json) |
| `C2NeutralCycle`     | Kit's neutral component colour                                               | [T4](../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundT4.json) |
| `C3Renumbered`       | The control's design records renumbered without gaps                         | [T5](../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundT5.json) |
| `C4KitMembers`       | Every member except the DWG built by Kit, with Kit's record numbering       | [T5](../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundT5.json) |
| `D1Vertical` to `D4Diameter` | Kit's dimension of each kind and its block, in place of the plain control dimension | [T6](../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundT6.json) |
| `D5Short`, `D6OnLine` | A short aligned dimension with arrows and text outside, with and without extension lines | [T8](../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundT8.json) |
| `D7Split`, `D8Flank` | A short aligned dimension with only its text outside, and a short vertical one with only its arrows outside | [T9](../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundT9.json) |
| `S1AsmeB` to `S3AsmeA` | `T3Sheet` on ASME B, D and A paper in millimetres with Kit's ASME border   | [T7](../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundT7.json) |
| `V1LeftBelow` to `V3AboveBelow` | Kit's left and below, right and back, or above and below projected views | [T10](../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundT10.json) |
| `V4KitModel` to `V6RightBackKitModel` | Also Kit's model space places for the views | [T10](../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundT10.json) |
| `V7NoEdges` to `V9AboveBelowNoCurves` | Views with no stored edges, as Kit wrote them then, then also no curves | [T10](../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundT10.json) |
The ASME grafts opened with the same views and dimension on sheets of 431.8 × 279.4, 863.6 × 558.8 and 215.9 × 279.4 mm.
Fusion took each sheet size from the DWG layout.

All nine view grafts opened with one dimension on a 420 × 297 mm sheet.
Views with stored edges showed 5, 4 and 4 curves; views without them showed none until a scale change made Fusion find the edges.

An empty DWG member gave the dialog `Drawing file is not valid.`, so Fusion does not rebuild a missing DWG.

### Stored view edge rounds

The [T16 report](../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundT16.json) records rounds E1 and T16 in Fusion 2706.1.17.
Each graft removed every stored edge from the A3 control's views.
Each run opened the graft, read the curves, halved the base scale and restored it, read again and exported a DWG.
The export keeps the edge lists Fusion computed in that update.

| Graft | Views | Curves on open | Curves after the update | Fusion's exported edges |
| ----- | ----- | -------------- | ----------------------- | ----------------------- |
| `E1HiddenA` | Right and above, hidden style, no edges | 0, 0, 0 | 5, 6, 6 | The training set for the hidden style |
| `T16VisibleA`, `T16HiddenA` | Right and above, Kit's edges | 5, 4, 4 and 5, 6, 6 | The same, in the same boxes | Equal to Kit's |
| `T16VisibleLeftBelow`, `T16HiddenLeftBelow` | Left and below, held out | 5, 4, 4 and 5, 6, 6 | The same, in the same boxes | Equal to Kit's |
| `T16VisibleRightBack`, `T16HiddenRightBack` | Right and back, held out | 5, 4, 5 and 5, 6, 5 | The same, in the same boxes | Equal to Kit's |
| `T16VisibleAboveBelow`, `T16HiddenAboveBelow` | Above and below, held out | 5, 4, 4 and 5, 6, 6 | The same, in the same boxes | Equal to Kit's |

In all 24 T16 views, Fusion's exported rows and drawn entities equal Kit's, apart from handles.
The layout A boxes equal those Fusion drew in E1 after its own update.
Kit's views of BoxA, an unrelated Fusion-saved design, equal its stored rows in both views.
That check ran offline, because no other Fusion-saved drawing has a single body seen along an axis.
Fillets, part arcs and partly hidden edges have no Fusion evidence, and Kit raises for them.

## Fixture privacy scrub

Fusion-saved fixtures carried account data in nested protein assets. The [scrub ledger](../../../re/Fusion/LocalOracle/ScrubLedger.json), SHA-256 `1397150b5a27b2b768e0623b3ffcb69ff855642591fc6325c0d4cccd401ec1af`, lists 354 rewritten archives and one captured reflection archive. There are 237 fixtures under `re/Fusion/LocalOracle` and 117 study saves under `re/Fusion/Study`. Each archive records its Fusion-saved and committed SHA-256, and all 354 committed digests match the checked-in files. Fusion saved 28 part feature controls again during later acceptance runs. Those saves held no account residue, so the ledger no longer lists them. The rewrite uses same-length placeholders, and Kit readers do not decode the replaced bytes. See the [fixture scrub entry](../../Changes/Fusion/Privacy/FusionFixtureScrub.md), the [scrub rules entry](../../Changes/Fusion/Privacy/FusionScrubRules.md), the [study scrub entry](../../Changes/Fusion/Privacy/FusionStudyScrub.md) and the [heap residue gotcha](../../Gotchas/Conversion/Fusion/Records/FusionProteinHeapResidue.md).
