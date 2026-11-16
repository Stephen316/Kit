from pathlib import Path as FilePath
from zipfile import ZIP_DEFLATED as KDeflateZip, ZipFile

from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal


# shared journal archive setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def JournalArchive(Target: FilePath, Payload: bytes) -> JournalModel:
    with ZipFile(Target, "w", compression=KDeflateZip) as Archive:
        Archive.writestr(
            "FusionAssetName[Active]/Breps.BlobParts/BREP.semantic.smbh", Payload
        )
    with ZipFile(Target) as Archive:
        return ReadJournal(Archive.read(Archive.namelist()[0]))
