# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import dataclass as Dataclass

from convert.formats.Fusion.RecordSpan import RecordSpan
from interchange.assembly.ComponentInstance import ComponentInst


# neutral membership and bounded native records are checked against one another
@Dataclass(frozen=True, slots=True)
class AsmEditIndex:
    Owners: dict[int, RecordSpan]
    ComponentSpans: dict[int, RecordSpan]
    Components: dict[str, int]
    Occurrences: dict[int, ComponentInst]
