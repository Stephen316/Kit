# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.Sketches.RulePrefix import ReadRulePrefix

# the primary core class encodes observed planar relation kinds without tool controllers
KGeomRuleGuid = "60403D47-0C49-49B0-BDE8-1679608164A2"


# separate lists retain native dependency order and semantic argument order
@MakeDataClass(frozen=True, slots=True)
class GeomRuleRecord:
    OwnerId: int
    CodeValue: int
    Dependencies: tuple[int, ...]
    Arguments: tuple[int, ...]


# full framing prevents a partial controller from posing as a planar relation
def ReadGeomRule(BodyValue: bytes) -> GeomRuleRecord:
    Cursor = MetaCursor(BodyValue)
    Dependencies, Slots, Props = ReadRulePrefix(Cursor)
    Genesis = Props.get("EntityGenesis")
    if type(Genesis) is not int or Props != {"EntityGenesis": 2} or any(Slots):
        raise ValueError(
            "Unsupported Fusion geometric relation attributes or dependency slots"
        )
    OwnerId = ReadNativeRef(Cursor)
    CodeValue = Cursor.ReadLong()
    if Cursor.ReadCount(16) != len(Dependencies):
        raise ValueError("Fusion geometric relation argument counts disagree")
    Arguments = tuple(ReadNativeRef(Cursor) for _ in Dependencies)
    if (
        len(set(Arguments)) != len(Arguments)
        or set(Arguments) != set(Dependencies)
        or Cursor.TakeBytes(1) != b"\0"
        or Cursor.Offset != len(BodyValue)
    ):
        raise ValueError("Invalid Fusion geometric relation argument copies or extent")
    return GeomRuleRecord(OwnerId, CodeValue, Dependencies, Arguments)
