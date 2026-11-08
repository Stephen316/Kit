# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from struct import pack as PackValue

from convert.formats.Fusion.AssetCodec.BrowserFolders import KDocFolder, KFolderClasses
from convert.formats.Fusion.AssetCodec.SegmentFrame import SegmentFrame
from convert.formats.Fusion.SegmentCodec.Browser.BrowserRoot import BrowserRoot

# a scoped group belongs to the registered design browser scope record
KScopeClass = "596C8B98-D176-4E40-B294-6404BAD566BC"


# named folders must resolve to records with their exact typed role and counted label
def CheckBrowGroups(
    RootValue: BrowserRoot, Design: SegmentFrame, Browser: SegmentFrame
) -> None:
    Found: set[str] = set()
    for GroupValue in RootValue.Groups:
        IsScoped = GroupValue.ScopeId is not None
        if IsScoped != (len(GroupValue.Folders) == 5):
            raise ValueError("Fusion asset Browser folder group scope disagrees")
        if IsScoped:
            Scope = Design.Owners.get(GroupValue.ScopeId)
            if Scope is None or (Scope.ClassGuid, Scope.ClassSpace) != (
                KScopeClass,
                "Component",
            ):
                raise ValueError("Missing Fusion asset Browser folder scope")
        for Folder in GroupValue.Folders:
            FolderSpan = Browser.Owners.get(Folder.BrowserId)
            Expected = KFolderClasses.get(Folder.Label)
            ClassSpace = "BrowserAddInIdentifier" if IsScoped else "Fusion"
            Signature = (
                PackValue("<I", len(Folder.Label))
                + Folder.Label.encode("ascii")
                + bytes(4)
            )
            if (
                Folder.Label in Found
                or IsScoped == (Folder.Label == KDocFolder)
                or FolderSpan is None
                or FolderSpan.ClassGuid != Expected
                or FolderSpan.ClassSpace != ClassSpace
                or not Browser.BulkData.endswith(
                    Signature, FolderSpan.PayloadOffset, FolderSpan.EndOffset
                )
            ):
                raise ValueError("Fusion asset Browser folder role or label disagrees")
            Found.add(Folder.Label)
