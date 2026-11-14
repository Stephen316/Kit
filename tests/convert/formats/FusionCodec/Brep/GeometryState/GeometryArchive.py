from pathlib import Path as FilePath
from zipfile import ZIP_DEFLATED as KDeflateZip, ZipFile

from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry


def GeometryArchive(Target: FilePath, Payload: bytes) -> GeometryState:
    with ZipFile(Target, "w", compression=KDeflateZip) as Archive:
        Archive.writestr("Breps.BlobParts/BREP.current.smb", Payload)
    with ZipFile(Target) as Archive:
        return ReadGeometry(Archive.read(Archive.namelist()[0]))
