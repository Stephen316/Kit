from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime as DateTime

from tools.TestShards.Reuse.Cache.ReadTexts import ReadTexts
from tools.TestShards.Reuse.Cache.ReusableOutcomes import KReusableOutcomes
from tools.TestShards.Reuse.Cache.TreeIndex import TreeIndex


def MatchEntry(
    ModKey: str,
    Entry: Mapping[str, object],
    Members: Sequence[str],
    TreeInfo: TreeIndex,
    Oldest: DateTime,
) -> dict[str, str] | None:
    Measured = DateTime.fromisoformat(str(Entry.get("MeasuredAt")))
    if Measured.tzinfo is None:
        raise ValueError(f"the test cache entry for {ModKey} has no time zone")
    Outcomes = ReadTexts(Entry.get("Outcomes"), ModKey)
    Files = ReadTexts(Entry.get("Files"), ModKey)
    Folders = ReadTexts(Entry.get("Folders"), ModKey)
    Results = {TestId: Outcomes.get(TestId, "missing") for TestId in Members}
    if Measured < Oldest or ModKey not in Files:
        return None
    if not KReusableOutcomes.issuperset(Results.values()):
        return None
    if any(
        TreeInfo.Blobs.get(PathText) != BlobId for PathText, BlobId in Files.items()
    ):
        return None
    if any(
        TreeInfo.Digests.get(PathText) != Digest for PathText, Digest in Folders.items()
    ):
        return None
    return Results
