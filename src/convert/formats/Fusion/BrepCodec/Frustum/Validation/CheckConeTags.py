from convert.formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags


def CheckConeTags(Identity: BodyIdentity, TagSet: TopologyTags) -> None:
    Faces = (TagSet.SideFace, TagSet.TopFace, TagSet.BottomFace)
    if len({Value.PrimaryId for Value in Faces}) != 3:
        raise ValueError("Frustum face primary identities must be distinct")
    if any(
        Value.OperationIds != (Identity.OperationId,)
        or Value.SecondaryId
        or Value.ApproachId
        for Value in (*Faces, TagSet.TopEdge, TagSet.BottomEdge)
    ):
        raise ValueError("Unsupported frustum topology tag operation profile")
