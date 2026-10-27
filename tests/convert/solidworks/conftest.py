# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from pathlib import Path as FilePath
from tempfile import TemporaryDirectory
from typing import Iterator

import pytest as PytestLib


# supplies compliant temporary paths so test signatures remain valid under naming steering
@PytestLib.fixture
def TmpPath() -> Iterator[FilePath]:
    with TemporaryDirectory(prefix="KitSolidworks") as TempName:
        yield FilePath(TempName)
