from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath
from sys import version_info as PythonVersion

from pytest import mark as MarkTests, raises as RaisesError

from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CappedLayout import (
    CappedLayout,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CappedShape import (
    CappedShape,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormBody,
    FormWindow,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.PatchCell import PatchCell
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline
from tests.convert.formats.FusionCodec.Documents.Form.CappedCages import (
    BoxCreases,
    BoxParts,
    CubeParts,
    MakeSurface,
    PrismParts,
    TorusParts,
)
from tests.convert.formats.FusionCodec.Documents.Form.CreaseFiles import KDartCage
from tests.convert.formats.FusionCodec.Documents.Form.ReadConverted import (
    ReadConverted,
)
from tests.convert.formats.FusionCodec.Documents.Form.ReadFormFile import (
    ReadFormFile,
)

KShapeSlack = 1e-12
KNeedZip = MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Form archive requires ZIP Zstandard"
)
KNativeCases = (
    (
        "re/Fusion/LocalOracle/FormDocuments/Acceptance/Saved/BoxControl.f3d",
        "7201e611c9e68d49397f6d877e95f1aba94b8e058e29d1fa516e9a179b6a9755",
    ),
    (
        "re/Fusion/LocalOracle/FormDocuments/Acceptance/Saved/PlaneCreasedControl.f3d",
        "5bb5a4256990d72cd8e60756729a37f90415162a738b99cee9a2d467c3e3bf2a",
    ),
    (
        "re/Fusion/LocalOracle/FormDocuments/Acceptance/Saved/PlaneControl.f3d",
        "7d09d4698b57fefff528de75bb35757c615312f1eb6bdd7f1570751ab1ea219a",
    ),
)
KLetterCubes = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
KTeeCubes = [(0, 0, 0), (1, 0, 0), (2, 0, 0), (1, 1, 0)]


def RegionFaces(Shape: CappedShape) -> list[tuple[int, ...]]:
    return [tuple(CellValue.Face for CellValue in Cells) for Cells in Shape.Regions]


def RegionOffsets(Shape: CappedShape, Region: int) -> list[tuple[float, float, int]]:
    return [CellValue.Offset for CellValue in Shape.Regions[Region]]


def EdgeUsers(Shape: CappedShape) -> dict[int, list[tuple[int, bool]]]:
    Found: dict[int, list[tuple[int, bool]]] = {}
    for FaceValue in Shape.Faces:
        for UseValue in FaceValue.Uses:
            Entry = (FaceValue.Region, UseValue.Reversed)
            Found.setdefault(UseValue.EdgeIndex, []).append(Entry)
    return Found


def SolidShape(Shape: CappedShape) -> None:
    assert [Entry.Region for Entry in Shape.Faces] == list(
        reversed(range(len(Shape.Regions)))
    )
    assert [Entry.Label for Entry in Shape.Faces] == [
        str(Entry.Region + 1) for Entry in Shape.Faces
    ]
    assert all(
        (Entry.DoubleSided, Entry.Contained) == (False, None) for Entry in Shape.Faces
    )
    assert all(
        (Entry.Label, Entry.Windows, Entry.Bounds) == ("", (), None)
        for Entry in Shape.Edges
    )
    Users = EdgeUsers(Shape)
    assert sorted(Users) == list(range(len(Shape.Edges)))
    for EdgeIndex, Members in Users.items():
        assert sorted(IsBack for _, IsBack in Members) == [False, True]
        Curve = Shape.Curves[Shape.Edges[EdgeIndex].CurveIndex]
        assert Curve.Region == min(Region for Region, _ in Members)


def TraceShape(Shape: CappedShape) -> None:
    for FaceValue in Shape.Faces:
        for UseValue in FaceValue.Uses:
            Curve = Shape.Curves[Shape.Edges[UseValue.EdgeIndex].CurveIndex]
            Trace = UseValue.Pcurve
            assert Trace.Knots == (Curve.Lower, Curve.Upper)
            assert (Trace.Degree, Trace.Closure, Trace.Multiplicity) == (
                1,
                Curve.Closure,
                (1, 1),
            )
            assert UseValue.Fit == 0.0


def TestBoxShape() -> None:
    Shape = CappedLayout(MakeSurface(BoxParts((1, 1, 1))))
    assert (len(Shape.Faces), len(Shape.Edges), len(Shape.Points)) == (6, 12, 8)
    assert RegionFaces(Shape) == [(Index,) for Index in range(6)]
    assert all(Entry.Convexity == "tangent" for Entry in Shape.Edges)
    assert Shape.Periods == ((0, 0),) * 6
    SolidShape(Shape)
    TraceShape(Shape)


def TestBoxCells() -> None:
    Shape = CappedLayout(MakeSurface(BoxParts((2, 3, 4))))
    assert [len(Cells) for Cells in Shape.Regions] == [12, 12, 8, 8, 6, 6]
    assert (len(Shape.Edges), len(Shape.Points)) == (12, 8)
    SolidShape(Shape)
    TraceShape(Shape)


def TestLetterPrism() -> None:
    Shape = CappedLayout(MakeSurface(CubeParts(KLetterCubes)))
    Singles = [(Index,) for Index in (2, 3, 5, 6, 7, 8, 9, 11, 12, 13)]
    assert RegionFaces(Shape) == [(0, 4), (1, 10), *Singles]
    assert RegionOffsets(Shape, 0) == RegionOffsets(Shape, 1) == [(0, 0, 0), (0, -1, 0)]
    assert (len(Shape.Edges), len(Shape.Points)) == (26, 16)
    Ranges = [(Entry.Lower, Entry.Upper) for Entry in Shape.Curves]
    assert (Ranges[0], Ranges[6], Ranges[21]) == ((-2.0, -1.0), (1.0, 2.0), (-1.0, 0.0))
    SolidShape(Shape)
    TraceShape(Shape)


def TestTeeBlocks() -> None:
    with RaisesError(ValueError, match="face lines tie"):
        _ = CappedLayout(MakeSurface(CubeParts(KTeeCubes)))


def TestDartRefusal() -> None:
    Surface = ReadTspline(ReadFormFile(*KDartCage))
    with RaisesError(ValueError, match="dart rule needs a cap point or crease"):
        _ = CappedLayout(Surface)


def TestTurnOffsets() -> None:
    Shape = CappedLayout(MakeSurface(PrismParts(3)))
    Singles = [(Index,) for Index in range(6)]
    Quads = [(6, 7, 8, 9), (10, 11, 12, 13), (14, 15, 16, 17)]
    assert RegionFaces(Shape) == [*Singles, *Quads]
    for Region in (6, 7, 8):
        assert RegionOffsets(Shape, Region) == [
            (0, 0, 0),
            (2, 0, 1),
            (2, 2, 2),
            (0, 2, 3),
        ]
    assert (len(Shape.Edges), len(Shape.Points)) == (21, 14)
    SolidShape(Shape)
    TraceShape(Shape)


def TestTorusSeams() -> None:
    Shape = CappedLayout(MakeSurface(TorusParts((8, 6))))
    assert Shape.Regions == (
        tuple(
            PatchCell(Index, (0, 1, 0, 1), (-(Index % 6), -(Index // 6), 0))
            for Index in range(48)
        ),
    )
    assert (Shape.Points, Shape.Periods) == ((0,), ((8, 6),))
    EdgeEnds = [
        (Entry.StartVertex, Entry.EndVertex, Entry.Convexity) for Entry in Shape.Edges
    ]
    assert EdgeEnds == [(0, 0, "tangent"), (0, 0, "tangent")]
    Ranges = [(Entry.Lower, Entry.Upper, Entry.Closure) for Entry in Shape.Curves]
    assert Ranges == [(0.0, 8.0, 2), (0.0, 6.0, 2)]
    TorusUses = Shape.Faces[0].Uses
    assert [(Entry.EdgeIndex, Entry.Reversed) for Entry in TorusUses] == [
        (0, False),
        (1, False),
        (0, True),
        (1, True),
    ]
    Lines = (((0.0, 0.0), (8.0, 0.0)), ((0.0, 0.0), (0.0, 6.0)))
    assert [Entry.Pcurve.Poles for Entry in TorusUses] == [*Lines, *Lines]
    Bottom = [FormWindow(Index * 6, 0.0, 1.0, 0.0, 0.0) for Index in range(8)]
    LeftSide = [FormWindow(Index, 0.0, 0.0, 0.0, 1.0) for Index in range(6)]
    assert [list(Entry.Windows) for Entry in Shape.Edges] == [Bottom * 2, LeftSide * 2]
    Labels = [Shape.Faces[0].Label, *(Entry.Label for Entry in Shape.Edges)]
    assert sorted(int(Label) for Label in Labels) == [1, 2, 3]
    TraceShape(Shape)


def TestSharpBox() -> None:
    Parts = BoxParts((2, 2, 2))
    Plain = MakeSurface(Parts)
    Creases = BoxCreases(Parts, Plain, 2.0)
    assert len(Creases.EdgeIndices) == 24
    Shape = CappedLayout(ReplaceValue(Plain, Creases=Creases))
    assert RegionFaces(Shape) == [
        tuple(range(Start, Start + 4)) for Start in range(0, 24, 4)
    ]
    assert RegionOffsets(Shape, 0) == [(-1, 0, 0), (0, 0, 0), (-1, -1, 0), (0, -1, 0)]
    assert (len(Shape.Edges), len(Shape.Points)) == (12, 8)
    assert all(Entry.Convexity == "unknown" for Entry in Shape.Edges)
    SolidShape(Shape)


def ScaledCage(Surface: TsplineSurface, Values: list[float]) -> TsplineSurface:
    Topology = Surface.Topology
    Edges = tuple(
        ReplaceValue(EdgeValue, KnotInterval=Values[Index % len(Values)])
        for Index, EdgeValue in enumerate(Topology.Edges)
    )
    return ReplaceValue(Surface, Topology=ReplaceValue(Topology, Edges=Edges))


def TestKnotScale() -> None:
    Plain = MakeSurface(BoxParts((2, 2, 2)))
    BaseShape = CappedLayout(Plain)
    Scaled = CappedLayout(ScaledCage(Plain, [2.0]))
    assert all(
        CellValue.Window == (0, 2, 0, 2)
        for Cells in Scaled.Regions
        for CellValue in Cells
    )
    assert [
        (2 * CellValue.Offset[0], 2 * CellValue.Offset[1], CellValue.Offset[2])
        for Cells in BaseShape.Regions
        for CellValue in Cells
    ] == [CellValue.Offset for Cells in Scaled.Regions for CellValue in Cells]
    assert [(2 * Entry.Lower, 2 * Entry.Upper) for Entry in BaseShape.Curves] == [
        (Entry.Lower, Entry.Upper) for Entry in Scaled.Curves
    ]
    with RaisesError(ValueError, match="one shared knot interval"):
        _ = CappedLayout(ScaledCage(Plain, [1.0, 2.0]))
    with RaisesError(ValueError, match="whole knot interval"):
        _ = CappedLayout(ScaledCage(Plain, [1.5]))


def TraceSpread(LeftCurve: BsCurve, RightCurve: BsCurve) -> float:
    Plain = ReplaceValue(LeftCurve, Knots=RightCurve.Knots, Poles=RightCurve.Poles)
    assert Plain == RightCurve
    assert len(LeftCurve.Poles) == len(RightCurve.Poles)
    Knots = [
        abs(Former - Latter)
        for Former, Latter in zip(LeftCurve.Knots, RightCurve.Knots, strict=True)
    ]
    Poles = [
        abs(Former - Latter)
        for LeftPole, RightPole in zip(LeftCurve.Poles, RightCurve.Poles)
        for Former, Latter in zip(LeftPole, RightPole, strict=True)
    ]
    return max(Knots + Poles)


def WindowSpread(
    Built: tuple[FormWindow, ...], Stored: tuple[FormWindow, ...]
) -> float:
    assert [Entry.Face for Entry in Built] == [Entry.Face for Entry in Stored]
    return max(
        (
            abs(Former - Latter)
            for LeftWindow, RightWindow in zip(Built, Stored)
            for Former, Latter in zip(
                (LeftWindow.ULow, LeftWindow.UHigh, LeftWindow.VLow, LeftWindow.VHigh),
                (
                    RightWindow.ULow,
                    RightWindow.UHigh,
                    RightWindow.VLow,
                    RightWindow.VHigh,
                ),
            )
        ),
        default=0.0,
    )


def NativeEdges(Shape: CappedShape, Native: FormBody) -> None:
    assert len(Shape.Edges) == len(Native.Edges)
    for EdgeValue, NativeEdge in zip(Shape.Edges, Native.Edges):
        Curve = Shape.Curves[EdgeValue.CurveIndex]
        Knots = NativeEdge.Curve.Knots
        assert (EdgeValue.StartVertex, EdgeValue.EndVertex) == (
            NativeEdge.StartVertex,
            NativeEdge.EndVertex,
        )
        assert (EdgeValue.Convexity, EdgeValue.Bounds) == (
            NativeEdge.Convexity,
            NativeEdge.Bounds,
        )
        assert (
            max(abs(Curve.Lower - Knots[0]), abs(Curve.Upper - Knots[-1]))
            <= KShapeSlack
        )
        assert Curve.Closure == NativeEdge.Curve.Closure
        assert bool(EdgeValue.Label) == bool(NativeEdge.Label)
        assert WindowSpread(EdgeValue.Windows, NativeEdge.Windows) <= KShapeSlack


def NativeFaces(Shape: CappedShape, Native: FormBody) -> None:
    assert len(Shape.Faces) == len(Native.Faces)
    for FaceValue, NativeFace in zip(Shape.Faces, Native.Faces):
        assert (FaceValue.Region, FaceValue.DoubleSided, FaceValue.Contained) == (
            NativeFace.Surface.Region,
            NativeFace.DoubleSided,
            NativeFace.Contained,
        )
        for UseValue, NativeUse in zip(FaceValue.Uses, NativeFace.Uses, strict=True):
            assert (UseValue.EdgeIndex, UseValue.Reversed) == (
                NativeUse.EdgeIndex,
                NativeUse.Reversed,
            )
            assert TraceSpread(UseValue.Pcurve, NativeUse.Pcurve) <= KShapeSlack
            assert abs(UseValue.Fit - NativeUse.Fit) <= KShapeSlack


@KNeedZip
@MarkTests.parametrize(
    "CaseValue", KNativeCases, ids=lambda CaseValue: FilePath(CaseValue[0]).stem
)
def TestNativeShape(CaseValue: tuple[str, str]) -> None:
    Model = ReadDocument(ReadFormFile(CaseValue[0], CaseValue[1]))
    Shape = CappedLayout(Model.Forms[0].Surface)
    Native = ReadConverted(Model)
    assert Shape.Regions == Native.Regions
    assert len(Shape.Points) == len(Native.PointsCm)
    NativeEdges(Shape, Native)
    NativeFaces(Shape, Native)
    Labels = [Entry.Label for Entry in Shape.Faces]
    Labels += [Entry.Label for Entry in Shape.Edges if Entry.Label]
    Natives = [Entry.Label for Entry in Native.Faces]
    Natives += [Entry.Label for Entry in Native.Edges if Entry.Label]
    assert sorted(Labels, key=int) == sorted(Natives, key=int)
