from io import BytesIO as ByteBuffer
from zipfile import ZIP_STORED as KStoredMode, ZipFile as ZipArchive

from convert.formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from convert.formats.Fusion.MeshCodec.EmitParaMesh import EmitParaMesh
from convert.formats.Fusion.MeshCodec.Geometry.CornerNormal import CornerNormal
from convert.formats.Fusion.MeshCodec.ReadParaMesh import ReadParaMesh
from tests.convert.formats.FusionCodec.Mesh.AuthoredMesh import AuthoredMesh


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
