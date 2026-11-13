from __future__ import annotations

from collections.abc import Mapping

from tools.TestShards.Reuse.Cache.TreeIndex import TreeIndex
from tools.TestShards.Reuse.Track.ModuleDeps import ModuleDeps


def BuildEntry(
    Closure: ModuleDeps,
    TreeInfo: TreeIndex,
    Outcomes: Mapping[str, str],
    Stamp: Mapping[str, str],
) -> dict[str, object] | str:
    if Closure.Opaque:
        return "started a process"
    if not Closure.Files.issubset(TreeInfo.Blobs):
        return "used files that git does not track"
    if not Closure.Folders.issubset(TreeInfo.Digests):
        return "listed folders that git does not track"
    return {
        **Stamp,
        "Outcomes": dict(sorted(Outcomes.items())),
        "Files": {
            PathText: TreeInfo.Blobs[PathText] for PathText in sorted(Closure.Files)
        },
        "Folders": {
            PathText: TreeInfo.Digests[PathText] for PathText in sorted(Closure.Folders)
        },
    }
