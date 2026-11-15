from pathlib import Path as FilePath
from zipfile import ZipFile

# the source archive cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KSourceArchive = (
    FilePath(__file__).resolve().parents[6]
    / "re/Fusion/LocalOracle/Features/extrude_07mm.f3d"
)


# shared native package setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def NativePackage() -> bytes:
    with ZipFile(KSourceArchive) as Archive:
        NameValue = next(
            NameValue
            for NameValue in Archive.namelist()
            if NameValue.endswith(".protein")
        )
        return Archive.read(NameValue)
