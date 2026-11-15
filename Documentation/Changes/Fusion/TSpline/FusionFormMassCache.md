# Derived Fusion Form mass caches

## Behavior

`EmitFormDoc` now writes one complete `MassPropertyCacheValue` for each emitted Form body.
The previous zeroed cache returned a zero center of mass until Fusion recomputed the document.
Area, volume, first moments, second moments, inertia, off-diagonal products, and the revision id now come from the typed model.

`FormCache` uses sixteen-point Gaussian quadrature on every bicubic knot span.
It applies the divergence theorem to the surface position and the cross product of the partial derivatives.
`SurfaceMass` hoists expanded knot vectors and maps each nonzero interval to its basis span once.
`SurfaceSample` evaluates only the local pole window for each sample.
The [local sampling gotcha](../../../Gotchas/Conversion/Fusion/TSpline/FormBodies/MassSamplingUsesLocalPoles.md) records why full-net evaluators are unsuitable inside this loop.
Origin-based second moments produce inertia, while the first moments separately produce the center of mass.
Translation terms therefore remain in the tensor and in its off-diagonal fields.
The sixteen-point rule is a mathematical integration rule, not fitted document data.
The [native area precision gotcha](../../../Gotchas/Conversion/Fusion/TSpline/FormBodies/NativeAreaCacheHasPrecision.md) records convergence within `4e-13` cm² and the separate native cache approximation.
No curved-area tolerance is relaxed to equate distinct numerical estimators; `TestPlanarArea` supplies an exact `1e-8` cache check instead.
The cache requires no vendor-saved measurements or CAD runtime. The [field model](../../../../re/Fusion/Reconstruction/FormDocuments/General/CapMassCacheModel.json) records each field and its confidence status.

Open sheets have zero volume and no invented center.
Nonperiodic faces must use complete parameter-space boundaries; `CheckTrimming` rejects other faces instead of integrating a wrong region.
Periodic surfaces retain their complete parametric domain.
The [cache gotcha](../../../Gotchas/Conversion/Fusion/TSpline/FormBodies/FormMassCacheMustBeDerived.md) records why zero placeholders and cache omission are not alternatives.

## Native evidence

The [initial failure](../../../../re/Fusion/LocalOracle/FormDocuments/General/CapAccept/InitialMassFailure.json) has SHA-256 `867c19ac0dbbe739ca55a5786b46e61b28bdda20777a75c3939c034e1e3b9f87`.
It records 30 center-coordinate differences across 10 cases.
The first center issue occurred before recompute, while the subsequent center values agreed.

The accepted [native lifecycle](../../../../re/Fusion/LocalOracle/FormDocuments/General/CapAccept/NativeAcceptance.json) has SHA-256 `55e37af5b25d4603399b042fc8ae1fb8c1dba9639afae4818b4d08ba43e8f109`.
Fusion 2706.1.17 accepted all 11 independently emitted documents in fresh process 24703.
The previous preflight process was 98846, and `fresh_process_verified` is true.
The run reports 319 comparisons, zero problems, zero dropped items, and zero open documents before and after.
Top-level `vendor_loadable` and `application_usable` are both true.
The largest absolute scalar deviation is `2.9103830456733704e-11` across the mixed-unit measurements.

| Cage       | Initial area and volume                       | Initial center (cm)                                            |
| ---------- | --------------------------------------------- | -------------------------------------------------------------- |
| Box3       | 28.19774998549261 cm²; 12.441043578278578 cm³ | 1.1999999999999993, 1.1999974483503766, 1.199999999999999      |
| HeldPrism5 | 14.693249836881733 cm²; 4.640593243655995 cm³ | 0.006053534296884169, 0.024431953783258003, 0.7660045084104143 |

After the same control-point edit, Box3 has volume 12.398528701468491 cm³ and center `(1.2029980173529884, 1.2028781421663373, 1.2030568225219829)` cm.
HeldPrism5 has volume 4.622316303609363 cm³ and center `(0.009218588314258315, 0.02659344913314795, 0.7670432896233793)` cm.
Those values survive export and reopen.
The native after-controls match their edited control measurements with zero problems.

`Box3ShiftedG2` proves the tensor frame after translating all grips by `(13, -21, 42)` cm.
Its initial and edited centers are `(14.2, -19.80000255164962, 43.2)` and `(14.202998017352988, -19.79712185783366, 43.20305682252197)` cm.
All six tensor components match the native control at every measured stage.

`getXYZMomentsOfInertia()` returns one success flag followed by six mass-weighted moments.
The native controls use Steel at `0.00785 kg/cm³`, while the Kit documents use `0.001 kg/cm³`.
The oracle preserves those raw material observations and divides the six moments by each body's density before geometry comparison.
This produces comparable volumetric tensors in `cm⁵`, rather than treating the material difference as a geometry defect.
The earlier [raw-density comparison](../../../../re/Fusion/LocalOracle/FormDocuments/General/CapAccept/InertiaDensityFailure.json) has SHA-256 `3903a5228555b5ed5bf7ac19053af72bfc7de47d8a08a9b28fc154ac5eb10f13`.
It records 264 differences caused by comparing unlike materials directly; it is not accepted evidence.

## Integration coverage

`TestCubeMass` builds a closed unit-cube cage with the existing sharp-box constructors, converts it, emits a complete F3D, and reads the archive back.
The recovered body has 8 vertices, 12 edges, and 6 outward bicubic faces with exact parameter boundaries.
The test asserts the typed cache's area 6 cm², volume 1 cm³, center `(0.5, 0.5, 0.5)` cm, diagonal inertia `2/3 cm⁵`, and all three off-diagonal products `-1/4 cm⁵` at `1e-8` absolute and relative tolerance.
This full writer/reader integration independently rejects a shared absolute mass-scale error that translation invariance cannot detect.

`TestShiftMass` independently emits Box3 and its translated G2 counterpart through the current writer.
It checks area and volume invariance, the translated center, and the parallel-axis prediction for all six origin-tensor components at `1e-8` absolute and relative tolerance.
This detects an incorrect centroid frame without substituting a native curved-cache approximation.
`TestPlanarArea` compares the exact planar cache area at `1e-8` absolute and relative tolerance.
Its [native primitive report](../../../../re/Fusion/LocalOracle/FormDocuments/Grid/NativeAcceptance.json) records the untouched plane cages and healthy conversion. The test reuses the typed cage of `Grid/Primitives/Plane3x2.f3d` as its independent control.
The exact curved BRep comparisons remain at `1e-8` cm, with the convergence record separate from native numerical approximation.
`TestCapDeclFlow` also distinguishes Kit's original declaration from Fusion's G1 canonicalization.
The final controls required two privacy scrubs; all 11 typed models remained identical afterward.
Remote CI executes these integration cases. No local automated test suite ran.
