# A Fusion torus carrier can have a negative minor radius

## Expectation

A `torus-surface` record has a positive major radius and a positive minor radius.

## Actual behavior

The journal of the `rule_all_both` fillet save holds 4 tori with a minor radius of `-0.1` cm. Their major radius is `0.2` cm. Kit raised `ValueError("Fusion round carriers require positive finite radii")` for this file.

The census of all torus and sphere records gave these signs.

| Carrier | Radius signs | Records |
| --- | --- | --- |
| Torus | Major and minor positive | 30 |
| Torus | Major positive, minor negative | 4 |
| Sphere | Positive | 25 |

All 34 tori are ring tori, with the minor magnitude less than the major radius. This census does not show what the negative sign means. Kit keeps the sign as saved.

## Workaround

Accept a negative torus minor radius. Require a finite, nonzero minor radius whose magnitude is less than the positive major radius. Keep the positive radius check for spheres.

## Evidence

- [Round radii](../../../../../re/Fusion/Reconstruction/ReaderCoverage/JournalStructure/RoundRadii.json)
- [Census delta](../../../../../re/Fusion/Reconstruction/ReaderCoverage/JournalStructure/CensusDelta.json)
