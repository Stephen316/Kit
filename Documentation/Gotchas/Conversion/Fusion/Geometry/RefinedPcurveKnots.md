# Fusion can report a refined pcurve with full knot multiplicity

## Expectation

The `NurbsCurve2D` of a coedge has the knots and poles of its stored parameter curve. A knot inserted once is reported once.

## Actual behavior

One knot was inserted once into the second parameter curve of an `int_int_cur` record. The curve is cubic. Fusion 2706.1.17 reported the new knot three times, so the coedge curve had 7 poles instead of 5.

| Item | Stored | Reported |
| --- | --- | --- |
| Degree | 3 | 3 |
| Inserted knot | -2.3126131813790116, once | -2.3126131813790116, three times |
| Poles | 5 | 7 |
| Largest distance from the stored curve at 201 parameters | Not applicable | 8.9e-16 |
| Largest pole distance from the stored curve with the knot raised to multiplicity 3 | Not applicable | 0 |

The reported curve is the stored curve, split at the new knot into two Bézier pieces. The other refined curves were reported pole for pole.

| Refined curve | Degree | Reported |
| --- | --- | --- |
| `par_int_cur` first parameter curve | 1 | Pole for pole |
| `exp_par_cur` definition used by two coedges | 1 | Pole for pole |
| `par_int_cur` 3D curve used by two edges | 3 | Pole for pole |
| `cl_loft_spl_sur` and `sum_spl_sur` approximations | 3 by 3 and 1 by 2 | Pole for pole |

## Workaround

Compare a coedge curve from Fusion with its stored curve as geometry when a knot can change multiplicity. Do not require equal pole counts for an `int_int_cur` parameter curve.

## Evidence

- [Diagnosis run with the reported curves](../../../../../re/Fusion/LocalOracle/ComplexGeometry/SecondPass/Runs/Diagnose.json)
- [Analysis](../../../../../re/Fusion/LocalOracle/ComplexGeometry/SecondPass/Analysis.json), field `representations`
- [Referenced pcurve forms](ReferencedPcurveForms.md)
