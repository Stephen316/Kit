from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath

from convert.formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from tests.convert.formats.FusionCodec.Mesh.MeshCase import MeshCase

KRootPath = FilePath(__file__).resolve().parents[5]


def ReadMeshFile(CaseValue: MeshCase) -> bytes:
    Source = (KRootPath / CaseValue["Archive"]).read_bytes()
    assert HashBytes(Source).hexdigest() == CaseValue["SourceHash"]
    with OpenFusionZip(Source) as Archive:
        Payload = Archive.ReadMember(CaseValue["Member"], 64 * 1024 * 1024)
    assert HashBytes(Payload).hexdigest() == CaseValue["PayloadHash"]
    return Payload
