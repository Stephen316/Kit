from __future__ import annotations

import os as OsLib

from tools.TestShards.Reuse.Cache.DigestFolders import DigestFolders
from tools.TestShards.Reuse.Cache.TreeIndex import TreeIndex


def ReadTree(TreeBytes: bytes) -> TreeIndex:
    Blobs: dict[str, str] = {}
    for EntryBytes in TreeBytes.split(b"\0"):
        if not EntryBytes:
            continue
        Header, _, PathBytes = EntryBytes.partition(b"\t")
        FieldList = Header.split(b" ")
        if len(FieldList) != 3 or not PathBytes:
            raise ValueError("the git tree listing has a malformed entry")
        Blobs[OsLib.fsdecode(PathBytes)] = FieldList[2].decode("ascii")
    if not Blobs:
        raise ValueError("the git tree listing is empty")
    return TreeIndex(Blobs, DigestFolders(Blobs))
