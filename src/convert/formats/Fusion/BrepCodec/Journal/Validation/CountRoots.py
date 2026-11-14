from convert.formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity


def CountRoots(Entities: tuple[KJournalEntity, ...]) -> int:
    return sum(
        isinstance(Value, BodyNode)
        or (isinstance(Value, FaceNode) and Value.OwnerShell == -1)
        or (isinstance(Value, EdgeNode) and Value.OwnerCoedge == -1)
        for Value in Entities
    )
