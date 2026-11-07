# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from io import BytesIO
from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import KSourceType
from convert.adapters.Fusion.ArchiveBounds import KArchiveLimit


# memory and stream sources share the parser bound while paths retain source identity
def ReadSourceMut(SourceData: KSourceType) -> str | FilePath | bytes:
    if isinstance(SourceData, (str, FilePath)):
        return SourceData
    if isinstance(SourceData, (bytes, bytearray)):
        if len(SourceData) > KArchiveLimit:
            raise ValueError("Fusion ZIP exceeds input size limit")
        return bytes(SourceData)
    Buffer = BytesIO()
    while True:
        Block = SourceData.read(min(65536, KArchiveLimit + 1 - Buffer.tell()))
        if not isinstance(Block, bytes):
            raise TypeError("Fusion F3D source must be a binary stream")
        if not Block:
            return Buffer.getvalue()
        if len(Block) > KArchiveLimit - Buffer.tell():
            raise ValueError("Fusion ZIP exceeds input size limit")
        Buffer.write(Block)
