# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import dataclass as Dataclass

from interchange.geometry.models.Selection import SelectPathElem


# a qualified pick carries its native source chain and any neutral path it resolves
@Dataclass(frozen=True, slots=True)
class RevolvePick:
    ObjectId: int
    Descriptor: int
    Terminal: int
    PathElems: tuple[SelectPathElem, ...] = ()
    DependencyId: str | None = None
