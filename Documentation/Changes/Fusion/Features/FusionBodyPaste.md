# Body copy and paste

`PasteSpec(SourceBody, FeatureName)` copies a visible body of a part in place. Fusion writes it as the timeline item that `comp.features.copyPasteBodies.add(body)` makes. The copy is a new visible body, and it follows its source when the source changes.

```python
from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import ExtrudeSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LineCurve import LineCurve
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PasteSpec import PasteSpec

Corners = ((0.0, 0.0), (40.0, 0.0), (40.0, 30.0), (0.0, 30.0))
Block = ExtrudeSpec(
    tuple(LineCurve(Corners[Index], Corners[(Index + 1) % 4]) for Index in range(4)),
    20.0,
)
Specification = DocumentSpec(
    Title="Pasted block",
    ParamName="height",
    LengthMm=20.0,
    ProfileKind="part",
    BodyName="Body1",
    Features=(Block, PasteSpec(1, "Body paste")),
)
Payload = EmitDocument(Specification)
```

`SourceBody` names a visible body by its number, as in combines and body patterns. The pasted body takes the next body number. The adapter step kind is `KNative`, and the feature has no driving parameter.

## Native model

A paste is two Design features. `DcPasteBodies` is the timeline item. It owns a `ModelDataRef` and a `DRBody` that name the source body, and an empty progenitor table. A hidden `DcBaseFeature` holds the result. It owns a `DcDirectModelingData` node, a hidden body in the cache bodies and the new visible body. The two bodies name each other through the `BASEFEAT_PM_BODY_REF` and `BASEFEAT_DM_BODY_REF` attributes. A `BodyUuidProgenitor` in the base feature table maps the hidden body to the visible one, and `AssoctedPIDMap` maps the source body to the hidden body.

The paste takes two operations. The first belongs to the base feature and the second to the paste. The base feature owns the journal state and carries the model history indexes. The paste carries -1 for both. Only the paste appears in `DcCreationOrderFeatures`. The fragment counts the base feature as `DcBaseFeatureMetaType`.

In the journal the pasted body is a new body. Its body tag is the first operation with secondary id 1. Every face tag of the source appends the first operation, and edge tags stay as in the source. The [paste base gotcha](../../../Gotchas/Conversion/Fusion/Features/FeaturePasteBase.md) records the evidence.

## Vocabulary

`DcPasteBodies` and `DcReparentBodiesFeature` are missing from the shipped native catalog. Their schemas come from the black-box derivation in [PasteSchemas.json](../../../../re/Fusion/Reconstruction/FeatureAuthoring/PasteSchemas.json). Class identities and versions come from the saved class tables. Names, bases and member names come from the public `Document.DumpAcitveDocSchema` and `PEntity.Properties` text commands. With these members every record of the four paste controls decodes with no byte left over. Members that are empty in every control keep the `unsupported` element kind, and Kit writes them empty.

`MakeFeatureVocabulary.py --paste` writes `PasteClasses.json` and `PasteDefaults.json`. The defaults are schema-neutral. Body identifiers, the identifier map and the associative flag have no default. `AuthorSchemas` adds the paste classes only to a part that pastes a body, so every other document keeps its class table. `ReadDocSchemas` reads them so that `ReadDocument` can read a pasted part.

Every emitted value comes from the vocabulary or from the part. Identifiers are fresh UUIDs. The recipe and the operation map name the source body label. The cached mass is the solved mass of the copy.

## Native acceptance

`AcceptPastes.py` runs the acceptance script on six cases and writes `NativeAcceptancePastes.json`. The rules were fitted on `PastePlain` and `PasteFillet`. `PasteTwice` and `PasteSecond` match native controls that the rules were not fitted on. `PastePocket` and `PasteCombine` have no native capture of their own.

Each case ran in Fusion 2706.1.17 with no document open before or after the run. Every check matched the native control: the opened document, every rollback marker, `computeAll`, the edit, the reopened export and its `computeAll`. The base is a 40 × 30 × 20 mm block. Volumes are those of the opened Kit document after `computeAll`. Each edit changes the source, and the copy follows it.

| Case | Features | Volume (cm³) | Faces, edges, vertices | Edits | Edited volume (cm³) |
| --- | --- | ---: | --- | --- | ---: |
| `PastePlain` | block, paste of the block | 2 × 24.00000000 | 6, 12, 8 each | Base extrude AlongDistance 25 mm | 2 × 30.00000000 |
| `PasteFillet` | block, 3 mm round on one vertical edge, paste of the block | 2 × 23.96137167 | 7, 15, 10 each | Corner round 4 mm | 2 × 23.93132741 |
| `PasteTwice` | block, two pastes of the block | 3 × 24.00000000 | 6, 12, 8 each | Base extrude AlongDistance 15 mm | 3 × 18.00000000 |
| `PasteSecond` | block, 5 mm radius post as a new body, paste of the post | 24.00000000 + 2 × 1.57079633 | 6, 12, 8; 3, 2, 2 each | Post extrude AlongDistance 15 mm | 24.00000000 + 2 × 1.17809725 |
| `PastePocket` | block, 3 mm radius pocket, paste of the block | 2 × 23.43451332 | 7, 14, 10 each | Pocket extrude AlongDistance 10 mm | 2 × 23.71725666 |
| `PasteCombine` | block, 10 mm radius post on a block corner as a new body, paste of the post, cut of the block by the copy | 22.42920367 + 6.28318531 | 7, 15, 10; 3, 2, 2 | Post extrude AlongDistance 30 mm | 22.42920367 + 9.42477796 |

The opened documents of the six cases have 4, 5, 5, 6, 6 and 7 rollback markers. Fusion left no stray document open.

## Verification

`PasteTests.py` checks paste solids against the native controls, the face labels of the copy, the records, the journal identities, the class scope and the rejects. Tests run remotely, and no local tests were executed.

## Limits

| Request                                                     | Status                     |
| ----------------------------------------------------------- | -------------------------- |
| Pastes of hidden bodies, tapered bodies or sweep bodies     | Rejected with `ValueError` |
| Pastes of several bodies at once                            | Not authored               |
| Pastes into another component or of a moved copy            | Not authored               |
| Cut and paste, which moves the body instead of copying it   | Not authored               |
| The hidden body snapshot in the cache bodies part           | Not written; Fusion rebuilds it on recompute |
