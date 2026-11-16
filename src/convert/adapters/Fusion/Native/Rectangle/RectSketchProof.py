# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as MakeDataClass

from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from interchange.geometry.Models.Sketch import SketchRelation


# qualified rectangle records flow into strict policy and projection as the same exact graph members
@MakeDataClass(frozen=True, slots=True)
class RectSketchProof:
    Rules: tuple[NativeNode, ...]
    Dimensions: tuple[NativeNode, ...]
    Bindings: tuple[NativeNode, ...]
    Parameters: tuple[NativeNode, ...]
    Anchor: NativeNode
    Origin: NativeNode
    Relations: tuple[SketchRelation, ...]
