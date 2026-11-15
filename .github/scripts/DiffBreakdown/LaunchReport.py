from __future__ import annotations

import argparse as Argparse

from GitHubCli import GhFailure
from RunReport import RunReport
from WriteOutputs import KOutputPath, WriteJson

# limit notice needs one explicit bound so diff reporting cannot accept inconsistent resource or layout limits
KLimitNotice = (
    "::warning::GitHub API rate limit reached; this head's diff breakdown was not "
    "published. The next push reports against the last published head."
)


# the report operation needs one orchestration boundary so published evidence stays bound to the reviewed revision
def LaunchReport() -> None:
    Parser = Argparse.ArgumentParser(description="Publish a PR diff breakdown")
    Parser.add_argument("--publish", action="store_true")
    Options = Parser.parse_args()
    try:
        RunReport(bool(Options.publish))
    except GhFailure as ErrorInfo:
        if not ErrorInfo.IsRateLimited():
            raise
        WriteJson(KOutputPath / "Status.json", {"Status": "rate_limited"})
        print(KLimitNotice)


if __name__ == "__main__":
    LaunchReport()
