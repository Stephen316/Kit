from __future__ import annotations

from GitRunner import GitRunner
from ParseDiff import ParseNumstat, ParseStatuses
from RequireSha import RequireSha
from Rules.RuleSet import RuleSet

KDiffOptions = (
    "diff",
    "--no-ext-diff",
    "--no-textconv",
    "--ignore-submodules=none",
    "--find-renames=50%",
)
KSpaceOptions = ("--ignore-all-space", "--ignore-blank-lines")


def CollectFiles(
    Runner: GitRunner, BaseSha: str, HeadSha: str, Rules: RuleSet
) -> list[dict[str, object]]:
    Revisions = (RequireSha(BaseSha), RequireSha(HeadSha), "--")
    RawData = Runner.RunGit(*KDiffOptions, "--numstat", "-z", *Revisions).stdout
    NameData = Runner.RunGit(*KDiffOptions, "--name-status", "-z", *Revisions).stdout
    SpaceData = Runner.RunGit(
        *KDiffOptions, "--numstat", "-z", *KSpaceOptions, *Revisions
    ).stdout
    StatusMap = ParseStatuses(NameData)
    Meaningful = {
        Entry[0]
        for Entry in ParseNumstat(SpaceData)
        if Entry[2] or Entry[3] or Entry[4]
    }
    FileList: list[dict[str, object]] = []
    for PathText, OldPath, AddCount, DelCount, IsBinary in ParseNumstat(RawData):
        StatusText = StatusMap[PathText]
        IsChanged = AddCount + DelCount > 0 and PathText not in Meaningful
        IsSpacing = not IsBinary and IsChanged and StatusText == "M"
        Details = Rules.Classify(PathText, IsBinary, IsSpacing)
        OldRisks = Rules.Classify(OldPath)["Risks"] if OldPath else []
        FileList.append(
            {
                "Path": PathText,
                "PreviousPath": OldPath,
                "Status": StatusText,
                "Additions": AddCount,
                "Deletions": DelCount,
                "Binary": IsBinary,
                **Details,
                "Risks": sorted({*Details["Risks"], *OldRisks}),
            }
        )
    return sorted(FileList, key=lambda Entry: str(Entry["Path"]))
