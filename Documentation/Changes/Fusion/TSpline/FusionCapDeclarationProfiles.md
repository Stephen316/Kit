# Fusion TSM cap declaration profiles

## Behavior

`ReadTspline` now accepts `G0CAPS`, `G1CAPS`, and `G2CAPS` declarations. It also accepts `star-smoothness` values 0, 1, and 2.
The existing degree, unit, end-condition, knot-rule, version, counter, and tolerance checks remain unchanged.
Other cap names and star values still raise `ValueError`.

`ConvertCage` uses `CheckSurface` as its single declaration gate. It no longer applies a second G1-only restriction.
`SurfaceHeader` keeps `G1CAPS` and star value 0 as the defaults for new cages.
`WriteHeader` preserves the declaration stored in a parsed surface.
Fusion canonicalizes G0 and G2 declarations to G1 during its native lifecycle. It preserves the star value.
The [canonicalization gotcha](../../../Gotchas/Conversion/Fusion/TSpline/FormBodies/FusionCanonicalizesCapTypes.md) prevents confusion with Kit data loss.
`SwapFormCage` still requires matching declarations in the old and new layouts.

Fusion ignores these two declarations when it selects the cap solve for the qualified profiles. The cage topology and grips determine the resulting body.
This rule has no per-layout table, saved geometry, donor payload, CAD runtime, or research-file dependency in production.

## Preparation

`PrepareCapVariants.py` applies each declaration through `dataclasses.replace` and emits the TSM through `EmitTspline`.
It builds each converted body through `ConvertForm` and each complete F3D through `EmitFormDoc`.
The five Box3 cases reproduce the existing one-field controls.
The five HeldPrism5 cases use a separate held-out cage with valence-five caps.
`Box3ShiftedG2` moves every Box3 grip by `(13, -21, 42)` cm to expose coordinate-frame errors.

Each prepared Box3 body has 6 faces, 12 edges, and 8 vertices.
Each prepared HeldPrism5 body has 15 faces, 35 edges, and 22 vertices.
The [preparation report](../../../../re/Fusion/LocalOracle/FormDocuments/General/CapAccept/Preparation.json) binds every generated TSM and F3D digest.

## Fusion acceptance

Fusion 2706.1.17 accepted all 11 independently emitted documents.
The [native acceptance report](../../../../re/Fusion/LocalOracle/FormDocuments/General/CapAccept/NativeAcceptance.json) has SHA-256 `55e37af5b25d4603399b042fc8ae1fb8c1dba9639afae4818b4d08ba43e8f109`.
It contains 319 comparisons, zero problems, and a largest absolute scalar deviation of `2.9103830456733704e-11` across the mixed-unit measurements.
Zero documents were open before and after the run.
The preflight process was 98846, and the measured process was 24703. `fresh_process_verified` is true.
Every case has `dropped = []`, `vendor_loadable = true`, and `application_usable = true`.

For each case, Fusion imported the same TSM as the native control. Kit's F3D opened separately.
Both documents ran `computeAll`, moved the same control point, exported, and reopened.
The comparison covered topology, timeline nodes, health, NURBS data, face grids, edge curves, bounds, centers, area, volume, and density-normalized inertia.
The translated case proves origin-frame tensors across three coordinates and six tensor components.
Its six normalized components match the native control at every stage; the [mass-cache change](FusionFormMassCache.md) gives the measured values and material-density rule.

| Cage                              | Loaded area and volume                        | Edited and reopened area and volume           | Loaded center (cm)                                             | Edited and reopened center (cm)                               |
| --------------------------------- | --------------------------------------------- | --------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------- |
| Box3, all five declarations       | 28.19774998549261 cm²; 12.441043578278578 cm³ | 28.08639550286362 cm²; 12.398528701468491 cm³ | 1.1999999999999993, 1.1999974483503766, 1.199999999999999      | 1.2029980173529884, 1.2028781421663373, 1.2030568225219829    |
| HeldPrism5, all five declarations | 14.693249836881733 cm²; 4.640593243655995 cm³ | 14.67340314680529 cm²; 4.622316303609363 cm³  | 0.006053534296884169, 0.024431953783258003, 0.7660045084104143 | 0.009218588314258315, 0.02659344913314795, 0.7670432896233793 |

The [static artifact inspection](../../../../re/Fusion/LocalOracle/FormDocuments/General/CapAccept/ContainerInspection.json) independently inventoried the held-out `G2CAPS` F3D.
It found 24 ZIP occurrences, including 16 files, with zero integrity contradictions.
Its digest matched the preparation record. The static inspection did not execute Fusion or establish runtime semantics.

The [scrub validation](../../../../re/Fusion/LocalOracle/FormDocuments/General/CapAccept/ScrubValidation.json) compared all 11 retained native controls before and after scrubbing.
The scrubber changed two archives, and every typed document model remained identical.
`changed_by_scrubber` is 2, and all 11 model digests match their pre-scrub values.

## Compatibility coverage

The compressed TSM archive catalog now contains 23 cases, including all 11 prepared declaration cases.
`TestTsmArchive` checks typed read, semantic digests, byte-exact emission, and a second read.
`TestTsmReject` adds unknown cap-name and star-value rejection through the public reader.
`TestGeneralCase` compares `ConvertForm` against the retained native body for all 11 variants.
`TestCapDeclFlow` checks Kit emission against the source declaration and native G1 canonicalization.
`TestShiftMass` verifies translation invariance and the parallel-axis tensor prediction through the current writer, as the [mass-cache change](FusionFormMassCache.md) describes.
These integration cases run in remote CI, not locally.

Run the reproducible research preparation with:

```sh
PYTHONPATH=src python3.14 re/Fusion/Reconstruction/FormDocuments/General/PrepareCapVariants.py
```

The separate local-Fusion oracle requires an available frontend bridge. Set `General/tmp/AcceptancePlan.txt` to `CapAccept` before dispatching `AcceptGeneral.py`.
The production codec does not use that bridge.
