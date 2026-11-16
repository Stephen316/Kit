from pathlib import Path as FilePath

from pytest import mark as MarkTests
from pytest import raises as RaisesError

from convert.Formats.Fusion.TSplineCodec.EmitTspline import EmitTspline
from convert.Formats.Fusion.TSplineCodec.MakeClosedCage import MakeClosedCage
from convert.Formats.Fusion.TSplineCodec.Model.CageOrientation import (
    CageOrientation,
)
from convert.Formats.Fusion.TSplineCodec.Model.ControlGrip import ControlGrip
from convert.Formats.Fusion.TSplineCodec.ReadTspline import ReadTspline
from tests.Convert.Formats.FusionCodec.TSpline.OrientState import OrientState

# the box points cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KBoxPoints = (
    (0.0, 0.0, 0.0),
    (0.0, 2.3, 0.0),
    (1.7, 0.0, 0.0),
    (1.7, 2.3, 0.0),
    (0.0, 0.0, 3.1),
    (0.0, 2.3, 3.1),
    (1.7, 0.0, 3.1),
    (1.7, 2.3, 3.1),
)

# the box faces cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KBoxFaces = (
    (2, 0, 1, 3),
    (0, 2, 6, 4),
    (0, 4, 5, 1),
    (4, 6, 7, 5),
    (5, 7, 3, 1),
    (6, 2, 3, 7),
)

# the box spokes cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KBoxSpokes = (1, 5, 3, 7, 5, 1, 7, 3)

# the box edges cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KBoxEdges = (
    (0, 2),
    (0, 1),
    (0, 4),
    (4, 6),
    (4, 5),
    (1, 3),
    (1, 5),
    (5, 7),
    (2, 3),
    (2, 6),
    (6, 7),
    (3, 7),
)

# the native box cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KNativeBox = (
    FilePath(__file__).resolve().parents[5]
    / "re/Fusion/LocalOracle/TSplineCodec/Evaluation/NativePrimitiveInitial.tsm"
)


# the tsm orient contract needs boundary coverage so stored document relationships remain consistent
def TestTsmOrient(TmpPath: FilePath) -> None:
    Grips = tuple(ControlGrip(*Value) for Value in KBoxPoints)
    Orientation = CageOrientation(KBoxSpokes, KBoxEdges)
    Authored = MakeClosedCage(Grips, KBoxFaces, Orientation=Orientation)
    OutputPath = TmpPath / "Oriented.tsm"
    _ = OutputPath.write_bytes(EmitTspline(Authored))
    Decoded = ReadTspline(OutputPath.read_bytes())
    Native = ReadTspline(KNativeBox.read_bytes())
    assert Decoded == Authored
    assert OrientState(Decoded) == OrientState(Native)
    Default = MakeClosedCage(Grips, KBoxFaces)
    assert OrientState(Default)[0] == OrientState(Native)[0]
    assert OrientState(Default)[2] == OrientState(Native)[2]
    assert OrientState(Default)[1] != OrientState(Native)[1]


# the orient deny contract needs boundary coverage so stored document relationships remain consistent
@MarkTests.parametrize("Fault", ("spoke", "count", "missing", "repeat"))
def TestOrientDeny(Fault: str) -> None:
    Grips = tuple(ControlGrip(*Value) for Value in KBoxPoints)
    Spokes: tuple[int, ...] = KBoxSpokes
    Edges: tuple[tuple[int, int], ...] = KBoxEdges
    if Fault == "spoke":
        Spokes = (7,) + KBoxSpokes[1:]
    if Fault == "count":
        Spokes = KBoxSpokes[:-1]
    if Fault == "missing":
        Edges = KBoxEdges[:-1]
    if Fault == "repeat":
        Edges = KBoxEdges + ((2, 0),)
    with RaisesError(ValueError):
        _ = MakeClosedCage(Grips, KBoxFaces, Orientation=CageOrientation(Spokes, Edges))
