# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import dataclass as Dataclass

from convert.formats.Fusion.Assembly.NativeComponent import NativeComponent


# component backlinks qualify both its occurrence collection and the unique root
@Dataclass(frozen=True, slots=True)
class ComponentEntry:
    Component: NativeComponent
    CollectionId: int
    RootOccurrence: int | None
