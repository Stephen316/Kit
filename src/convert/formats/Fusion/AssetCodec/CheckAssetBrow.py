# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.AssetCodec.CheckAssetGroups import CheckBrowGroups
from convert.formats.Fusion.AssetCodec.CheckAssetRoutes import CheckBrowRoutes
from convert.formats.Fusion.AssetCodec.SegmentFrame import SegmentFrame
from convert.formats.Fusion.SegmentCodec.Browser.BrowserLayout import KMaxRootLength
from convert.formats.Fusion.SegmentCodec.Browser.ReadBrowserRoot import ReadBrowserRoot

# the root dictionary is distinct from the linked browser root node
KBrowserRecord = "33F72249-4935-47EB-8282-B2C3D93546CE"

# the linked design record is the active component browser root
KDesignRoot = "CE2913AA-CFE0-4F04-9102-24424ED3BCFA"

# the linked browser node reciprocates the active design root
KBrowserNode = "DBD7EE26-FC31-4777-A1D2-A72EB3C65DB9"


# a generated browser segment must link back to the same design and local roots
def CheckAssetBrow(Design: SegmentFrame, Browser: SegmentFrame) -> None:
    Record = Browser.Owners.get(0)
    if (
        Record is None
        or (Record.ClassGuid, Record.ClassSpace) != (KBrowserRecord, "Fusion")
        or Record.EndOffset - Record.PayloadOffset > KMaxRootLength
        or sum(Value.ClassGuid == KBrowserRecord for Value in Browser.Spans) != 1
    ):
        raise ValueError("Missing or ambiguous Fusion asset Browser root dictionary")
    RootValue = ReadBrowserRoot(
        Browser.BulkData[Record.PayloadOffset : Record.EndOffset]
    )
    DesignRoot = Design.Owners.get(RootValue.DesignRootId)
    BrowserRoot = Browser.Owners.get(RootValue.BrowserRootId)
    if (
        DesignRoot is None
        or BrowserRoot is None
        or (DesignRoot.ClassGuid, DesignRoot.ClassSpace) != (KDesignRoot, "Component")
        or (BrowserRoot.ClassGuid, BrowserRoot.ClassSpace) != (KBrowserNode, "Fusion")
    ):
        raise ValueError("Missing typed Fusion asset Browser roots")
    CheckBrowRoutes(RootValue, Design, Browser)
    CheckBrowGroups(RootValue, Design, Browser)
