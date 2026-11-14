from convert.formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismTags import PrismTags


def CheckPrismTags(Identity: BodyIdentity, TagSet: PrismTags) -> None:
    if (
        type(TagSet.Faces) is not tuple
        or len(TagSet.Faces) != 6
        or type(TagSet.Sketches) is not tuple
        or len(TagSet.Sketches) != 4
    ):
        raise ValueError("Prism history requires six face tags and four sketch links")
    if len({Value.PrimaryId for Value in TagSet.Faces}) != 6:
        raise ValueError("Prism face primary identities must be distinct")
    if any(
        Value.OperationIds != (Identity.OperationId,)
        or Value.SecondaryId
        or Value.ApproachId
        for Value in TagSet.Faces
    ):
        raise ValueError("Unsupported prism face tag operation profile")
    TagKeys = {
        (
            Value.PrimaryId,
            Value.SecondaryId,
            Value.SplitSequenceId,
            Value.SplitTotalNumber,
        )
        for Value in TagSet.Sketches
    }
    if len(TagKeys) != 4:
        raise ValueError("Prism source sketch links must be distinct")
