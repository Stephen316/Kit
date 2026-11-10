# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import dataclass as Dataclass

from convert.formats.Fusion.Assembly.ComponentEntry import ComponentEntry
from convert.formats.Fusion.Assembly.OccurRecord import OccurRecord


# native ownership records stay separate until their reciprocal links agree
@Dataclass(frozen=True, slots=True)
class AssemblyIndex:
    Components: dict[int, ComponentEntry]
    Occurrences: dict[int, OccurRecord]
    Collections: dict[int, tuple[int, tuple[int, ...]]]
