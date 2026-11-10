# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.formats.Fusion.SegmentCodec.Browser.BrowserLayout import (
    KFolderSizes,
    KMaxLabelLength,
)
from convert.formats.Fusion.SegmentCodec.Browser.BrowserRefs import IsNativeId
from convert.formats.Fusion.SegmentCodec.Browser.BrowserRoot import (
    BrowserFolder,
    BrowserGroup,
)


# typed folder validation keeps both native group orders within their exact field bounds
def CheckGroups(Groups: tuple[BrowserGroup, ...]) -> None:
    if type(Groups) is not tuple or len(Groups) != len(KFolderSizes):
        raise ValueError("Invalid Fusion Browser group list")
    for Group in Groups:
        if (
            type(Group) is not BrowserGroup
            or (Group.ScopeId is not None and not IsNativeId(Group.ScopeId))
            or type(Group.Folders) is not tuple
            or len(Group.Folders) not in KFolderSizes
        ):
            raise ValueError("Invalid Fusion Browser group")
        for Folder in Group.Folders:
            if (
                type(Folder) is not BrowserFolder
                or type(Folder.Label) is not str
                or not 0 < len(Folder.Label) <= KMaxLabelLength
                or not Folder.Label.isascii()
                or not Folder.Label.isprintable()
                or not IsNativeId(Folder.BrowserId)
            ):
                raise ValueError("Invalid Fusion Browser folder")
    if tuple(sorted(len(Group.Folders) for Group in Groups)) != KFolderSizes:
        raise ValueError("Invalid Fusion Browser folder list sizes")
