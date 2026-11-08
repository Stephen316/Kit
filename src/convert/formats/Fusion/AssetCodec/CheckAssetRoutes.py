# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.AssetCodec.BrowserFolders import KDocFolder, KFolderClasses
from convert.formats.Fusion.AssetCodec.BrowserLinks import KBrowserLinks
from convert.formats.Fusion.AssetCodec.SegmentFrame import SegmentFrame
from convert.formats.Fusion.SegmentCodec.Browser.BrowserRefs import (
    KDesignLane,
    PackRouteRef,
)
from convert.formats.Fusion.SegmentCodec.Browser.BrowserRoot import BrowserRoot


# routing must select the typed design owner and its reciprocal browser reference
def CheckBrowRoutes(
    RootValue: BrowserRoot, Design: SegmentFrame, Browser: SegmentFrame
) -> None:
    Visited: set[int] = set()
    HasRoot = False
    for RouteValue in RootValue.Routes:
        Owner = Design.Owners.get(RouteValue.DesignId)
        Child = Browser.Owners.get(RouteValue.BrowserId)
        Layout = KBrowserLinks.get(Child.ClassGuid) if Child is not None else None
        if (
            RouteValue.BrowserId in Visited
            or Owner is None
            or Child is None
            or Layout is None
            or Owner.ClassGuid != Layout[0]
            or RouteValue.RouteFlag
            != int(Child.ClassGuid == KFolderClasses[KDocFolder])
        ):
            raise ValueError("Fusion asset Browser route classes disagree")
        Reference = PackRouteRef(RouteValue.DesignId, KDesignLane)
        if not Browser.BulkData.startswith(
            Reference, Child.PayloadOffset + Layout[1], Child.EndOffset
        ):
            raise ValueError("Fusion asset Browser route owner reference disagrees")
        Visited.add(RouteValue.BrowserId)
        HasRoot |= (
            RouteValue.DesignId == RootValue.DesignRootId
            and RouteValue.BrowserId == RootValue.BrowserRootId
            and RouteValue.RouteFlag == 0
        )
    if not HasRoot:
        raise ValueError("Missing Fusion asset Browser root route")
