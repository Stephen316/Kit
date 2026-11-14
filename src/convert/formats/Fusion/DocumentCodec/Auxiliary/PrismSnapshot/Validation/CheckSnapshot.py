from convert.formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.formats.Fusion.BrepCodec.Prism.Validation.CheckPrismFrame import (
    CheckPrismFrame,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.PrismSnapshot import (
    PrismSnapshot,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Validation.CheckRegion import (
    CheckRegion,
)


def CheckSnapshot(Value: PrismSnapshot) -> None:
    if Value.Header != BrepHeader(23200, 4, 2, 10.0, 1e-6, 1e-10):
        raise ValueError("Unsupported cuboid snapshot header")
    CheckPrismFrame(Value.Model, Value.Frame)
    TagValues = Value.TagSet
    if (
        type(TagValues.Faces) is not tuple
        or len(TagValues.Faces) != 6
        or type(TagValues.Sketches) is not tuple
        or len(TagValues.Sketches) != 4
    ):
        raise ValueError("Snapshot requires six face tags and four sketch links")
    if len({TagValue.PrimaryId for TagValue in TagValues.Faces}) != 6:
        raise ValueError("Snapshot face primary identities must be distinct")
    if any(
        len(TagValue.OperationIds) != 1 or TagValue.SecondaryId or TagValue.ApproachId
        for TagValue in TagValues.Faces
    ):
        raise ValueError("Unsupported snapshot face tag operation profile")
    if len({TagValue.OperationIds for TagValue in TagValues.Faces}) != 1:
        raise ValueError("Snapshot face operation identities disagree")
    CheckRegion(Value.Profile, Value.Frame.CornersCm)
    CheckRegion(Value.Sketch, Value.Frame.CornersCm)
