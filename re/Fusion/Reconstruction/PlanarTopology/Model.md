# Shape-independent planar topology and transform model

The new production family extends complete typed journal entities with an explicit transform and derives a convex closed-polyhedron view from topology rather than fixed cylinder/cuboid ordinals. It separately constructs source-free polyhedra from immutable point coordinates and outward face-index loops. There is no raw record retention.

## Controls and identities

`ControlSummary.json` binds complete named-field geometry in `Controls.json.xz` to two source histories:

- `meshconverts-4b42d39fb1d5/faceted_closed.f3d`, member `BREP.284868a5-5b8b-41da-871b-2d80983ca7d7.smbh`, 7,383 bytes, SHA-256 `68e30de4207ea13fc4f3aa505a14772503caee32f9a6f1c41dc4ccf2946b51c9`: 54 current entities, body tag 30, next tag 31, current/max state 4, initial state 2. The four vertices are `(0,0,0)`, `(20,0,0)`, `(0,30,0)`, `(0,0,40)` mm. Closed topology has four faces, six edges and four vertices; signed volume is 4 cm³.
- `pipemodes-87cfa7d8d82b/triangular.f3d`, member `BREP.038e0fee-eddd-4a0d-ad88-3cc6cc1bcbbc.smbh`, 9,768 bytes, SHA-256 `26ebfcf743b59b8b1284bdde4b67eb253e7c41d7ce34f998d6d558893235d175`: 74 current entities, body tag 0, next tag 1, current/max state 3, initial state 2. Closed topology has five faces, nine edges and six vertices. The triangular section spans 6 mm vertically, and the path runs 60 mm along X; volume is 1.2470765814495919 cm³.

`DesignStates.json.xz` fully decodes 275 and 319 source Design records and selects the actual feature/history/parameter joins. The tetrahedron source joins `DcParaMeshToBREPMetaType` entity 268 to states `2→4` and contains zero model parameters. The pipe joins `DcPipeFeatureMetaType` entity 236 to `2→3`. `ParameterMetaType` entity 250 is internal `SectionSize`, user name `d3`, expression `6 mm`, value 0.6000000000000001 cm; its numeric binding is entity 251. The `AlongDistance` and `AgainstDistance` parameters are dimensionless fractions, so editing them as lengths would be incorrect.

## Geometry interpretation

The body owns one lump, which owns one shell, which owns a face chain. Each qualified face owns exactly one loop. Loop coedges have reciprocal next/prior links and exactly one opposite partner on the same edge. Coedge sense selects the edge start or end vertex as the boundary start. Edge sense separately reverses the carrier parameter used to evaluate those endpoints.

All current controls use forward planar faces. The view nevertheless respects the explicit face sense when comparing outward polygon winding with the plane normal. Face polygons are strictly convex, planar and single-loop; every body point must lie on or inside each outward face plane. Every edge has two opposite uses and the closed shell satisfies `V−E+F=2`. Signed tetrahedral integration gives volume. This is a convex closed-shell qualification, not acceptance of all planar bodies.

`CreatePolyBody` independently allocates the body/lump/shell, face and loop arrays, paired coedges, unique undirected edges, vertex/point pairs, planar surfaces and bounded straight carriers. Endpoint parameters are `0..edge_length_cm`, with a unit direction from the lower indexed vertex to the higher indexed vertex. Coedge sense and vertex owner indices are derived from those choices. All bytes, including a complete two-state insertion journal, are derived from this semantic topology.

## Transform model

`TransformEvidence.json` records the corpus decode. A transform record holds the entity base, three matrix vectors, translation, overall scale, then three flags. The mapping is `world = scale * (x*columnX + y*columnY + z*columnZ) + translationCm`.

The sampled corpus's 290 records across 208 unique blobs are all identity transforms. The nonidentity acceptance candidate below is therefore the evidence for the mapping. Its accepted, saved and reopened volume, centroid and bounds match the column convention and an unscaled translation.

An earlier version also cited static inspection of installed Fusion libraries. That material was removed. The flag names rotation, reflection and shear came from it. They are not confirmed by a black-box experiment. Preserve the three flags independently.

The source-free tetrahedron uses intercepts 17, 23 and 31 mm. Its transformed variant uses columns `(0,1,0)`, `(-1,0,0)`, `(0,0,1)`, scale 1.25 and translation `(1.1,-0.7,0.5)` cm. Expected centroid is `(0.38125,-0.16875,1.46875)` cm and expected bounds are `(-1.775,-0.7,0.5)..(1.1,1.425,4.375)` cm. The separate triangular prism uses a right-triangle base with legs 19 and 13 mm and height 37 mm.

## Native boundary

`PrepareProduction.py` prepares exact and independently permuted source-history candidates, preserving each source's own non-history members. The same helper independently constructs three standalone SMB bodies from the declared dimensions without reading any archive for those outputs. `AcceptPlanarTopology.py` is a parent-run native driver: all rollback markers, restore/rebuild, the pipe's `d3` edit 6→8 mm, save/reopen, and independent geometry/centroid/bounds checks. It records the tetrahedron's lack of native model parameters rather than inventing a parametric edit.

[NativeAcceptance.json](../../LocalOracle/PlanarTopology/NativeAcceptance.json), SHA-256 `9974d4d3abb6305e21d3a843e8bbd19defbad1d4d49830de9b21fa4e95e0976d`, accepted both source controls and four exact/permuted history candidates through all rollback markers, restoration, rebuild, pipe section 6→8 mm, save and reopen. It also accepted all three source-free standalone SMB bodies, including persisted/reopened topology, volume, centroid and bounds for the nonidentity transform. Zero documents remained open. [ProductionPreparation.json](../../LocalOracle/PlanarTopology/ProductionPreparation.json), SHA-256 `9f067b8d51ce6023bad780f8339bb89823c02fe8d06f62f22cb28734c3ddd855`, binds the generated inputs. Standalone payload hashes are tetrahedron `b4e27899ef807d6793889e276023ac0e5a4d54044202b903ed6c81b95e1d6f72`, triangular prism `1764ed97ff80ce7cfd2daf929d591a834f73f4b3024b4869d8092f78c8547029`, and placed tetrahedron `1be381d5a93a3b0ccc1190b0a92e17cb63af22e81172862a9ca98eb35383b5f0`. Complete full-document reemission remains a separate qualification.

## Attribution

The transform field layout was compared with the locally pinned cadmpeg specification, `docs/formats/asm.md`, commit `de2726870ff728352163f601ab4e60bbd54fbade` (specification CC-BY-4.0; implementation Apache-2.0). The mapping above is corroborated by the native acceptance of the nonidentity transform. No raw-payload retention or external implementation code was adopted.
