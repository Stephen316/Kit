from dataclasses import replace as Replace
from math import cos as Cosine, sin as SineValue
from typing import Mapping as TypeMap

from interchange.enums.EnumFeatures import FeatureKind
from interchange.enums.EnumValues import ValueKind
from interchange.features.DistanceParam import GetDistParam
from interchange.features.FeatureBoundPlane import BoundDatum
from interchange.features.FeatureStep import FeatureStep
from interchange.features.PlaneExtFrame import GetExtFrame
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector
from interchange.records.RecordParameter import Parameter


# vector combinations express translation and rotation within the authored local basis
def AddPlaneVector(
    First: SpaceVector, FirstScale: float, Other: SpaceVector, OtherScale: float
) -> SpaceVector:
    return SpaceVector(
        First.x * FirstScale + Other.x * OtherScale,
        First.y * FirstScale + Other.y * OtherScale,
        First.z * FirstScale + Other.z * OtherScale,
    )


# construction parameters follow the same exact owned unit conversion as solid controls
def ReadPlaneParam(
    StepValue: FeatureStep,
    Identity: str,
    Parameters: TypeMap[str, Parameter],
    KindValue: ValueKind,
) -> float:
    Param = Parameters.get(Identity)
    if Param is None or Param.id != Identity:
        raise ValueError(f"construction plane parameter {Identity} is missing")
    try:
        return GetDistParam(StepValue, Identity, Parameters, KindValue)
    except ValueError as ErrorInfo:
        raise ValueError(
            f"construction plane parameter {Identity} needs an owned finite {KindValue.value}"
        ) from ErrorInfo


# offsets and angles both derive the current frame from the unchanged authored zero basis
def GetDatumFrame(
    StepValue: FeatureStep,
    Definition: BoundDatum,
    Parameters: TypeMap[str, Parameter],
) -> Transform:
    if StepValue.kind != FeatureKind.KReference:
        raise ValueError("construction plane requires a reference feature")
    Extra = ReadPlaneParam(
        StepValue, Definition.OffsetParameterId, Parameters, ValueKind.KLength
    )
    if Extra != 0.0:
        raise ValueError("construction plane inactive offset must be zero")
    Frame = Definition.ReferenceFrame
    IsAngle = Definition.Method == "angle"
    Scalar = ReadPlaneParam(
        StepValue,
        Definition.ScalarParameterId,
        Parameters,
        ValueKind.KAngle if IsAngle else ValueKind.KLength,
    )
    if IsAngle:
        CosValue = Cosine(Scalar)
        SinValue = SineValue(Scalar)
        Result = Replace(
            Frame,
            y_axis=AddPlaneVector(Frame.y_axis, CosValue, Frame.z_axis, SinValue),
            z_axis=AddPlaneVector(Frame.z_axis, CosValue, Frame.y_axis, -SinValue),
        )
    else:
        Result = Replace(
            Frame, origin=AddPlaneVector(Frame.origin, 1.0, Frame.z_axis, Scalar)
        )
    try:
        _ = GetExtFrame(Result)
    except ValueError as ErrorInfo:
        raise ValueError("construction plane derived frame is invalid") from ErrorInfo
    return Result
