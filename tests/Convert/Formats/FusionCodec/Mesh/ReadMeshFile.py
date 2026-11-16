from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath

from convert.Formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from tests.Convert.Formats.FusionCodec.Mesh.MeshCase import MeshCase

# root path needs a stable location so native document reconstruction resolves inputs independently of the caller working directory
KRootPath = FilePath(__file__).resolve().parents[5]


# shared read mesh file setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def ReadMeshFile(CaseValue: MeshCase) -> bytes:
    Source = (KRootPath / CaseValue["Archive"]).read_bytes()
    assert HashBytes(Source).hexdigest() == CaseValue["SourceHash"]
    with OpenFusionZip(Source) as Archive:
        Payload = Archive.ReadMember(CaseValue["Member"], 64 * 1024 * 1024)
    assert HashBytes(Payload).hexdigest() == CaseValue["PayloadHash"]
    return Payload
