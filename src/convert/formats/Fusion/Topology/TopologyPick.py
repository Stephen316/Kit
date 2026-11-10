# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


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
