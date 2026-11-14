from pathlib import Path as FilePath
from sys import version_info as PythonVersion

from pytest import approx as ApproxValue, mark as TestMarks

from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.formats.Fusion.BrepCodec.Journal.Round.SphereNode import SphereNode
from convert.formats.Fusion.BrepCodec.Journal.Round.TorusNode import TorusNode
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.EmitGeometry import EmitGeometry
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.PermuteGeometry import (
    PermuteGeometry,
)
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry
from tests.convert.formats.FusionCodec.Brep.GeometryState.GeometryArchive import (
    GeometryArchive,
)
from tests.convert.formats.FusionCodec.Brep.Round.NativeRound import NativeRound


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize("Label", ("Sphere", "Torus", "TiltedTorus", "PlacedTorus"))
@TestMarks.parametrize("Reordered", (False, True))
def TestRoundSmb(TmpPath: FilePath, Label: str, Reordered: bool) -> None:
    Original = NativeRound(Label)
    Native = ReadGeometry(Original)
    assert len(Native.Entities) == 8
    Model = (
        PermuteGeometry(Native, (0, 1, *reversed(range(2, 8)))) if Reordered else Native
    )
    Payload = EmitGeometry(Model)
    assert (Payload != Original) == Reordered
    Parsed = GeometryArchive(TmpPath / "RoundGeometry.zip", Payload)
    assert Parsed == Model
    assert not any(
        isinstance(Value, (EdgeNode, VertexNode)) for Value in Parsed.Entities
    )
    Faces = tuple(Value for Value in Parsed.Entities if isinstance(Value, FaceNode))
    assert len(Faces) == 1 and Faces[0].FirstLoop == -1
    Surface = Parsed.Entities[Faces[0].Surface]
    assert isinstance(Surface, (SphereNode, TorusNode))
    assert Surface.CenterCm == ApproxValue(
        (0.0, 0.0, 0.0) if Label == "Torus" else (1.1, -0.7, 0.5)
    )
    if isinstance(Surface, SphereNode):
        assert Surface.RadiusCm == ApproxValue(1.7)
    else:
        assert Surface.MajorRadiusCm == ApproxValue(2.3)
        assert Surface.MinorRadiusCm == ApproxValue(0.7)
