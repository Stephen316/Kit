# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.Profiles.Trimmed.LinePartitions import FindLineCuts
from convert.formats.Fusion.Profiles.Trimmed.LineTopology import ReadLineGraph
from convert.formats.Fusion.Profiles.Trimmed.TrimPortion import TrimPortion
from convert.formats.Fusion.Profiles.Trimmed.TrimSelectors import TrimMember
from interchange.geometry.models.Sketch import SketchEntity


# finite line portion ordinals increase from the explicit native start endpoint
def ReadLineTrim(
    Lines: tuple[SketchEntity, ...], Members: tuple[TrimMember, ...]
) -> tuple[TrimPortion, ...]:
    if len(Members) != 4 or len({Entity.id for Entity, _ in Members}) != 4:
        raise ValueError("Unsupported Fusion trimmed line membership")
    Cuts = FindLineCuts(ReadLineGraph(Lines))
    Portions = []
    for Entity, Selector in Members:
        Ordinal, Count = Selector[4:6]
        Fractions = Cuts[Entity.id]
        if Ordinal not in (1, 2) or Count != 2 or len(Fractions) != 1:
            raise ValueError("Fusion line trim selector disagrees with source cuts")
        Bounds = (0.0, Fractions[0], 1.0)
        Portions.append(
            TrimPortion(Entity.id, Bounds[Ordinal - 1], Bounds[Ordinal], Selector)
        )
    return tuple(Portions)
