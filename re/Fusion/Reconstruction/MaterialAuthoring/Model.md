# Independently authored material model

## Causal evidence

The native mass probe in `../../LocalOracle/RectangleAuthoring/MassProbe.json` opens both a Kit cylinder and cuboid with valid geometry but zero density, mass, inertia, and centre of mass. Both `body.material` getters fail on `!materialId.empty()`. Native assignment of a physical material changes those properties immediately while leaving geometry unchanged. The control material's density is 7850 kg/m³. The cuboid's volume is 12.121 cm³, mass becomes 0.09514985 kg, and centre becomes (0.85, 1.15, 1.55) cm.

`../RectangleAuthoring/MassFields.json` decodes the pre-assignment and saved post-assignment graph. The geometric cache already contains the correct centre. Body and component mass-property overrides are all -1 before and after assignment. The component's default material remains empty after the successful assignment. The required delta is a body material assignment, manager references, and a material package, not a geometric-cache change.

## Identity graph

Each authored solid receives twelve fresh UUIDs: package, asset container, library, four instances, four definitions, and package part name. The library identity is explicit local provenance; no built-in Autodesk library or material identity is borrowed.

| Graph field | Authored value |
| --- | --- |
| `ProteinAssetManager.partName` | `ProteinAsset.<fresh UUID>.protein` |
| Manager physical references/counts | Physical instance UUID / 1 |
| Manager visual references/counts | Appearance instance UUID / 1 |
| `Body.physicalMaterial.ProteinAssetManager` | Local manager entity reference |
| `Body.physicalMaterial.assetReference` | Physical instance UUID |
| `Body.physicalMaterial.proteinMaterialID` | Physical definition UUID |
| `Body.physicalMaterial.libraryID` | Fresh library UUID |
| Body visual fields | Same mapping for appearance identity |
| `VisualMaterialValue.UseCustomizedColor` | False, allowing the package appearance to supply color |
| Material instance `AssetLibID` | Fresh library UUID |
| Physical `physmat_aspects` | Enabled structural, thermal, and appearance instance references |
| Definition `VersionGUID` | That asset's fresh definition UUID |
| Definition `BaseSchema` | Declared concrete schema name |
| Definition `UIName` | User material name plus the aspect role where applicable |

The new package uses one appearance directly for both the physical aspect and the body appearance. The native assignment control had a separate customized-color appearance plus a legacy conversion pair; those extra instances are not copied or assumed necessary. Native validation must qualify the reduced, directly linked arrangement.

## Semantic values

`MaterialSpec` supplies a name, density in kg/m³, and four RGBA channels. Its generic default density is 1000 kg/m³. All other instance values come from the registered property declarations: `val`, `valR/G/B/A`, and `ChoiceValue` mappings. Empty multiple-string defaults become empty tuples. Reference defaults have absent connections except the explicitly constructed physical aspects.

The writer emits four concrete assets using nine schema declarations. The declaration JSON contains tag names, attribute pairs, and child nodes only. No instance, definition, binary record, source identity, or package envelope is copied. `PromoteSchemas.py` extracts only these declarations and records the source digest in the research-only provenance artifact.

The native unit mapping is established by `ProteinInstances/DecodeInstances.py`, matching each serialized unit code to its schema unit declaration in the assigned material control:

| Declared unit | Code |
| --- | ---: |
| JoulePerGramCelsius | 286721 |
| KilogramPerCubicMeter | 69633 |
| Kilopascal | 135176 |
| MicrometerPerMeterCelsius | 274435 |
| NanogramPerPascalSecondSquareMeter | 290817 |
| OhmMeter | 294913 |
| Unitless | 4097 |
| WattPerMeterKelvin | 282625 |

The unit-bearing float grammar is signed i32 code followed immediately by f64 magnitude. Existing native package-rewrite acceptance established that changing code-69633 density values changes the native material density. This independent authoring step still requires native acceptance of its fresh identities, schema defaults, and reduced four-asset graph.

## Expected physical measurements

For the 17 × 23 × 31 mm cuboid at 1000 kg/m³, expected volume is 12.121 cm³, mass is 0.012121 kg, and centre is (0.85, 1.15, 1.55) cm. Changing the driving height to 37 mm gives volume 14.467 cm³, mass 0.014467 kg, and centre (0.85, 1.15, 1.85) cm. The geometric inertia cache remains volume-weighted; Fusion applies the material density for physical inertia.

The material is generic. Schema defaults for structural and thermal coefficients are serialization defaults, not a claim of measured or certified engineering properties.

## Independent native acceptance

The fresh four-asset package and identity graph were accepted by Fusion 2706.1.17 in `../../LocalOracle/RectangleAuthoring/NativeAcceptance.json`. The source SHA-256 is `9a8bef0ec7d6d0a9012bfb282da594baf3527076b40274a988068d62aa1ece41`. The 31 mm cuboid reports the expected density, mass and centre before recompute. Rollback/restore, rebuild, edit to 37 mm, save and reopen preserve the expected measurements. The saved SHA-256 is `62c03b7aa11ce2c79193e51376e4405e6bbfd34aa5ab8097b72043ad49f38683`. This qualifies the reduced shared-appearance graph and fresh local library/instance/definition identities, rather than merely a same-source package rewrite.

Strict cylinder acceptance also passed in `../../LocalOracle/Authored/ProductionMaterialDocumentAcceptance.json`, source `9f2d11fc13dd407c4b07711be7c6d11811bda336a8fc45d872b263db2dc00359` and saved `1a2ace125ada2843a80fac604239ba51d9626963ba9e51d02f9427c41ff2ad70`. Its initial 17.25 mm height gives V=8.467573949 cm³, mass=0.008467573949 kg and centre Z=0.8625 cm. At 23 mm these become V=11.290098599 cm³, mass=0.011290098599 kg and centre Z=1.15 cm. Native save/reopen preserves the fresh material identity and name.
