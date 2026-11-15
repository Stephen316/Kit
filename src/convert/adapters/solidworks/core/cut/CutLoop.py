from dataclasses import dataclass as Dataclass
from math import dist as Distance

from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.core.RectBindings import KPointToleranceMm
from convert.adapters.solidworks.core.RectSource import RectSource
from convert.adapters.solidworks.sketch.GeometryTypes import SketchGeometry, SketchLine
from convert.adapters.solidworks.sketch.InlineSketch import InlineRead
from convert.adapters.solidworks.sketch.MemberSpans import MemberSpan
from interchange.core.Common import FreezeMapping
from interchange.enums.EnumGeometry import GeometryKind
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Sketch import SketchEntity
from interchange.geometry.models.VectorPlane import PlaneVector


# each source line retains its serialized slots separately from its loop direction
@Dataclass(frozen=True, slots=True)
class CutLine:
    Source: SketchLine
    SpanValue: MemberSpan
    Slots: tuple[int, int]


# the active perimeter is selected by authored member identity and the typed line spans
def ReadCutLines(DataValue: InlineRead) -> list[CutLine]:
    Result: list[CutLine] = []
    for Source, SpanValue in zip(
        DataValue.Geometry["lines"], DataValue.Members.Lines, strict=True
    ):
        if Source["native_id"] < 0:
            continue
        First, Second = Source["point_indices"]
        RequireArch(First != Second, True, "nondegenerate cut perimeter slots")
        Result.append(CutLine(Source, SpanValue, (First, Second)))
    RequireArch(len(Result), 4, "four authored cut perimeter lines")
    RequireArch(
        len({Value.Source["native_id"] for Value in Result}),
        4,
        "unique cut line identities",
    )
    return Result


# each successive line must be uniquely adjacent until the four distinct slots close
def OrderCutLines(Lines: list[CutLine]) -> tuple[CutLine, ...]:
    Start = Lines[0].Slots[0]
    Current = Lines[0].Slots[1]
    Ordered = [Lines[0]]
    Remaining = Lines[1:]
    Visited = {Start}
    for _ in range(len(Remaining)):
        RequireArch(Current not in Visited, True, "distinct cut perimeter vertices")
        Visited.add(Current)
        Choices = [Value for Value in Remaining if Current in Value.Slots]
        RequireArch(len(Choices), 1, "unique next cut perimeter edge")
        (Choice,) = Choices
        Remaining.remove(Choice)
        First, Second = Choice.Slots
        Following = Second if First == Current else First
        Ordered.append(CutLine(Choice.Source, Choice.SpanValue, (Current, Following)))
        Current = Following
    RequireArch(Current, Start, "closed cut perimeter")
    return tuple(Ordered)


# local sketch coordinates come from the saved point slots in their proven loop direction
def CutLineEntity(
    LineValue: CutLine, Points: list[tuple[float, ...]], SketchId: str, StreamName: str
) -> SketchEntity:
    Start, Finish = (
        tuple(1000 * Value for Value in Points[Index]) for Index in LineValue.Slots
    )
    RequireArch(Distance(Start, Finish) > 0, True, "nondegenerate cut perimeter line")
    NativeId = LineValue.Source["native_id"]
    return SketchEntity(
        f"{SketchId}:native-segment:{NativeId}",
        GeometryKind.KLine,
        LineGeometry(PlaneVector(*Start), PlaneVector(*Finish)),
        provenance=RectSource(
            str(NativeId), StreamName, LineValue.SpanValue, "config-sketch-line"
        ),
        attributes=FreezeMapping(
            {
                "native_segment_id": NativeId,
                "native_member_index": LineValue.Source["member_index"],
                "native_point_indices": tuple(LineValue.Source["point_indices"]),
            }
        ),
    )


# the saved horizontal and vertical targets must alternate around the same four local lines
def CheckCutAxes(Geometry: SketchGeometry, Lines: tuple[CutLine, ...]) -> None:
    Relations = Geometry["member_relations"]
    AxisKinds = {Value["segment_native_id"]: Value["kind"] for Value in Relations}
    RequireArch((len(Relations), len(AxisKinds)), (4, 4), "one saved axis per cut line")
    Ordered = tuple(AxisKinds[Value.Source["native_id"]] for Value in Lines)
    RequireArch(
        Ordered in (("horizontal", "vertical") * 2, ("vertical", "horizontal") * 2),
        True,
        "alternating cut perimeter axes",
    )
    Points = Geometry["points_metres"]
    for LineValue, KindValue in zip(Lines, Ordered, strict=True):
        AxisIndex = 1 if KindValue == "horizontal" else 0
        Start, Finish = (Points[Index][AxisIndex] for Index in LineValue.Slots)
        RequireArch(
            abs(Start - Finish) * 1000 <= KPointToleranceMm,
            True,
            "saved cut axis matches its local line",
        )


# a cut perimeter must retain four physically distinct local vertices
def BuildCutLoop(
    DataValue: InlineRead, SketchId: str, StreamName: str
) -> tuple[SketchEntity, ...]:
    Lines = OrderCutLines(ReadCutLines(DataValue))
    CheckCutAxes(DataValue.Geometry, Lines)
    Points = DataValue.Geometry["points_metres"]
    RequireArch(
        len({Points[Value.Slots[0]] for Value in Lines}),
        4,
        "distinct cut vertex positions",
    )
    return tuple(CutLineEntity(Value, Points, SketchId, StreamName) for Value in Lines)
