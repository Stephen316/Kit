from pathlib import Path as FilePath
from zipfile import ZipFile

from tests.Convert.Runtime.RuntimeRules import KNativeSuffixes
from tests.Convert.Runtime.WheelMetadata import CheckWheelMeta


# wheel extraction verifies portability before isolated execution consumes the artifact
def ExtractWheel(WheelPath: FilePath, InstallRoot: FilePath) -> None:
    with ZipFile(WheelPath) as ArchiveData:
        EntryNames = tuple(ArchiveData.namelist())
        assert not any(
            NameValue.casefold().endswith(KNativeSuffixes) for NameValue in EntryNames
        )
        CheckWheelMeta(ArchiveData, EntryNames)
        ArchiveData.extractall(InstallRoot)
