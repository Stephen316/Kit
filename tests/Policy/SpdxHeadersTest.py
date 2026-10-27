# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from importlib.util import module_from_spec as BuildModule
from importlib.util import spec_from_file_location as BuildSpec
from pathlib import Path as FilePath
import sys as System
from types import ModuleType as ModuleKind
from typing import Callable as CallType
from typing import Protocol
from typing import cast as TypeCast


# dynamic guard loading needs concrete signatures so policy tests retain strict call validation
class GuardContract(Protocol):
    CheckFile: CallType[[FilePath, list[str], FilePath], tuple[bool, str]]
    CheckWorktree: CallType[[FilePath, str], tuple[FilePath | None, str]]
    GetDiffFiles: CallType[[str, str, FilePath], list[str]]
    IsCommit: CallType[[str, FilePath], bool]
    IsPathExempt: CallType[[str], bool]
    LoadCanon: CallType[[], list[str]]
    ParseDiff: CallType[[bytes], list[str]]
    RenderLines: CallType[[list[str], str], list[str]]
    RepairHeadMut: CallType[[FilePath, list[str], FilePath], tuple[bool, str]]
    ResolvePath: CallType[[FilePath, str], FilePath | None]
    StatLib: ModuleKind


# workflow code needs direct loading because its host directory is not a python package
def LoadGuard() -> GuardContract:
    GuardPath = (
        FilePath(__file__).parents[2] / ".github" / "scripts" / "VerifySpdxHeaders.py"
    )
    GuardSpec = BuildSpec("SpdxGuardTest", GuardPath)
    if GuardSpec is None or GuardSpec.loader is None:
        raise RuntimeError("spdx guard script cannot be loaded")
    GuardModule = BuildModule(GuardSpec)
    OriginalPaths = System.path.copy()
    try:
        System.path.insert(0, str(GuardPath.parent))
        GuardSpec.loader.exec_module(GuardModule)
        return TypeCast(GuardContract, GuardModule)
    finally:
        System.path[:] = OriginalPaths
