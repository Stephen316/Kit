# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from struct import pack as PackFields

from JournalAttach import EncodeJournal, JournalAttach, ReadJournal
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor


# the four empty lists expose the end of the notebook before the outer definition resumes
def ReadNotebook(BlobValue: bytes, Offset: int) -> tuple[JournalAttach, int]:
    Attachment, BodyOffset = ReadJournal(BlobValue, Offset)
    Cursor = FieldCursor(BlobValue, BodyOffset)
    RequireArch(Cursor.ReadInts("<H"), (0,), "empty first notebook list")
    RequireArch(Cursor.ReadInts("<i"), (1,), "initial first notebook state")
    RequireArch(Cursor.ReadInts("<H"), (0,), "empty second notebook list")
    RequireArch(Cursor.ReadInts("<i"), (1,), "initial second notebook state")
    RequireArch(Cursor.ReadInts("<2H"), (0, 0), "empty final notebook lists")
    return Attachment, Cursor.Offset


# a fresh notebook has empty collections and both constructor initialized fields
def EncodeNotebook(Attachment: JournalAttach) -> bytes:
    EmptyCount = 0
    InitialState = 1
    return EncodeJournal(Attachment) + PackFields(
        "<HiHiHH",
        EmptyCount,
        InitialState,
        EmptyCount,
        InitialState,
        EmptyCount,
        EmptyCount,
    )
