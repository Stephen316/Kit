# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations
from dataclasses import dataclass as DataClass
from pathlib import Path as PathInfo
from typing import Any as AnyInfo


# needed to keep reverse engineering responsibilities isolated and maintainable
@DataClass(frozen=True, slots=True)
class ProgramData:
    VariantPath: str
    SourcePath: PathInfo
    SourceText: str
    OwnerName: str
    OpsName: str
    Streams: tuple[tuple[str, tuple[tuple[int, int, str, str, AnyInfo], ...]], ...]
    PublicNames: tuple[str, ...]
    ByteStats: tuple[tuple[str, int, str], ...]


# needed to keep reverse engineering responsibilities isolated and maintainable
@DataClass(frozen=True, slots=True)
class MethodData:
    GroupPath: str
    OwnerSites: tuple[tuple[object, str], ...]
    StreamOps: tuple[tuple[str, tuple[tuple[int, int, object, str, AnyInfo], ...]], ...]


# needed to keep reverse engineering responsibilities isolated and maintainable
KHeaderText = "# SPDX-License-Identifier: MIT\n# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt\n"

# needed to keep reverse engineering responsibilities isolated and maintainable
KOwnerNames = ("FieldOwners", "KFieldOwners")

# needed to keep reverse engineering responsibilities isolated and maintainable
KOperationNames = (
    "StreamPrograms",
    "ConfigOps",
    "KConfigOps",
    "ResolvedOps",
    "KResolvedOps",
    "AnnotationOps",
)

# needed to keep reverse engineering responsibilities isolated and maintainable
KSingleStreams = {
    "ConfigOps": "Configuration",
    "KConfigOps": "Configuration",
    "ResolvedOps": "ResolvedFeatures",
    "KResolvedOps": "ResolvedFeatures",
    "AnnotationOps": "AnnotationManager",
}
