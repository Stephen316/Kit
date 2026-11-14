from convert.formats.Fusion.DocumentCodec.Defaults.MakeNumeric import MakeNumeric
from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Rectangle.Dimensions.Model.DimensionAxis import (
    DimensionAxis,
)


def BindDimMut(
    Author: AuthorState, AxisValue: DimensionAxis, CreationIndex: int, RuntimeId: int
) -> None:
    RoleName = AxisValue.RoleName
    Reference = Author.Reference
    Parameter = MakeNumeric(
        "d" + str(CreationIndex), AxisValue.LengthMm, "", Author.Policy.ParamBirthday
    )
    Parameter.update(
        creationIndex=CreationIndex,
        dcParameter=Reference(RoleName + "_binding"),
        expression=AxisValue.ParamName,
        isUserDefined=False,
        name="Linear Dimension-" + str(CreationIndex - 1),
    )
    Author.Change(RoleName + "_model", **Parameter)
    Author.Change(
        RoleName + "_binding",
        value=AxisValue.LengthMm / 10.0,
        parameter=Reference(RoleName + "_model"),
        rparamId=RuntimeId,
        rrOwnerFeature=Reference("dc_sketch"),
        rParentFeature=Reference("dc_sketch"),
        rDynamicUpdateData=Reference(RoleName + "_dynamic"),
    )
    Author.Change(
        RoleName + "_dynamic",
        rOwnerNode=Reference(RoleName + "_binding"),
        timeStamp=Author.Policy.TimeStamp,
    )
