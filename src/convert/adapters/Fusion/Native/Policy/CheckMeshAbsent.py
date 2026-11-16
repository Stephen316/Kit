# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.Fusion.Native.Graph.GraphChecks import RequireFields
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.Formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.Formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# an empty mesh scaffold must have the original defaults and direct component ownership
def CheckMeshAbsent(Graph: NativeGraph, Component: NativeNode) -> None:
    Groups = Graph.ByClass("ParaMeshBodies")
    Textures = Graph.ByClass("ParaMeshTextureStore")
    if not Groups and not Textures:
        return
    if (
        len(Groups) != 1
        or len(Textures) != 1
        or any(
            NodeValue.SegmentId != Component.SegmentId
            for NodeValue in Groups + Textures
        )
    ):
        raise ValueError("Native Fusion mesh scaffold ownership is ambiguous")
    Group = Groups[0]
    Texture = Textures[0]
    RequireFields(
        Group,
        {
            "creationIndex": 0,
            "isSelectable": True,
            "isVisible": True,
            "textureStore": LocalRef(Texture.ObjectId),
            "children": ValueSeries(()),
            "rParent": LocalRef(Component.ObjectId),
            "rClientObject": None,
        },
    )
    RequireFields(
        Texture,
        {"uuidToTextureInfoMap": ValueMap(()), "uuidToTextureMap": ValueMap(())},
    )
