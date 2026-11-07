# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import dataclass as Dataclass


# a framed topology descriptor keeps the recipe and geometric witness independent
@Dataclass(frozen=True, slots=True)
class TopologyPick:
    RecipeId: int
    ContextId: int
    AnchorId: int
    HelperId: int
    SupportId: int
    Namespace: str
    EntityGuid: str
