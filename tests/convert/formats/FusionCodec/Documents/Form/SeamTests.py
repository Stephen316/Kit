from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CappedLayout import (
    CappedLayout,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CappedShape import (
    CappedShape,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.ConvertForm import (
    ConvertForm,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormBody,
    FormUse,
    FormWindow,
)
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline
from tests.convert.formats.FusionCodec.Documents.Form.CappedCages import (
    MakeSurface,
    RingCreases,
    TorusParts,
)
from tests.convert.formats.FusionCodec.Documents.Form.ReadFormFile import (
    ReadFormFile,
)

KUseEnd = tuple[tuple[float, ...], tuple[float, ...], int]
KParallel = {Major * 6 for Major in range(8)}
KMeridian = set(range(6))
KBottom = [FormWindow(Index * 6, 0.0, 1.0, 0.0, 0.0) for Index in range(8)]
KUpper = [FormWindow(Index * 6 + 5, 0.0, 1.0, 1.0, 1.0) for Index in range(8)]
KLeft = [FormWindow(Index, 0.0, 0.0, 0.0, 1.0) for Index in range(6)]
KRight = [FormWindow(42 + Index, 1.0, 1.0, 0.0, 1.0) for Index in range(6)]
KSeamUses = [(0, False), (1, False), (0, True), (1, True)]
KSlicesCage = (
    "re/Fusion/LocalOracle/FormDocuments/General/HeldOut/HeldCreaseSlices.tsm",
    "f9a75c5dd0b7454b53fa0b57dcd631fb0733c71640c5f7b157aeedfffdc39077",
)
KSlicesEdges = [
    (0, 1, "tangent"),
    (2, 1, "unknown"),
    (3, 2, "unknown"),
    (1, 3, "unknown"),
    (4, 0, "unknown"),
    (5, 4, "unknown"),
    (0, 5, "unknown"),
    (1, 0, "tangent"),
]
KSlicesUses = [
    [(0, False), (1, True), (2, True), (3, True)]
    + [(0, True), (4, True), (5, True), (6, True)],
    [(7, False), (6, False), (5, False), (4, False)]
    + [(7, True), (3, False), (2, False), (1, False)],
]


def CreasedTorus(Rings: list[set[int]]) -> TsplineSurface:
    Plain = MakeSurface(TorusParts((8, 6)))
    return ReplaceValue(Plain, Creases=RingCreases(Plain, Rings))


def UseEnd(UseValue: FormUse) -> KUseEnd:
    Poles = UseValue.Pcurve.Poles
    return (Poles[0], Poles[-1], UseValue.Pcurve.Closure)


def ShapeEnds(Shape: CappedShape) -> list[KUseEnd]:
    return [UseEnd(UseValue) for UseValue in Shape.Faces[0].Uses]


def TestRingSeam() -> None:
    Shape = CappedLayout(CreasedTorus([KParallel]))
    Ranges = [(Entry.Lower, Entry.Upper, Entry.Closure) for Entry in Shape.Curves]
    assert Ranges == [(0.0, 8.0, 2), (0.0, 6.0, 1)]
    UseList = Shape.Faces[0].Uses
    assert [(Entry.EdgeIndex, Entry.Reversed) for Entry in UseList] == KSeamUses
    assert ShapeEnds(Shape) == [
        ((0.0, 0.0), (8.0, 0.0), 2),
        ((0.0, 0.0), (0.0, 6.0), 1),
        ((0.0, 0.0), (8.0, 0.0), 2),
        ((8.0, 0.0), (8.0, 6.0), 1),
    ]
    assert [list(Entry.Windows) for Entry in Shape.Edges] == [
        KBottom * 2,
        KLeft + KRight,
    ]


def TestCrossSeams() -> None:
    Shape = CappedLayout(CreasedTorus([KParallel, KMeridian]))
    Ranges = [(Entry.Lower, Entry.Upper, Entry.Closure) for Entry in Shape.Curves]
    assert Ranges == [(0.0, 8.0, 1), (0.0, 6.0, 1)]
    UseList = Shape.Faces[0].Uses
    assert [(Entry.EdgeIndex, Entry.Reversed) for Entry in UseList] == KSeamUses
    assert ShapeEnds(Shape) == [
        ((0.0, 0.0), (8.0, 0.0), 1),
        ((0.0, 0.0), (0.0, 6.0), 1),
        ((0.0, 6.0), (8.0, 6.0), 1),
        ((8.0, 0.0), (8.0, 6.0), 1),
    ]
    assert [list(Entry.Windows) for Entry in Shape.Edges] == [
        KBottom + KUpper,
        KLeft + KRight,
    ]


def BodyUses(BodyValue: FormBody) -> list[list[tuple[int, bool]]]:
    return [
        [(Entry.EdgeIndex, Entry.Reversed) for Entry in FaceValue.Uses]
        for FaceValue in BodyValue.Faces
    ]


def TestSlicePieces() -> None:
    BodyValue = ConvertForm(ReadTspline(ReadFormFile(*KSlicesCage)))
    EdgeHeads = [
        (Entry.StartVertex, Entry.EndVertex, Entry.Convexity)
        for Entry in BodyValue.Edges
    ]
    assert EdgeHeads == KSlicesEdges
    assert BodyUses(BodyValue) == KSlicesUses
    Pieces = [Entry.Bounds for Entry in BodyValue.Edges[1:4]]
    assert all(Bounds is not None for Bounds in Pieces)
