from __future__ import annotations

import subprocess as Subprocess

from CollectFiles import CollectFiles
from GitRunner import GitRunner
from Rules.RuleSet import RuleSet
from SummarizeFiles import SummarizeFiles

KPushGap = (
    "The previous head could not be fetched, so the actual push diff is unavailable. "
    "Full PR composition and historical snapshot deltas are still shown."
)


def AnalyzePull(
    Runner: GitRunner,
    Rules: RuleSet,
    Identity: dict[str, object],
    Previous: dict[str, object] | None,
) -> dict[str, object]:
    BaseSha, HeadSha = str(Identity["Base"]), str(Identity["Head"])
    Runner.FetchCommit(BaseSha)
    Runner.FetchCommit(HeadSha)
    MergeBase = Runner.FindMergeBase(BaseSha, HeadSha)
    FileList = CollectFiles(Runner, MergeBase, HeadSha, Rules)
    Snapshot = {
        **Identity,
        "MergeBase": MergeBase,
        "RulesVersion": Rules.Version,
        "Files": FileList,
        **SummarizeFiles(FileList),
        "PreviousHead": Previous["Head"] if Previous else None,
        "PushFiles": [],
        "PushLimit": None,
        "Rewritten": False,
    }
    if Previous is None:
        return Snapshot
    OldHead = str(Previous["Head"])
    try:
        Runner.FetchCommit(OldHead)
    except (Subprocess.SubprocessError, OSError):
        return {**Snapshot, "PushLimit": KPushGap}
    return {
        **Snapshot,
        "Rewritten": not Runner.IsAncestor(OldHead, HeadSha),
        "PushFiles": CollectFiles(Runner, OldHead, HeadSha, Rules),
    }
