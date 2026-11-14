from pathlib import Path as FilePath
from zipfile import ZipFile

KRepoRoot = FilePath(__file__).resolve().parents[6]


def NativeGeometry(
    FileName: str = "re/Fusion/Study/pipemodes-87cfa7d8d82b/triangular.f3d",
) -> bytes:
    Source = KRepoRoot / FileName
    with ZipFile(Source) as Archive:
        Names = tuple(
            NameValue for NameValue in Archive.namelist() if NameValue.endswith(".smb")
        )
        if len(Names) != 1:
            raise ValueError("Expected one controlled current geometry member")
        return Archive.read(Names[0])
