from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity


# the count roots contract needs a shared interpretation so inconsistent revision links fail before history reconstruction
def CountRoots(Entities: tuple[KJournalEntity, ...]) -> int:
    return sum(
        isinstance(Value, BodyNode)
        or (isinstance(Value, FaceNode) and Value.OwnerShell == -1)
        or (isinstance(Value, EdgeNode) and Value.OwnerCoedge == -1)
        for Value in Entities
    )
