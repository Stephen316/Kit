from convert.formats.Fusion.TSplineCodec.Model.ControlGrip import ControlGrip
from convert.formats.Fusion.TSplineCodec.Writing.NumberText import NumberText


def WritePoint(GripValue: ControlGrip) -> str:
    return " ".join(
        NumberText(Value)
        for Value in (
            GripValue.CoordX,
            GripValue.CoordY,
            GripValue.CoordZ,
            GripValue.Weight,
        )
    )
