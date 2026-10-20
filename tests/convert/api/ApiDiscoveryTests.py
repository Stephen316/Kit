# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
import sys as SysModule

import pytest as Pytest

from convert.adapters import AdapterDiscoveryError
from convert.adapters import AdapterRegistry


# empty format packages must fail because silent omission would make catalog coverage misleading
def CheckEmptyPack(TmpPath: FilePath, MonkeyPatch: Pytest.MonkeyPatch) -> None:
    PackageName = f"kit_empty_{TmpPath.name.replace('-', '_')}"
    PackagePath = TmpPath / PackageName
    FormatPath = PackagePath / "empty"
    FormatPath.mkdir(parents=True)
    _ = (PackagePath / "__init__.py").write_text("", encoding="utf-8")
    _ = (FormatPath / "__init__.py").write_text("__all__ = []\n", encoding="utf-8")
    MonkeyPatch.setattr(SysModule, "path", [str(TmpPath), *SysModule.path])
    with Pytest.raises(AdapterDiscoveryError, match="contains no adapter"):
        _ = AdapterRegistry().introspect(PackageName)


# discovery must inspect package contents because export lists are optional implementation details
def CheckHiddenPack(TmpPath: FilePath, MonkeyPatch: Pytest.MonkeyPatch) -> None:
    PackageName = f"kit_hidden_{TmpPath.name.replace('-', '_')}"
    PackagePath = TmpPath / PackageName
    FormatPath = PackagePath / "hidden"
    FormatPath.mkdir(parents=True)
    _ = (PackagePath / "__init__.py").write_text("", encoding="utf-8")
    _ = (FormatPath / "__init__.py").write_text(
        "from convert.adapters.json.Adapter import JsonAdapter as _JsonAdapter\n"
        + "class HiddenAdapter(_JsonAdapter):\n    discovered = True\n"
        + "__all__ = []\n",
        encoding="utf-8",
    )
    MonkeyPatch.setattr(SysModule, "path", [str(TmpPath), *SysModule.path])
    RegistryData = AdapterRegistry()
    assert RegistryData.introspect(PackageName) == ("interchange.json",)


# single module adapters must remain discoverable because package folders are not required
def CheckSingleMod(TmpPath: FilePath, MonkeyPatch: Pytest.MonkeyPatch) -> None:
    PackageName = f"kit_module_{TmpPath.name.replace('-', '_')}"
    PackagePath = TmpPath / PackageName
    PackagePath.mkdir()
    _ = (PackagePath / "__init__.py").write_text("", encoding="utf-8")
    _ = (PackagePath / "single.py").write_text(
        "from convert.adapters.json.Adapter import JsonAdapter as _JsonAdapter\n"
        + "class SingleAdapter(_JsonAdapter):\n    discovered = True\n",
        encoding="utf-8",
    )
    MonkeyPatch.setattr(SysModule, "path", [str(TmpPath), *SysModule.path])
    RegistryData = AdapterRegistry()
    assert RegistryData.introspect(PackageName) == ("interchange.json",)
