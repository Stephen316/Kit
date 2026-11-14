# Fusion saves apple tori

## Expectation

A Fusion torus carrier is a ring torus. Its minor radius magnitude is smaller than its major radius.

## Actual behavior

`re/Fusion/LocalOracle/FeatureAuthoring/Authored/vendor_RoundRimChain.f3d` holds a torus with major radius 0.2 cm and minor radius 0.3 cm. Fusion saved it after a 3 mm fillet on a 2 mm rim. The reader raised `Only positive ring-torus carriers are qualified`.

`TorusCensus.py` reads every torus carrier in the corpus:

| Kind | Records | Files |
| --- | --- | --- |
| Ring, minor positive | 276 | 53 |
| Ring, minor negative | 98 | 10 |
| Apple, minor greater than major | 24 | 3 |

`vendor_RoundHoleRim.f3d` and `vendor_RoundPostEdge.f3d` in the same folder also hold apple tori. They already read, because their tori sit in typed views that fell back to the exact journal.

## Workaround

Accept a torus carrier with a positive major radius and a nonzero minor radius. The minor radius magnitude must differ from the major radius. The horn torus, with equal magnitudes, has no corpus record and stays refused.

## Evidence

- [Read gap notes](../../../../../re/Fusion/Reconstruction/ReadGaps/ReadGapNotes.md#spindle-torus-carriers)
- [Torus census](../../../../../re/Fusion/Reconstruction/ReadGaps/TorusCensus.json)
