from pathlib import Path as FilePath
from zipfile import ZIP_DEFLATED as KDeflateZip, ZipFile

from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry


# shared geometry archive setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def GeometryArchive(Target: FilePath, Payload: bytes) -> GeometryState:
    with ZipFile(Target, "w", compression=KDeflateZip) as Archive:
        Archive.writestr("Breps.BlobParts/BREP.current.smb", Payload)
    with ZipFile(Target) as Archive:
        return ReadGeometry(Archive.read(Archive.namelist()[0]))
