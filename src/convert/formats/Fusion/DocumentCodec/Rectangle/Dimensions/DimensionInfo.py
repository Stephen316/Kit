from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Rectangle.Dimensions.Model.DimensionAxis import (
    DimensionAxis,
)
from convert.formats.Fusion.DocumentCodec.Values.ValueShapes import MakeColor, MakePoint


def DimensionInfo(
    Author: AuthorState, AxisValue: DimensionAxis
) -> list[dict[str, object]]:
    Start = AxisValue.StartPoint
    Finish = AxisValue.EndPoint
    ShiftedStart = tuple(
        Coord + Delta for Coord, Delta in zip(Start, AxisValue.Offset, strict=True)
    )
    ShiftedEnd = tuple(
        Coord + Delta for Coord, Delta in zip(Finish, AxisValue.Offset, strict=True)
    )
    Midpoint = tuple(
        (First + Second) / 2.0
        for First, Second in zip(ShiftedStart, ShiftedEnd, strict=True)
    )
    return [
        Author.MakeGroup(
            "LinearDimensionInfoValue",
            dict(
                DimEndPoint=MakePoint(*ShiftedEnd),
                DimStartPoint=MakePoint(*ShiftedStart),
                endPoint=MakePoint(*Finish),
                extnStartPoint=MakePoint(*Start),
                isSingleArrow=False,
                length=AxisValue.LengthMm / 10.0,
                startPoint=MakePoint(*Start),
            ),
        ),
        Author.MakeGroup(
            "DimensionInfoValue",
            dict(
                bDriven=False,
                color=MakeColor(0.51, 0.78, 0.25),
                hasTextPoint=True,
                plane=dict(
                    normalReversed=False,
                    origin=MakePoint(),
                    uAxis=MakePoint(1.0),
                    vAxis=MakePoint(0.0, 1.0),
                ),
                prefix="fx: ",
                text=AxisValue.ParamName,
                textPosition=MakePoint(*Midpoint),
            ),
        ),
    ]
