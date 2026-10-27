# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from interchange.serialization.Wire import GetWireType

# registered types allow wire data to reconstruct concrete immutable records safely
KTypeRegistry: dict[str, type[object]] = {}


# explicit registration prevents deserialization from importing arbitrary classes by name
def RegisterTypes(*ClassTypes: type[object]) -> None:
    for ClassType in ClassTypes:
        WireType = GetWireType(ClassType)
        ExistingType = KTypeRegistry.get(WireType)
        if ExistingType is not None and ExistingType is not ClassType:
            raise ValueError(f"duplicate interchange type name {WireType!r}")
        KTypeRegistry[WireType] = ClassType
