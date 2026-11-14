from pathlib import Path as FilePath
from sys import version_info as PythonVersion

from pytest import mark as TestMarks

from convert.formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.EmitGeometry import EmitGeometry
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.PermuteGeometry import (
    PermuteGeometry,
)
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry
from tests.convert.formats.FusionCodec.Brep.GeometryState.GeometryArchive import (
    GeometryArchive,
)
from tests.convert.formats.FusionCodec.Brep.GeometryState.NativeGeometry import (
    NativeGeometry,
)
from tests.convert.formats.FusionCodec.Brep.GeometryState.GeometryCases import (
    KGeometryCases,
)


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize("Reordered", (False, True))
@TestMarks.parametrize(
    "FileName,EntityCount,BodyCount,FaceCount,BoundaryCount", KGeometryCases
)
def TestGeometryZip(
    TmpPath: FilePath,
    Reordered: bool,
    FileName: str,
    EntityCount: int,
    BodyCount: int,
    FaceCount: int,
    BoundaryCount: int,
) -> None:
    Payload = NativeGeometry(FileName)
    Native = ReadGeometry(Payload)
    assert len(Native.Entities) == EntityCount
    assert Native.Header.RootCount == BodyCount + 1
    assert sum(isinstance(Value, BodyNode) for Value in Native.Entities) == BodyCount
    assert sum(isinstance(Value, FaceNode) for Value in Native.Entities) == FaceCount
    assert (
        sum(
            isinstance(Value, CoedgeNode) and Value.Partner == -1
            for Value in Native.Entities
        )
        == BoundaryCount
    )
    Model = (
        PermuteGeometry(
            Native,
            (*range(BodyCount + 1), *reversed(range(BodyCount + 1, EntityCount))),
        )
        if Reordered
        else Native
    )
    Encoded = EmitGeometry(Model)
    assert (Encoded != Payload) == Reordered
    Parsed = GeometryArchive(TmpPath / "CurrentState.zip", Encoded)
    assert Parsed == Model
