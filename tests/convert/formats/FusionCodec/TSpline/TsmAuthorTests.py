from pathlib import Path as FilePath

from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline
from convert.formats.Fusion.TSplineCodec.MakeClosedCage import MakeClosedCage
from convert.formats.Fusion.TSplineCodec.Model.ControlGrip import ControlGrip
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline


def TestTsmAuthor(TmpPath: FilePath) -> None:
    Vertices = tuple(
        ControlGrip(*Value)
        for Value in (
            (0.0, 0.0, 0.0),
            (1.7, 0.0, 0.0),
            (1.7, 2.3, 0.0),
            (0.0, 2.3, 0.0),
            (0.0, 0.0, 3.1),
            (1.7, 0.0, 3.1),
            (1.7, 2.3, 3.1),
            (0.0, 2.3, 3.1),
        )
    )
    Faces = (
        (0, 3, 2, 1),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (1, 2, 6, 5),
        (2, 3, 7, 6),
        (3, 0, 4, 7),
    )
    Authored = MakeClosedCage(Vertices, Faces)
    OutputPath = TmpPath / "Independent.tsm"
    _ = OutputPath.write_bytes(EmitTspline(Authored))
    Decoded = ReadTspline(OutputPath.read_bytes())
    assert Decoded == Authored
    assert Decoded.Grips == Vertices
    assert len(Decoded.Topology.Faces) == 6
    assert len(Decoded.Topology.Edges) == 12
    assert len(Decoded.Topology.Vertices) == 8
    assert all(Value.FaceIndex >= 0 for Value in Decoded.Topology.Links)
