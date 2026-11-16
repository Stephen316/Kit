# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as DataClass
from struct import pack as PackFields

from convert.adapters.solidworks.Container.Archive import (
    KDefinitionKind,
    EncodeClass,
    EncodeString,
    ReadTag,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor


# the attachment record has a smaller field boundary than its surrounding notebook
@DataClass(frozen=True, slots=True)
class JournalAttach:
    AttachmentName: str
    TimeWord: int
    StateWord: int


# first occurrence framing lets archive observations isolate the actual journal object
def ReadJournal(BlobValue: bytes, Offset: int) -> tuple[JournalAttach, int]:
    TagValue = ReadTag(BlobValue, Offset)
    RequireArch(
        (TagValue.kind, TagValue.class_name, TagValue.schema),
        (KDefinitionKind, "uoJournal_c", 0),
        "journal attachment class definition",
    )
    Cursor = FieldCursor(BlobValue, Offset + TagValue.size)
    AttachmentName = Cursor.ReadText()
    TimeWord, StateWord = Cursor.ReadInts("<ii")
    return JournalAttach(AttachmentName, TimeWord, StateWord), Cursor.Offset


# the archive experiment needs a standalone object derived from explicit fields
def EncodeJournal(Attachment: JournalAttach) -> bytes:
    return (
        EncodeClass("uoJournal_c", 0)
        + EncodeString(Attachment.AttachmentName)
        + PackFields("<ii", Attachment.TimeWord, Attachment.StateWord)
    )
