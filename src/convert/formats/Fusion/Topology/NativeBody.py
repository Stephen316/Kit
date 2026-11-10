# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import dataclass as Dataclass


# native bodies retain the saved identity and typed label evidence independently of geometry
@Dataclass(frozen=True, slots=True)
class NativeBody:
    ObjectId: int
    ComponentId: int
    CollectionId: int
    Name: str
    NameHelperId: int | None
