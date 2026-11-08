# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import TYPE_CHECKING
from zipfile import BadZipFile

if TYPE_CHECKING:
    from convert.formats.Fusion.ArchiveRead.IndexedArchive import IndexedArchive

# native streams and evidence remain scoped to the same active asset
KDesignPrefix = "FusionAssetName[Active]/FusionDesignSegmentType1/"


# source projection and proof share the same mandatory member selection and errors
def ReadDesignPair(Archive: IndexedArchive) -> tuple[bytes, bytes]:
    Streams: list[bytes] = []
    try:
        for MemberName in ("BulkStream.dat", "MetaStream.dat"):
            Member = Archive.Entries.get(KDesignPrefix + MemberName)
            if Member is None or Member.is_dir():
                raise ValueError(f"Missing active Fusion design {MemberName}")
            Streams.append(Archive.ReadEntryMut(Member))
    except BadZipFile as ErrorInfo:
        raise ValueError("Invalid Fusion ZIP archive") from ErrorInfo
    except NotImplementedError as ErrorInfo:
        raise ValueError(
            "Fusion ZIP Zstandard requires a compatible codec"
        ) from ErrorInfo
    BulkData, MetaData = Streams
    return BulkData, MetaData
