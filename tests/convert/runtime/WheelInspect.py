# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from pathlib import Path as FilePath
from zipfile import ZipFile

from tests.convert.runtime.RuntimeRules import KNativeSuffixes
from tests.convert.runtime.WheelMetadata import CheckWheelMeta


# wheel extraction verifies portability before isolated execution consumes the artifact
def ExtractWheel(WheelPath: FilePath, InstallRoot: FilePath) -> None:
    with ZipFile(WheelPath) as ArchiveData:
        EntryNames = tuple(ArchiveData.namelist())
        assert not any(
            NameValue.casefold().endswith(KNativeSuffixes) for NameValue in EntryNames
        )
        CheckWheelMeta(ArchiveData, EntryNames)
        ArchiveData.extractall(InstallRoot)
