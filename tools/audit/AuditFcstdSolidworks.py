# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

import sys as System
from pathlib import Path as FilePath

# repository insertion keeps package imports available when this file runs directly
KEntryRoot = FilePath(__file__).resolve().parents[2]

if str(KEntryRoot) not in System.path:
    System.path.insert(0, str(KEntryRoot))

from tools.audit.FcstdCompat import GetLegacyAttr, KLegacyApi
from tools.audit.FcstdCli import MainRun


# compatibility resolution prevents module restructuring from breaking existing audit automation
def __getattr__(NameText: str) -> object:
    return GetLegacyAttr(NameText)


# compatibility discovery keeps supported legacy names visible to introspection tools
def __dir__() -> list[str]:
    return sorted(set(globals()) | set(KLegacyApi))


if __name__ == "__main__":
    raise SystemExit(MainRun())
