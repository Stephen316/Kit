from __future__ import annotations

from collections.abc import Mapping


# the list conftests contract needs a shared interpretation so dependency changes cannot revive stale passing results
def ListConftests(ModKey: str, Blobs: Mapping[str, str]) -> list[str]:
    Parts = ModKey.split("/")[:-1]
    Candidates = [
        "/".join([*Parts[:Count], "conftest.py"]) for Count in range(len(Parts) + 1)
    ]
    return [PathText for PathText in Candidates if PathText in Blobs]
