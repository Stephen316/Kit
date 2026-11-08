# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import tau as FullTurn

from convert.formats.Fusion.Profiles.Trimmed.CirclePartitions import FindCircleCuts
from convert.formats.Fusion.Profiles.Trimmed.TrimPortion import TrimPortion
from convert.formats.Fusion.Profiles.Trimmed.TrimSelectors import TrimMember
from interchange.geometry.models.GeometryCurves import CircleGeometry

# only known circular selector pairs identify independently corroborated source intervals
KCircleSelectors = frozenset(((1, 2), (2, 2), (2, 4), (4, 4)))


# circle portion one crosses the reference seam and later portions follow increasing angle
def ReadCircleTrim(
    Circles: dict[int, CircleGeometry], Members: tuple[TrimMember, ...]
) -> tuple[TrimPortion, ...]:
    Selected: dict[int, list[tuple[int, int]]] = {}
    for _, Selector in Members:
        TagValue = Selector[1]
        PairValue = Selector[4], Selector[5]
        if PairValue not in KCircleSelectors:
            raise ValueError("Unsupported Fusion circular trim selector")
        Selected.setdefault(TagValue, []).append(PairValue)
    if Selected.keys() != Circles.keys() or any(
        len(Pairs) > 1 and sorted(Pairs) != [(2, 4), (4, 4)]
        for Pairs in Selected.values()
    ):
        raise ValueError("Unsupported Fusion circular trim source coverage")
    Cuts = {
        TagValue: FindCircleCuts(
            Source,
            tuple(Other for OtherTag, Other in Circles.items() if OtherTag != TagValue),
        )
        for TagValue, Source in Circles.items()
    }
    Portions = []
    for Entity, Selector in Members:
        Angles = Cuts[Selector[1]]
        Ordinal, Count = Selector[4:6]
        if Count != len(Angles):
            raise ValueError(
                "Fusion circular trim selector count disagrees with source cuts"
            )
        if Ordinal == 1:
            Lower, Upper = Angles[-1], Angles[0] + FullTurn
        else:
            Lower, Upper = Angles[Ordinal - 2], Angles[Ordinal - 1]
        Portions.append(TrimPortion(Entity.id, Lower, Upper, Selector))
    return tuple(Portions)
