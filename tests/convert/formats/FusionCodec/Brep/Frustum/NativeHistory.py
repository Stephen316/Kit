from pathlib import Path as FilePath
from zipfile import ZipFile

# repo root needs a stable location so native document reconstruction resolves inputs independently of the caller working directory
KRepoRoot = FilePath(__file__).resolve().parents[6]


# shared native history setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def NativeHistory(RelativePath: str) -> bytes:
    with ZipFile(KRepoRoot / RelativePath) as Archive:
        Names = tuple(
            NameValue for NameValue in Archive.namelist() if NameValue.endswith(".smbh")
        )
        if len(Names) != 1:
            raise ValueError("Native frustum fixture must contain one history stream")
        return Archive.read(Names[0])
