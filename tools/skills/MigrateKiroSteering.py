# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

import sys as System
from pathlib import Path as FilePath

# repository insertion keeps package imports available when this file runs directly
KEntryRoot = FilePath(__file__).resolve().parents[2]

if str(KEntryRoot) not in System.path:
    System.path.insert(0, str(KEntryRoot))

from tools.skills.SkillCompat import GetLegacyAttr, KLegacyApi
from tools.skills.SkillCli import MainRun


# legacy attribute resolution avoids forcing existing callers through an immediate migration
def __getattr__(NameText: str) -> object:
    return GetLegacyAttr(NameText)


# legacy discovery remains visible so introspection matches supported compatibility behavior
def __dir__() -> list[str]:
    return sorted(set(globals()) | set(KLegacyApi))


if __name__ == "__main__":
    raise SystemExit(MainRun())
