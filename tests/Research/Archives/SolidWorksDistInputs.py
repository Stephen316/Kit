from json import loads as LoadJson
from math import hypot as Hypot
from typing import TypedDict, cast as CastValue

from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# the capture reports an oriented edge so hosted geometry need not use saved dimension bytes
class MeasuredEdge(TypedDict):
    start_world_mm: list[float]
    end_world_mm: list[float]


# principal support and profile vertices are measured independently of the distance serializer
class MeasuredSketch(TypedDict):
    name: str
    support_name: str
    entities: list[MeasuredEdge]


# the operation independently measures magnitude and reversal in different fields
class MeasuredEnd(TypedDict):
    depth_m: float
    reverse_direction: bool


# the reopened feature reports its parameter name and system value for a separate depth check
class MeasuredParam(TypedDict):
    name: str
    system_value: float


# the boss measurement ties the operation and its driving parameter to the same feature
class MeasuredBoss(TypedDict):
    name: str
    operation: MeasuredEnd
    dimensions: list[MeasuredParam]


# each reopened native file records both the boss and its independent sketch observations
class ReopenedPart(TypedDict):
    sketches: list[MeasuredSketch]
    feature_tree: list[MeasuredBoss]


# the receipt indexes independently reopened observations by the exact saved filename
class ReopenedSet(TypedDict):
    reopened_files: dict[str, ReopenedPart]


# the pinned measurement receipt provides a source independent of the archive replay
class BossMeasures(TypedDict):
    observations: ReopenedSet


# the codec receives typed neutral geometry and authored length without any archive slices
class DistInputs(TypedDict):
    frame: Transform
    normal: SpaceVector
    tangent: SpaceVector
    reverse: bool
    name: str
    depth_mm: float


# the known principal variants select different corners without consulting saved distance points
def ReadDistInputs(Measurements: bytes, Variant: str) -> DistInputs:
    Captures = CastValue(BossMeasures, LoadJson(Measurements))
    Reopened = Captures["observations"]["reopened_files"][
        f"P03-solidworks-{Variant}.SLDPRT"
    ]
    (SketchValue,) = (
        Sketch for Sketch in Reopened["sketches"] if Sketch["name"] == "RectangleSketch"
    )
    (BossValue,) = (
        Boss for Boss in Reopened["feature_tree"] if Boss["name"] == "BlindBoss"
    )
    (Parameter,) = (
        Value for Value in BossValue["dimensions"] if Value["name"] == "depth_mm"
    )
    Operation = BossValue["operation"]
    assert Parameter["system_value"] == Operation["depth_m"] > 0
    assert SketchValue["support_name"] == (
        "Right Plane" if Variant == "plane-yz" else "Front Plane"
    )
    Vertices = {
        tuple(Point)
        for EdgeValue in SketchValue["entities"]
        for Point in (EdgeValue["start_world_mm"], EdgeValue["end_world_mm"])
    }
    assert len(SketchValue["entities"]) == len(Vertices) == 4
    IsRight = SketchValue["support_name"] == "Right Plane"
    AnchorX, AnchorY, AnchorZ = min(Vertices) if IsRight else max(Vertices)
    Anchor = SpaceVector(AnchorX, AnchorY, AnchorZ)
    FirstEdge = SketchValue["entities"][0]
    DeltaX, DeltaY, DeltaZ = (
        EndValue - StartValue
        for StartValue, EndValue in zip(
            FirstEdge["start_world_mm"], FirstEdge["end_world_mm"], strict=True
        )
    )
    EdgeLength = Hypot(DeltaX, DeltaY, DeltaZ)
    assert EdgeLength > 0
    return {
        "frame": Transform(
            origin=Anchor,
            x_axis=SpaceVector(1, 0, 0),
            y_axis=SpaceVector(0, 0, -1),
            z_axis=SpaceVector(0, 1, 0),
        ),
        "normal": SpaceVector(1, 0, 0) if IsRight else SpaceVector(0, 0, 1),
        "tangent": SpaceVector(
            DeltaX / EdgeLength, DeltaY / EdgeLength, DeltaZ / EdgeLength
        ),
        "reverse": Operation["reverse_direction"],
        "name": Parameter["name"],
        "depth_mm": Operation["depth_m"] * 1000,
    }
