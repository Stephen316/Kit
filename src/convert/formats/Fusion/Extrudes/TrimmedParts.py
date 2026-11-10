# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import tau as FullTurn
from sys import float_info as FloatInfo

from convert.adapters.base.WriteValidate import IsObjectTuple
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.GeometryCurves import (
    ArcGeometry,
    CircleGeometry,
    LineGeometry,
)
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.VectorPlane import PlaneVector


# affine evaluation keeps a selected line segment on its exact native source carrier
def TrimLine(LineValue: LineGeometry, Lower: float, Upper: float) -> LineGeometry:
    Start, EndValue = LineValue.start, LineValue.end
    DeltaX, DeltaY = EndValue.x - Start.x, EndValue.y - Start.y
    return LineGeometry(
        PlaneVector(Start.x + Lower * DeltaX, Start.y + Lower * DeltaY),
        PlaneVector(Start.x + Upper * DeltaX, Start.y + Upper * DeltaY),
    )


# selected intervals create bounded analytic geometry without altering the source sketch
def ReadTrimParts(
    StepValue: FeatureStep, SketchValue: Sketch
) -> tuple[LineGeometry | ArcGeometry, ...]:
    RowValues = StepValue.attributes.get("fusion.profile_portions")
    if not IsObjectTuple(RowValues) or len(RowValues) not in (2, 4):
        raise ValueError("Missing Fusion trimmed profile boundary")
    Sources = {
        Entity.id: Entity.geometry
        for Entity in SketchValue.entities
        if not Entity.construction
    }
    Parts: list[LineGeometry | ArcGeometry] = []
    for RowValue in RowValues:
        if not IsObjectTuple(RowValue) or len(RowValue) != 4:
            raise ValueError("Invalid Fusion trimmed profile portion")
        EntityId, Lower, Upper, Selector = RowValue
        if (
            not isinstance(EntityId, str)
            or (type(Lower) is not float and type(Lower) is not int)
            or (type(Upper) is not float and type(Upper) is not int)
            or not 0 <= Lower < Upper <= FloatInfo.max
            or not IsObjectTuple(Selector)
            or len(Selector) != 7
            or any(type(Value) is not int for Value in Selector)
        ):
            raise ValueError("Invalid Fusion trimmed profile interval or selector")
        Source = Sources.get(EntityId)
        if isinstance(Source, LineGeometry) and Upper <= 1.0:
            Parts.append(TrimLine(Source, Lower, Upper))
        elif (
            isinstance(Source, CircleGeometry)
            and Upper <= 2 * FullTurn
            and Upper - Lower < FullTurn
        ):
            Parts.append(ArcGeometry(Source.center, Source.radius, Lower, Upper))
        else:
            raise ValueError("Fusion trimmed profile source and interval disagree")
    return tuple(Parts)
