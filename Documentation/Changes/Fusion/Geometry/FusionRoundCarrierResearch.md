# Sphere and torus persistence research

Owned native sphere and torus controls now bind analytic geometry, native SMT text and F3D binary snapshots. This is research evidence, not a new production carrier or independent native writer claim.

[The capture](../../../../re/Fusion/LocalOracle/RoundCarriers/Capture.json) creates one sphere and two tori through the native temporary-BRep API, then persists them in direct-design documents. Each has one face, zero edges and zero vertices. A closed periodic surface can therefore bound a valid solid without explicit trim loops. A polygon-only Euler check cannot classify such a model.

[The named field inventory](../../../../re/Fusion/Reconstruction/RoundCarriers/Evidence.json) covers 28 sphere/torus records in 16 initial geometry tables across 11 archives, including the four new controls. It retains the complete field sequences and the accompanying transform records. The capture and evidence scripts are adjacent to their reports. Native SMT files are retained byte-exact in `.smt.xz` artifacts, including their original trailing spaces; `NativeText.json` binds compressed and uncompressed hashes.

A sphere first stores the common attribute reference, entity tag and reserved reference. After those, the sphere stores center, signed radius, reference direction, pole direction, V reversal and four optional parameter bounds. The sphere control, made from known inputs, stores center `(1.1,-0.7,0.5)` cm and radius 1.7 cm in those positions. The names of the direction and reversal fields, and the save-version gate for them, came from binary inspection. They are not confirmed by a black-box experiment. Signed radius remains a distinct stored field.

An evaluation equation for the sphere also came from binary inspection. It is not confirmed by a black-box experiment, so this entry does not state it.

A torus stores center, axis, major radius, signed minor radius, reference direction, V reversal and the same four optional bounds. The torus controls store the requested center, axis and radii 2.3 and 0.7 cm in those positions, including the tilted axis `(0,0.6,0.8)`. The reference direction and reversal names are not confirmed by a black-box experiment. The signed minor radius must not be normalized away. General horn/spindle/self-intersecting parameterizations remain outside this research qualification.

The native sphere radius 1.7 cm has volume 20.579526276115537 cm³. Native tori with major/minor radii 2.3/0.7 cm have volume 22.246088320055406 cm³. The tilted axis `(0,0.6,0.8)` and an explicitly translated axial control preserve center `(1.1,-0.7,0.5)` cm. The first axial API call unexpectedly returned an origin-centered torus; the [specific API gotcha](../../../Gotchas/Conversion/Fusion/Api/FusionTorusPlacement.md) records that discrepancy and its measured workaround. No format rule is inferred from the unsuccessful placement request.

No local tests ran. All remaining observations come from owned native captures and read-only archive decoding. Product readers, writers and native acceptance for independently generated sphere/torus bodies remain separate work.
