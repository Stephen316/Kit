from __future__ import annotations

import importlib.util as ImportUtil
import os as OsLib
import sys as System
from functools import lru_cache as Memoize

from tools.TestShards.Reuse.Track.LocateFile import LocateFile


@Memoize(maxsize=None)
def ImportedFiles(
    RootText: str, NameText: str, Package: str, Members: tuple[str, ...], Level: int
) -> tuple[str, ...]:
    BaseName = (
        ImportUtil.resolve_name("." * Level + NameText, Package) if Level else NameText
    )
    NameParts = BaseName.split(".")
    ModNames = [".".join(NameParts[:Count]) for Count in range(1, len(NameParts) + 1)]
    ModNames.extend(f"{BaseName}.{Member}" for Member in Members)
    Located: list[str] = []
    for ModName in ModNames:
        FileText = getattr(System.modules.get(ModName), "__file__", None)
        if not isinstance(FileText, str):
            continue
        RelText = LocateFile(RootText, OsLib.path.abspath(FileText))
        if RelText:
            Located.append(RelText)
    return tuple(Located)
