from __future__ import annotations

from pathlib import Path as FilePath

from AnalyzePull import AnalyzePull
from GitHubCli import CommentClient
from GitRunner import GitRunner
from PublishComment import PublishComment
from ReadHistory import FindDuplicate, IsSuperseded, ReadHistory
from Report.RenderReport import RenderReport
from Rules.RuleSet import RuleSet
from RunContext import BuildIdentity, ReadContext
from WriteOutputs import KOutputPath, KRequestPath, WriteJson, WriteOutputs

# root path needs a stable location so diff reporting resolves inputs independently of the caller working directory
KRootPath = FilePath(__file__).resolve().parents[3]

# config path needs a stable location so diff reporting resolves inputs independently of the caller working directory
KConfigPath = KRootPath / ".github" / "config"


# the report operation needs one orchestration boundary so published evidence stays bound to the reviewed revision
def RunReport(IsPublish: bool) -> None:
    Context = ReadContext()
    Rules = RuleSet(
        (KConfigPath / "DiffRules.txt").read_text(),
        (KConfigPath / "DiffBreakdown.json").read_text(),
    )
    Runner = GitRunner(KRootPath)
    Trusted = Runner.ReadText("rev-parse", "HEAD")
    IsTrusted = Context["EventName"] == "pull_request_target"
    if IsPublish and not (IsTrusted and Trusted == Context["TrustedSha"]):
        raise ValueError(
            "Publication requires the trusted pull_request_target revision"
        )
    Repository, PullNumber = str(Context["Repository"]), int(Context["Pull"])
    Client = CommentClient(Repository, PullNumber)
    History = (
        ReadHistory(Client.ListComments(), Repository, PullNumber) if IsPublish else []
    )
    IsDuplicate = FindDuplicate(History, str(Context["Head"])) is not None
    if IsPublish and (IsDuplicate or IsSuperseded(History, int(Context["RunNumber"]))):
        WriteJson(KOutputPath / "Status.json", {"Status": "duplicate_or_superseded"})
        return
    Previous = History[-1] if History else None
    Identity = BuildIdentity(Context, Trusted, Previous)
    Snapshot = AnalyzePull(Runner, Rules, Identity, Previous)
    Stored = WriteOutputs(Snapshot, RenderReport(Snapshot, Rules, Previous, History))
    if IsPublish:
        CommentId, Status = PublishComment(Client, Snapshot, KRequestPath, History)
        WriteJson(
            KOutputPath / "Snapshot.json",
            {**Stored, "CommentId": CommentId, "Publication": Status},
        )
    Totals = Snapshot["Totals"]
    print(
        f"Diff breakdown: {Totals['Lines']} changed lines across {Totals['Files']} files"
    )
