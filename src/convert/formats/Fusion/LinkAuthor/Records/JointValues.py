from convert.formats.Fusion.EntityCodec.Model.OptionalValue import OptionalValue
from convert.formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.LinkAuthor.Model.RootFacts import RootFacts
from convert.formats.Fusion.LinkAuthor.Records.LinkGuids import (
    KConstraintOperand,
    KConstraintState,
    KDcConstraintState,
    KJointOccState,
    KJointValueState,
)
from convert.formats.Fusion.LinkAuthor.Records.PathValues import OccurPath
from convert.formats.Fusion.LinkAuthor.Records.RecordValues import (
    MakeGroup,
    MakeMatrix,
)
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# the joint state contract needs a stable decomposition so cross document references retain their intended ownership
def JointState() -> ValueObject[KEntityValue]:
    return ValueObject(
        (
            MakeGroup(
                KJointValueState,
                ("conflict", None),
                ("value0", None),
                ("value1", None),
                ("value2", None),
                ("value3", None),
                ("value4", None),
                ("value5", None),
            ),
            MakeGroup(KConstraintState, ("suppressed", False)),
        )
    )


# the feature state contract needs a shared interpretation so cross document references retain their intended ownership
def FeatureState(Feature: int) -> ValueObject[KEntityValue]:
    return ValueObject(
        (
            MakeGroup(KJointOccState, ("state", OptionalValue(JointState()))),
            MakeGroup(KDcConstraintState, ("rFeature", LocalRef(Feature))),
        )
    )


# the operand value contract needs a shared interpretation so cross document references retain their intended ownership
def OperandValue(
    RootInfo: RootFacts, InstanceId: int, Alignment: tuple[float, ...] | None
) -> ValueObject[KEntityValue]:
    return ValueObject(
        (
            MakeGroup(
                KConstraintOperand,
                ("alignment", MakeMatrix(Alignment)),
                ("occPath", OccurPath(RootInfo, (InstanceId,))),
            ),
        )
    )
