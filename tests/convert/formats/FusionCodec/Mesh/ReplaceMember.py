from io import BytesIO as ByteBuffer
from zipfile import ZIP_STORED as KStoredMode, ZipFile as ZipArchive

from convert.formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from tests.convert.formats.FusionCodec.Mesh.MeshCase import MeshCase
from tests.convert.formats.FusionCodec.Mesh.ReadMeshFile import KRootPath


def ReplaceMember(CaseValue: MeshCase, Payload: bytes) -> bytes:
    Source = (KRootPath / CaseValue["Archive"]).read_bytes()
    Output = ByteBuffer()
    with OpenFusionZip(Source) as Archive:
        with ZipArchive(Output, "w", compression=KStoredMode) as Target:
            for Entry in Archive.Members:
                if Entry.IsDirectory:
                    Target.writestr(Entry.Name, b"")
                    continue
                DataValue = (
                    Payload
                    if Entry.Name == CaseValue["Member"]
                    else Archive.ReadMember(Entry.Name, 64 * 1024 * 1024)
                )
                Target.writestr(Entry.Name, DataValue)
    return Output.getvalue()
