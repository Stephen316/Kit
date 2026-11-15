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

# the use end shape must stay shared so native document reconstruction uses one contract for compatible values
KUseEnd = tuple[tuple[float, ...], tuple[float, ...], int]

# the parallel cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KParallel = {Major * 6 for Major in range(8)}

# the meridian cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KMeridian = set(range(6))

# the bottom cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KBottom = [FormWindow(Index * 6, 0.0, 1.0, 0.0, 0.0) for Index in range(8)]

# the upper cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KUpper = [FormWindow(Index * 6 + 5, 0.0, 1.0, 1.0, 1.0) for Index in range(8)]

# the left cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KLeft = [FormWindow(Index, 0.0, 0.0, 0.0, 1.0) for Index in range(6)]

# the right cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KRight = [FormWindow(42 + Index, 1.0, 1.0, 0.0, 1.0) for Index in range(6)]

# the seam uses cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KSeamUses = [(0, False), (1, False), (0, True), (1, True)]

# the slices cage cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KSlicesCage = (
    "re/Fusion/LocalOracle/FormDocuments/General/HeldOut/HeldCreaseSlices.tsm",
    "f9a75c5dd0b7454b53fa0b57dcd631fb0733c71640c5f7b157aeedfffdc39077",
)

# the slices edges cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
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

# the slices uses cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KSlicesUses = [
    [(0, False), (1, True), (2, True), (3, True)]
    + [(0, True), (4, True), (5, True), (6, True)],
    [(7, False), (6, False), (5, False), (4, False)]
    + [(7, True), (3, False), (2, False), (1, False)],
]


# shared creased torus setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def CreasedTorus(Rings: list[set[int]]) -> TsplineSurface:
    Plain = MakeSurface(TorusParts((8, 6)))
    return ReplaceValue(Plain, Creases=RingCreases(Plain, Rings))


# shared use end setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def UseEnd(UseValue: FormUse) -> KUseEnd:
    Poles = UseValue.Pcurve.Poles
    return (Poles[0], Poles[-1], UseValue.Pcurve.Closure)


# shared shape ends setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def ShapeEnds(Shape: CappedShape) -> list[KUseEnd]:
    return [UseEnd(UseValue) for UseValue in Shape.Faces[0].Uses]


# the ring seam contract needs boundary coverage so stored document relationships remain consistent
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


# the cross seams contract needs boundary coverage so stored document relationships remain consistent
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


# shared body uses setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def BodyUses(BodyValue: FormBody) -> list[list[tuple[int, bool]]]:
    return [
        [(Entry.EdgeIndex, Entry.Reversed) for Entry in FaceValue.Uses]
        for FaceValue in BodyValue.Faces
    ]


# the slice pieces contract needs boundary coverage so stored document relationships remain consistent
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
