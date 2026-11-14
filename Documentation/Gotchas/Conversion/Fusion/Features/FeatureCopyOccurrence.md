# Pattern and mirror copies need occurrence records

## Expectation

A feature pattern stores its source feature, its counts and its spacing.
Fusion derives the copies from those inputs.
A mirror stores its source feature and its plane like a pattern without a count.

## Actual behavior

Native pattern and mirror features store each copy as an occurrence with its own tag and operation identifier.
The copied geometry also stays in the solved journal state, as for every other feature.

| Record                                         | Native rule                                                                       |
| ---------------------------------------------- | --------------------------------------------------------------------------------- |
| `DcPatternBodyOccurrence.occTagId`             | Rectangular: `(u + v)(u + v + 1) / 2 + u + 1`, with U varying fastest             |
| `DcPatternBodyOccurrence.occTagId`             | Circular and mirror: 1 to the occurrence count                                    |
| Operation identifiers                          | One for the feature and one for each copy after the source                        |
| `DcPatternBaseData.occOperationIdsMap`         | Copy occurrence tag to operation identifier, without the source occurrence        |
| `DcPatternBaseData.extengType`                 | False for rectangular patterns and true for circular patterns and mirrors         |
| `DcPatternSource.adjacentFaceCaches`           | Empty for rectangular patterns and one face for circular patterns and mirrors     |
| Source faces in the journal                    | A `TrackAttrib` on every wall and floor of the source names its Design reference  |
| Copy faces in the journal                      | The source tag plus the pattern and copy operation identifiers, floors included   |
| Mirror parameters                              | `countU` and `mirrorStitchTolerance` exist but stay out of `allParameters`        |

A `MirrorSpec` with its plane takes two operation identifiers after the plane identifier.
In the native `MirrorFeature` control, the plane has 306 and the mirror starts at 307.

The native `DiscBore` control cuts four blind pockets from the base with a circular pattern and then adds a counterbore.
Kit first gave every copy floor the source floor tag, tracked only the source walls and named the top face as the adjacent face.
The hole after the pattern then warned `Failed to evaluate the direction due to the invalid input` after the first `computeAll`.
The warning appeared in some runs only, and a second `computeAll` cleared it.

| Probe documents, first `computeAll` after open                 | Runs with the warning |
| -------------------------------------------------------------- | --------------------- |
| Native `DiscBore`                                              | 0 of 6                |
| Kit disc with a hole and no pattern                            | 0 of 10               |
| Kit blind pockets in a ring, top face as the adjacent face     | 36 of 82              |
| Kit through pockets in a ring, top face as the adjacent face   | 1 of 6                |
| Kit blind or through pockets in a ring, base face as adjacent  | 0 of 24               |

The 82 runs include variants with native copy floor tags, floor tracks, moved cap plane roots and shifted hole caches.
None of those changes removed the warning.

## Workaround

Kit writes every occurrence, operation map entry and track attribute with the native numbering.
A cap face bounded only by the walls of one copy takes the source tag with that copy's operation identifiers.
The source floor carries the same `TrackAttrib` as the source walls.
For an extrusion source, the adjacent face cache names the base face, where the source sketch lies.
For a hole source, it names the top face, where the hole starts, without native evidence for that case.
The writer still emits the solved copy geometry, because Fusion does not recompute it on open.
Kit-authored rectangular, circular and mirror parts match the native controls in volume, area, faces and edges.

The [native records](../../../../../re/Fusion/Reconstruction/FeatureAuthoring/FamilyRecords.json.xz) and the [native controls](../../../../../re/Fusion/LocalOracle/FeatureAuthoring/Controls/Capture.json) preserve the evidence.
