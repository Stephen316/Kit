from pathlib import Path as FilePath
from sys import version_info as PythonVersion

from pytest import mark as MarkTests, raises as RaisesError

from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.convert.formats.FusionCodec.Documents.Mesh.MutateMeshDoc import MutateMeshDoc
from tests.convert.formats.FusionCodec.Mesh.ReadMeshCases import ReadMeshCases
from tests.convert.formats.FusionCodec.Mesh.ReadMeshFile import KRootPath


@MarkTests.parametrize(
    "Variant, Message",
    (
        ("missing", "missing component"),
        ("uuid", "UUID disagrees"),
        ("orphan", "all current and historical geometries"),
        ("reciprocal", "not reciprocal"),
        ("body", "local Design entity reference"),
        ("stale", "up-to-date component"),
    ),
)
@MarkTests.skipif(
    PythonVersion < (3, 14), reason="native mesh archive requires ZIP Zstandard"
)
def TestMeshLinks(TmpPath: FilePath, Variant: str, Message: str) -> None:
    Source = KRootPath / ReadMeshCases()[0]["Archive"]
    Target = TmpPath / "BrokenMesh.f3d"
    _ = Target.write_bytes(MutateMeshDoc(Source.read_bytes(), Variant))
    with RaisesError(ValueError, match=Message):
        _ = ReadDocument(Target.read_bytes())
