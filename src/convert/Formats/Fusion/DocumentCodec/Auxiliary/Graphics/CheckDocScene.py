from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.GraphicsCodec.Validation.SceneTargets import SceneTargets
from convert.Formats.Fusion.MetaIndex import SegmentKind


# invalid doc scene input must fail here so supporting records retain their owning document relationships
def CheckDocScene(Value: DocumentModel) -> None:
    if Value.Graphics is None:
        return
    Owners = {
        (Segment.Metadata.Header.SegmentId, Record.ObjectId)
        for Segment in Value.Segments
        for Record in Segment.Records
        if Record.IsPrimary
    }
    ActIds = tuple(
        SlotValue.SegmentId
        for SlotValue in Value.Asset.Segments
        if SlotValue.Segment == SegmentKind.KAct
    )
    if len(ActIds) != 1:
        raise ValueError("Graphics entity links require an unambiguous ACT segment")
    Targets = SceneTargets(Value.Graphics, ActIds[0])
    if any((Target.SegmentId, Target.ObjectId) not in Owners for Target in Targets):
        raise ValueError("Graphics references an absent document entity")
