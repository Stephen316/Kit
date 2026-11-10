# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from collections.abc import Callable, Mapping
from zipfile import BadZipFile, ZipInfo
from zlib import error as InflateError

# native streams and evidence remain scoped to the same active asset
KDesignPrefix = "FusionAssetName[Active]/FusionDesignSegmentType1/"


# source projection and proof share the same mandatory member selection and errors
def ReadDesignPair(
    Entries: Mapping[str, ZipInfo], ReadEntry: Callable[[ZipInfo], bytes]
) -> tuple[bytes, bytes]:
    Streams: list[bytes] = []
    try:
        for MemberName in ("BulkStream.dat", "MetaStream.dat"):
            Member = Entries.get(KDesignPrefix + MemberName)
            if Member is None or Member.is_dir():
                raise ValueError(f"Missing active Fusion design {MemberName}")
            Streams.append(ReadEntry(Member))
    except (BadZipFile, InflateError) as ErrorInfo:
        raise ValueError("Invalid Fusion ZIP archive") from ErrorInfo
    except NotImplementedError as ErrorInfo:
        raise ValueError(
            "Fusion ZIP Zstandard requires a compatible codec"
        ) from ErrorInfo
    BulkData, MetaData = Streams
    return BulkData, MetaData
