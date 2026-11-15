from convert.formats.Fusion.TSplineCodec.Model.ControlGrip import ControlGrip
from convert.formats.Fusion.TSplineCodec.Writing.NumberText import NumberText


# the point operation needs a consistent construction rule so control cage topology retains its native connectivity
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
