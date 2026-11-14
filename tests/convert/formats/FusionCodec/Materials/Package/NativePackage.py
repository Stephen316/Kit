from pathlib import Path as FilePath
from zipfile import ZipFile

KSourceArchive = (
    FilePath(__file__).resolve().parents[6]
    / "re/Fusion/LocalOracle/Features/extrude_07mm.f3d"
)


def NativePackage() -> bytes:
    with ZipFile(KSourceArchive) as Archive:
        NameValue = next(
            NameValue
            for NameValue in Archive.namelist()
            if NameValue.endswith(".protein")
        )
        return Archive.read(NameValue)
