# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as MakeDataClass

from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode


# five linked design records identify one sketch owned circle dimension
@MakeDataClass(frozen=True, slots=True)
class RadialBinding:
    Dimension: NativeNode
    Binding: NativeNode
    Parameter: NativeNode
    Update: NativeNode
    Circle: NativeNode
