from pytest import mark as MarkTests, raises as RaisesError

from convert.Formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from convert.Formats.Fusion.MeshCodec.ReadParaMesh import ReadParaMesh
from tests.Convert.Formats.FusionCodec.Mesh.MutateMesh import MutateMesh
from tests.Convert.Formats.FusionCodec.Mesh.ReadMeshCases import ReadMeshCases
from tests.Convert.Formats.FusionCodec.Mesh.ReadMeshFile import ReadMeshFile
from tests.Convert.Formats.FusionCodec.Mesh.ReplaceMember import ReplaceMember


# the mesh guard contract needs boundary coverage so stored document relationships remain consistent
@MarkTests.parametrize(
    "KindValue, Message",
    (
        ("allocation", "decoded allocation exceeds"),
        ("override", "missing corner"),
        ("facegroup", "undeclared face group"),
        ("edge", "outside triangle topology"),
        ("registry", "stream references"),
    ),
)
def TestMeshGuard(KindValue: str, Message: str) -> None:
    CaseValue = ReadMeshCases()[0]
    Model = ReadParaMesh(ReadMeshFile(CaseValue))
    ArchiveData = ReplaceMember(CaseValue, MutateMesh(Model, KindValue))
    with OpenFusionZip(ArchiveData) as Archive:
        Payload = Archive.ReadMember(CaseValue["Member"], 64 * 1024 * 1024)
    with RaisesError(ValueError, match=Message):
        _ = ReadParaMesh(Payload)
