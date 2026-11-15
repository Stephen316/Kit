from __future__ import annotations

import hashlib as HashLib
from collections.abc import Iterable


# the digest folders contract needs a shared interpretation so dependency changes cannot revive stale passing results
def DigestFolders(PathList: Iterable[str]) -> dict[str, str]:
    Children: dict[str, set[str]] = {}
    for PathText in PathList:
        Parts = PathText.split("/")
        for Count in range(len(Parts)):
            Children.setdefault("/".join(Parts[:Count]), set()).add(Parts[Count])
    return {
        Folder: HashLib.sha256(
            "\n".join(sorted(Names)).encode("utf-8", "surrogateescape")
        ).hexdigest()
        for Folder, Names in Children.items()
    }
