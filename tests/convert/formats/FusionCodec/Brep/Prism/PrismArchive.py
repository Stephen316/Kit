from pathlib import Path as FilePath
from zipfile import ZipFile


# shared store prism setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def StorePrism(Target: FilePath, Payload: bytes) -> bytes:
    with ZipFile(Target, "w") as Archive:
        Archive.writestr("Breps.BlobParts/Solved.smbh", Payload)
    with ZipFile(Target) as Archive:
        return Archive.read("Breps.BlobParts/Solved.smbh")


# shared read prism file setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def ReadPrismFile(Source: FilePath) -> bytes:
    with ZipFile(Source) as Archive:
        Names = tuple(
            NameValue for NameValue in Archive.namelist() if NameValue.endswith(".smbh")
        )
        assert len(Names) == 1
        return Archive.read(Names[0])
