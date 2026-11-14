# External corroboration of the Fusion data model

The [Fusion data model](../../Reference/Research/FusionDataModel.md) now explains in detail why the format was difficult to reverse engineer. It also records the T-spline, round body and external evidence that supports the model. This entry adds no production code.

## Data model additions

| Section | Content |
| --- | --- |
| Why the format is difficult | Eighteen difficulties in seven layers: container, object graph, identity, geometry, evaluation state, display members and tooling |
| Method that resolved the format | Corpus inventory, controlled variants, byte-exact re-emission, independent authoring and native acceptance |
| T-spline control cages and orientation | TSM declaration profile, record fields, extension namespaces, orientation roots and acceptance values |
| Authored round bodies and trimmed round histories | Sphere and torus field order, loop-free closed faces and acceptance values |
| External corroboration | The cadmpeg comparison |

The [acceptance matrix](../../Reference/Research/FusionAcceptanceEvidence.md) adds T-spline and round body rows. It also records the remote result for revision `55aeed29b` and the repairs for its failures.

## cadmpeg comparison

The [comparison](../../../re/Fusion/External/CadmpegComparison.md) reads cadmpeg at commit `de2726870ff728352163f601ab4e60bbd54fbade`. cadmpeg code is Apache-2.0 and its specifications are CC-BY-4.0. Kit copies no cadmpeg code, and the local clone is ignored by Git.

The comparison finds that cadmpeg covers more feature families and package forms. Kit names more fields from native classes and has Fusion acceptance of independently written output. Kit evidence resolves cadmpeg items HS-01 and DR-80 and partly resolves four more. It contradicts eight cadmpeg statements, including four TSM field meanings.
Some of these results rested in part on binary inspection, which was removed at the tip.
Those parts are not confirmed by a black-box experiment.

## Verification

Each cadmpeg statement in the contradiction table was checked against the cadmpeg specification text at the pinned commit. No local tests ran. This entry changes documentation and research files only.
The binary inventories this entry first described were removed at the tip; they remain in git history.
