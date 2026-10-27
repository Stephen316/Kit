# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations


# source casing stays derived because one mapping rule prevents silent skill inventory drift
def GetSourceStem(SkillName: str) -> str:
    return "".join(NamePart.capitalize() for NamePart in SkillName.split("-"))
