from dataclasses import dataclass as MakeDataClass, replace as Replace
from math import isfinite as IsFinite, prod as Product

from convert.Formats.Fusion.Topology.AsmEdge.AsmPrismEdges import AsmPrismEdge
from convert.Formats.Fusion.Topology.AsmEdge.AsmRim import AsmUse
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable
from convert.Formats.Fusion.Topology.CutResult.CheckCutPocket import CheckCutPocket
from convert.Formats.Fusion.Topology.CutResult.CheckMetricLoop import CheckMetricLoop
from convert.Formats.Fusion.Topology.CutResult.CutMetricBox import (
    CutMetricBox,
    ReadCutBoxes,
)
from convert.Formats.Fusion.Topology.CutResult.CutMetricLoop import MetricLoops
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordTopology import TopologyCounts


# unsupported scalar geometry still retains the verified counts and bounds
@MakeDataClass(frozen=True, slots=True)
class CutResultStats:
    Topology: TopologyCounts
    Centroid: SpaceVector | None
    Refusal: str | None = None


# product and midpoint are derived from the exact carrier coordinate extrema
def BoxMeasure(BoxValue: CutMetricBox) -> tuple[float, tuple[float, ...]]:
    Spans = tuple(
        Finish - Start
        for Start, Finish in zip(BoxValue.Lower, BoxValue.Upper, strict=True)
    )
    return Product(Spans), tuple(
        Start + SpanValue * 0.5
        for Start, SpanValue in zip(BoxValue.Lower, Spans, strict=True)
    )


# use relative center displacement to avoid subtracting large absolute moments
def PocketMeasure(
    Outer: CutMetricBox, Inner: CutMetricBox
) -> tuple[float, SpaceVector]:
    OuterVolume, OuterCenter = BoxMeasure(Outer)
    InnerVolume, InnerCenter = BoxMeasure(Inner)
    Volume = OuterVolume - InnerVolume
    if not IsFinite(Volume) or Volume <= 0:
        raise ValueError("Fusion Cut mass requires finite positive volume")
    Center = tuple(
        OuterValue - (InnerValue - OuterValue) * (InnerVolume / Volume)
        for OuterValue, InnerValue in zip(OuterCenter, InnerCenter, strict=True)
    )
    if not all(IsFinite(Value) for Value in Center):
        raise ValueError("Fusion Cut mass requires a finite centroid")
    return Volume, SpaceVector(*Center)


# both the saved boundary and the authored extent must describe the same cavity
def ReadCutMass(
    Table: AsmTable,
    Loops: tuple[tuple[AsmUse, ...], ...],
    Edges: dict[int, AsmPrismEdge],
    Points: dict[int, SpaceVector],
    Normals: dict[int, SpaceVector],
    Topology: TopologyCounts,
    Definition: ExtrudeFeature,
) -> CutResultStats:
    Bounds = Topology.bounding_box
    if Bounds is None:
        return CutResultStats(
            Topology, None, "Fusion Cut mass lacks verified body bounds"
        )
    try:
        Outer, Inner = ReadCutBoxes(Points, Bounds)
        CutAxis, Openings = CheckCutPocket(Outer, Inner, Definition)
        CheckMetricLoop(
            Table,
            Loops,
            Edges,
            Points,
            Normals,
            MetricLoops(Outer, Inner, CutAxis, Openings),
        )
        Volume, Center = PocketMeasure(Outer, Inner)
    except ValueError as ErrorInfo:
        return CutResultStats(Topology, None, str(ErrorInfo))
    return CutResultStats(Replace(Topology, volume=Volume), Center)
