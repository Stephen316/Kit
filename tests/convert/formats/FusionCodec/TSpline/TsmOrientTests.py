from pathlib import Path as FilePath

from pytest import mark as MarkTests
from pytest import raises as RaisesError

from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline
from convert.formats.Fusion.TSplineCodec.MakeClosedCage import MakeClosedCage
from convert.formats.Fusion.TSplineCodec.Model.CageOrientation import (
    CageOrientation,
)
from convert.formats.Fusion.TSplineCodec.Model.ControlGrip import ControlGrip
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline
from tests.convert.formats.FusionCodec.TSpline.OrientState import OrientState

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
KBoxFaces = (
    (2, 0, 1, 3),
    (0, 2, 6, 4),
    (0, 4, 5, 1),
    (4, 6, 7, 5),
    (5, 7, 3, 1),
    (6, 2, 3, 7),
)
KBoxSpokes = (1, 5, 3, 7, 5, 1, 7, 3)
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
KNativeBox = (
    FilePath(__file__).resolve().parents[5]
    / "re/Fusion/LocalOracle/TSplineCodec/Evaluation/NativePrimitiveInitial.tsm"
)


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
