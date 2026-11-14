from pathlib import Path as FilePath
from zipfile import ZipFile

KRepoRoot = FilePath(__file__).resolve().parents[6]


def NativeHistory(RelativePath: str) -> bytes:
    with ZipFile(KRepoRoot / RelativePath) as Archive:
        Names = tuple(
            NameValue for NameValue in Archive.namelist() if NameValue.endswith(".smbh")
        )
        if len(Names) != 1:
            raise ValueError("Native frustum fixture must contain one history stream")
        return Archive.read(Names[0])
