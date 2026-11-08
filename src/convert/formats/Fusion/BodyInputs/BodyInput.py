# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as Dataclass

from interchange.enums.EnumFeatures import BooleanOp


# native source records retain their ordered roles before resolving historical bodies
@Dataclass(frozen=True, slots=True)
class BodyInput:
    Role: str
    ProxyId: int
    DescriptorId: int
    AssociationId: int | None = None


# combine controls travel alongside operands without inferring output lifecycle
@Dataclass(frozen=True, slots=True)
class BodyInputs:
    Picks: tuple[BodyInput, ...]
    Operation: BooleanOp | None = None
    KeepTools: bool | None = None
