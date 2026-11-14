# A sweep tags its floor and roof once for every path segment

## Expectation

A sweep could follow the loft records.
Each face would take one progenitor and one tag, and the body progenitor would list both caps with the sides.

## Actual behavior

The native `SweepBend` control sweeps a 10 × 10 mm rectangle on the XZ plane.
The sweep path is a 20 mm line and a quarter arc of 30 mm radius.
The native `SweepHook` control adds a second line, so its path has three segments.
Both controls show the same record pattern.

| Record                  | Native sweep                                                                                         |
| ----------------------- | ---------------------------------------------------------------------------------------------------- |
| Path progenitors        | One `EntityProgenitor` for each path curve, with tags from 3, each holding a `SketchCurveEntityRecipe` |
| Path end points         | Named `EdgeStartVertexProgenitor` and `EdgeEndVertexProgenitor` metadata of type `StrongRefMetaType` |
| `SweepFaceProgenitor`   | One profile curve and one path progenitor tag for each face tag                                      |
| Face tag order          | For each path segment, the top, right, bottom and left sides of the profile                           |
| Floor and roof          | One face each, with one tag for every path segment, all assigned in the first segment                |
| Caps                    | Journal labels `1` at the start and `2` at the end, and no progenitor                                |
| `BodyProgenitor`        | One label for each face tag, sorted as text, where floor and roof tags repeat the first tag of their face |

The first segment assigns the floor and roof tags for segments 1 to P − 1 and then for segment 0.
Here, P is the number of path curves.
With two path curves, the path takes tags 3 and 4 and the faces take tags 5 to 12.
The roof takes 5 and 6, the floor takes 8 and 9, and the body progenitor takes 13.
The body progenitor therefore lists `10`, `11`, `12`, `5`, `5`, `7`, `8` and `8`, and the table `tagId` is 14.
The feature keeps six parameters: `AlongDistance`, `AgainstDistance`, `AlongRailDistance`, `AgainstRailDistance`, `TwistAngle` and `TaperAngle`.
The Fusion API shows only the first, the twist and the taper.
The native start cap edges also carry sketch curve links.

## Workaround

`SweepTags` builds the native tag order, and `AddSweepFeat` writes the path progenitors, the face progenitors and the body progenitor in that order.
`SweepSolid` labels the floor and the roof with all their tags in ascending order, so the journal names one face with several tags.
The design profile carries the native named types, because `StrongRefMetaType` metadata cannot be encoded without them.
Kit writes no sketch links on the start cap edges, as for revolves, and Fusion accepted every case.
All four sweep cases passed native acceptance, including the `AlongDistance` edit.

The [bend sweep control](../../../../../re/Fusion/LocalOracle/FeatureAuthoring/Controls/SweepBend.f3d) and the [hook sweep control](../../../../../re/Fusion/LocalOracle/FeatureAuthoring/Controls/SweepHook.f3d) record the evidence.
