from io import BytesIO as ByteBuffer
from zipfile import ZIP_STORED as KStoredMode, ZipFile as ZipArchive

from convert.Formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from convert.Formats.Fusion.MeshCodec.EmitParaMesh import EmitParaMesh
from convert.Formats.Fusion.MeshCodec.Geometry.CornerNormal import CornerNormal
from convert.Formats.Fusion.MeshCodec.ReadParaMesh import ReadParaMesh
from tests.Convert.Formats.FusionCodec.Mesh.AuthoredMesh import AuthoredMesh


# the authored contract needs boundary coverage so stored document relationships remain consistent
def TestAuthored() -> None:
    Model = AuthoredMesh()
    Member = "FusionAssetName[Active]/ParaMeshGeometry.BlobParts/ParaMeshGeometry.authored.paramesh"
    Buffer = ByteBuffer()
    with ZipArchive(Buffer, "w", compression=KStoredMode) as Archive:
        Archive.writestr(Member, EmitParaMesh(Model))
    with OpenFusionZip(Buffer.getvalue()) as Container:
        Actual = ReadParaMesh(Container.ReadMember(Member, 64 * 1024 * 1024))
    assert Actual == Model
    assert CornerNormal(Actual, 0) == (0.0, 0.0, 1.0)
    assert Actual.TerminalWord == 47
